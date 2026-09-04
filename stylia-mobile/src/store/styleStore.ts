import { create } from 'zustand';
import { StyleSuggestion, Outfit, ClothingItem, Occasion } from '../types';
import { MOCK_SUGGESTIONS } from '../data/mockData';
import { MOCK_CLOTHING } from '../data/mockData';

interface StyleState {
  suggestions: StyleSuggestion[];
  isGenerating: boolean;
  selectedOccasion: Occasion | null;
  builderItems: string[]; // IDs of items in the outfit builder

  // Actions
  generateSuggestions: (occasion?: Occasion) => Promise<void>;
  setOccasion: (occ: Occasion | null) => void;
  addToBuilder: (itemId: string) => void;
  removeFromBuilder: (itemId: string) => void;
  clearBuilder: () => void;
  saveBuilderAsOutfit: (name: string) => Outfit;
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export const useStyleStore = create<StyleState>((set, get) => ({
  suggestions: MOCK_SUGGESTIONS,
  isGenerating: false,
  selectedOccasion: null,
  builderItems: [],

  generateSuggestions: async (occasion) => {
    set({ isGenerating: true });
    // Simulate AI processing delay
    await sleep(2200);

    // In production this would call your backend AI endpoint
    const filtered = occasion
      ? MOCK_SUGGESTIONS.filter((s) => s.outfit.occasion === occasion)
      : MOCK_SUGGESTIONS;

    // Shuffle to simulate new suggestions
    const shuffled = [...filtered].sort(() => Math.random() - 0.5);

    set({
      suggestions: shuffled.length > 0 ? shuffled : MOCK_SUGGESTIONS,
      isGenerating: false,
      selectedOccasion: occasion ?? null,
    });
  },

  setOccasion: (occ) => set({ selectedOccasion: occ }),

  addToBuilder: (itemId) => {
    const { builderItems } = get();
    const item = MOCK_CLOTHING.find((c) => c.id === itemId);
    if (!item) return;

    // Only one item per category
    const withoutCategory = builderItems.filter((id) => {
      const existing = MOCK_CLOTHING.find((c) => c.id === id);
      return existing?.category !== item.category;
    });

    set({ builderItems: [...withoutCategory, itemId] });
  },

  removeFromBuilder: (itemId) =>
    set((s) => ({ builderItems: s.builderItems.filter((id) => id !== itemId) })),

  clearBuilder: () => set({ builderItems: [] }),

  saveBuilderAsOutfit: (name) => {
    const { builderItems } = get();
    const outfit: Outfit = {
      id: `o_${Date.now()}`,
      name,
      items: builderItems,
      occasion: 'Casual',
      season: ['All Season'],
      tags: ['custom'],
      dateCreated: new Date().toISOString(),
      isFavorite: false,
    };
    return outfit;
  },
}));
