import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useStyleStore } from '../store/styleStore';
import { StyleSuggestionCard } from '../components/StyleSuggestionCard';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';
import { Occasion } from '../types';
import { useUserStore } from '../store/userStore';

const OCCASIONS: Occasion[] = ['Casual', 'Work', 'Formal', 'Party', 'Date Night', 'Sport', 'Beach'];

const OCCASION_LABELS: Record<Occasion, string> = {
  Casual: 'Günlük',
  Work: 'Ofis',
  Formal: 'Resmi',
  Party: 'Parti',
  'Date Night': 'Akşam',
  Sport: 'Spor',
  Beach: 'Plaj',
};

const OCCASION_EMOJIS: Record<Occasion, string> = {
  Casual: '☀️',
  Work: '💼',
  Formal: '🎩',
  Party: '🎉',
  'Date Night': '🌙',
  Sport: '🏃',
  Beach: '🌊',
};

const MOODS = [
  { label: 'Güçlü', emoji: '🖤', color: Colors.textPrimary },
  { label: 'Romantik', emoji: '🌸', color: Colors.dresses },
  { label: 'Minimal', emoji: '✦', color: Colors.textSecondary },
  { label: 'Cesur', emoji: '🔥', color: Colors.error },
  { label: 'Rahat', emoji: '🌿', color: Colors.success },
  { label: 'Şık', emoji: '✨', color: Colors.gold },
];

export const AIStyleScreen: React.FC = () => {
  const suggestions = useStyleStore((s) => s.suggestions);
  const isGenerating = useStyleStore((s) => s.isGenerating);
  const generateSuggestions = useStyleStore((s) => s.generateSuggestions);
  const selectedOccasion = useStyleStore((s) => s.selectedOccasion);
  const setOccasion = useStyleStore((s) => s.setOccasion);

  const productLink = useUserStore((s) => s.productLink);
  const setProductLink = useUserStore((s) => s.setProductLink);

  const [selectedMood, setSelectedMood] = useState<string | null>(null);
  const [cameraUri, setCameraUri] = useState<string | null>(null);
  const [linkInput, setLinkInput] = useState(productLink);

  const handleGenerate = () => {
    generateSuggestions(selectedOccasion ?? undefined);
  };

  const handleShoot = async () => {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) {
      Alert.alert('İzin gerekli', 'Kamera izni olmadan kabin görseli alınamaz.');
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      quality: 0.7,
      allowsEditing: true,
      aspect: [3, 4],
    });
    if (!result.canceled) {
      setCameraUri(result.assets[0].uri);
    }
  };

  const handleSaveLink = () => {
    if (!linkInput.trim().startsWith('http')) {
      Alert.alert('Geçersiz bağlantı', 'Ürün bağlantısı http/https ile başlamalı.');
      return;
    }
    setProductLink(linkInput);
    Alert.alert('Bağlantı kaydedildi', 'Kabin akışında ürün linki kullanılacak.');
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <LinearGradient colors={['#191203', Colors.background]} style={styles.header}>
        <View style={styles.headerBadge}>
          <Ionicons name="sparkles" size={14} color={Colors.gold} />
          <Text style={styles.headerBadgeText}>KABİN AI</Text>
        </View>
        <Text style={styles.title}>STYLIA Kabin Asistanı</Text>
        <Text style={styles.subtitle}>Stiline, ölçüne ve moduna göre premium kombin önerileri.</Text>
      </LinearGradient>

      <View style={styles.section}>
        <Text style={styles.sectionLabel}>Etkinlik</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.occRow}>
          <TouchableOpacity style={[styles.occChip, !selectedOccasion && styles.occChipActive]} onPress={() => setOccasion(null)}>
            <Text style={styles.occEmoji}>🌟</Text>
            <Text style={[styles.occLabel, !selectedOccasion && styles.occLabelActive]}>Farketmez</Text>
          </TouchableOpacity>
          {OCCASIONS.map((occ) => (
            <TouchableOpacity
              key={occ}
              style={[styles.occChip, selectedOccasion === occ && styles.occChipActive]}
              onPress={() => setOccasion(occ)}
            >
              <Text style={styles.occEmoji}>{OCCASION_EMOJIS[occ]}</Text>
              <Text style={[styles.occLabel, selectedOccasion === occ && styles.occLabelActive]}>
                {OCCASION_LABELS[occ]}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionLabel}>Ruh hali</Text>
        <View style={styles.moodGrid}>
          {MOODS.map((mood) => (
            <TouchableOpacity
              key={mood.label}
              style={[
                styles.moodChip,
                selectedMood === mood.label && {
                  borderColor: mood.color,
                  backgroundColor: mood.color + '22',
                },
              ]}
              onPress={() => setSelectedMood(selectedMood === mood.label ? null : mood.label)}
            >
              <Text style={styles.moodEmoji}>{mood.emoji}</Text>
              <Text style={[styles.moodLabel, selectedMood === mood.label && { color: mood.color }]}>
                {mood.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Kabin aksiyonları</Text>
        <View style={styles.kabinStack}>
          <View style={styles.kabinAction}>
            <View style={styles.kabinActionHeader}>
              <Ionicons name="link-outline" size={18} color={Colors.gold} />
              <Text style={styles.kabinActionTitle}>Ürün linki ekle</Text>
            </View>
            <TextInput
              value={linkInput}
              onChangeText={setLinkInput}
              placeholder="https://marka.com/urun"
              placeholderTextColor={Colors.textMuted}
              autoCapitalize="none"
              style={styles.linkInput}
            />
            <TouchableOpacity style={styles.inlineButton} onPress={handleSaveLink}>
              <Text style={styles.inlineButtonText}>Linki kaydet</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.kabinAction}>
            <View style={styles.kabinActionHeader}>
              <Ionicons name="camera-outline" size={18} color={Colors.gold} />
              <Text style={styles.kabinActionTitle}>Kamera ile görünüm çek</Text>
            </View>
            {cameraUri ? <Image source={{ uri: cameraUri }} style={styles.cameraPreview} /> : <Text style={styles.emptyNote}>Henüz görsel çekilmedi.</Text>}
            <TouchableOpacity style={styles.inlineButton} onPress={handleShoot}>
              <Text style={styles.inlineButtonText}>Kamera aç</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>

      <TouchableOpacity style={[styles.generateBtn, Shadow.gold, isGenerating && styles.generateBtnDisabled]} onPress={handleGenerate} disabled={isGenerating} activeOpacity={0.85}>
        <LinearGradient colors={[Colors.goldLight, Colors.gold, Colors.goldDark]} style={StyleSheet.absoluteFill} />
        {isGenerating ? (
          <>
            <ActivityIndicator size="small" color={Colors.background} />
            <Text style={styles.generateBtnText}>Kabin analiz ediliyor...</Text>
          </>
        ) : (
          <>
            <Ionicons name="sparkles" size={18} color={Colors.background} />
            <Text style={styles.generateBtnText}>Öneri üret</Text>
          </>
        )}
      </TouchableOpacity>

      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>{isGenerating ? 'Güncelleniyor...' : `${suggestions.length} kombin önerisi`}</Text>
        </View>
        {isGenerating ? (
          <View style={styles.generatingState}>
            {[1, 2].map((i) => (
              <View key={i} style={styles.skeleton} />
            ))}
          </View>
        ) : (
          <View style={styles.suggestionsList}>
            {suggestions.map((s, idx) => (
              <View key={s.id}>
                {idx === 0 && (
                  <View style={styles.topPickBadge}>
                    <Ionicons name="trophy" size={12} color={Colors.gold} />
                    <Text style={styles.topPickText}>Öne çıkan seçim</Text>
                  </View>
                )}
                <StyleSuggestionCard suggestion={s} />
              </View>
            ))}
          </View>
        )}
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
    paddingBottom: Spacing['4xl'],
  },
  header: {
    padding: Spacing.base,
    paddingTop: Spacing.xl,
    paddingBottom: Spacing.xl,
    gap: Spacing.sm,
  },
  headerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: Colors.gold + '22',
    borderRadius: Radius.full,
    paddingHorizontal: 10,
    paddingVertical: 4,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: Colors.gold + '44',
  },
  headerBadgeText: {
    fontSize: Typography.xs,
    color: Colors.gold,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  title: {
    fontSize: Typography['2xl'],
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  subtitle: {
    fontSize: Typography.base,
    color: Colors.textSecondary,
    lineHeight: 22,
  },
  section: {
    paddingHorizontal: Spacing.base,
    marginBottom: Spacing.xl,
    gap: Spacing.md,
  },
  sectionLabel: {
    fontSize: Typography.sm,
    fontWeight: '700',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sectionTitle: {
    fontSize: Typography.md,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  occRow: {
    gap: Spacing.sm,
    paddingRight: Spacing.base,
  },
  occChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: Spacing.md,
    paddingVertical: 9,
    borderRadius: Radius.full,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  occChipActive: {
    backgroundColor: Colors.gold + '22',
    borderColor: Colors.gold,
  },
  occEmoji: {
    fontSize: 15,
  },
  occLabel: {
    fontSize: Typography.sm,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  occLabelActive: {
    color: Colors.gold,
  },
  moodGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
  },
  moodChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: Spacing.md,
    paddingVertical: 8,
    borderRadius: Radius.full,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  moodEmoji: {
    fontSize: 14,
  },
  moodLabel: {
    fontSize: Typography.sm,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  kabinStack: {
    gap: Spacing.md,
  },
  kabinAction: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.base,
    gap: Spacing.sm,
  },
  kabinActionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  kabinActionTitle: {
    color: Colors.textPrimary,
    fontSize: Typography.base,
    fontWeight: '700',
  },
  linkInput: {
    borderWidth: 1,
    borderColor: Colors.borderLight,
    backgroundColor: Colors.surfaceElevated,
    borderRadius: Radius.md,
    color: Colors.textPrimary,
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.sm,
  },
  inlineButton: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.gold + '22',
    borderColor: Colors.gold,
    borderWidth: 1,
    borderRadius: Radius.full,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
  },
  inlineButtonText: {
    color: Colors.gold,
    fontWeight: '700',
    fontSize: Typography.xs,
  },
  emptyNote: {
    color: Colors.textSecondary,
    fontSize: Typography.xs,
  },
  cameraPreview: {
    width: '100%',
    height: 140,
    borderRadius: Radius.md,
  },
  generateBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginHorizontal: Spacing.base,
    marginBottom: Spacing.xl,
    borderRadius: Radius.full,
    paddingVertical: Spacing.base,
    overflow: 'hidden',
    position: 'relative',
  },
  generateBtnDisabled: {
    opacity: 0.7,
  },
  generateBtnText: {
    fontSize: Typography.base,
    fontWeight: '800',
    color: Colors.background,
    letterSpacing: 0.2,
  },
  generatingState: {
    gap: Spacing.md,
  },
  skeleton: {
    height: 200,
    borderRadius: Radius.xl,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  suggestionsList: {
    gap: Spacing.md,
  },
  topPickBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    marginBottom: Spacing.sm,
  },
  topPickText: {
    fontSize: Typography.xs,
    color: Colors.gold,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
});
