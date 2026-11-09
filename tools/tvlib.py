#!/usr/bin/env python3
"""tvlib: probe, match, back up, debloat and restore an Android TV / Google TV / Fire TV over ADB.

Every change is `pm disable-user --user 0` (reversible), logged, and applied one batch at a time.

    export TV_HOST=192.168.1.50            # or pass --host on every command
    python3 -I tools/tvlib.py connect
    python3 -I tools/tvlib.py probe        # who is this TV, which platform
    python3 -I tools/tvlib.py match        # best tested lists for it, ranked by package overlap
    python3 -I tools/tvlib.py backup       # snapshot before changing anything
    python3 -I tools/tvlib.py plan  models/android-tv/<id>/debloat.txt
    python3 -I tools/tvlib.py apply models/android-tv/<id>/debloat.txt --yes   # ONE batch, then stops
    python3 -I tools/tvlib.py verify       # still disabled after reboot? Home still OK?
    python3 -I tools/tvlib.py restore --last-batch | --all | <pkg> ...
    python3 -I tools/tvlib.py dns samsung --format hosts

Set TVLIB_ADB to use a different adb binary (the tests use a fake one).
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
PACKAGE_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+")

# Core Android packages that no list may disable: with one of these off, Android can stop booting.
# Pattern from cleanyourtv tools/recovery.py (MIT), see THIRD_PARTY.md.
CORE_RE = re.compile(
    r"^(android|android\.ext\.(services|shared)|com\.android\.sdksandbox|com\.android\.location\.fused|"
    r"com\.android\.systemui|com\.android\.shell|com\.android\.phone|com\.android\.settings|com\.android\.tv\.settings|"
    r"com\.(google\.)?android\.(permissioncontroller|packageinstaller|ext\.services|ext\.shared|modulemetadata)|"
    r"com\.google\.android\.overlay\.modules.*|com\.android\.providers\..*|com\.cltv\.mal|"
    r"com\.mediatek\.(tis|tv\.service|tv\.agent))$")
CORE_OK = re.compile(r"^com\.android\.providers\.(calendar|contacts|userdictionary|blockednumber)$")

# Disabling these is only safe once a replacement launcher is installed and owns Home.
HOME_GATED = {
    "com.google.android.apps.tv.launcherx", "com.google.android.tvlauncher",
    "com.google.android.leanbacklauncher", "com.google.android.tungsten.setupwraith",
    "com.mitv.tvhome.atv", "com.amazon.tv.launcher", "com.amazon.firebat",
}

# Always kept unless the person explicitly lists them with --force: inputs, remote, keyboard, updates, Play.
KEEP_RE = re.compile(
    r"(inputmethod|\.ime$|keyboard|\.tvinput$|\.tv\.inputs?$|\.inputs$|remote|_rcu_|bluetooth|autopair|"
    r"updater|\.ota$|\.ota\.|otaupdate|otaservice|usbupgrade|systemupdate|fwupdate|updateservice|com\.google\.android\.gms$|com\.google\.android\.gsf$|"
    r"com\.android\.vending$|com\.google\.android\.tts$|livetv|com\.android\.tv$|com\.tcl\.tv$|"
    r"com\.tcl\.suspension$|com\.tcl\.ttvs$)", re.I)

BATCH = 10
SETTLE_SECONDS = 60  # some sets lose a disable if rebooted sooner (seen on Hisense, OnePlus)


# ---------------------------------------------------------------- adb plumbing

def adb_bin():
    exe = os.environ.get("TVLIB_ADB") or shutil.which("adb")
    if not exe:
        sys.exit("adb not found. macOS: brew install android-platform-tools | Debian/Ubuntu: sudo apt install adb | "
                 "Windows: Google's SDK platform-tools, then add it to PATH.")
    return exe


def host_of(args):
    h = args.host or os.environ.get("TV_HOST")
    if not h:
        sys.exit("No TV given: pass --host <ip[:port]> or set TV_HOST.")
    return h if ":" in h else f"{h}:5555"


def adb(host, *cmd, check=True, timeout=60):
    r = subprocess.run([adb_bin(), "-s", host, *cmd], capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        sys.exit(f"adb {' '.join(cmd)} failed: {(r.stderr or r.stdout).strip()}")
    return r.stdout


def sh(host, command, check=True):
    return adb(host, "shell", command, check=check)


def packages(host, flag=""):
    out = sh(host, f"pm list packages {flag}".strip())
    return {l.split(":", 1)[1].strip() for l in out.splitlines() if l.startswith("package:")}


def home_packages(host):
    """Package that currently owns Home, and every package that can answer the Home intent."""
    cur = sh(host, "cmd package resolve-activity --brief -a android.intent.action.MAIN "
                   "-c android.intent.category.HOME", check=False).strip().splitlines()
    current = cur[-1].split("/")[0] if cur and "/" in cur[-1] else ""
    q = sh(host, "cmd package query-activities --brief -a android.intent.action.MAIN "
                 "-c android.intent.category.HOME", check=False)
    answers = {l.strip().split("/")[0] for l in q.splitlines() if "/" in l}
    return current, answers


def state_dir(host):
    d = STATE / re.sub(r"[^A-Za-z0-9_.-]", "_", host)
    d.mkdir(parents=True, exist_ok=True)
    return d


def log_event(host, **event):
    event["ts"] = dt.datetime.now().isoformat(timespec="seconds")
    with open(state_dir(host) / "log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def read_log(host):
    p = state_dir(host) / "log.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def read_list(path):
    names = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        body = line.split("#", 1)[0].strip()
        if not body:
            continue
        name = body.split()[0]
        if not (PACKAGE_RE.fullmatch(name) or name == "android"):
            sys.exit(f"{path}:{n}: not a package name: {name!r}. Nothing was sent to the TV.")
        names.append(name)
    return names


# ---------------------------------------------------------------- commands

PROPS = ["ro.product.brand", "ro.product.manufacturer", "ro.product.model", "ro.product.device",
         "ro.product.name", "ro.build.product", "ro.board.platform", "ro.build.version.release",
         "ro.build.version.sdk", "ro.build.version.incremental", "ro.build.fingerprint"]


def cmd_connect(a):
    host = host_of(a)
    r = subprocess.run([adb_bin(), "connect", host], capture_output=True, text=True, timeout=30)
    out = (r.stdout + r.stderr).strip()
    print(out)
    if "connected" not in out or "unable" in out or "failed" in out:
        print("If the TV shows 'Allow USB debugging?', accept it (tick 'Always allow') and run connect again.\n"
              "Android 11+ with Wireless debugging: run `adb pair <ip>:<pair-port>` with the code on screen first.")
        return 1
    return 0


def detect_platform(props, pkgs):
    man = (props.get("ro.product.manufacturer", "") + props.get("ro.product.brand", "")).lower()
    if "amazon" in man or "com.amazon.tv.launcher" in pkgs:
        return "fire-os"
    if "com.google.android.apps.tv.launcherx" in pkgs:
        return "android-tv (Google TV)"
    return "android-tv"


def cmd_probe(a):
    host = host_of(a)
    props = {p: sh(host, f"getprop {p}", check=False).strip() for p in PROPS}
    pkgs = packages(host)
    current, answers = home_packages(host)
    info = {"host": host, "platform": detect_platform(props, pkgs), "props": props,
            "package_count": len(pkgs), "home": current, "home_candidates": sorted(answers)}
    d = state_dir(host)
    (d / "probe.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    (d / "packages.txt").write_text("\n".join(sorted(pkgs)) + "\n", encoding="utf-8")
    print(json.dumps(info, indent=1))
    return 0


def load_index():
    return json.loads((ROOT / "index" / "models.json").read_text(encoding="utf-8"))


def cmd_match(a):
    host = host_of(a) if (a.host or os.environ.get("TV_HOST")) and not a.packages_file else None
    if a.packages_file:
        installed = {l.split(":", 1)[-1].strip() for l in Path(a.packages_file).read_text().splitlines() if l.strip()}
        props = {}
    else:
        installed = packages(host)
        props = {p: sh(host, f"getprop {p}", check=False).strip().lower() for p in PROPS[:6]}
    ident = {t for v in props.values() for t in re.findall(r"[a-z0-9][a-z0-9_\-]{2,}", v)}
    brand = props.get("ro.product.brand", "") or props.get("ro.product.manufacturer", "")
    scored = []
    for row in load_index():
        if not row["lists"]:
            continue
        lst = set(read_list(ROOT / row["lists"][0]))
        overlap = len(lst & installed) / len(lst) if lst else 0
        tok = len(ident & set(row["match_tokens"]))
        same_brand = bool(brand) and (brand in row["brand"].lower() or row["brand_slug"] in brand)
        score = overlap + 0.15 * min(tok, 3) + (0.1 if same_brand else 0)
        scored.append((score, overlap, tok, row))
    scored.sort(key=lambda s: -s[0])
    print(f"{'score':>5} {'overlap':>7} {'id-hits':>7}  model / list")
    for score, overlap, tok, row in scored[: a.top]:
        print(f"{score:5.2f} {overlap:7.0%} {tok:7d}  {row['tv']}\n{'':22}{row['lists'][0]}")
    best = scored[0] if scored else None
    if not best or best[1] < 0.6:
        print("\nNo strong match (<60% of the best list's packages are on this TV). Use "
              "brands/<brand>/consensus.txt as a starting point and review every line with the owner.")
    elif best[2] == 0:
        print("\nBest match shares packages but not model identifiers: likely a sibling model. "
              "Review the list before applying.")
    return 0


def cmd_backup(a):
    host = host_of(a)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    d = state_dir(host) / f"backup-{stamp}"
    d.mkdir(parents=True)
    for name, flag in [("all", ""), ("system", "-s"), ("disabled", "-d"), ("third-party", "-3")]:
        (d / f"packages-{name}.txt").write_text("\n".join(sorted(packages(host, flag))) + "\n", encoding="utf-8")
    for ns in ("global", "secure", "system"):
        (d / f"settings-{ns}.txt").write_text(sh(host, f"settings list {ns}", check=False), encoding="utf-8")
    current, answers = home_packages(host)
    (d / "home.txt").write_text(f"current={current}\ncandidates={','.join(sorted(answers))}\n", encoding="utf-8")
    (d / "meminfo.txt").write_text(sh(host, "dumpsys meminfo", check=False)[:200000], encoding="utf-8")
    log_event(host, action="backup", path=str(d.relative_to(ROOT)))
    print(f"Backup written to {d.relative_to(ROOT)}  (packages, settings, home, meminfo)")
    return 0


def build_plan(a, host):
    wanted = []
    for f in a.lists:
        for p in read_list(f):
            if p not in wanted:
                wanted.append(p)
    keep = set(a.keep or [])
    if a.keep_file:
        keep |= set(read_list(a.keep_file))
    force = set(a.force or [])
    installed, disabled = packages(host), packages(host, "-d")
    current_home, home_answers = home_packages(host)
    todo, skipped = [], []
    for p in wanted:
        if CORE_RE.match(p) and not CORE_OK.match(p):
            skipped.append((p, "core Android package: never disabled"))
        elif p not in installed:
            skipped.append((p, "not on this TV"))
        elif p in disabled:
            skipped.append((p, "already disabled"))
        elif p in keep:
            skipped.append((p, "owner asked to keep"))
        elif p == current_home:
            skipped.append((p, "currently owns Home: install and select a new launcher first"))
        elif (p in HOME_GATED or p in home_answers) and not a.launcher_ready:
            skipped.append((p, "launcher/Home package: only with --launcher-ready"))
        elif KEEP_RE.search(p) and p not in force:
            skipped.append((p, "looks like input/remote/keyboard/update/Play: pass --force <pkg> to override"))
        else:
            todo.append(p)
    done = {e["pkg"] for e in read_log(host) if e.get("action") == "disable" and e.get("ok")}
    return todo, skipped, done


def print_plan(todo, skipped, batch):
    for p, why in skipped:
        print(f"  skip  {p:<55} {why}")
    batches = [todo[i:i + batch] for i in range(0, len(todo), batch)]
    for i, b in enumerate(batches, 1):
        print(f"\nBatch {i}/{len(batches)}:")
        for p in b:
            print(f"  disable {p}")
    if not todo:
        print("\nNothing left to disable from these lists.")
    return batches


def cmd_plan(a):
    host = host_of(a)
    todo, skipped, _ = build_plan(a, host)
    print_plan(todo, skipped, a.batch)
    return 0


def cmd_apply(a):
    host = host_of(a)
    if not any(e.get("action") == "backup" for e in read_log(host)):
        sys.exit("No backup recorded for this TV. Run `tvlib.py backup` first.")
    todo, skipped, _ = build_plan(a, host)
    batches = print_plan(todo, skipped, a.batch)
    if not batches:
        return 0
    batch = batches[0]
    if not a.yes:
        print("\nDry run. Re-run with --yes to disable batch 1 only.")
        return 0
    batch_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"\nApplying batch {batch_id} ({len(batch)} packages)...")
    for p in batch:
        out = sh(host, f"pm disable-user --user 0 {p}", check=False).strip()
        ok = "disabled" in out
        log_event(host, action="disable", pkg=p, batch=batch_id, ok=ok, out=out)
        print(f"  {'ok ' if ok else 'ERR'} {p}  {out}")
    if a.no_settle:
        wait = 0
    else:
        wait = SETTLE_SECONDS
        print(f"Waiting {wait}s so the TV saves the state before any reboot...")
        time.sleep(wait)
    if a.reboot_check:
        print("Rebooting to check the batch sticks...")
        adb(host, "reboot", check=False)
        time.sleep(5)
        for _ in range(60):
            if subprocess.run([adb_bin(), "connect", host], capture_output=True, text=True).returncode == 0 and \
               sh(host, "getprop sys.boot_completed", check=False).strip() == "1":
                break
            time.sleep(5)
        cmd_verify(a)
    left = len(batches) - 1
    print(f"\nBatch done. {left} batch(es) left.\nNOW CHECK ON THE TV: Home button, Inputs/HDMI switching, remote, "
          "sound, Wi-Fi, on-screen keyboard, the owner's streaming apps.\nAll fine -> run apply again. "
          "Anything broken -> `tvlib.py restore --last-batch`.")
    return 0


def cmd_verify(a):
    host = host_of(a)
    log = read_log(host)
    wanted = {}
    for e in log:
        if e.get("action") == "disable" and e.get("ok"):
            wanted[e["pkg"]] = True
        if e.get("action") == "enable":
            wanted.pop(e["pkg"], None)
    disabled = packages(host, "-d")
    drift = sorted(p for p in wanted if p not in disabled)
    current, _ = home_packages(host)
    print(f"Logged disabled: {len(wanted)}  still disabled: {len(wanted) - len(drift)}  Home: {current or '?'}")
    for p in drift:
        print(f"  RE-ENABLED (firmware update or reboot too soon): {p}")
    if drift:
        print("Re-apply with: tvlib.py apply <list> --yes   (the plan only picks up what is enabled again)")
    log_event(host, action="verify", drift=drift, home=current)
    return 1 if drift else 0


def cmd_restore(a):
    host = host_of(a)
    log = read_log(host)
    disables = [e for e in log if e.get("action") == "disable" and e.get("ok")]
    if a.packages:
        targets = a.packages
    elif a.last_batch:
        if not disables:
            sys.exit("Nothing logged to restore.")
        last = disables[-1]["batch"]
        targets = [e["pkg"] for e in disables if e["batch"] == last]
    elif a.all:
        targets = list(dict.fromkeys(e["pkg"] for e in disables))
    else:
        sys.exit("Say what to restore: --last-batch, --all, or package names.")
    for p in reversed(targets):
        out = sh(host, f"pm enable {p}", check=False).strip()
        log_event(host, action="enable", pkg=p, out=out)
        print(f"  enable {p}  {out}")
    print(f"Re-enabled {len(targets)} package(s). Reboot the TV and check it.")
    return 0


def cmd_dns(a):
    f = ROOT / "dns" / f"{a.brand.lower()}.txt"
    if not f.exists():
        sys.exit(f"No DNS list for {a.brand}. Available: {', '.join(sorted(p.stem for p in (ROOT / 'dns').glob('*.txt')))}")
    for line in f.read_text(encoding="utf-8").splitlines():
        d = line.strip()
        if not d or d.startswith("#"):
            continue
        print({"hosts": f"0.0.0.0 {d}", "adguard": f"||{d}^", "plain": d}[a.format])
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", help="TV address ip[:port] (default: $TV_HOST, port 5555)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("connect")
    sub.add_parser("probe")
    m = sub.add_parser("match")
    m.add_argument("--packages-file", help="offline: a saved `pm list packages` instead of a live TV")
    m.add_argument("--top", type=int, default=5)
    sub.add_parser("backup")
    for name in ("plan", "apply"):
        p = sub.add_parser(name)
        p.add_argument("lists", nargs="+", help="debloat list file(s)")
        p.add_argument("--keep", nargs="*", help="packages the owner wants left on")
        p.add_argument("--keep-file")
        p.add_argument("--force", nargs="*", help="override the input/remote/keyboard/update guard for these")
        p.add_argument("--launcher-ready", action="store_true",
                       help="a replacement launcher is installed and selected; allow stock Home packages")
        p.add_argument("--batch", type=int, default=BATCH)
        if name == "apply":
            p.add_argument("--yes", action="store_true", help="actually disable (otherwise dry run)")
            p.add_argument("--reboot-check", action="store_true", help="reboot after the batch and verify")
            p.add_argument("--no-settle", action="store_true", help="skip the 60 s wait (tests only)")
    sub.add_parser("verify")
    r = sub.add_parser("restore")
    r.add_argument("packages", nargs="*")
    r.add_argument("--last-batch", action="store_true")
    r.add_argument("--all", action="store_true")
    d = sub.add_parser("dns")
    d.add_argument("brand")
    d.add_argument("--format", choices=["hosts", "adguard", "plain"], default="plain")
    a = ap.parse_args()
    return globals()[f"cmd_{a.cmd}"](a)


if __name__ == "__main__":
    sys.exit(main() or 0)
