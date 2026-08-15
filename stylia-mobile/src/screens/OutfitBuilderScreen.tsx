import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  FlatList,
  Image,
  TextInput,
  Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useWardrobeStore } from '../store/wardrobeStore';
import { useStyleStore } from '../store/styleStore';
import { ClothingCard } from '../components/ClothingCard';
import { CategoryFilter } from '../components/CategoryFilter';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';
import { ClothingCategory } from '../types';

const SLOT_CATEGORIES: ClothingCategory[] = ['Tops', 'Bottoms', 'Dresses', 'Outerwear', 'Shoes', 'Accessories'];

const SLOT_EMOJIS: Record<ClothingCategory, string> = {
  Tops: '👕',
  Bottoms: '👖',
  Dresses: '👗',
  Outerwear: '🧥',
  Shoes: '👟',
  Accessories: '💛',
  Activewear: '🏃',
};

export const OutfitBuilderScreen: React.FC = () => {
  const items = useWardrobeStore((s) => s.items);
  const getItemById = useWardrobeStore((s) => s.getItemById);
  const addOutfit = useWardrobeStore((s) => s.addOutfit);
  const builderItems = useStyleStore((s) => s.builderItems);
  const addToBuilder = useStyleStore((s) => s.addToBuilder);
  const removeFromBuilder = useStyleStore((s) => s.removeFromBuilder);
  const clearBuilder = useStyleStore((s) => s.clearBuilder);
  const saveBuilderAsOutfit = useStyleStore((s) => s.saveBuilderAsOutfit);

  const [activeCategory, setActiveCategory] = useState<ClothingCategory>('Tops');
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [outfitName, setOutfitName] = useState('');

  const categoryItems = items.filter((i) => i.category === activeCategory);
  const builderItemObjects = builderItems.map((id) => getItemById(id)).filter(Boolean);

  const handleSave = () => {
    if (!outfitName.trim()) {
      Alert.alert('Name required', 'Please give your outfit a name.');
      return;
    }
    const outfit = saveBuilderAsOutfit(outfitName.trim());
    addOutfit(outfit);
    clearBuilder();
    setOutfitName('');
    setShowSaveModal(false);
    Alert.alert('✨ Outfit Saved!', `"${outfit.name}" has been added to your collection.`);
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Outfit Builder</Text>
          <Text style={styles.subtitle}>Mix & match your wardrobe</Text>
        </View>
        {builderItems.length > 0 && (
          <View style={styles.headerActions}>
            <TouchableOpacity style={styles.clearBtn} onPress={clearBuilder}>
              <Ionicons name="refresh" size={16} color={Colors.textSecondary} />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.saveBtn}
              onPress={() => setShowSaveModal(true)}
            >
              <Ionicons name="save-outline" size={16} color={Colors.background} />
              <Text style={styles.saveBtnText}>Save</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      {/* Outfit Canvas */}
      <View style={[styles.canvas, Shadow.md]}>
        {builderItems.length === 0 ? (
          <View style={styles.canvasEmpty}>
            <Text style={styles.canvasEmptyEmoji}>✦</Text>
            <Text style={styles.canvasEmptyText}>Start building your outfit below</Text>
          </View>
        ) : (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.canvasItems}
          >
            {builderItemObjects.map((item) => (
              <View key={item!.id} style={styles.canvasItem}>
                <Image
                  source={{ uri: item!.imageUri }}
                  style={styles.canvasItemImage}
                  resizeMode="cover"
                />
                <LinearGradient
                  colors={['transparent', 'rgba(0,0,0,0.8)']}
                  style={StyleSheet.absoluteFill}
                />
                <TouchableOpacity
                  style={styles.canvasItemRemove}
                  onPress={() => removeFromBuilder(item!.id)}
                >
                  <Ionicons name="close" size={14} color={Colors.textPrimary} />
                </TouchableOpacity>
                <Text style={styles.canvasItemEmoji}>{item!.emoji}</Text>
                <Text style={styles.canvasItemName} numberOfLines={1}>
                  {item!.name}
                </Text>
              </View>
            ))}
          </ScrollView>
        )}

        {/* Slot indicators */}
        <View style={styles.slots}>
          {SLOT_CATEGORIES.map((cat) => {
            const filled = builderItemObjects.some((i) => i?.category === cat);
            return (
              <TouchableOpacity
                key={cat}
                style={[styles.slot, filled && styles.slotFilled, activeCategory === cat && styles.slotActive]}
                onPress={() => setActiveCategory(cat)}
              >
                <Text style={styles.slotEmoji}>{SLOT_EMOJIS[cat]}</Text>
                {filled && (
                  <View style={styles.slotCheck}>
                    <Ionicons name="checkmark" size={8} color={Colors.background} />
                  </View>
                )}
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Category selector */}
      <View style={styles.categorySection}>
        <Text style={styles.categoryTitle}>
          {SLOT_EMOJIS[activeCategory]} {activeCategory}
        </Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.categoryButtons}
        >
          {SLOT_CATEGORIES.map((cat) => (
            <TouchableOpacity
              key={cat}
              style={[styles.catBtn, activeCategory === cat && styles.catBtnActive]}
              onPress={() => setActiveCategory(cat)}
            >
              <Text style={styles.catBtnEmoji}>{SLOT_EMOJIS[cat]}</Text>
              <Text style={[styles.catBtnText, activeCategory === cat && styles.catBtnTextActive]}>
                {cat}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Items to pick from */}
      {categoryItems.length === 0 ? (
        <View style={styles.noItems}>
          <Text style={styles.noItemsText}>No {activeCategory} in your wardrobe yet</Text>
        </View>
      ) : (
        <FlatList
          data={categoryItems}
          keyExtractor={(item) => item.id}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.itemList}
          renderItem={({ item }) => (
            <ClothingCard
              item={item}
              size="md"
              isSelected={builderItems.includes(item.id)}
              onPress={() => {
                if (builderItems.includes(item.id)) {
                  removeFromBuilder(item.id);
                } else {
                  addToBuilder(item.id);
                }
              }}
            />
          )}
        />
      )}

      {/* Save Outfit Modal */}
      <Modal
        visible={showSaveModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowSaveModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Name Your Outfit</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="e.g. Monday Power Look"
              placeholderTextColor={Colors.textMuted}
              value={outfitName}
              onChangeText={setOutfitName}
              autoFocus
            />
            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.modalCancel}
                onPress={() => setShowSaveModal(false)}
              >
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.modalSave} onPress={handleSave}>
                <Ionicons name="sparkles" size={16} color={Colors.background} />
                <Text style={styles.modalSaveText}>Save Outfit</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.base,
    paddingTop: Spacing.base,
    paddingBottom: Spacing.md,
  },
  title: {
    fontSize: Typography['2xl'],
    fontWeight: '800',
    color: Colors.textPrimary,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: Typography.sm,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  headerActions: {
    flexDirection: 'row',
    gap: Spacing.sm,
  },
  clearBtn: {
    width: 38,
    height: 38,
    borderRadius: Radius.md,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  saveBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: Colors.gold,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
  },
  saveBtnText: {
    fontSize: Typography.sm,
    fontWeight: '700',
    color: Colors.background,
  },
  canvas: {
    marginHorizontal: Spacing.base,
    backgroundColor: Colors.surface,
    borderRadius: Radius.xl,
    borderWidth: 1,
    borderColor: Colors.border,
    overflow: 'hidden',
    minHeight: 180,
  },
  canvasEmpty: {
    height: 130,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.sm,
  },
  canvasEmptyEmoji: {
    fontSize: 32,
    color: Colors.textMuted,
  },
  canvasEmptyText: {
    fontSize: Typography.sm,
    color: Colors.textMuted,
  },
  canvasItems: {
    padding: Spacing.base,
    gap: Spacing.md,
  },
  canvasItem: {
    width: 100,
    height: 120,
    borderRadius: Radius.lg,
    overflow: 'hidden',
    position: 'relative',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  canvasItemImage: {
    width: '100%',
    height: '100%',
  },
  canvasItemRemove: {
    position: 'absolute',
    top: 5,
    right: 5,
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: 'rgba(0,0,0,0.7)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2,
  },
  canvasItemEmoji: {
    position: 'absolute',
    bottom: 24,
    left: 6,
    fontSize: 12,
  },
  canvasItemName: {
    position: 'absolute',
    bottom: 6,
    left: 6,
    right: 6,
    fontSize: 9,
    color: Colors.textPrimary,
    fontWeight: '600',
  },
  slots: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.base,
    paddingBottom: Spacing.md,
    paddingTop: Spacing.sm,
    gap: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  slot: {
    width: 36,
    height: 36,
    borderRadius: Radius.sm,
    backgroundColor: Colors.surfaceElevated,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
    position: 'relative',
  },
  slotFilled: {
    borderColor: Colors.gold,
    backgroundColor: Colors.gold + '22',
  },
  slotActive: {
    borderColor: Colors.gold,
    borderWidth: 2,
  },
  slotEmoji: {
    fontSize: 16,
  },
  slotCheck: {
    position: 'absolute',
    top: -4,
    right: -4,
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: Colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
  },
  categorySection: {
    paddingHorizontal: Spacing.base,
    paddingTop: Spacing.md,
    paddingBottom: Spacing.sm,
    gap: Spacing.sm,
  },
  categoryTitle: {
    fontSize: Typography.md,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  categoryButtons: {
    gap: Spacing.sm,
    paddingRight: Spacing.base,
  },
  catBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: Spacing.md,
    paddingVertical: 7,
    borderRadius: Radius.full,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  catBtnActive: {
    backgroundColor: Colors.gold + '22',
    borderColor: Colors.gold,
  },
  catBtnEmoji: {
    fontSize: 14,
  },
  catBtnText: {
    fontSize: Typography.sm,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  catBtnTextActive: {
    color: Colors.gold,
  },
  itemList: {
    paddingHorizontal: Spacing.base,
    paddingBottom: Spacing.base,
    gap: Spacing.md,
  },
  noItems: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing['2xl'],
  },
  noItemsText: {
    fontSize: Typography.base,
    color: Colors.textMuted,
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.75)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing['2xl'],
  },
  modalCard: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.xl,
    padding: Spacing.xl,
    width: '100%',
    borderWidth: 1,
    borderColor: Colors.border,
    gap: Spacing.base,
  },
  modalTitle: {
    fontSize: Typography.lg,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  modalInput: {
    backgroundColor: Colors.surfaceElevated,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.base,
    fontSize: Typography.base,
    color: Colors.textPrimary,
  },
  modalActions: {
    flexDirection: 'row',
    gap: Spacing.md,
    marginTop: Spacing.sm,
  },
  modalCancel: {
    flex: 1,
    padding: Spacing.md,
    borderRadius: Radius.md,
    backgroundColor: Colors.surfaceElevated,
    alignItems: 'center',
  },
  modalCancelText: {
    fontSize: Typography.base,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  modalSave: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    padding: Spacing.md,
    borderRadius: Radius.md,
    backgroundColor: Colors.gold,
  },
  modalSaveText: {
    fontSize: Typography.base,
    fontWeight: '700',
    color: Colors.background,
  },
});
