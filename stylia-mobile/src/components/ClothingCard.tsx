import React from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { ClothingItem } from '../types';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';

interface Props {
  item: ClothingItem;
  onPress?: () => void;
  onFavoriteToggle?: () => void;
  size?: 'sm' | 'md' | 'lg';
  showDetails?: boolean;
  isSelected?: boolean;
}

export const ClothingCard: React.FC<Props> = ({
  item,
  onPress,
  onFavoriteToggle,
  size = 'md',
  showDetails = true,
  isSelected = false,
}) => {
  const cardWidth = size === 'sm' ? 110 : size === 'lg' ? 200 : 155;
  const imageHeight = size === 'sm' ? 110 : size === 'lg' ? 200 : 155;

  return (
    <TouchableOpacity
      style={[
        styles.card,
        { width: cardWidth },
        isSelected && styles.cardSelected,
        Shadow.sm,
      ]}
      onPress={onPress}
      activeOpacity={0.85}
    >
      <View style={[styles.imageContainer, { height: imageHeight }]}>
        <Image
          source={{ uri: item.imageUri }}
          style={styles.image}
          resizeMode="cover"
        />
        <View style={styles.emojiOverlay}>
          <Text style={styles.emoji}>{item.emoji}</Text>
        </View>

        {onFavoriteToggle && (
          <TouchableOpacity
            style={styles.favoriteBtn}
            onPress={onFavoriteToggle}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Ionicons
              name={item.isFavorite ? 'heart' : 'heart-outline'}
              size={18}
              color={item.isFavorite ? Colors.gold : Colors.textSecondary}
            />
          </TouchableOpacity>
        )}

        {isSelected && (
          <View style={styles.selectedOverlay}>
            <Ionicons name="checkmark-circle" size={28} color={Colors.gold} />
          </View>
        )}
      </View>

      {showDetails && (
        <View style={styles.details}>
          <Text style={styles.name} numberOfLines={1}>
            {item.name}
          </Text>
          {item.brand && (
            <Text style={styles.brand} numberOfLines={1}>
              {item.brand}
            </Text>
          )}
          <View style={styles.meta}>
            <View style={[styles.categoryDot, { backgroundColor: getCategoryColor(item.category) }]} />
            <Text style={styles.category}>{item.category}</Text>
          </View>
        </View>
      )}
    </TouchableOpacity>
  );
};

const getCategoryColor = (cat: string) => {
  const map: Record<string, string> = {
    Tops: Colors.tops,
    Bottoms: Colors.bottoms,
    Shoes: Colors.shoes,
    Accessories: Colors.accessories,
    Outerwear: Colors.outerwear,
    Dresses: Colors.dresses,
    Activewear: Colors.success,
  };
  return map[cat] ?? Colors.textMuted;
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  cardSelected: {
    borderColor: Colors.gold,
    borderWidth: 2,
  },
  imageContainer: {
    width: '100%',
    backgroundColor: Colors.surfaceElevated,
    position: 'relative',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  emojiOverlay: {
    position: 'absolute',
    bottom: 6,
    left: 8,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: Radius.sm,
    paddingHorizontal: 5,
    paddingVertical: 2,
  },
  emoji: {
    fontSize: 14,
  },
  favoriteBtn: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: Radius.full,
    width: 30,
    height: 30,
    alignItems: 'center',
    justifyContent: 'center',
  },
  selectedOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(201,168,76,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  details: {
    padding: Spacing.sm,
    gap: 2,
  },
  name: {
    fontSize: Typography.sm,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  brand: {
    fontSize: Typography.xs,
    color: Colors.gold,
    fontWeight: '500',
  },
  meta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 2,
  },
  categoryDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  category: {
    fontSize: Typography.xs,
    color: Colors.textSecondary,
  },
});
