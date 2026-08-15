import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Image,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { useWardrobeStore } from '../store/wardrobeStore';
import { useStyleStore } from '../store/styleStore';
import { StyleSuggestionCard } from '../components/StyleSuggestionCard';
import { OutfitCard } from '../components/OutfitCard';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';
import { RootStackParamList } from '../types';

const { width } = Dimensions.get('window');

type Nav = StackNavigationProp<RootStackParamList>;

export const HomeScreen: React.FC = () => {
  const navigation = useNavigation<Nav>();
  const items = useWardrobeStore((s) => s.items);
  const outfits = useWardrobeStore((s) => s.outfits);
  const suggestions = useStyleStore((s) => s.suggestions);
  const topSuggestion = suggestions[0];

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });

  const stats = [
    { label: 'Items', value: items.length, icon: 'shirt-outline' },
    { label: 'Outfits', value: outfits.length, icon: 'layers-outline' },
    { label: 'Favorites', value: items.filter((i) => i.isFavorite).length, icon: 'heart-outline' },
  ];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <LinearGradient colors={['#1A1200', '#0D0D0D']} style={styles.header}>
        <View>
          <Text style={styles.date}>{today}</Text>
          <Text style={styles.greeting}>Good morning ✦</Text>
          <Text style={styles.headline}>What will you wear{'\n'}today?</Text>
        </View>
        <View style={styles.logoContainer}>
          <Text style={styles.logo}>S</Text>
        </View>
      </LinearGradient>

      {/* Stats Row */}
      <View style={styles.statsRow}>
        {stats.map((stat) => (
          <View key={stat.label} style={[styles.statCard, Shadow.sm]}>
            <Ionicons name={stat.icon as any} size={18} color={Colors.gold} />
            <Text style={styles.statValue}>{stat.value}</Text>
            <Text style={styles.statLabel}>{stat.label}</Text>
          </View>
        ))}
      </View>

      {/* Daily AI Suggestion */}
      {topSuggestion && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
              <Ionicons name="sparkles" size={16} color={Colors.gold} />
              <Text style={styles.sectionTitle}>AI Pick of the Day</Text>
            </View>
          </View>
          <StyleSuggestionCard suggestion={topSuggestion} />
        </View>
      )}

      {/* Recent Outfits */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recent Outfits</Text>
          <TouchableOpacity>
            <Text style={styles.seeAll}>See all</Text>
          </TouchableOpacity>
        </View>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.horizontalList}
        >
          {outfits.slice(0, 4).map((outfit) => (
            <View key={outfit.id} style={{ width: width * 0.72 }}>
              <OutfitCard outfit={outfit} />
            </View>
          ))}
        </ScrollView>
      </View>

      {/* Recently Added Items */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recently Added</Text>
          <TouchableOpacity>
            <Text style={styles.seeAll}>See all</Text>
          </TouchableOpacity>
        </View>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.horizontalList}
        >
          {items.slice(0, 6).map((item) => (
            <TouchableOpacity key={item.id} style={styles.recentItem} activeOpacity={0.85}>
              <Image
                source={{ uri: item.imageUri }}
                style={styles.recentItemImage}
                resizeMode="cover"
              />
              <LinearGradient
                colors={['transparent', 'rgba(0,0,0,0.7)']}
                style={styles.recentItemGradient}
              />
              <Text style={styles.recentItemName} numberOfLines={1}>{item.name}</Text>
              <Text style={styles.recentItemEmoji}>{item.emoji}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Quick Actions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.quickActions}>
          <TouchableOpacity
            style={[styles.quickAction, Shadow.sm]}
            onPress={() => navigation.navigate('AddItem', {})}
          >
            <View style={[styles.quickActionIcon, { backgroundColor: Colors.gold + '22' }]}>
              <Ionicons name="add-circle" size={24} color={Colors.gold} />
            </View>
            <Text style={styles.quickActionLabel}>Add Item</Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.quickAction, Shadow.sm]}>
            <View style={[styles.quickActionIcon, { backgroundColor: Colors.tops + '22' }]}>
              <Ionicons name="layers" size={24} color={Colors.tops} />
            </View>
            <Text style={styles.quickActionLabel}>Build Outfit</Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.quickAction, Shadow.sm]}>
            <View style={[styles.quickActionIcon, { backgroundColor: Colors.success + '22' }]}>
              <Ionicons name="analytics" size={24} color={Colors.success} />
            </View>
            <Text style={styles.quickActionLabel}>Stats</Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.quickAction, Shadow.sm]}>
            <View style={[styles.quickActionIcon, { backgroundColor: Colors.dresses + '22' }]}>
              <Ionicons name="calendar" size={24} color={Colors.dresses} />
            </View>
            <Text style={styles.quickActionLabel}>Plan Week</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={{ height: Spacing['3xl'] }} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    paddingBottom: Spacing['4xl'],
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    padding: Spacing.base,
    paddingTop: Spacing.xl,
    paddingBottom: Spacing.xl,
  },
  date: {
    fontSize: Typography.xs,
    color: Colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 4,
  },
  greeting: {
    fontSize: Typography.sm,
    color: Colors.gold,
    fontWeight: '500',
    marginBottom: 6,
  },
  headline: {
    fontSize: Typography['3xl'],
    fontWeight: '800',
    color: Colors.textPrimary,
    lineHeight: 42,
    letterSpacing: -0.5,
  },
  logoContainer: {
    width: 48,
    height: 48,
    borderRadius: Radius.full,
    backgroundColor: Colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: {
    fontSize: Typography.xl,
    fontWeight: '900',
    color: Colors.background,
  },
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.base,
    gap: Spacing.sm,
    marginTop: -Spacing.md,
    marginBottom: Spacing.base,
  },
  statCard: {
    flex: 1,
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    alignItems: 'center',
    gap: 4,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  statValue: {
    fontSize: Typography.xl,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  statLabel: {
    fontSize: Typography.xs,
    color: Colors.textSecondary,
  },
  section: {
    paddingHorizontal: Spacing.base,
    marginBottom: Spacing.xl,
    gap: Spacing.md,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  sectionTitle: {
    fontSize: Typography.md,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  seeAll: {
    fontSize: Typography.sm,
    color: Colors.gold,
    fontWeight: '600',
  },
  horizontalList: {
    gap: Spacing.md,
    paddingRight: Spacing.base,
  },
  recentItem: {
    width: 110,
    height: 140,
    borderRadius: Radius.lg,
    overflow: 'hidden',
    position: 'relative',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  recentItemImage: {
    width: '100%',
    height: '100%',
  },
  recentItemGradient: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 60,
  },
  recentItemName: {
    position: 'absolute',
    bottom: 8,
    left: 6,
    right: 6,
    fontSize: Typography.xs,
    color: Colors.textPrimary,
    fontWeight: '600',
  },
  recentItemEmoji: {
    position: 'absolute',
    top: 6,
    right: 6,
    fontSize: 16,
  },
  quickActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.md,
  },
  quickAction: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    alignItems: 'center',
    gap: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  quickActionIcon: {
    width: 48,
    height: 48,
    borderRadius: Radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  quickActionLabel: {
    fontSize: Typography.sm,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
});
