import { create } from 'zustand';
import { ClothingItem, ClothingCategory, Outfit, Occasion } from '../types';
import { MOCK_CLOTHING, MOCK_OUTFITS } from '../data/mockData';

interface WardrobeState {
  items: ClothingItem[];
  outfits: Outfit[];
  selectedCategory: ClothingCategory | 'All';
  searchQuery: string;

  // Actions
  addItem: (item: ClothingItem) => void;
  removeItem: (id: string) => void;
  toggleFavorite: (id: string) => void;
  incrementWorn: (id: string) => void;
  setCategory: (cat: ClothingCategory | 'All') => void;
  setSearchQuery: (q: string) => void;
  addOutfit: (outfit: Outfit) => void;
  removeOutfit: (id: string) => void;
  toggleOutfitFavorite: (id: string) => void;

  // Computed helpers
  getFilteredItems: () => ClothingItem[];
  getItemById: (id: string) => ClothingItem | undefined;
  getOutfitById: (id: string) => Outfit | undefined;
  getItemsByCategory: (cat: ClothingCategory) => ClothingItem[];
  getOutfitsByOccasion: (occ: Occasion) => Outfit[];
}

export const useWardrobeStore = create<WardrobeState>((set, get) => ({
  items: MOCK_CLOTHING,
  outfits: MOCK_OUTFITS,
  selectedCategory: 'All',
  searchQuery: '',

  addItem: (item) => set((s) => ({ items: [item, ...s.items] })),

  removeItem: (id) =>
    set((s) => ({ items: s.items.filter((i) => i.id !== id) })),

  toggleFavorite: (id) =>
    set((s) => ({
      items: s.items.map((i) =>
        i.id === id ? { ...i, isFavorite: !i.isFavorite } : i
      ),
    })),

  incrementWorn: (id) =>
    set((s) => ({
      items: s.items.map((i) =>
        i.id === id ? { ...i, timesWorn: i.timesWorn + 1 } : i
      ),
    })),

  setCategory: (cat) => set({ selectedCategory: cat }),

  setSearchQuery: (q) => set({ searchQuery: q }),

  addOutfit: (outfit) => set((s) => ({ outfits: [outfit, ...s.outfits] })),

  removeOutfit: (id) =>
    set((s) => ({ outfits: s.outfits.filter((o) => o.id !== id) })),

  toggleOutfitFavorite: (id) =>
    set((s) => ({
      outfits: s.outfits.map((o) =>
        o.id === id ? { ...o, isFavorite: !o.isFavorite } : o
      ),
    })),

  getFilteredItems: () => {
    const { items, selectedCategory, searchQuery } = get();
    return items.filter((item) => {
      const matchesCat =
        selectedCategory === 'All' || item.category === selectedCategory;
      const matchesSearch =
        !searchQuery ||
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (item.brand?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false) ||
        item.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesCat && matchesSearch;
    });
  },

  getItemById: (id) => get().items.find((i) => i.id === id),

  getOutfitById: (id) => get().outfits.find((o) => o.id === id),

  getItemsByCategory: (cat) => get().items.filter((i) => i.category === cat),

  getOutfitsByOccasion: (occ) =>
    get().outfits.filter((o) => o.occasion === occ),
}));
