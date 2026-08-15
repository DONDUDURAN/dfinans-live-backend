import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { ClothingCategory } from '../types';
import { Colors, Radius, Spacing, Typography } from '../theme';
import { trCategory } from '../utils/translations';

const CATEGORIES: (ClothingCategory | 'All')[] = [
  'All',
  'Tops',
  'Bottoms',
  'Dresses',
  'Outerwear',
  'Shoes',
  'Accessories',
  'Activewear',
];

const CATEGORY_EMOJIS: Record<string, string> = {
  All: '✦',
  Tops: '👕',
  Bottoms: '👖',
  Dresses: '👗',
  Outerwear: '🧥',
  Shoes: '👟',
  Accessories: '💛',
  Activewear: '🏃',
};

interface Props {
  selected: ClothingCategory | 'All';
  onSelect: (cat: ClothingCategory | 'All') => void;
}

export const CategoryFilter: React.FC<Props> = ({ selected, onSelect }) => {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.container}
    >
      {CATEGORIES.map((cat) => (
        <TouchableOpacity
          key={cat}
          style={[styles.chip, selected === cat && styles.chipActive]}
          onPress={() => onSelect(cat)}
          activeOpacity={0.8}
        >
          <Text style={styles.emoji}>{CATEGORY_EMOJIS[cat]}</Text>
          <Text style={[styles.label, selected === cat && styles.labelActive]}>
            {trCategory(cat)}
          </Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: Spacing.base,
    gap: Spacing.sm,
    paddingVertical: Spacing.xs,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: Colors.surface,
    borderRadius: Radius.full,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  chipActive: {
    backgroundColor: Colors.gold + '22',
    borderColor: Colors.gold,
  },
  emoji: {
    fontSize: 14,
  },
  label: {
    fontSize: Typography.sm,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  labelActive: {
    color: Colors.gold,
  },
});
