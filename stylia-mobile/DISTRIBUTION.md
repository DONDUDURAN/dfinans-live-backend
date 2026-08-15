# STYLIA — Build & Distribution Guide

## 🚀 Quick Local Test (Expo Go — Free, No Account Needed)

```bash
cd stylia-mobile
npm install
npx expo start        # LAN mode — phone and computer must be on same Wi-Fi
```
Scan the QR code with **Expo Go** (iOS App Store / Google Play).

> **Tip:** If your phone can't reach the LAN IP, add `--tunnel` (requires `@expo/ngrok`):
> ```bash
> npx expo start --tunnel
> ```

---

## 📦 Production Builds with EAS

### Prerequisites

```bash
npm install -g eas-cli
eas login          # create free account at expo.dev
eas init           # links project → updates eas.json projectId
```

---

## 🍎 iOS Distribution

### Option A — AdHoc (Direct device install, up to 100 devices)
> **Requires Apple Developer account ($99/year)**
> Devices must be pre-registered in the Apple Developer portal.

```bash
npm run build:adhoc:ios
```
1. EAS generates a provisioning profile automatically (first run prompts for Apple ID)
2. You receive a download link → install via **Safari on iPhone**
3. Settings → General → VPN & Device Management → Trust the certificate

> **Register a device first:**
> ```bash
> eas device:create   # generates a registration URL to open on the iPhone
> ```

### Option B — TestFlight (Up to 10,000 testers)
> Requires Apple Developer account ($99/year)

```bash
npm run build:prod:ios
npm run submit:ios
```
Configure in `eas.json` → `submit.production.ios`:
```json
{
  "appleId": "you@example.com",
  "ascAppId": "1234567890",
  "appleTeamId": "ABCDE12345"
}
```

### Option C — Simulator (Mac only, no account)

```bash
npm run build:dev:ios
# or locally:
npm run ios
```

---

## 🤖 Android Distribution

### Option A — APK (Sideload, any Android phone)
> No Google account required, simplest option

```bash
npm run build:apk:android
```
1. Download the `.apk` from the EAS build URL
2. On Android: **Settings → Install unknown apps → Allow**
3. Open the `.apk` file to install

### Option B — Google Play Internal Testing
> Requires Google Play Developer account ($25 one-time)

```bash
npm run build:prod:android   # produces .aab
npm run submit:android
```
Configure `google-service-account.json` from Google Play Console.

---

## ⚡ OTA Updates (No rebuild required)

After your first build, push JS-only updates instantly:

```bash
# Push to preview testers
npm run update:preview

# Push to production users
npm run update:production
```

Users get the update on next app launch — no App Store review needed for JS changes.

---

## 🔑 Required Secrets (GitHub Actions)

Add to **GitHub → Settings → Secrets → Actions**:

| Secret | Where to get |
|--------|-------------|
| `EXPO_TOKEN` | expo.dev → Account Settings → Access Tokens |

For iOS submits, EAS stores Apple credentials securely — no extra GitHub secrets needed.

---

## 🔄 CI/CD Flow (GitHub Actions)

| Trigger | Action |
|---------|--------|
| Push to `main` (stylia-mobile/ changed) | Android APK + iOS AdHoc build + OTA update |
| Pull Request | TypeScript lint check |
| Manual (`workflow_dispatch`) | Choose platform + profile |

---

## 📋 Build Profiles Summary

| Profile | iOS | Android | Use Case |
|---------|-----|---------|----------|
| `development` | Simulator | APK (debug) | Local dev |
| `adhoc` | AdHoc (device) | APK | Internal testing |
| `preview` | — | APK | QA testing |
| `production` | App Store | AAB | Store release |
