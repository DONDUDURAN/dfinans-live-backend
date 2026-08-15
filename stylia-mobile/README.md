# STYLIA — AI-Powered Wardrobe & Styling App

> **Prototype handoff package** · React Native Expo · Dark luxury UI · AI styling features  
> Branch: `donduduran-stylia-mobile-app` · PR: #150

---

## ⚡ Run in 60 Seconds

```bash
# Prerequisites: Node 18+, Expo Go on your phone

cd stylia-mobile
npm install
npm start        # Metro starts with --clear + LAN mode → scan QR with Expo Go
```

> Phone and Mac must be on the **same Wi-Fi**.  
> `http://localhost:8081` will NOT open on a phone — use the QR code.  
> If QR doesn't connect: `npm run start:tunnel`

---

## 📱 Screens

| Screen | What it does |
|--------|-------------|
| **Home** | Daily AI outfit pick, recent outfits carousel, wardrobe stats, quick actions |
| **Wardrobe** | Full closet — grid/list toggle, live search, 7-category filter, favorites |
| **Outfit Builder** | Slot-based canvas (Tops / Bottoms / Shoes / etc.), save outfits by name |
| **AI Style** | Suggestions filtered by occasion & mood, confidence scores, style tips |
| **Add Item** | 4-step guided flow: photo → name/category → color/season → occasions |
| **Profile** | Most-worn item, cost-per-wear, category bar chart, settings |

---

## 🏗 Tech Stack

| Layer | Choice |
|-------|--------|
| Framework | React Native + Expo ~51 |
| Navigation | React Navigation (bottom tabs + stack) |
| State | Zustand |
| UI | Custom design system — `#0D0D0D` bg, `#C9A84C` gold accent |
| Icons | `@expo/vector-icons` (Ionicons) |
| Gradients | `expo-linear-gradient` |
| Camera/Gallery | `expo-image-picker` |
| OTA updates | `expo-updates` |

---

## 📁 Project Structure

```
stylia-mobile/
├── App.tsx                        # Entry point
├── app.json                       # Expo + EAS config
├── eas.json                       # Build profiles (development/adhoc/preview/production)
├── eas-build-pre-install.sh       # EAS pre-install hook (Node check, SDK licenses)
├── DISTRIBUTION.md                # Full build & distribution guide
├── .github/workflows/
│   └── eas-build.yml              # CI: lint → EAS build → OTA update
└── src/
    ├── navigation/AppNavigator.tsx
    ├── screens/          (HomeScreen, WardrobeScreen, OutfitBuilderScreen,
    │                      AIStyleScreen, AddItemScreen, ProfileScreen)
    ├── components/       (ClothingCard, OutfitCard, StyleSuggestionCard, CategoryFilter)
    ├── store/            (wardrobeStore.ts, styleStore.ts — Zustand)
    ├── data/mockData.ts  (12 clothing items, 4 outfits, 3 AI suggestions)
    ├── types/index.ts
    └── theme/index.ts    (Colors, Typography, Spacing, Radius, Shadow)
```

---

## 🚀 Distribution Decision Tree

```
Who needs to test?
│
├─ Just you (free, instant)
│   └─ npm start  →  Expo Go on same Wi-Fi
│
├─ Small team / up to 100 devices  (iOS requires Apple Dev $99/yr)
│   ├─ Android  →  npm run build:apk:android  →  sideload .apk
│   └─ iOS      →  npm run build:adhoc:ios    →  install via Safari link
│
└─ Public / App Store
    ├─ Android  →  npm run build:prod:android  →  npm run submit:android
    └─ iOS      →  npm run build:prod:ios      →  npm run submit:ios
```

> See **DISTRIBUTION.md** for step-by-step instructions for every path.

---

## 🔑 Credentials Needed

| Platform | What's needed | Where |
|----------|--------------|-------|
| Expo / EAS | Free account | expo.dev |
| GitHub CI | `EXPO_TOKEN` secret | expo.dev → Account → Access Tokens |
| iOS AdHoc/Store | Apple Developer ($99/yr) | developer.apple.com |
| Android Store | Google Play ($25 one-time) | play.google.com/console |

EAS manages signing keys and provisioning profiles automatically (`credentialsSource: auto`).

---

## 🔗 Backend Integration

Prototype uses local mock data. To connect to **dfinans-live-backend**:

```bash
# stylia-mobile/.env
EXPO_PUBLIC_API_URL=https://your-backend.railway.app
```

Replace calls in `src/store/wardrobeStore.ts` and `src/store/styleStore.ts`  
with `fetch(process.env.EXPO_PUBLIC_API_URL + '/endpoint')`.

Suggested endpoints:
- `GET  /wardrobe/items` → clothing list
- `POST /wardrobe/items` → add item
- `GET  /style/suggest`  → AI suggestions
- `POST /outfits`        → save outfit

---

## 🤖 CI/CD (GitHub Actions)

| Trigger | Jobs |
|---------|------|
| Push to `main` (stylia-mobile/** changed) | lint → Android APK build → iOS AdHoc build* → OTA update |
| Pull Request | TypeScript lint only |
| Manual (`workflow_dispatch`) | Choose platform + profile |

\* iOS AdHoc job is skipped if `APPLE_ID` secret is not set.

---

Built with ❤️ for STYLIA
