# Roku OS (Roku TVs and players)

**Brands:** Roku-branded TVs, plus Roku TV models from TCL, Hisense, Sharp, onn, Philips, Westinghouse,
Element, JVC, RCA.

**What's possible:** settings, boot-to-input, DNS. No debloat or launcher swap: developer mode and the
ECP API on port 8060 only control the TV (keypress, launch, input), they can't disable anything.

## 1. Privacy

Settings › **Privacy**:
- **Smart TV Experience** › untick **Use Info from TV Inputs** (ACR on HDMI/antenna) and the content
  viewing disclosure.
- **Advertising** › turn on **Limit ad tracking** / opt out of personalized ads; tick **Limit use of
  sensitive information** where offered.
- **Microphone** › review **Channel Microphone Access** and **Channel Permissions**.

## 2. Home screen (2026 redesign)

Roku's 2026 home pushes the app grid down under promoted rows. Settings › **Home Screen**: hide the
recommendation rows and the quick-access menu to bring the apps back to the centre. Use the * button
on an app tile to move it.
Screensaver: pick an ad-free one (e.g. Aquatic Life) instead of Roku City.
Antenna users: turn off **More Ways to Watch** (pop-up suggestions over live TV).

## 3. Boot behaviour

Settings › System › Power › **Power on** › **Last used input** (TVs only).

## 4. DNS

`dns/roku.txt` is short on purpose: Roku serves ads and the home screen from the same hosts, so heavy
blocking breaks the home screen and channel store. Test with the owner.
