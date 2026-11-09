#!/usr/bin/env python3
"""Rebuild the library's model folders, index and brand consensus lists from upstream sources.

    python3 -I tools/build_index.py --cleanyourtv <path to cleanyourtv checkout> \
                                    --perflyst <path to PiHoleBlocklist checkout>

Run it from the library root. It only reads the upstream checkouts and writes inside this library:
  models/<platform>/<id>/      copied debloat*.txt, tv.json, README.md (MIT, see THIRD_PARTY.md)
  index/models.json, .csv      one row per tested model, plus brand-level rows for closed platforms
  index/MODELS.md              browsable table
  brands/<brand>/consensus.txt packages a brand's tested lists agree on, with counts
  dns/<brand>.txt              per-brand DNS blocklists cut from Perflyst's SmartTV list (MIT)
"""
import argparse
import csv
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+")
UPSTREAM_URL = "https://github.com/Gathin23/cleanyourtv/tree/main/examples/"

BRAND_ALIASES = {
    "amazon fire tv": "amazon", "insignia fire tv": "insignia", "nvidia shield": "nvidia",
    "anker nebula": "anker", "redmi": "xiaomi", "ffalcon": "tcl", "sharp": "sharp",
}

# Closed platforms: no shell, so one entry per brand/platform instead of per model.
CLOSED = [
    ("samsung", "Samsung", "samsung-tizen", "Tizen", "All Samsung smart TVs (2015+)"),
    ("lg", "LG", "lg-webos", "webOS", "All LG smart TVs (webOS 1-25)"),
    ("roku", "Roku / Roku TV (TCL, Hisense, Sharp, onn, Philips, Westinghouse...)", "roku", "Roku OS", "Roku TVs and Roku players"),
    ("vizio", "Vizio", "vizio-smartcast", "SmartCast / Vizio OS", "Vizio smart TVs"),
    ("hisense", "Hisense / Toshiba (VIDAA models)", "hisense-vidaa", "VIDAA", "Hisense and Toshiba sets running VIDAA"),
    ("panasonic", "Panasonic (My Home Screen)", "panasonic-mhs", "My Home Screen", "Panasonic 2014-2023 non-Fire TV sets"),
    ("philips", "Philips (Saphi)", "philips-saphi", "Saphi", "Cheaper Philips sets not running Android/Google TV"),
]


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def brand_slug(brand):
    b = brand.strip().lower()
    return slug(BRAND_ALIASES.get(b, b))


def platform_of(os_text):
    return "fire-os" if os_text.lower().startswith("fire") else "android-tv"


def read_list(text):
    """(disabled {pkg: note}) from a debloat list."""
    out = {}
    for line in text.splitlines():
        body, _, note = line.partition("#")
        body = body.strip()
        if not body:
            continue
        name = body.split()[0]
        if PACKAGE_RE.fullmatch(name):
            out[name] = note.strip()
    return out


def header_tokens(text):
    """Lowercased identifiers from a list's header comment (model, device, board names)."""
    head = "\n".join(l for l in text.splitlines()[:12] if l.startswith("#"))
    return sorted({t for t in re.findall(r"[a-z0-9][a-z0-9_\-]{2,}", head.lower()) if any(c.isdigit() for c in t)})


def import_models(cyt):
    rows, by_brand = [], defaultdict(list)
    ex = cyt / "examples"
    for tvj in sorted(ex.glob("*/tv.json")):
        folder = tvj.parent
        meta = json.loads(tvj.read_text(encoding="utf-8"))
        lists = sorted(folder.glob("debloat*.txt"))
        if not lists:
            continue
        platform = platform_of(meta.get("os", ""))
        dest = ROOT / "models" / platform / folder.name
        dest.mkdir(parents=True, exist_ok=True)
        for f in lists + [tvj] + [p for p in [folder / "README.md"] if p.exists()]:
            shutil.copyfile(f, dest / f.name)
        main = read_list(lists[0].read_text(encoding="utf-8-sig", errors="replace"))
        tokens = set(header_tokens(lists[0].read_text(encoding="utf-8-sig", errors="replace")))
        tokens |= {t for t in re.findall(r"[a-z0-9][a-z0-9\-]{2,}", (meta["tv"] + " " + folder.name).lower()) if any(c.isdigit() for c in t)}
        b = brand_slug(meta.get("brand", "unknown"))
        row = {
            "id": folder.name,
            "brand": meta.get("brand", ""),
            "brand_slug": b,
            "platform": platform,
            "os": meta.get("os", ""),
            "tv": meta["tv"],
            "method": "adb-disable",
            "lists": [str((dest / f.name).relative_to(ROOT)) for f in lists],
            "package_count": len(main),
            "notes": meta.get("notes", ""),
            "match_tokens": sorted(tokens),
            "status": "tested-by-submitter",
            "source": UPSTREAM_URL + folder.name,
        }
        rows.append(row)
        by_brand[b].append(main)
    return rows, by_brand


def write_consensus(by_brand, rows):
    meta = {r["brand_slug"]: r["brand"] for r in rows}
    for b, lists in sorted(by_brand.items()):
        counts, notes = Counter(), defaultdict(Counter)
        for lst in lists:
            for pkg, note in lst.items():
                counts[pkg] += 1
                if note:
                    notes[pkg][note] += 1
        n = len(lists)
        threshold = 1 if n == 1 else 2
        d = ROOT / "brands" / b
        d.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# {meta.get(b, b)}: packages disabled across {n} tested list(s) for this brand.",
            "# Use ONLY when your exact model has no list in models/. Generated by tools/build_index.py.",
            f"# A package appears here if at least {threshold} list(s) disabled it. The count is how many.",
            "# Higher count = more sets survived it. Still apply in batches and check after each reboot.",
            "# Format: <package>  # <count>/<lists> <most common note>",
            "",
        ]
        for pkg, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            if c < threshold:
                continue
            note = notes[pkg].most_common(1)[0][0] if notes[pkg] else ""
            lines.append(f"{pkg:<55} # {c}/{n} {note}".rstrip())
        (d / "consensus.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_dns(perflyst):
    """Split Perflyst SmartTV.txt into per-brand files. Commented domains are kept as warnings."""
    src = (perflyst / "SmartTV.txt").read_text(encoding="utf-8", errors="replace").splitlines()
    sections, current = defaultdict(list), None
    known = {"samsung": "samsung", "lg": "lg", "sony": "sony", "philips": "philips", "panasonic": "panasonic",
             "roku": "roku", "vizio": "vizio", "tcl": "tcl", "hisense": "hisense", "toshiba": "toshiba",
             "xiaomi": "xiaomi", "amazon": "amazon", "samba": "samba-acr", "alphonso": "alphonso-acr",
             "gamers nexus": "lg"}
    for line in src:
        s = line.strip()
        if s.startswith("# ") and not re.search(r"[a-z0-9-]+\.[a-z]{2,}", s.split()[1] if len(s.split()) > 1 else ""):
            low = s[2:].lower()
            hit = next((v for k, v in known.items() if low.startswith(k)), None)
            if hit:
                current = hit
                continue
        if current:
            sections[current].append(line)
    out = ROOT / "dns"
    out.mkdir(exist_ok=True)
    for name, lines in sections.items():
        active = [l.split("#")[0].strip() for l in lines if l.strip() and not l.strip().startswith("#")]
        warn = [l.strip() for l in lines if re.match(r"^#\s*[a-z0-9.-]+\.[a-z]{2,}", l.strip())]
        body = [f"# {name}: domains from Perflyst/PiHoleBlocklist SmartTV.txt (MIT). Generated, do not edit by hand.",
                "# Lines starting with '#<domain>' are NOT blocked on purpose: upstream reports they break apps,",
                "# updates or connectivity. Keep them commented.", ""]
        body += sorted(set(a for a in active if a))
        if warn:
            body += ["", "# --- deliberately left unblocked (upstream notes) ---"] + warn
        (out / f"{name}.txt").write_text("\n".join(body) + "\n", encoding="utf-8")
    return sorted(sections)


PLAYBOOK = {"panasonic-mhs": "other-closed", "philips-saphi": "other-closed"}


def closed_rows():
    return [{
        "id": f"{pid}-all", "brand": brand, "brand_slug": pid, "platform": plat, "os": os_name,
        "tv": desc, "method": "settings+dns", "lists": [], "package_count": 0,
        "notes": f"No shell access on {os_name}. Follow platforms/{PLAYBOOK.get(plat, plat)}.md: privacy toggles, boot-to-input, DNS blocklist.",
        "playbook": f"platforms/{PLAYBOOK.get(plat, plat)}.md",
        "match_tokens": [], "status": "playbook", "source": "",
    } for pid, brand, plat, os_name, desc in CLOSED]


def write_index(rows):
    idx = ROOT / "index"
    idx.mkdir(exist_ok=True)
    (idx / "models.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    with open(idx / "models.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "brand", "platform", "os", "tv", "method", "package_count", "status", "lists", "source"])
        for r in rows:
            w.writerow([r["id"], r["brand"], r["platform"], r["os"], r["tv"], r["method"], r["package_count"],
                        r["status"], ";".join(r["lists"]), r["source"]])
    by_brand = defaultdict(list)
    for r in rows:
        by_brand[r["brand_slug"]].append(r)
    md = ["# Model index", "",
          f"{sum(1 for r in rows if r['method'] == 'adb-disable')} tested model lists across "
          f"{len({r['brand_slug'] for r in rows if r['method'] == 'adb-disable'})} brands, plus playbooks for "
          f"{sum(1 for r in rows if r['method'] != 'adb-disable')} closed platforms. Generated by `tools/build_index.py`.", "",
          "Can't find your model? Run `python3 -I tools/tvlib.py match` with the TV connected, or use "
          "`brands/<brand>/consensus.txt`.", ""]
    for b in sorted(by_brand):
        md += [f"## {by_brand[b][0]['brand']}", "", "| Model | OS | Method | Packages | List |", "|---|---|---|---|---|"]
        for r in sorted(by_brand[b], key=lambda r: r["id"]):
            lst = f"`{r['lists'][0]}`" if r["lists"] else f"`{r['playbook']}`"
            tv = r["tv"].replace("|", "/")
            md.append(f"| {tv} | {r['os']} | {r['method']} | {r['package_count'] or '-'} | {lst} |")
        md.append("")
    (idx / "MODELS.md").write_text("\n".join(md), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cleanyourtv", required=True, type=Path)
    ap.add_argument("--perflyst", required=True, type=Path)
    a = ap.parse_args()
    for sub in ("models", "brands", "dns"):
        if (ROOT / sub).exists() and sub != "dns":
            shutil.rmtree(ROOT / sub)
    rows, by_brand = import_models(a.cleanyourtv)
    write_consensus(by_brand, rows)
    dns = write_dns(a.perflyst)
    rows += closed_rows()
    write_index(rows)
    print(f"models: {sum(1 for r in rows if r['lists'])}  brands with consensus: {len(by_brand)}  "
          f"closed-platform rows: {len(CLOSED)}  dns files: {', '.join(dns)}")


if __name__ == "__main__":
    sys.exit(main())
