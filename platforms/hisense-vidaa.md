# Hisense / Toshiba (VIDAA)

Hisense sells four OSes. Check first: Settings › System › About.
- **Google TV / Android TV** → `android-tv.md` (full debloat).
- **Fire TV Edition** → `fire-os.md`.
- **Roku TV** → `roku.md`.
- **VIDAA** → this page: settings and DNS only. No ADB; the remote-control interfaces (DevTools on old
  firmware, MQTT on newer) can't remove apps.

## Privacy

Settings › **Support** or **System** › **Privacy** / **Viewing Information**:
- **Smart TV Experience** / **Viewing Information Services** (ACR) › Off.
- **Personalized Advertising** › Off.
- **Terms & Privacy**: decline optional agreements; declining the main agreement removes smart features.

Settings › System › **Advanced** › **Power On Mode** / **Input at power on** › last input (wording varies).

## DNS

`dns/hisense.txt` (Perflyst). A dedicated VIDAA list is maintained at
github.com/ipanalytics/Hisense-VIDAA-DNS-Clean-TV-Blocklist (check its license before copying in).

Avoid the hidden service menus (Balance + 1969 etc.) unless the owner accepts the risk: they hold panel
and factory settings.
