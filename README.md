# TV Clean Library

A library and agent playbook for removing ads, tracking and bloat from smart TVs, organised by platform,
brand and model, with one safety-first tool that does every change reversibly.

| | |
|---|---|
| Tested model lists (Android TV, Google TV, Fire TV) | **457 models, 120 brands** (`index/MODELS.md`) |
| Brand consensus lists for untested models | `brands/<brand>/consensus.txt` |
| Playbooks for closed platforms | Samsung, LG, Roku, Vizio, Hisense VIDAA, Panasonic, Philips Saphi |
| DNS blocklists | `dns/<brand>.txt` (9 brands) |
| Agent instructions | `CLAUDE.md` (also used by AGENTS.md / GEMINI.md) |
| Tool | `tools/tvlib.py`: probe, match, backup, plan, apply, verify, restore, dns |

## How it's organised

```
platforms/      what each TV OS allows, settings paths, traps (the first thing to read)
models/         one folder per tested model: debloat.txt, tv.json, README.md
  android-tv/   439 models
  fire-os/      18 models
community/      lists contributed here (see CONTRIBUTING.md); never overwritten by the sync
brands/         consensus.txt per brand: packages its tested lists agree on, with counts
dns/            per-brand blocklists; '#domain' lines are deliberately left unblocked
index/          models.json / models.csv / MODELS.md: every model + closed-platform rows
tools/          tvlib.py (the only thing that talks to a TV), build_index.py (regenerates the above)
tests/          end-to-end test against a fake adb
state/          created at run time: per-TV backups and the change log (keep it, don't publish it)
```

## Quick start

With Claude Code (or any coding agent) in this folder: *"My TV is a <brand> <model>. Clean it up following
CLAUDE.md."* The agent identifies the platform, matches a tested list, backs up, and applies in batches,
stopping after each one for you to check the TV.

By hand (Android/Google/Fire TV, adb installed, debugging on):
```
export TV_HOST=192.168.1.50
python3 -I tools/tvlib.py connect
python3 -I tools/tvlib.py match
python3 -I tools/tvlib.py backup
python3 -I tools/tvlib.py apply models/android-tv/<id>/debloat.txt --yes --reboot-check
python3 -I tools/tvlib.py restore --all     # undo everything
```

## Safety design

- Disable only (`pm disable-user --user 0`); nothing is uninstalled, a factory reset restores everything.
- Refuses to run without a backup. Max 10 packages per run, then stops for a human check.
- Hard guards: core Android packages are never touched; inputs, remote, keyboard, Play Services and
  updaters need an explicit `--force`; the stock launcher and `setupwraith` need `--launcher-ready`.
- Waits 60 s before any reboot (some sets lose a disable otherwise).
- `verify` detects packages a firmware update turned back on.

## Status labels

- `tested-by-submitter`: applied and reboot-checked on that model and firmware by the person who submitted
  it upstream. Different firmware can differ. Read the header of each list.
- `playbook`: closed platform, settings + DNS guidance only.
- Consensus lists are **not** tested as a set: they are a starting point for review.

## Contributing

Cleaned up a TV that isn't listed? Add it: `CONTRIBUTING.md`, or open an **Add my TV model** issue.
Upstream lists are pulled in weekly by a bot pull request.

## Rebuilding the index

```
git clone https://github.com/Gathin23/cleanyourtv ../cleanyourtv
git clone https://github.com/Perflyst/PiHoleBlocklist ../PiHoleBlocklist
python3 -I tools/build_index.py --cleanyourtv ../cleanyourtv --perflyst ../PiHoleBlocklist
python3 -I tools/validate.py && python3 -I tests/test_tvlib.py
```

## Limits

- Brand settings menus move with firmware updates; paths in `platforms/` are a guide, not a guarantee.
- Samsung, LG, Roku, Vizio and VIDAA can't be debloated without root. This library doesn't do root.
- Debloating can void a support conversation with the manufacturer. Use on TVs you own.

Credits and licenses: `THIRD_PARTY.md`.
