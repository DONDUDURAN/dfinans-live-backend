export type ClothingCategory =
  | 'Tops'
  | 'Bottoms'
  | 'Shoes'
  | 'Accessories'
  | 'Outerwear'
  | 'Dresses'
  | 'Activewear';

export type Season = 'Spring' | 'Summer' | 'Fall' | 'Winter' | 'All Season';

export type Occasion =
  | 'Casual'
  | 'Work'
  | 'Formal'
  | 'Sport'
  | 'Party'
  | 'Date Night'
  | 'Beach';

export type Color =
  | 'Black'
  | 'White'
  | 'Gray'
  | 'Beige'
  | 'Brown'
  | 'Navy'
  | 'Blue'
  | 'Green'
  | 'Red'
  | 'Pink'
  | 'Purple'
  | 'Yellow'
  | 'Orange'
  | 'Multi';

export interface ClothingItem {
  id: string;
  name: string;
  brand?: string;
  category: ClothingCategory;
  color: Color;
  colors?: Color[];
  season: Season[];
  occasions: Occasion[];
  imageUri: string;
  emoji: string;
  tags: string[];
  dateAdded: string;
  timesWorn: number;
  isFavorite: boolean;
}

export interface Outfit {
  id: string;
  name: string;
  items: string[]; // ClothingItem IDs
  occasion: Occasion;
  season: Season[];
  tags: string[];
  dateCreated: string;
  isFavorite: boolean;
  aiGenerated?: boolean;
  rating?: number;
}

export interface StyleSuggestion {
  id: string;
  title: string;
  description: string;
  outfit: Outfit;
  mood: string;
  confidence: number; // 0–100
  reasons: string[];
  createdAt: string;
}

export interface UserProfile {
  id: string;
  name: string;
  stylePreferences: Occasion[];
  favoriteColors: Color[];
  bodyType?: string;
  sustainabilityScore: number;
  wardrobeValue: number;
  totalItems: number;
}

export type RootStackParamList = {
  MainTabs: undefined;
  AddItem: { category?: ClothingCategory };
  ItemDetail: { itemId: string };
  OutfitDetail: { outfitId: string };
  StyleResult: { suggestionId: string };
};

export type TabParamList = {
  Home: undefined;
  Wardrobe: undefined;
  OutfitBuilder: undefined;
  AIStyle: undefined;
  Profile: undefined;
};
