export const Colors = {
  // Core brand palette — luxury monochrome with gold accent
  background: '#08080A',
  surface: '#111217',
  surfaceElevated: '#1A1D24',
  border: '#2B2F3A',
  borderLight: '#3B4050',

  // Text
  textPrimary: '#F8F8FA',
  textSecondary: '#C6CBD7',
  textMuted: '#8B92A1',

  // Accent — premium teal / deep aqua (replaces amber gold)
  gold: '#10A8A0',
  goldLight: '#6CDDD6',
  goldDark: '#0A7A74',

  // Status
  success: '#4CAF7D',
  warning: '#E8A435',
  error: '#E85555',
  info: '#5585E8',

  // Category colors
  tops: '#7B8CE8',
  bottoms: '#E87B8C',
  shoes: '#8CE87B',
  accessories: '#E8C97A',
  outerwear: '#7BE8D8',
  dresses: '#D87BE8',
};

export const Typography = {
  // Font families (Expo uses system fonts by default)
  fontRegular: 'System',
  fontMedium: 'System',
  fontBold: 'System',

  // Sizes
  xs: 11,
  sm: 13,
  base: 15,
  md: 17,
  lg: 20,
  xl: 24,
  '2xl': 30,
  '3xl': 36,
  '4xl': 44,

  // Line heights
  lineHeightTight: 1.2,
  lineHeightBase: 1.5,
  lineHeightRelaxed: 1.75,
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  base: 16,
  lg: 20,
  xl: 24,
  '2xl': 32,
  '3xl': 48,
  '4xl': 64,
};

export const Radius = {
  sm: 6,
  md: 12,
  lg: 16,
  xl: 24,
  full: 9999,
};

export const Shadow = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 3,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
    elevation: 6,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.5,
    shadowRadius: 16,
    elevation: 12,
  },
  gold: {
    shadowColor: '#10A8A0',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 8,
  },
};
