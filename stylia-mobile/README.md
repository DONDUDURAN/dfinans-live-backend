# STYLIA — AI-Powered Wardrobe & Styling App

A luxury mobile app prototype built with **React Native Expo** that transforms your wardrobe into a smart styling assistant.

## ✦ Features

### 👗 Wardrobe Management
- Add clothing items with photos (camera or gallery)
- Categorize by type, color, season, and occasion
- Grid and list view with live search and filtering
- Track how often each item is worn
- Mark favorites

### 🎨 Outfit Builder
- Visual drag-and-drop style outfit assembly
- Category-slot system (Tops, Bottoms, Shoes, etc.)
- Save custom outfits with names
- Preview your outfit on a canvas

### ✨ AI Style Assistant
- AI-powered outfit suggestions based on your wardrobe
- Filter by occasion and mood
- Confidence scores and personalized reasons
- Style tips and fashion guidance

### 📊 Profile & Insights
- Wardrobe statistics (items, outfits, total wears)
- Most-worn item tracking
- Cost-per-wear calculation
- Category breakdown visualization
- Style persona

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Expo CLI: `npm install -g expo-cli`
- Expo Go app on iOS/Android (for testing)

### Installation

```bash
cd stylia-mobile
npm install
```

### Run

```bash
# Start Expo dev server
npm start

# Run on iOS simulator
npm run ios

# Run on Android emulator
npm run android

# Run in browser (web)
npm run web
```

Scan the QR code with **Expo Go** on your device for instant live preview.

---

## 📁 Project Structure

```
stylia-mobile/
├── App.tsx                  # Entry point
├── app.json                 # Expo configuration
├── src/
│   ├── navigation/
│   │   └── AppNavigator.tsx # Bottom tabs + stack nav
│   ├── screens/
│   │   ├── HomeScreen.tsx       # Dashboard & daily AI pick
│   │   ├── WardrobeScreen.tsx   # Full wardrobe grid/list
│   │   ├── OutfitBuilderScreen.tsx  # Interactive outfit builder
│   │   ├── AIStyleScreen.tsx    # AI suggestions & mood filter
│   │   ├── AddItemScreen.tsx    # 4-step item onboarding
│   │   └── ProfileScreen.tsx   # Stats, insights & settings
│   ├── components/
│   │   ├── ClothingCard.tsx
│   │   ├── OutfitCard.tsx
│   │   ├── StyleSuggestionCard.tsx
│   │   └── CategoryFilter.tsx
│   ├── store/
│   │   ├── wardrobeStore.ts     # Zustand wardrobe state
│   │   └── styleStore.ts        # AI style + outfit builder state
│   ├── data/
│   │   └── mockData.ts          # Seed clothing & outfit data
│   ├── types/
│   │   └── index.ts             # TypeScript types
│   └── theme/
│       └── index.ts             # Colors, Typography, Spacing
```

---

## 🎨 Design System

| Token | Value |
|-------|-------|
| Background | `#0D0D0D` — near black |
| Surface | `#1A1A1A` |
| Gold Accent | `#C9A84C` |
| Text Primary | `#F5F5F0` |
| Text Secondary | `#9E9E9E` |

Typography uses system fonts with weights from 400–900.

---

## 🔗 Backend Integration

This prototype uses local mock data. To connect to the **dfinans-live-backend** (or a dedicated STYLIA backend):

1. Create a `.env` file:
   ```
   EXPO_PUBLIC_API_URL=https://your-backend.railway.app
   ```

2. Replace mock data calls in `src/store/` with `fetch()` or `axios` requests.

3. Suggested endpoints:
   - `GET /wardrobe/items` — fetch clothing items
   - `POST /wardrobe/items` — add new item
   - `GET /style/suggest` — AI outfit suggestions
   - `POST /outfits` — save outfit

---

## 📦 Key Dependencies

| Package | Purpose |
|---------|---------|
| `expo` ~51 | React Native runtime |
| `@react-navigation` | Tab + stack navigation |
| `zustand` | Lightweight state management |
| `expo-image-picker` | Camera & gallery access |
| `expo-linear-gradient` | Gradient UI elements |
| `@expo/vector-icons` | Ionicons icon set |

---

## 📸 Screens Overview

| Screen | Description |
|--------|-------------|
| **Home** | Today's AI pick, recent outfits, quick stats |
| **Wardrobe** | Full closet with search, filter & grid/list view |
| **Outfit Builder** | Slot-based visual outfit assembly |
| **AI Style** | Personalized suggestions by mood & occasion |
| **Profile** | Wardrobe insights, stats & settings |

---

Built with ❤️ by STYLIA
