import React from 'react';
import {
  Dimensions,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { useWardrobeStore } from '../store/wardrobeStore';
import { useStyleStore } from '../store/styleStore';
import { useUserStore } from '../store/userStore';
import { StyleSuggestionCard } from '../components/StyleSuggestionCard';
import { OutfitCard } from '../components/OutfitCard';
import { BrandMark } from '../components/BrandMark';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';

const { width } = Dimensions.get('window');

export const HomeScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<any>();
  const items = useWardrobeStore((s) => s.items);
  const outfits = useWardrobeStore((s) => s.outfits);
  const suggestions = useStyleStore((s) => s.suggestions);
  const fullName = useUserStore((s) => s.fullName);

  const topSuggestion = suggestions[0];

  const stats = [
    { label: 'Parça', value: items.length, icon: 'shirt-outline' },
    { label: 'Stil', value: outfits.length, icon: 'layers-outline' },
    { label: 'Favori', value: items.filter((i) => i.isFavorite).length, icon: 'heart-outline' },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <LinearGradient colors={['#050D08', Colors.background]} style={[styles.header, { paddingTop: insets.top + Spacing.base }]}>
        <BrandMark size="md" />
        <Text style={styles.greeting}>{fullName.split(' ')[0] || 'stil sahibi'}</Text>
        <Text style={styles.headline}>Bugün sanal ikizin{'\n'}ne giyiyor?</Text>
      </LinearGradient>

      <View style={styles.statsRow}>
        {stats.map((stat) => (
          <View key={stat.label} style={styles.statCard}>
            <Ionicons name={stat.icon as any} size={18} color={Colors.gold} />
            <Text style={styles.statValue}>{stat.value}</Text>
            <Text style={styles.statLabel}>{stat.label}</Text>
          </View>
        ))}
      </View>

      {topSuggestion && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
              <Ionicons name="sparkles" size={16} color={Colors.gold} />
            <Text style={styles.sectionTitle}>Günün Seçimi</Text>
            </View>
          </View>
          <StyleSuggestionCard suggestion={topSuggestion} />
        </View>
      )}

      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Son Stiller</Text>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.horizontalList}>
          {outfits.slice(0, 4).map((outfit) => (
            <View key={outfit.id} style={{ width: width * 0.72 }}>
              <OutfitCard outfit={outfit} />
            </View>
          ))}
        </ScrollView>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Sanal İkiz Kabini</Text>
        <View style={styles.kabinStack}>
          <TouchableOpacity style={styles.kabinAction} onPress={() => navigation.navigate('AIStyle')}>
            <View style={[styles.kabinIconWrap, { backgroundColor: Colors.gold + '22' }]}>
              <Ionicons name="body-outline" size={20} color={Colors.gold} />
            </View>
            <View style={styles.kabinText}>
              <Text style={styles.kabinTitle}>Kabinde dene</Text>
            </View>
            <Ionicons name="chevron-forward" size={16} color={Colors.textMuted} />
          </TouchableOpacity>

          <TouchableOpacity style={styles.kabinAction} onPress={() => navigation.navigate('Profile')}>
            <View style={[styles.kabinIconWrap, { backgroundColor: Colors.success + '22' }]}>
              <Ionicons name="person-outline" size={20} color={Colors.success} />
            </View>
            <View style={styles.kabinText}>
              <Text style={styles.kabinTitle}>İkizi güncelle</Text>
            </View>
            <Ionicons name="chevron-forward" size={16} color={Colors.textMuted} />
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Yeni Eklenenler</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.horizontalList}>
          {items.slice(0, 6).map((item) => (
            <TouchableOpacity key={item.id} style={styles.recentItem} activeOpacity={0.85}>
              <Image source={{ uri: item.imageUri }} style={styles.recentItemImage} resizeMode="cover" />
              <LinearGradient colors={['transparent', 'rgba(0,0,0,0.7)']} style={styles.recentItemGradient} />
              <Text style={styles.recentItemName} numberOfLines={1}>
                {item.name}
              </Text>
              <Text style={styles.recentItemEmoji}>{item.emoji}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
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
    padding: Spacing.base,
    paddingBottom: Spacing['2xl'],
    gap: 8,
  },
  greeting: {
    fontSize: Typography.sm,
    color: Colors.goldLight,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  headline: {
    fontSize: Typography['2xl'],
    fontWeight: '700',
    color: Colors.textPrimary,
    lineHeight: 38,
    letterSpacing: -0.5,
  },
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.base,
    gap: Spacing.sm,
    marginTop: -Spacing.sm,
    marginBottom: Spacing.base,
  },
  statCard: {
    flex: 1,
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    alignItems: 'center',
    gap: 2,
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
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  sectionTitle: {
    color: Colors.textMuted,
    fontSize: Typography.xs,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1.5,
  },
  horizontalList: {
    gap: Spacing.md,
    paddingRight: Spacing.base,
  },
  kabinStack: {
    gap: Spacing.md,
  },
  kabinAction: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.base,
  },
  kabinIconWrap: {
    width: 42,
    height: 42,
    borderRadius: Radius.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  kabinText: {
    flex: 1,
    gap: 2,
  },
  kabinTitle: {
    color: Colors.textPrimary,
    fontSize: Typography.base,
    fontWeight: '700',
  },
  kabinDesc: {
    color: Colors.textSecondary,
    fontSize: Typography.xs,
  },
  recentItem: {
    width: 110,
    height: 140,
    borderRadius: Radius.lg,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  recentItemImage: {
    width: '100%',
    height: '100%',
  },
  recentItemGradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
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
});
