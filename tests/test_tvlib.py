#!/usr/bin/env python3
"""End-to-end test of tools/tvlib.py against tests/fake_adb.py. Run: python3 -I tests/test_tvlib.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TV = "10.9.9.9:5555"


def run(*args, ok=True):
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "tvlib.py"), "--host", TV, *args],
                       capture_output=True, text=True, env=os.environ)
    if ok and r.returncode != 0:
        raise AssertionError(f"{args} -> {r.returncode}\n{r.stdout}\n{r.stderr}")
    return r


def tv_state():
    return json.load(open(os.environ["FAKE_ADB_STATE"]))


def main():
    idx = json.loads((ROOT / "index" / "models.json").read_text())
    row = next(r for r in idx if r["brand_slug"] == "tcl" and r["platform"] == "android-tv" and r["package_count"] >= 15)
    lst = ROOT / row["lists"][0]
    sys.path.insert(0, str(ROOT / "tools"))
    import tvlib
    model_pkgs = tvlib.read_list(lst)
    extra = ["android", "com.android.systemui", "com.android.tv.settings", "com.google.android.apps.tv.launcherx",
             "com.google.android.tungsten.setupwraith", "com.google.android.inputmethod.latin", "com.google.android.gms"]
    tmp = Path(tempfile.mkdtemp())
    state = tmp / "tv.json"
    state.write_text(json.dumps({
        "packages": sorted(set(model_pkgs + extra)), "disabled": [], "unsaved": [],
        "props": {"ro.product.brand": "TCL", "ro.product.manufacturer": "TCL", "ro.product.model": row["id"]},
        "home": "com.google.android.apps.tv.launcherx",
        "home_candidates": ["com.google.android.apps.tv.launcherx", "com.google.android.tungsten.setupwraith"],
    }))
    wrapper = tmp / "adb"
    wrapper.write_text(f"#!/bin/sh\nexec {sys.executable} -I {ROOT / 'tests' / 'fake_adb.py'} \"$@\"\n")
    wrapper.chmod(0o755)
    os.environ.update(TVLIB_ADB=str(wrapper), FAKE_ADB_STATE=str(state))
    statedir = ROOT / "state" / "10.9.9.9_5555"
    shutil.rmtree(statedir, ignore_errors=True)

    assert "connected" in run("connect").stdout
    probe = json.loads(run("probe").stdout)
    assert probe["platform"].startswith("android-tv (Google TV)"), probe

    m = run("match").stdout
    assert row["lists"][0] in m.splitlines()[2], f"own list should rank first:\n{m}"

    # apply refuses before a backup
    r = run("apply", str(lst), "--yes", "--no-settle", ok=False)
    assert r.returncode != 0 and "backup" in (r.stderr + r.stdout)
    run("backup")

    # a list that names core / Home / keyboard packages must skip them
    bad = tmp / "bad.txt"
    bad.write_text("android\ncom.android.systemui\ncom.google.android.apps.tv.launcherx\n"
                   "com.google.android.tungsten.setupwraith\ncom.google.android.inputmethod.latin\n")
    out = run("plan", str(bad)).stdout
    assert "Nothing left" in out and "core Android" in out and "owns Home" in out and "--launcher-ready" in out, out

    # dry run changes nothing
    run("apply", str(lst))
    assert tv_state()["disabled"] == []

    # batches of 10, one per call
    run("apply", str(lst), "--yes", "--no-settle")
    first = set(tv_state()["disabled"])
    assert 0 < len(first) <= 10, first
    run("apply", str(lst), "--yes", "--no-settle")
    assert len(tv_state()["disabled"]) > len(first)

    # verify passes, then simulate a firmware update re-enabling one package
    assert run("verify").returncode == 0
    st = tv_state(); victim = sorted(first)[0]; st["disabled"].remove(victim); state.write_text(json.dumps(st))
    r = run("verify", ok=False)
    assert r.returncode == 1 and victim in r.stdout

    # restore last batch, then everything
    before = set(tv_state()["disabled"])
    run("restore", "--last-batch")
    assert set(tv_state()["disabled"]) < before
    run("restore", "--all")
    assert tv_state()["disabled"] == []

    # dns export
    out = run("dns", "samsung", "--format", "hosts").stdout.splitlines()
    assert out and all(l.startswith("0.0.0.0 ") for l in out)

    shutil.rmtree(statedir, ignore_errors=True)
    print(f"OK  (model {row['id']}, {len(model_pkgs)} packages in its list)")


if __name__ == "__main__":
    main()
