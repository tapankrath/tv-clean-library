#!/usr/bin/env python3
"""A fake `adb` for tests: keeps a TV's package state in the JSON file named by $FAKE_ADB_STATE."""
import json
import os
import sys

state_path = os.environ["FAKE_ADB_STATE"]
st = json.load(open(state_path))
args = sys.argv[1:]
if args[:1] == ["connect"]:
    print(f"connected to {args[1]}")
    sys.exit(0)
if args[:1] == ["-s"]:
    args = args[2:]
if args[:1] == ["reboot"]:
    # packages disabled less than "settle" ago come back, like the real low-RAM sets
    st["disabled"] = [p for p in st["disabled"] if p not in st.get("unsaved", [])]
    st["unsaved"] = []
    json.dump(st, open(state_path, "w"))
    sys.exit(0)
assert args[0] == "shell", args
cmd = args[1].split()
pkgs, dis = st["packages"], set(st["disabled"])


def save():
    st["disabled"] = sorted(dis)
    json.dump(st, open(state_path, "w"))


if cmd[:3] == ["pm", "list", "packages"]:
    flag = cmd[3] if len(cmd) > 3 else ""
    sel = {"": pkgs, "-d": sorted(dis), "-s": pkgs, "-3": []}[flag]
    print("\n".join(f"package:{p}" for p in sel))
elif cmd[:2] == ["pm", "disable-user"]:
    p = cmd[-1]
    if p not in pkgs:
        print(f"Error: unknown package {p}"); sys.exit(1)
    dis.add(p); save()
    print(f"Package {p} new state: disabled-user")
elif cmd[:2] == ["pm", "enable"]:
    dis.discard(cmd[-1]); save()
    print(f"Package {cmd[-1]} new state: enabled")
elif cmd[0] == "getprop":
    print(st["props"].get(cmd[1], ""))
elif cmd[:3] == ["cmd", "package", "resolve-activity"]:
    print("priority=0 preferredOrder=0 match=0x108000 specificIndex=-1 isDefault=false")
    print(f"{st['home']}/.Main")
elif cmd[:3] == ["cmd", "package", "query-activities"]:
    for h in st["home_candidates"]:
        print(f"{h}/.Main")
elif cmd[0] in ("settings", "dumpsys"):
    print("dummy=1")
else:
    print(f"fake adb: unhandled {cmd}", file=sys.stderr); sys.exit(2)
