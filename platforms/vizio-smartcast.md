# Vizio (SmartCast / Vizio OS)

**What's possible:** settings, DNS. No debloat or launcher swap. The local HTTPS API (port 7345,
PIN-paired) controls power, inputs, keys and settings, nothing that removes apps.
Vizio is owned by Walmart and the ad business is the point of the platform: expect settings to move.

## 1. Privacy

Settings › **Admin & Privacy** (older: System › Reset & Admin):
- **Viewing Data** › Off (Vizio's ACR, "Inscape").
- **Advertising** › turn on **Limit Ad Tracking** / turn off ad personalization.
- Review **Additional Policies** / **Notices** and decline optional data sharing.

## 2. Home screen

Settings › System › **Home Screen** / WatchFree+ : turn off auto-launch of WatchFree+ and preview autoplay
where offered. Settings › System › Power Mode › set **Eco Mode** if the owner doesn't need Cast wake-up
(also stops background traffic while off).

## 3. DNS

`dns/vizio.txt` (Perflyst). Known: blocking the platform's own hosts can break SmartCast apps and casting.

## Dumb panel

Most reliable option on Vizio: no network connection plus an external streaming box.
