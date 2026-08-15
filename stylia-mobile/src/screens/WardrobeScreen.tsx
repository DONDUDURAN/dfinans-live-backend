import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { useWardrobeStore } from '../store/wardrobeStore';
import { ClothingCard } from '../components/ClothingCard';
import { CategoryFilter } from '../components/CategoryFilter';
import { Colors, Radius, Spacing, Typography } from '../theme';
import { RootStackParamList } from '../types';

const { width } = Dimensions.get('window');
const CARD_GAP = Spacing.md;
const CARD_WIDTH = (width - Spacing.base * 2 - CARD_GAP) / 2;

type Nav = StackNavigationProp<RootStackParamList>;

export const WardrobeScreen: React.FC = () => {
  const navigation = useNavigation<Nav>();
  const selectedCategory = useWardrobeStore((s) => s.selectedCategory);
  const setCategory = useWardrobeStore((s) => s.setCategory);
  const searchQuery = useWardrobeStore((s) => s.searchQuery);
  const setSearchQuery = useWardrobeStore((s) => s.setSearchQuery);
  const getFilteredItems = useWardrobeStore((s) => s.getFilteredItems);
  const toggleFavorite = useWardrobeStore((s) => s.toggleFavorite);

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const items = getFilteredItems();

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Wardrobe</Text>
          <Text style={styles.subtitle}>{items.length} items</Text>
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.iconBtn}
            onPress={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
          >
            <Ionicons
              name={viewMode === 'grid' ? 'list' : 'grid'}
              size={20}
              color={Colors.textSecondary}
            />
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.iconBtn, styles.addBtn]}
            onPress={() => navigation.navigate('AddItem', {})}
          >
            <Ionicons name="add" size={22} color={Colors.background} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Search */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={18} color={Colors.textMuted} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search by name, brand, tag..."
          placeholderTextColor={Colors.textMuted}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <Ionicons name="close-circle" size={18} color={Colors.textMuted} />
          </TouchableOpacity>
        )}
      </View>

      {/* Category Filter */}
      <CategoryFilter selected={selectedCategory} onSelect={setCategory} />

      {/* Items Grid / List */}
      {items.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyEmoji}>🧺</Text>
          <Text style={styles.emptyTitle}>No items found</Text>
          <Text style={styles.emptySubtitle}>
            {searchQuery ? 'Try a different search term' : 'Add your first clothing item'}
          </Text>
          <TouchableOpacity
            style={styles.emptyBtn}
            onPress={() => navigation.navigate('AddItem', {})}
          >
            <Ionicons name="add" size={16} color={Colors.background} />
            <Text style={styles.emptyBtnText}>Add Item</Text>
          </TouchableOpacity>
        </View>
      ) : viewMode === 'grid' ? (
        <FlatList
          data={items}
          keyExtractor={(item) => item.id}
          numColumns={2}
          contentContainerStyle={styles.grid}
          columnWrapperStyle={styles.gridRow}
          showsVerticalScrollIndicator={false}
          renderItem={({ item }) => (
            <ClothingCard
              item={item}
              size="lg"
              onPress={() => navigation.navigate('ItemDetail', { itemId: item.id })}
              onFavoriteToggle={() => toggleFavorite(item.id)}
            />
          )}
        />
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.listItem}
              onPress={() => navigation.navigate('ItemDetail', { itemId: item.id })}
              activeOpacity={0.85}
            >
              <ClothingCard item={item} size="sm" showDetails={false} />
              <View style={styles.listItemDetails}>
                <Text style={styles.listItemName}>{item.name}</Text>
                {item.brand && (
                  <Text style={styles.listItemBrand}>{item.brand}</Text>
                )}
                <View style={styles.listItemMeta}>
                  <Text style={styles.listItemCategory}>{item.category}</Text>
                  <Text style={styles.listItemWorn}>Worn {item.timesWorn}×</Text>
                </View>
                <View style={styles.listItemTags}>
                  {item.tags.slice(0, 3).map((tag) => (
                    <View key={tag} style={styles.listTag}>
                      <Text style={styles.listTagText}>{tag}</Text>
                    </View>
                  ))}
                </View>
              </View>
              <TouchableOpacity
                onPress={() => toggleFavorite(item.id)}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              >
                <Ionicons
                  name={item.isFavorite ? 'heart' : 'heart-outline'}
                  size={20}
                  color={item.isFavorite ? Colors.gold : Colors.textMuted}
                />
              </TouchableOpacity>
            </TouchableOpacity>
          )}
        />
      )}
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
    alignItems: 'center',
    gap: Spacing.sm,
  },
  iconBtn: {
    width: 38,
    height: 38,
    borderRadius: Radius.md,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addBtn: {
    backgroundColor: Colors.gold,
    borderColor: Colors.gold,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    borderWidth: 1,
    borderColor: Colors.border,
    marginHorizontal: Spacing.base,
    marginBottom: Spacing.sm,
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.md,
  },
  searchInput: {
    flex: 1,
    fontSize: Typography.base,
    color: Colors.textPrimary,
  },
  grid: {
    padding: Spacing.base,
    gap: CARD_GAP,
  },
  gridRow: {
    gap: CARD_GAP,
    justifyContent: 'space-between',
  },
  list: {
    padding: Spacing.base,
    gap: Spacing.md,
  },
  listItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  listItemDetails: {
    flex: 1,
    gap: 3,
  },
  listItemName: {
    fontSize: Typography.base,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  listItemBrand: {
    fontSize: Typography.xs,
    color: Colors.gold,
    fontWeight: '500',
  },
  listItemMeta: {
    flexDirection: 'row',
    gap: Spacing.sm,
    marginTop: 2,
  },
  listItemCategory: {
    fontSize: Typography.xs,
    color: Colors.textSecondary,
  },
  listItemWorn: {
    fontSize: Typography.xs,
    color: Colors.textMuted,
  },
  listItemTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
    marginTop: 2,
  },
  listTag: {
    backgroundColor: Colors.border,
    borderRadius: Radius.full,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  listTagText: {
    fontSize: 10,
    color: Colors.textMuted,
  },
  empty: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.md,
    padding: Spacing['2xl'],
  },
  emptyEmoji: {
    fontSize: 64,
  },
  emptyTitle: {
    fontSize: Typography.lg,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  emptySubtitle: {
    fontSize: Typography.base,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  emptyBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: Colors.gold,
    borderRadius: Radius.full,
    paddingHorizontal: Spacing.xl,
    paddingVertical: Spacing.md,
    marginTop: Spacing.sm,
  },
  emptyBtnText: {
    fontSize: Typography.base,
    fontWeight: '700',
    color: Colors.background,
  },
});
