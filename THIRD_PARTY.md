# Third-party material

| What | From | License | Where it is here |
|---|---|---|---|
| 457 per-model debloat lists, tv.json and model READMEs; the core-package guard pattern | [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv) | MIT, © 2026 Gathin | `models/`, derived `brands/*/consensus.txt`, `CORE_RE` in `tools/tvlib.py` |
| Smart-TV DNS blocklist, split per brand | [Perflyst/PiHoleBlocklist](https://github.com/Perflyst/PiHoleBlocklist) `SmartTV.txt` | MIT, © 2018 Perflyst | `dns/*.txt` |
| Platform capability notes (Tizen sdb, webOS dev mode, Roku ECP, VIDAA, Vizio API, hotel modes, Google TV launcher traps) | [humblemuzzu/dumbtv](https://github.com/humblemuzzu/dumbtv) `docs/OTHER-TVS.md` | MIT, © 2026 dumbtv contributors | summarised in `platforms/` |
| LG layered blocklist | [hugobatista/lg-tv-ad-block](https://github.com/hugobatista/lg-tv-ad-block) | GPL-3.0 | linked only, not copied |
| Hisense VIDAA blocklist | [ipanalytics/Hisense-VIDAA-DNS-Clean-TV-Blocklist](https://github.com/ipanalytics/Hisense-VIDAA-DNS-Clean-TV-Blocklist) | see repo | linked only |

The MIT notices of the copied projects apply to the copied files. Files under `models/` keep their upstream
headers, which may mention upstream's `tools/disable.sh` / `restore.sh`; here the equivalent is
`tools/tvlib.py apply` / `restore`.

Menu paths in `platforms/` were compiled from Tom's Guide, Reclaim The Net, Lon.TV and the projects above
(November 2026) and are paraphrased.
