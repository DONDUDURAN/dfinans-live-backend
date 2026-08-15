import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Image,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { Outfit } from '../types';
import { useWardrobeStore } from '../store/wardrobeStore';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';
import { trOccasion } from '../utils/translations';

interface Props {
  outfit: Outfit;
  onPress?: () => void;
  onFavoriteToggle?: () => void;
  showActions?: boolean;
}

export const OutfitCard: React.FC<Props> = ({
  outfit,
  onPress,
  onFavoriteToggle,
  showActions = true,
}) => {
  const getItemById = useWardrobeStore((s) => s.getItemById);
  const items = outfit.items.slice(0, 4).map((id) => getItemById(id)).filter(Boolean);

  return (
    <TouchableOpacity
      style={[styles.card, Shadow.md]}
      onPress={onPress}
      activeOpacity={0.88}
    >
      {/* Item preview grid */}
      <View style={styles.previewGrid}>
        {items.length > 0 ? (
          items.map((item, idx) => (
            <View key={item!.id} style={[styles.previewCell, idx === 0 && styles.previewCellMain]}>
              <Image
                source={{ uri: item!.imageUri }}
                style={styles.previewImage}
                resizeMode="cover"
              />
            </View>
          ))
        ) : (
          <View style={styles.emptyPreview}>
            <Text style={styles.emptyEmoji}>👗</Text>
          </View>
        )}

        <LinearGradient
          colors={['transparent', 'rgba(0,0,0,0.85)']}
          style={styles.gradient}
        />

        {outfit.aiGenerated && (
          <View style={styles.aiBadge}>
            <Ionicons name="sparkles" size={10} color={Colors.background} />
            <Text style={styles.aiBadgeText}>AI</Text>
          </View>
        )}

        {showActions && onFavoriteToggle && (
          <TouchableOpacity style={styles.favoriteBtn} onPress={onFavoriteToggle}>
            <Ionicons
              name={outfit.isFavorite ? 'heart' : 'heart-outline'}
              size={18}
              color={outfit.isFavorite ? Colors.gold : Colors.textSecondary}
            />
          </TouchableOpacity>
        )}
      </View>

      {/* Details */}
      <View style={styles.details}>
        <View style={styles.row}>
          <Text style={styles.name} numberOfLines={1}>{outfit.name}</Text>
          {outfit.rating && (
            <View style={styles.ratingRow}>
              <Ionicons name="star" size={11} color={Colors.gold} />
              <Text style={styles.rating}>{outfit.rating}</Text>
            </View>
          )}
        </View>

        <View style={styles.tags}>
          <View style={styles.tag}>
            <Text style={styles.tagText}>{trOccasion(outfit.occasion)}</Text>
          </View>
          {outfit.tags.slice(0, 2).map((t) => (
            <View key={t} style={[styles.tag, styles.tagSecondary]}>
              <Text style={[styles.tagText, styles.tagTextSecondary]}>{t}</Text>
            </View>
          ))}
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.xl,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  previewGrid: {
    height: 180,
    flexDirection: 'row',
    flexWrap: 'wrap',
    position: 'relative',
    backgroundColor: Colors.surfaceElevated,
  },
  previewCell: {
    width: '50%',
    height: '50%',
    borderWidth: 0.5,
    borderColor: Colors.background,
  },
  previewCellMain: {
    width: '50%',
    height: '100%',
  },
  previewImage: {
    width: '100%',
    height: '100%',
  },
  emptyPreview: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyEmoji: {
    fontSize: 48,
  },
  gradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: 60,
  },
  aiBadge: {
    position: 'absolute',
    top: 10,
    left: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: Colors.gold,
    borderRadius: Radius.full,
    paddingHorizontal: 7,
    paddingVertical: 3,
  },
  aiBadgeText: {
    fontSize: Typography.xs,
    fontWeight: '700',
    color: Colors.background,
  },
  favoriteBtn: {
    position: 'absolute',
    top: 8,
    right: 10,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: Radius.full,
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  details: {
    padding: Spacing.base,
    gap: Spacing.sm,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  name: {
    fontSize: Typography.base,
    fontWeight: '700',
    color: Colors.textPrimary,
    flex: 1,
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  rating: {
    fontSize: Typography.sm,
    color: Colors.gold,
    fontWeight: '600',
  },
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  tag: {
    backgroundColor: Colors.gold + '22',
    borderRadius: Radius.full,
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderWidth: 1,
    borderColor: Colors.gold + '44',
  },
  tagText: {
    fontSize: Typography.xs,
    color: Colors.gold,
    fontWeight: '600',
  },
  tagSecondary: {
    backgroundColor: Colors.border,
    borderColor: Colors.borderLight,
  },
  tagTextSecondary: {
    color: Colors.textSecondary,
  },
});
