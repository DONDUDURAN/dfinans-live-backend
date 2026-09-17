# STYLIA — Premium AI Wardrobe & Kabin (Dijital Kabin) App

> **Prototype handoff package** · React Native Expo · Dark luxe UI · Türkçe arayüz · Üyelik + Stripe ödeme
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
| **Kayıt (Registration)** | Ad/e-posta ile hesap oluşturma, üyelik biçimi (Aylık/Yıllık) seçimi, 7 gün ücretsiz deneme, Stripe Payment Link ile ödeme |
| **Ana Sayfa (Home)** | Günün STYLIA seçimi, son kombinler, gardırop istatistikleri, Kabin aksiyonları (dikey sıralı) |
| **Gardırop (Wardrobe)** | Grid/list toggle, canlı arama, kategori filtresi, favoriler |
| **Kombin (Outfit Builder)** | Slot tabanlı canvas (Üst/Alt/Ayakkabı vb.), isimlendirip kaydetme |
| **Kabin (AI Style)** | Ürün linki ekleme + kamera ile görsel çekme (dikey sıralı aksiyonlar), etkinlik/ruh hali filtreli AI kombin önerileri |
| **Parça Ekle (Add Item)** | 4 adımlı akış: ürün linki/foto → isim/kategori → renk/sezon → kullanım amacı |
| **Profil (Profile)** | Aktif üyelik planı gösterimi + Stripe ile plan değiştirme, vücut ölçüleri formu, video-notu ile ölçü güncelleme, Style DNA |

---

## 💳 Üyelik & Ödeme

- Kayıt sırasında **Aylık STYLIA Plus** veya **Yıllık STYLIA Elite** seçilir (yıllık plan aylığa göre daha ucuz — %40 tasarruf).
- Her plana 7 gün ücretsiz deneme dahildir.
- Ödeme, uygulama içinde kart bilgisi **saklanmadan**, harici **Stripe Payment Link** açılarak alınır (`src/config/paymentLinks.ts`).
- Profil ekranından kullanıcı istediği zaman planını değiştirip yeniden Stripe linkini açabilir.
- Gerçek ortamda `STRIPE_PAYMENT_LINKS` değerlerini kendi Stripe Payment Link URL'lerinizle değiştirin.

---

## 🏗 Tech Stack

| Layer | Choice |
|-------|--------|
| Framework | React Native + Expo ~51 |
| Navigation | React Navigation (bottom tabs + stack) |
| State | Zustand (`wardrobeStore`, `styleStore`, `userStore`) |
| UI | Custom design system — dark luxe (`#08080A` bg, `#C9A84C` gold accent), high-contrast text |
| i18n | Türkçe arayüz (`src/utils/translations.ts` + inline Turkish copy) |
| Icons | `@expo/vector-icons` (Ionicons) |
| Gradients | `expo-linear-gradient` |
| Camera/Gallery | `expo-image-picker` (ürün fotoğrafı, Kabin görseli, video-notu ölçüm akışı) |
| Payments | Stripe Payment Links via `Linking.openURL` (no in-app card fields) |
| OTA updates | `expo-updates` |

---

## 📁 Project Structure

```
stylia-mobile/
├── App.tsx                        # Entry point (NavigationContainer + AppNavigator)
├── app.json                       # Expo + EAS config
├── eas.json                       # Build profiles (development/adhoc/preview/production)
├── eas-build-pre-install.sh       # EAS pre-install hook (Node check, SDK licenses)
├── DISTRIBUTION.md                # Full build & distribution guide
├── .github/workflows/
│   └── eas-build.yml              # CI: lint → EAS build → OTA update
└── src/
    ├── navigation/AppNavigator.tsx        (Registration gate → MainTabs/AddItem/ItemDetail)
    ├── screens/          (RegistrationScreen, HomeScreen, WardrobeScreen, OutfitBuilderScreen,
    │                      AIStyleScreen "Kabin", AddItemScreen, ItemDetailScreen, ProfileScreen)
    ├── components/       (ClothingCard, OutfitCard, StyleSuggestionCard, CategoryFilter)
    ├── store/            (wardrobeStore.ts, styleStore.ts, userStore.ts — Zustand)
    ├── config/paymentLinks.ts   (Stripe Payment Links + membership plan copy)
    ├── utils/translations.ts    (category/occasion → Turkish label helpers)
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
