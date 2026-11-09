# Contributing

The library is only as good as its tested lists. The most useful contribution is a list for a model that
isn't here yet, after you've lived with it for a few days.

## Add a model

1. Clean up your TV following `CLAUDE.md` (or by hand with `tools/tvlib.py`).
2. Use it for a few days: firmware quirks and "re-enabled at boot" problems show up later.
3. Create `community/<platform>/<brand-model>/` where `<platform>` is `android-tv` or `fire-os` and the
   folder name is lowercase with dashes, e.g. `community/android-tv/tcl-55q651g/`.
4. Add three files:

**`debloat.txt`** — one package per line, a `#` note after each, and a header like this:
```
# TCL 55Q651G (ro.product.model "55Q651G", device "G11"), USA
# Google TV 12, firmware V8-T652T01-LF1V1234, tested 2026-11-09, used 5 days since.
# Kept on purpose: com.tcl.ttvs (system updates), com.tcl.suspension (Inputs panel), Netflix, casting.
# Notes: wait 60 s before rebooting or disables are lost.

# Ads and recommendations
com.tcl.waterfall.overseas       # TCL recommendation browser
com.tcl.partnercustomizer        # TCL tweaks to the home rows
...
```
The header must mention `ro.product.model`, the firmware, and `tested` (CI checks).

**`tv.json`**
```json
{"tv": "TCL 55Q651G (G11), USA", "os": "Google TV 12", "brand": "TCL",
 "notes": "One-line summary: what's off, what's kept, any trap."}
```

**`README.md`** (optional) — anything the next owner of this model should know.

5. Open a pull request. CI rebuilds the index, validates the list, and runs the tests. You don't need to
   run `build_index.py` yourself.

No adb or Git? Open an **Add my TV model** issue instead and paste the same information.

## Rules for lists

- Disable only. Never `pm uninstall`.
- Never list core Android packages, inputs/tuner, remote/Bluetooth pairing, keyboards, Play Services/Store,
  Settings, SystemUI or the OTA updater. CI rejects core packages outright.
- Stock launcher / `setupwraith` / PatchWall entries go in a separate `debloat-launcher.txt`, since they
  only apply once a replacement launcher owns Home.
- Don't guess. If you're not sure what a package does, leave it on and say so in the header.

## Fix a settings path

Open a **Settings menu changed** issue or edit `platforms/<platform>.md` directly. Say which model, model
year and firmware you checked it on: menus move between years.

## Upstream

`models/` is synced weekly from [cleanyourtv](https://github.com/Gathin23/cleanyourtv) by a bot pull
request, so don't edit files there (they'd be overwritten). Fixes to those lists are best sent upstream;
a community list with a different folder name can override in the meantime.

## Code

`tools/tvlib.py` is the only thing that talks to a TV. Changes to it need a matching case in
`tests/test_tvlib.py`. Run before pushing:
```
python3 -I tools/validate.py && python3 -I tests/test_tvlib.py
```
