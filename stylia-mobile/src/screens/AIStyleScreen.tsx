import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useStyleStore } from '../store/styleStore';
import { StyleSuggestionCard } from '../components/StyleSuggestionCard';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';
import { Occasion } from '../types';

const OCCASIONS: Occasion[] = ['Casual', 'Work', 'Formal', 'Party', 'Date Night', 'Sport', 'Beach'];

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
  { label: 'Confident', emoji: '🖤', color: Colors.textPrimary },
  { label: 'Romantic', emoji: '🌸', color: Colors.dresses },
  { label: 'Minimal', emoji: '✦', color: Colors.textSecondary },
  { label: 'Bold', emoji: '🔥', color: Colors.error },
  { label: 'Relaxed', emoji: '🌿', color: Colors.success },
  { label: 'Chic', emoji: '✨', color: Colors.gold },
];

export const AIStyleScreen: React.FC = () => {
  const suggestions = useStyleStore((s) => s.suggestions);
  const isGenerating = useStyleStore((s) => s.isGenerating);
  const generateSuggestions = useStyleStore((s) => s.generateSuggestions);
  const selectedOccasion = useStyleStore((s) => s.selectedOccasion);
  const setOccasion = useStyleStore((s) => s.setOccasion);

  const [selectedMood, setSelectedMood] = useState<string | null>(null);

  const handleGenerate = () => {
    generateSuggestions(selectedOccasion ?? undefined);
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <LinearGradient colors={['#0D0A00', '#0D0D0D']} style={styles.header}>
        <View style={styles.headerBadge}>
          <Ionicons name="sparkles" size={14} color={Colors.gold} />
          <Text style={styles.headerBadgeText}>AI-Powered</Text>
        </View>
        <Text style={styles.title}>Style Assistant</Text>
        <Text style={styles.subtitle}>
          Get personalized outfit suggestions{'\n'}based on your wardrobe & preferences
        </Text>
      </LinearGradient>

      {/* Occasion Picker */}
      <View style={styles.section}>
        <Text style={styles.sectionLabel}>What's the occasion?</Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.occRow}
        >
          <TouchableOpacity
            style={[styles.occChip, !selectedOccasion && styles.occChipActive]}
            onPress={() => setOccasion(null)}
          >
            <Text style={styles.occEmoji}>🌟</Text>
            <Text style={[styles.occLabel, !selectedOccasion && styles.occLabelActive]}>
              Any
            </Text>
          </TouchableOpacity>
          {OCCASIONS.map((occ) => (
            <TouchableOpacity
              key={occ}
              style={[styles.occChip, selectedOccasion === occ && styles.occChipActive]}
              onPress={() => setOccasion(occ)}
            >
              <Text style={styles.occEmoji}>{OCCASION_EMOJIS[occ]}</Text>
              <Text style={[styles.occLabel, selectedOccasion === occ && styles.occLabelActive]}>
                {occ}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Mood Picker */}
      <View style={styles.section}>
        <Text style={styles.sectionLabel}>What's your mood?</Text>
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
              <Text
                style={[
                  styles.moodLabel,
                  selectedMood === mood.label && { color: mood.color },
                ]}
              >
                {mood.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Generate Button */}
      <TouchableOpacity
        style={[styles.generateBtn, Shadow.gold, isGenerating && styles.generateBtnDisabled]}
        onPress={handleGenerate}
        disabled={isGenerating}
        activeOpacity={0.85}
      >
        <LinearGradient
          colors={[Colors.goldLight, Colors.gold, Colors.goldDark]}
          style={StyleSheet.absoluteFill}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
        />
        {isGenerating ? (
          <>
            <ActivityIndicator size="small" color={Colors.background} />
            <Text style={styles.generateBtnText}>Analyzing your wardrobe...</Text>
          </>
        ) : (
          <>
            <Ionicons name="sparkles" size={18} color={Colors.background} />
            <Text style={styles.generateBtnText}>Generate Suggestions</Text>
          </>
        )}
      </TouchableOpacity>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>
              {isGenerating ? 'Updating...' : `${suggestions.length} Suggestions for You`}
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
                      <Text style={styles.topPickText}>Top Pick</Text>
                    </View>
                  )}
                  <StyleSuggestionCard suggestion={s} />
                </View>
              ))}
            </View>
          )}
        </View>
      )}

      {/* Style Tips */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Style Tips</Text>
        <View style={styles.tipsGrid}>
          {[
            { emoji: '🎨', tip: 'Stick to 3 colors max per outfit for a cohesive look', label: 'Color Rule' },
            { emoji: '📐', tip: 'Balance proportions: oversized top with slim bottom', label: 'Fit Balance' },
            { emoji: '✨', tip: 'Add one statement piece to elevate any outfit', label: 'Statement Piece' },
            { emoji: '🔄', tip: 'Rotate your wardrobe to discover forgotten gems', label: 'Rediscover' },
          ].map((tip) => (
            <View key={tip.label} style={[styles.tipCard, Shadow.sm]}>
              <Text style={styles.tipEmoji}>{tip.emoji}</Text>
              <Text style={styles.tipLabel}>{tip.label}</Text>
              <Text style={styles.tipText}>{tip.tip}</Text>
            </View>
          ))}
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
    fontSize: Typography['3xl'],
    fontWeight: '900',
    color: Colors.textPrimary,
    letterSpacing: -0.5,
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
  tipsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.md,
  },
  tipCard: {
    width: '47%',
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    gap: Spacing.xs,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  tipEmoji: {
    fontSize: 24,
  },
  tipLabel: {
    fontSize: Typography.sm,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  tipText: {
    fontSize: Typography.xs,
    color: Colors.textSecondary,
    lineHeight: 17,
  },
});
