# Android TV / Google TV

**Brands:** Sony, TCL, Xiaomi/Redmi, Hisense (Google TV models), Philips (Android/Google TV models), Sharp,
Skyworth, Toshiba (Android models), Panasonic (Android models), OnePlus, Nokia, JVC, Haier, Thomson, BenQ,
XGIMI and other projectors, Nvidia Shield, onn, Chromecast with Google TV, Google TV Streamer, and ~100 more.

**What's possible:** full debloat over ADB (`pm disable-user`), replacement launcher, privacy settings, DNS
filtering on the device (Private DNS) or the router. No root.

## 1. Settings first (no computer needed)

| Goal | Path (wording varies by model) |
|---|---|
| Ad personalization off | Settings › Privacy › Ads › **Delete advertising ID** and turn off **Ad personalization**. Some sets: Settings › Accounts › Google › Ads |
| Usage & diagnostics off | Settings › Privacy › **Usage & diagnostics** › off |
| Home-screen recommendations | Google TV: Settings › Accounts & sign-in › your account › **Apps only mode** on (removes the recommendation rows, also removes Google TV's watchlist) |
| Sony / Samba ACR | Settings › System or Privacy › **Samba Interactive TV** › decline / off. Re-check after updates |
| Sony | Settings › Initial setup › **Privacy setting** › untick Sony's viewing-data and ad options |
| TCL | Settings › Privacy › TCL's own **Privacy** / user-experience program toggles off |
| Xiaomi PatchWall | PatchWall settings › turn off **Personalized recommendations** and auto-play previews |
| Voice | Settings › Privacy › Assistant / Microphone; or keep Assistant if the owner uses voice search |

## 2. Turn on ADB

1. Settings › System › About (Google TV) or Settings › Device Preferences › About (Android TV).
2. Highlight **Build** and press OK until the TV says you are a developer (usually 7 presses).
3. Back › **Developer options** › turn on **USB debugging** (and **Network debugging** / **ADB over network**
   if the set has it). Android 11+ may show **Wireless debugging** with a pairing code: use `adb pair` first.
4. Note the TV's IP: Settings › Network › your Wi-Fi.

## 3. Debloat with the tool

```
export TV_HOST=<tv ip>
python3 -I tools/tvlib.py connect      # accept "Allow USB debugging?" on the TV, tick Always allow
python3 -I tools/tvlib.py probe
python3 -I tools/tvlib.py match        # ranks the 457 tested lists by how many of their packages this TV has
python3 -I tools/tvlib.py backup
python3 -I tools/tvlib.py plan  models/android-tv/<id>/debloat.txt
python3 -I tools/tvlib.py apply models/android-tv/<id>/debloat.txt --yes --reboot-check   # one batch
# test the TV, then repeat apply until the plan is empty
```

No exact match? `brands/<brand>/consensus.txt` lists what that brand's tested sets agree on, with counts.
Review it with the owner line by line.

## 4. Replace the home screen (optional, the biggest speed win)

Order matters. Getting it wrong is the classic black-screen brick.

1. Install the new launcher from Play (Projectivy Launcher, FLauncher) or `adb install`.
2. Open it once, and set it as Home if the TV offers a choice.
3. Only then disable the stock home: `com.google.android.apps.tv.launcherx` (Google TV) or
   `com.google.android.tvlauncher` (Android TV), **and** `com.google.android.tungsten.setupwraith` on
   Google TV: its RecoveryActivity also answers Home and can crash-loop `system_server` if left alone.
   Xiaomi: also `com.mitv.tvhome.atv` (PatchWall).
   With the tool: `apply <list> --yes --launcher-ready`.
4. Press Home from inside an app, then reboot, then press Home again.
5. `cmd package set-home-activity` prints Success and is then ignored on many sets: don't rely on it.

## 5. Known traps

- **Reboot too soon and the disable is lost.** Low-RAM sets save the state late. The tool waits 60 s.
- **Firmware updates re-enable packages.** Run `tvlib.py verify` after any update; re-run `apply` for drift.
- **Never disable:** inputs/HDMI/tuner services, the remote and Bluetooth pairing service, on-screen
  keyboard, Play Services/Play Store, Settings, SystemUI, OTA updater. The tool refuses these unless forced.
- Some China-market TCL/Xiaomi sets refuse any third-party launcher. Debloat only.
- Hisense Android 9 sets may need the factory menu to reach USB debugging (see the model's README).

## 6. DNS

Android 9+: `settings put global private_dns_mode hostname` and
`settings put global private_dns_specifier <your-filtering-DoT-host>` (NextDNS, AdGuard DNS, Control D),
or block at the router with `dns/<brand>.txt`. If the resolver ever stops answering, only adb can switch
Private DNS off on sets with no Private DNS screen: `settings put global private_dns_mode off`.
