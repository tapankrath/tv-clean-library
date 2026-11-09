# Samsung (Tizen)

**What's possible:** settings, boot-to-input, DNS blocking. **No debloat and no launcher swap.**
Tizen uses `sdb` (port 26101), not ADB. Developer Mode (Smart Hub › Apps › type 12345 › your PC's IP ›
reboot) gives no shell and no root: it can uninstall store/carrier apps only, not the `com.samsung.*` /
`org.tizen.*` packages where ads, ACR and telemetry live. An agent can't do more than guide the owner.

## 1. Privacy (menu names vary by year)

**Settings › Support › Terms & Privacy › Privacy Choices** (2024–2026 sets may show this under
Settings › All Settings › General & Privacy › Terms & Privacy):
- **Viewing Information Services** › Off. This is ACR: it fingerprints everything on screen, including
  HDMI inputs (cable box, console).
- **Interest-Based Advertising** › Off. Ads still show, untargeted.
- **Voice Recognition Services** › Off, unless the owner uses voice control (it stops working).
- Older sets: also open **Terms & Policy** and decline **SyncPlus and Marketing**.

## 2. Home-screen ads and boot behaviour

Settings › General › **Smart Features**:
- **Autorun Smart Hub** › Off: the TV boots to the last input instead of the ad-filled hub.
- **Autorun Last App** › Off.
- Turn off any **Auto Play** / promotion previews offered on the same screen.

Settings › General › Notifications or Settings › Support › Device Care: turn off promotional notifications
where offered.

## 3. Dumb-panel option

Hospitality (hotel) mode lets the TV power on straight into an HDMI input. With the TV on, press
**Mute › 1 › 1 › 9 › Enter** on the remote, then set the power-on source. This menu also exposes settings
that can break the picture; change only power-on source and only with the owner watching.
Then disconnect the TV from the network and feed it from a streaming box the owner controls.

## 4. DNS

`dns/samsung.txt` (Perflyst list). Entries commented with `#` are known to break apps or updates if blocked.
Expect: home-screen ad tiles go blank, Samsung TV Plus may stop working, apps should keep working.
Firmware updates still need the update hosts: don't block anything marked "required for updates".

## Agent role

Read this page to the owner step by step, have them confirm each toggle, record the firmware version
(Settings › Support › About This TV) and what they changed in `state/<tv>/manual-log.md`.
