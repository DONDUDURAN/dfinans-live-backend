import React from 'react';
import { Image, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { RouteProp, useNavigation, useRoute } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { RootStackParamList } from '../types';
import { useWardrobeStore } from '../store/wardrobeStore';
import { Colors, Radius, Spacing, Typography } from '../theme';
import { trCategory, trOccasion } from '../utils/translations';

type DetailRoute = RouteProp<RootStackParamList, 'ItemDetail'>;

export const ItemDetailScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation();
  const route = useRoute<DetailRoute>();
  const item = useWardrobeStore((s) => s.getItemById(route.params.itemId));

  if (!item) {
    return (
      <View style={styles.center}>
        <Text style={styles.title}>Ürün bulunamadı</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={[styles.content, { paddingTop: insets.top + Spacing.base }]}>
      <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
        <Ionicons name="arrow-back" size={20} color={Colors.textPrimary} />
      </TouchableOpacity>
      <Image source={{ uri: item.imageUri }} style={styles.image} />
      <Text style={styles.title}>{item.name}</Text>
      {!!item.brand && <Text style={styles.brand}>{item.brand}</Text>}
      <View style={styles.row}>
        <Text style={styles.meta}>Kategori: {trCategory(item.category)}</Text>
        <Text style={styles.meta}>Renk: {item.color}</Text>
      </View>
      <Text style={styles.sectionTitle}>Kullanım amaçları</Text>
      <View style={styles.tagRow}>
        {item.occasions.map((occ) => (
          <View key={occ} style={styles.tag}>
            <Text style={styles.tagText}>{trOccasion(occ)}</Text>
          </View>
        ))}
      </View>
      <Text style={styles.sectionTitle}>Etiketler</Text>
      <View style={styles.tagRow}>
        {item.tags.map((tag) => (
          <View key={tag} style={styles.tagMuted}>
            <Text style={styles.tagMutedText}>#{tag}</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    padding: Spacing.base,
    paddingTop: Spacing.base,
    gap: Spacing.sm,
  },
  center: {
    flex: 1,
    backgroundColor: Colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.sm,
  },
  image: {
    width: '100%',
    height: 320,
    borderRadius: Radius.lg,
  },
  title: {
    color: Colors.textPrimary,
    fontSize: Typography['2xl'],
    fontWeight: '800',
  },
  brand: {
    color: Colors.gold,
    fontSize: Typography.base,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  meta: {
    color: Colors.textSecondary,
    fontSize: Typography.sm,
  },
  sectionTitle: {
    marginTop: Spacing.sm,
    color: Colors.textPrimary,
    fontSize: Typography.base,
    fontWeight: '700',
  },
  tagRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
    flexWrap: 'wrap',
  },
  tag: {
    backgroundColor: Colors.gold + '22',
    borderColor: Colors.gold + '55',
    borderWidth: 1,
    borderRadius: Radius.full,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
  },
  tagText: {
    color: Colors.goldLight,
    fontSize: Typography.xs,
    fontWeight: '700',
  },
  tagMuted: {
    backgroundColor: Colors.surface,
    borderColor: Colors.border,
    borderWidth: 1,
    borderRadius: Radius.full,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
  },
  tagMutedText: {
    color: Colors.textSecondary,
    fontSize: Typography.xs,
  },
});
