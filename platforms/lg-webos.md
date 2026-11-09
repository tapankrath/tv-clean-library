# LG (webOS)

**What's possible:** settings, boot-to-input, DNS blocking. **No debloat and no launcher swap** on current
firmware. Developer Mode (from the LG Content Store) plus the `ares` CLI only installs your own IPK apps.
Root exploits existed (faultmanager, dejavuln) but current firmware for webOS 5/6/7/9 is patched;
this library does not use root paths.

## 1. Privacy (menu names vary by webOS version)

Settings › All Settings › **General** (newer: **General › System** or **Support**):
- **Live Plus** › Off. This is ACR, including HDMI inputs.
- **Additional Settings › Advertisement** › turn on **Limit Ad Tracking** / **Do Not Sell My Personal
  Information** (US), turn off **Personalized Advertising**.
- **Home Settings** › turn off **Home Promotion** and **Content Recommendation** where present.
- **User Agreements** (or About This TV › User Agreements): opt out of **Viewing Information**,
  **Personalized Advertising**, **Voice Information**, **Live Plus**. Opting out of the main Privacy
  Policy itself removes most smart features; only do that if the owner wants a dumb panel.
- **Channel Plus** / LG Channels › Off (removes free channels and their prompts).
- ThinQ / Google Assistant models: in Assistant, "disable information sharing" (disables voice control).

## 2. Dumb-panel option

Hotel/installer mode: hold the remote's **Settings** button ~5 s, enter **1105**, set **Power On Status**
to a fixed input or Last Input. Change nothing else there.

## 3. DNS

`dns/lg.txt` (Perflyst list, includes the per-country `nextlgsdp.com` ad hosts). A larger, layered LG list
is maintained at github.com/hugobatista/lg-tv-ad-block (GPL-3.0, so linked, not copied): its `list` file
is safe; `list-store` also blocks the Content Store and app updates.
Known side effect: blocking `ngfts.lge.com` blanks Content Store thumbnails (left unblocked here).

## Agent role

Guide only. Record firmware (Settings › General › About This TV) and every change in
`state/<tv>/manual-log.md`.
