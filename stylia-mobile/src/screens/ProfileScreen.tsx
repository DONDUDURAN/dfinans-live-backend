import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useWardrobeStore } from '../store/wardrobeStore';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';

const { width } = Dimensions.get('window');

const STYLE_PERSONAS = [
  { label: 'Minimalist', emoji: '◻', active: true },
  { label: 'Classic', emoji: '🎩', active: false },
  { label: 'Bohemian', emoji: '🌿', active: false },
  { label: 'Streetwear', emoji: '🏙', active: false },
];

export const ProfileScreen: React.FC = () => {
  const items = useWardrobeStore((s) => s.items);
  const outfits = useWardrobeStore((s) => s.outfits);

  const totalWorn = items.reduce((acc, i) => acc + i.timesWorn, 0);
  const topItem = [...items].sort((a, b) => b.timesWorn - a.timesWorn)[0];
  const categories = [...new Set(items.map((i) => i.category))];

  const costPerWear = (items.length * 85) / Math.max(totalWorn, 1);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      {/* Profile Header */}
      <LinearGradient colors={['#1A1200', '#0D0D0D']} style={styles.profileHeader}>
        <View style={styles.avatarContainer}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>S</Text>
          </View>
          <View style={styles.avatarBadge}>
            <Ionicons name="sparkles" size={10} color={Colors.background} />
          </View>
        </View>
        <Text style={styles.profileName}>Style Maven</Text>
        <Text style={styles.profileHandle}>@stylemaven</Text>
        <View style={styles.personaRow}>
          {STYLE_PERSONAS.filter((p) => p.active).map((p) => (
            <View key={p.label} style={styles.personaBadge}>
              <Text style={styles.personaEmoji}>{p.emoji}</Text>
              <Text style={styles.personaLabel}>{p.label}</Text>
            </View>
          ))}
        </View>
      </LinearGradient>

      {/* Stats */}
      <View style={styles.statsGrid}>
        {[
          { icon: 'shirt-outline', label: 'Items', value: items.length, color: Colors.tops },
          { icon: 'layers-outline', label: 'Outfits', value: outfits.length, color: Colors.dresses },
          { icon: 'repeat-outline', label: 'Total Wears', value: totalWorn, color: Colors.gold },
          { icon: 'star-outline', label: 'Favorites', value: items.filter((i) => i.isFavorite).length, color: Colors.accessories },
        ].map((stat) => (
          <View key={stat.label} style={[styles.statCard, Shadow.sm]}>
            <View style={[styles.statIcon, { backgroundColor: stat.color + '22' }]}>
              <Ionicons name={stat.icon as any} size={18} color={stat.color} />
            </View>
            <Text style={styles.statValue}>{stat.value}</Text>
            <Text style={styles.statLabel}>{stat.label}</Text>
          </View>
        ))}
      </View>

      {/* Wardrobe Insights */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Wardrobe Insights</Text>
        <View style={styles.insightsList}>
          {topItem && (
            <View style={[styles.insightCard, Shadow.sm]}>
              <View style={[styles.insightIcon, { backgroundColor: Colors.gold + '22' }]}>
                <Ionicons name="trophy" size={20} color={Colors.gold} />
              </View>
              <View style={styles.insightInfo}>
                <Text style={styles.insightTitle}>Most Worn</Text>
                <Text style={styles.insightValue}>{topItem.name}</Text>
                <Text style={styles.insightSub}>Worn {topItem.timesWorn} times</Text>
              </View>
            </View>
          )}

          <View style={[styles.insightCard, Shadow.sm]}>
            <View style={[styles.insightIcon, { backgroundColor: Colors.success + '22' }]}>
              <Ionicons name="calculator-outline" size={20} color={Colors.success} />
            </View>
            <View style={styles.insightInfo}>
              <Text style={styles.insightTitle}>Avg. Cost Per Wear</Text>
              <Text style={styles.insightValue}>${costPerWear.toFixed(2)}</Text>
              <Text style={styles.insightSub}>Based on average item price</Text>
            </View>
          </View>

          <View style={[styles.insightCard, Shadow.sm]}>
            <View style={[styles.insightIcon, { backgroundColor: Colors.info + '22' }]}>
              <Ionicons name="leaf-outline" size={20} color={Colors.info} />
            </View>
            <View style={styles.insightInfo}>
              <Text style={styles.insightTitle}>Style Diversity</Text>
              <Text style={styles.insightValue}>{categories.length} Categories</Text>
              <Text style={styles.insightSub}>{categories.join(', ')}</Text>
            </View>
          </View>
        </View>
      </View>

      {/* Category Breakdown */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Category Breakdown</Text>
        <View style={styles.breakdownList}>
          {categories.map((cat) => {
            const count = items.filter((i) => i.category === cat).length;
            const pct = Math.round((count / items.length) * 100);
            return (
              <View key={cat} style={styles.breakdownRow}>
                <Text style={styles.breakdownLabel}>{cat}</Text>
                <View style={styles.breakdownBar}>
                  <View style={[styles.breakdownFill, { width: `${pct}%` }]} />
                </View>
                <Text style={styles.breakdownCount}>{count}</Text>
              </View>
            );
          })}
        </View>
      </View>

      {/* Settings */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Settings</Text>
        <View style={styles.settingsList}>
          {[
            { icon: 'person-outline', label: 'Edit Profile', color: Colors.textSecondary },
            { icon: 'color-palette-outline', label: 'Style Preferences', color: Colors.textSecondary },
            { icon: 'notifications-outline', label: 'Notifications', color: Colors.textSecondary },
            { icon: 'cloud-upload-outline', label: 'Sync & Backup', color: Colors.textSecondary },
            { icon: 'share-social-outline', label: 'Share Wardrobe', color: Colors.gold },
          ].map((item) => (
            <TouchableOpacity key={item.label} style={[styles.settingRow, Shadow.sm]} activeOpacity={0.8}>
              <View style={[styles.settingIcon, { backgroundColor: item.color + '22' }]}>
                <Ionicons name={item.icon as any} size={18} color={item.color} />
              </View>
              <Text style={styles.settingLabel}>{item.label}</Text>
              <Ionicons name="chevron-forward" size={16} color={Colors.textMuted} />
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={{ height: Spacing['3xl'] }} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { paddingBottom: Spacing['4xl'] },
  profileHeader: {
    alignItems: 'center',
    paddingTop: Spacing.xl,
    paddingBottom: Spacing['2xl'],
    gap: Spacing.sm,
  },
  avatarContainer: { position: 'relative' },
  avatar: {
    width: 80, height: 80, borderRadius: 40,
    backgroundColor: Colors.gold, alignItems: 'center', justifyContent: 'center',
    borderWidth: 3, borderColor: Colors.goldDark,
  },
  avatarText: { fontSize: Typography['3xl'], fontWeight: '900', color: Colors.background },
  avatarBadge: {
    position: 'absolute', bottom: 0, right: 0,
    width: 22, height: 22, borderRadius: 11, backgroundColor: Colors.gold,
    alignItems: 'center', justifyContent: 'center', borderWidth: 2, borderColor: Colors.background,
  },
  profileName: { fontSize: Typography.xl, fontWeight: '800', color: Colors.textPrimary },
  profileHandle: { fontSize: Typography.sm, color: Colors.textSecondary },
  personaRow: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.xs },
  personaBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 5,
    backgroundColor: Colors.gold + '22', borderRadius: Radius.full,
    paddingHorizontal: 12, paddingVertical: 5, borderWidth: 1, borderColor: Colors.gold + '44',
  },
  personaEmoji: { fontSize: 12 },
  personaLabel: { fontSize: Typography.xs, color: Colors.gold, fontWeight: '700' },
  statsGrid: {
    flexDirection: 'row', flexWrap: 'wrap',
    paddingHorizontal: Spacing.base, gap: Spacing.md,
    marginTop: Spacing.base,
  },
  statCard: {
    width: (width - Spacing.base * 2 - Spacing.md) / 2 - Spacing.sm,
    backgroundColor: Colors.surface, borderRadius: Radius.lg,
    padding: Spacing.base, alignItems: 'center', gap: Spacing.sm,
    borderWidth: 1, borderColor: Colors.border,
  },
  statIcon: { width: 40, height: 40, borderRadius: Radius.md, alignItems: 'center', justifyContent: 'center' },
  statValue: { fontSize: Typography['2xl'], fontWeight: '800', color: Colors.textPrimary },
  statLabel: { fontSize: Typography.xs, color: Colors.textSecondary },
  section: { paddingHorizontal: Spacing.base, marginTop: Spacing.xl, gap: Spacing.md },
  sectionTitle: { fontSize: Typography.md, fontWeight: '700', color: Colors.textPrimary },
  insightsList: { gap: Spacing.md },
  insightCard: {
    flexDirection: 'row', alignItems: 'center', gap: Spacing.md,
    backgroundColor: Colors.surface, borderRadius: Radius.lg,
    padding: Spacing.base, borderWidth: 1, borderColor: Colors.border,
  },
  insightIcon: { width: 44, height: 44, borderRadius: Radius.md, alignItems: 'center', justifyContent: 'center' },
  insightInfo: { flex: 1, gap: 2 },
  insightTitle: { fontSize: Typography.xs, color: Colors.textMuted, textTransform: 'uppercase', letterSpacing: 0.5 },
  insightValue: { fontSize: Typography.base, fontWeight: '700', color: Colors.textPrimary },
  insightSub: { fontSize: Typography.xs, color: Colors.textSecondary },
  breakdownList: { gap: Spacing.md },
  breakdownRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md },
  breakdownLabel: { width: 90, fontSize: Typography.sm, color: Colors.textSecondary, fontWeight: '600' },
  breakdownBar: { flex: 1, height: 6, backgroundColor: Colors.border, borderRadius: 3, overflow: 'hidden' },
  breakdownFill: { height: '100%', backgroundColor: Colors.gold, borderRadius: 3 },
  breakdownCount: { width: 24, fontSize: Typography.sm, color: Colors.textMuted, textAlign: 'right' },
  settingsList: { gap: Spacing.sm },
  settingRow: {
    flexDirection: 'row', alignItems: 'center', gap: Spacing.md,
    backgroundColor: Colors.surface, borderRadius: Radius.lg,
    padding: Spacing.base, borderWidth: 1, borderColor: Colors.border,
  },
  settingIcon: { width: 36, height: 36, borderRadius: Radius.sm, alignItems: 'center', justifyContent: 'center' },
  settingLabel: { flex: 1, fontSize: Typography.base, color: Colors.textPrimary, fontWeight: '600' },
});
