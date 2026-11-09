# Agent instructions: cleaning up a smart TV

You are helping the owner of a TV remove ads, tracking and preinstalled bloat from **their own** TV,
reversibly. Read this whole file before touching anything. AGENTS.md and GEMINI.md point here.

## Ground rules (never break these)

1. **Disable, never uninstall.** Only `pm disable-user --user 0` through `tools/tvlib.py`. No
   `pm uninstall`, no `pm clear`, no root, no exploits, no firmware flashing, no factory/service menus.
2. **Backup before the first change.** `tvlib.py backup`. The tool refuses to apply without one.
3. **One batch at a time (max 10 packages), then stop.** After each batch the owner checks the TV. Do
   not run the next batch until they say it's fine.
4. **Never disable** core Android, inputs/HDMI/tuner, the remote/Bluetooth pairing, the on-screen
   keyboard, Play Services/Play Store, Settings, SystemUI or the OTA updater. The tool enforces this;
   use `--force <pkg>` only when the owner explicitly asks for that exact package after you explained
   what it does.
5. **Never disable the stock launcher** (or `setupwraith` on Google TV, PatchWall on Xiaomi) until a
   replacement launcher is installed, opened, and Home lands on it. Then use `--launcher-ready`.
6. **Ask about anything you can't explain.** Don't guess a package's purpose from its name.
7. **Everything goes in the log.** The tool writes `state/<tv>/log.jsonl`. For closed platforms, write
   what the owner changed to `state/<tv>/manual-log.md` yourself.
8. If the TV acts up: `tvlib.py restore --last-batch`, reboot, check. If it won't boot to Home, see
   "Recovery" below. Do not keep trying things.

## Step 1: Identify the platform

Ask the owner for the brand and model (sticker on the back, or Settings › About). Then:

| Brand / OS | Go to |
|---|---|
| Android TV, Google TV (Sony, TCL, Xiaomi, Philips, Sharp, Hisense Google TV, Nvidia Shield, onn, Chromecast...) | Step 2 (ADB) + `platforms/android-tv.md` |
| Fire TV (Amazon, Insignia, Toshiba Fire TV, Hisense Fire TV, Panasonic 2024+) | Step 2 (ADB) + `platforms/fire-os.md` |
| Samsung (Tizen) | `platforms/samsung-tizen.md` — guide only |
| LG (webOS) | `platforms/lg-webos.md` — guide only |
| Roku TV (any brand) | `platforms/roku.md` — guide only |
| Vizio | `platforms/vizio-smartcast.md` — guide only |
| Hisense / Toshiba VIDAA | `platforms/hisense-vidaa.md` — guide only |
| Panasonic My Home Screen, Philips Saphi | `platforms/other-closed.md` — guide only |

"Guide only" means: walk the owner through the settings one at a time, confirm each, offer the DNS list
(`tvlib.py dns <brand> --format hosts|adguard|plain`), log it. Do not claim you can debloat these.

## Step 2: Connect (ADB platforms)

Walk the owner through enabling Developer options and USB/Network debugging (see the platform page).
Then:
```
export TV_HOST=<tv ip>
python3 -I tools/tvlib.py connect   # owner accepts the prompt on the TV, ticks "Always allow"
python3 -I tools/tvlib.py probe
```
Settings changes first: go through section 1 of the platform page with the owner (ad personalization,
ACR, usage data). These need no package changes and carry no risk.

## Step 3: Pick the list

```
python3 -I tools/tvlib.py match
```
- **Exact model** (overlap ≥ 90% and id hits > 0): use that list. Read the model's `README.md` and the
  list header for model-specific warnings before going on.
- **Sibling model** (overlap ≥ 60%): show the owner the list and the differences; proceed if they agree.
- **No match**: start from `brands/<brand>/consensus.txt`. Copy it to `state/<tv>/my-list.txt`, go through
  it with the owner, comment out anything they use or that you can't explain. Prefer high counts.
- Ask the owner which apps they use (Netflix, YouTube, Prime, casting, voice, the TV tuner) and pass them
  with `--keep`.

## Step 4: Apply

```
python3 -I tools/tvlib.py backup
python3 -I tools/tvlib.py plan  <list> [--keep ...]
python3 -I tools/tvlib.py apply <list> [--keep ...] --yes --reboot-check
```
After each batch, ask the owner to check: Home button, Inputs/HDMI switching, remote + volume, sound,
Wi-Fi, on-screen keyboard, the apps they use. Only then run `apply` again. Repeat until the plan is empty.

Show the owner a short table at the end: what was disabled (one line each), RAM before/after if they
care (`backup` saves meminfo), and the one command that undoes everything:
`python3 -I tools/tvlib.py restore --all`.

## Step 5 (optional): New home screen

Only if the owner wants it. Follow section 4 of `platforms/android-tv.md` exactly. Not possible on Fire OS
without the dumbtv workaround.

## Step 6: Finish

- Offer DNS blocking (`dns/<brand>.txt`) at the router or via Private DNS.
- Tell the owner to turn **USB/Network debugging off** when done (it leaves port 5555 open on some sets).
- After any firmware update: `tvlib.py verify`, then re-run `apply` for anything that came back.

## Recovery

- Black screen / no Home: `adb shell pm enable com.google.android.apps.tv.launcherx` (or `tvlauncher`,
  `com.google.android.tungsten.setupwraith`, `com.mitv.tvhome.atv`), or `tvlib.py restore --last-batch`.
  ADB usually stays reachable even when Home is gone.
- Lost ADB too: Settings › Apps › Show system apps › re-enable from the TV's own menu if reachable.
- Last resort: factory reset (Settings › System › Reset, or the recovery menu). Disabled packages come back.
  This is why the library never uninstalls.

## Contributing a new model

When a cleanup succeeds on a model with no list, offer to save it: `models/<platform>/<brand-model>/`
with `debloat.txt` (header: model, `ro.product.model`, device, firmware build, date, what was kept and
why), `tv.json` ({tv, os, brand, notes}), and a README with gotchas. Mark it tested only after the owner
has used the TV for a few days. Then rebuild: `python3 -I tools/build_index.py ...` (see README).
