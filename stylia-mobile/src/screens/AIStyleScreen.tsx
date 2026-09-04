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
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useStyleStore } from '../store/styleStore';
import { StyleSuggestionCard } from '../components/StyleSuggestionCard';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';
import { Occasion } from '../types';
import { useUserStore } from '../store/userStore';
import { useNavigation } from '@react-navigation/native';

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
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<any>();
  const suggestions = useStyleStore((s) => s.suggestions);
  const isGenerating = useStyleStore((s) => s.isGenerating);
  const generateSuggestions = useStyleStore((s) => s.generateSuggestions);
  const selectedOccasion = useStyleStore((s) => s.selectedOccasion);
  const setOccasion = useStyleStore((s) => s.setOccasion);

  const productLink = useUserStore((s) => s.productLink);
  const setProductLink = useUserStore((s) => s.setProductLink);
  const measurements = useUserStore((s) => s.measurements);
  const videoNoteUri = useUserStore((s) => s.videoNoteUri);

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
      <LinearGradient colors={['#050D08', Colors.background]} style={[styles.header, { paddingTop: insets.top + Spacing.base }]}>
        <Text style={styles.title}>Kabin</Text>
      </LinearGradient>

      {/* ADIM 1 — Sanal İkiz */}
      <View style={styles.section}>
        <View style={styles.stepRow}>
          <View style={styles.stepNum}><Text style={styles.stepNumText}>1</Text></View>
          <Text style={styles.stepTitle}>İkiz Durumu</Text>
        </View>
        <View style={styles.stepCard}>
          <View style={styles.twinStatusRow}>
            <View style={styles.twinStatusItem}>
              <Ionicons
                name={measurements.boyCm ? 'checkmark-circle' : 'ellipse-outline'}
                size={16}
                color={measurements.boyCm ? Colors.gold : Colors.textMuted}
              />
              <Text style={[styles.twinStatusLabel, !!measurements.boyCm && styles.twinStatusLabelDone]}>Ölçüler</Text>
            </View>
            <View style={styles.twinStatusItem}>
              <Ionicons
                name={videoNoteUri ? 'checkmark-circle' : 'ellipse-outline'}
                size={16}
                color={videoNoteUri ? Colors.gold : Colors.textMuted}
              />
              <Text style={[styles.twinStatusLabel, !!videoNoteUri && styles.twinStatusLabelDone]}>Video notu</Text>
            </View>
            <View style={styles.twinStatusItem}>
              <Ionicons
                name={cameraUri ? 'checkmark-circle' : 'ellipse-outline'}
                size={16}
                color={cameraUri ? Colors.gold : Colors.textMuted}
              />
              <Text style={[styles.twinStatusLabel, !!cameraUri && styles.twinStatusLabelDone]}>Kabin görseli</Text>
            </View>
          </View>
          <TouchableOpacity style={styles.twinUpdateBtn} onPress={() => navigation.navigate('Profile')}>
            <Ionicons name="person-outline" size={14} color={Colors.gold} />
            <Text style={styles.twinUpdateText}>Profili güncelle</Text>
            <Ionicons name="arrow-forward" size={12} color={Colors.gold} />
          </TouchableOpacity>
        </View>
      </View>

      {/* ADIM 2 — Kıyafet / Link */}
      <View style={styles.section}>
        <View style={styles.stepRow}>
          <View style={styles.stepNum}><Text style={styles.stepNumText}>2</Text></View>
          <Text style={styles.stepTitle}>Kıyafet / Link</Text>
        </View>
        <View style={styles.kabinStack}>
          <View style={styles.kabinAction}>
            <View style={styles.kabinActionHeader}>
              <Ionicons name="link-outline" size={18} color={Colors.gold} />
              <Text style={styles.kabinActionTitle}>Ürün linki</Text>
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
              <Text style={styles.inlineButtonText}>Kaydet</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.kabinAction}>
            <View style={styles.kabinActionHeader}>
              <Ionicons name="camera-outline" size={18} color={Colors.gold} />
              <Text style={styles.kabinActionTitle}>Kabin görseli</Text>
            </View>
            {cameraUri
              ? <Image source={{ uri: cameraUri }} style={styles.cameraPreview} />
              : null}
            <TouchableOpacity style={styles.inlineButton} onPress={handleShoot}>
              <Text style={styles.inlineButtonText}>{cameraUri ? 'Yenile' : 'Kamera aç'}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* ADIM 3 — Kabin Dene */}
      <View style={styles.section}>
        <View style={styles.stepRow}>
          <View style={styles.stepNum}><Text style={styles.stepNumText}>3</Text></View>
          <Text style={styles.stepTitle}>Kabinde Dene</Text>
        </View>

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

        <Text style={[styles.sectionLabel, { marginTop: Spacing.sm }]}>Ruh hali</Text>
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

      <TouchableOpacity style={[styles.generateBtn, isGenerating && styles.generateBtnDisabled]} onPress={handleGenerate} disabled={isGenerating} activeOpacity={0.85}>
        <LinearGradient colors={[Colors.goldLight, Colors.gold, Colors.goldDark]} style={StyleSheet.absoluteFill} />
        {isGenerating
          ? <ActivityIndicator size="small" color={Colors.background} />
          : <Ionicons name="body-outline" size={18} color={Colors.background} />}
        <Text style={styles.generateBtnText}>{isGenerating ? 'Analiz ediliyor...' : 'Kabinde Dene'}</Text>
      </TouchableOpacity>

      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            {isGenerating ? 'Analiz ediliyor...' : `${suggestions.length} görünüm`}
          </Text>
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
                    <Text style={styles.topPickText}>En yakışan</Text>
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
    paddingBottom: Spacing.xl,
    gap: Spacing.sm,
  },
  headerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: Colors.gold + '22',
    borderRadius: Radius.full,
    paddingHorizontal: 10,
    paddingVertical: 4,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: Colors.gold + '44',
  },
  headerBadgeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.gold,
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
  stepRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  stepNum: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: Colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepNumText: {
    color: Colors.background,
    fontSize: Typography.xs,
    fontWeight: '800',
  },
  stepTitle: {
    color: Colors.textPrimary,
    fontSize: Typography.base,
    fontWeight: '700',
    flex: 1,
  },
  stepCard: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    gap: Spacing.md,
  },
  twinStatusRow: {
    flexDirection: 'row',
    gap: Spacing.xl,
  },
  twinStatusItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  twinStatusLabel: {
    color: Colors.textMuted,
    fontSize: Typography.xs,
  },
  twinStatusLabelDone: {
    color: Colors.gold,
    fontWeight: '600',
  },
  twinUpdateBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    alignSelf: 'flex-start',
    paddingVertical: 6,
  },
  twinUpdateText: {
    color: Colors.gold,
    fontSize: Typography.xs,
    fontWeight: '500',
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
    fontSize: Typography.xs,
    fontWeight: '600',
    color: Colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1.5,
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
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.borderLight,
    backgroundColor: 'transparent',
    color: Colors.textPrimary,
    paddingHorizontal: 0,
    paddingVertical: Spacing.sm,
  },
  inlineButton: {
    alignSelf: 'flex-start',
    paddingVertical: 6,
  },
  inlineButtonText: {
    color: Colors.gold,
    fontWeight: '500',
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
    borderRadius: Radius.md,
    paddingVertical: 14,
    overflow: 'hidden',
    position: 'relative',
    backgroundColor: Colors.goldDark,
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
