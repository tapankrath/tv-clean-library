# Fire TV (Fire OS)

**Brands:** Amazon Fire TV sticks/cubes/Omni, Fire TV Edition sets from Insignia, Toshiba, Hisense, Pioneer,
Panasonic (2024+), JVC, Onida, Croma.

**What's possible:** debloat over ADB (some Amazon packages are protected and refuse), privacy settings,
DNS. Fire OS does **not** let a third-party launcher take the Home button, so the ad-filled home stays
unless you use a workaround (dumbtv's accessibility "Guard", see THIRD_PARTY.md).
Fire OS 5 (2015–2016 sticks) refuses `pm disable-user` entirely.

## 1. Settings first

Settings › Preferences › **Privacy Settings**:
- **Device Usage Data** › Off
- **Collect App and Over-the-Air Usage** › Off
- **Interest-based Ads** › Off (ads still appear, just not targeted)

Settings › Preferences › **Featured Content** › turn off **Allow Video Autoplay** and **Allow Audio Autoplay**.
Settings › Preferences › **Data Monitoring** › Off. Settings › Applications › **Appstore** › Automatic
updates as the owner prefers.

## 2. ADB

Settings › My Fire TV (or Device & Software on Fire TV Edition sets) › About › press the device name
7 times › Developer options › **ADB debugging** On.

## 3. Debloat

Same tool and flow as Android TV: lists live in `models/fire-os/`. `tvlib.py match` picks the closest.

Never disable: `com.amazon.tv.launcher` (Home), the input/tuner/live TV packages on Fire TV Edition sets,
the remote/Bluetooth stack, `com.amazon.device.software.ota` unless the owner explicitly wants updates off.

## 4. Deeper

For Fire OS specifically, `humblemuzzu/dumbtv` goes further (protected-package app-ops lockdown, an
on-device DNS filter, a launcher that intercepts Home on Fire OS 6–8). Its own scripts are Fire-OS-only
and tested end to end on Fire OS 7/8.

## 5. DNS

`dns/` has no Amazon list on purpose: blocking Amazon's ad hosts on a Fire TV often breaks the home screen
and the Appstore. Perflyst's `AmazonFireTV.txt` exists upstream; test it with the owner before keeping it.
