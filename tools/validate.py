#!/usr/bin/env python3
"""Check every model list and the index. Runs in CI on every pull request.

    python3 -I tools/validate.py

Fails (exit 1) on: a list that does not parse, a list that disables a core Android package, a tv.json
missing fields, a community model whose id clashes with an upstream one, an index entry pointing at a
missing file, or a community list without the required header lines.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import tvlib  # noqa: E402

REQUIRED_TV = ("tv", "os", "brand", "notes")
PLATFORMS = ("android-tv", "fire-os")
COMMUNITY_HEADER = ("ro.product.model", "firmware", "tested")  # words a community header must mention


def check_list(path, errors, community):
    text = path.read_text(encoding="utf-8-sig")
    try:
        names = []
        for n, line in enumerate(text.splitlines(), 1):
            body = line.split("#", 1)[0].strip()
            if not body:
                continue
            name = body.split()[0]
            if not (tvlib.PACKAGE_RE.fullmatch(name) or name == "android"):
                errors.append(f"{path}:{n}: not a package name: {name!r}")
            names.append(name)
    except UnicodeDecodeError:
        errors.append(f"{path}: not UTF-8")
        return
    if not names:
        errors.append(f"{path}: no packages")
    for name in names:
        if tvlib.CORE_RE.match(name) and not tvlib.CORE_OK.match(name):
            errors.append(f"{path}: disables core Android package {name} (never allowed)")
    if len(names) != len(set(names)):
        errors.append(f"{path}: duplicate package lines")
    if community:
        head = "\n".join(l for l in text.splitlines()[:30] if l.startswith("#")).lower()
        for word in COMMUNITY_HEADER:
            if word not in head:
                errors.append(f"{path}: header must mention '{word}' (see CONTRIBUTING.md)")


def check_folder(folder, errors, community):
    tvj = folder / "tv.json"
    if not tvj.exists():
        errors.append(f"{folder}: missing tv.json")
        return
    try:
        meta = json.loads(tvj.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"{tvj}: invalid JSON ({e})")
        return
    for k in REQUIRED_TV:
        if not str(meta.get(k, "")).strip():
            errors.append(f"{tvj}: missing '{k}'")
    lists = sorted(folder.glob("debloat*.txt"))
    if not lists:
        errors.append(f"{folder}: no debloat*.txt")
    for lst in lists:
        check_list(lst, errors, community)


def main():
    errors = []
    upstream_ids = set()
    for plat in PLATFORMS:
        for folder in sorted((ROOT / "models" / plat).glob("*/")):
            upstream_ids.add(folder.name)
            check_folder(folder, errors, community=False)
    community = 0
    for plat_dir in sorted((ROOT / "community").glob("*/")):
        if plat_dir.name not in PLATFORMS:
            errors.append(f"{plat_dir}: platform folder must be one of {PLATFORMS}")
            continue
        for folder in sorted(plat_dir.glob("*/")):
            community += 1
            if folder.name in upstream_ids:
                errors.append(f"{folder}: id '{folder.name}' already exists in models/; pick another folder name")
            check_folder(folder, errors, community=True)
    rows = json.loads((ROOT / "index" / "models.json").read_text(encoding="utf-8"))
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("index/models.json: duplicate ids")
    for r in rows:
        for lst in r["lists"]:
            if not (ROOT / lst).exists():
                errors.append(f"index/models.json: {r['id']} points at missing {lst}")
        if r.get("playbook") and not (ROOT / r["playbook"]).exists():
            errors.append(f"index/models.json: {r['id']} points at missing {r['playbook']}")
    indexed_community = sum(1 for r in rows if r["status"] == "community-tested")
    if indexed_community != community:
        errors.append(f"index is stale: {community} community model(s) on disk, {indexed_community} indexed. "
                      "Run tools/build_index.py (CI's weekly sync also does this).")
    for e in errors:
        print("ERROR", e)
    print(f"{len(upstream_ids)} upstream + {community} community models, {len(rows)} index rows, {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
