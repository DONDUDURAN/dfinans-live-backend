import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import {
  useFonts,
  DancingScript_400Regular,
} from '@expo-google-fonts/dancing-script';
import { Radius, Spacing } from '../theme';

// ─── Palette ────────────────────────────────────────────────────────────────
const CHARCOAL = '#1C1C1E';
const HAT_GREEN = '#2A6B3C';

// ─── Hat icon — two stacked Views: crown + brim ────────────────────────────
function HatIcon({ scale = 1 }: { scale?: number }) {
  return (
    <View style={{ alignItems: 'center' }}>
      {/* Crown */}
      <View
        style={{
          width: Math.round(12 * scale),
          height: Math.round(9 * scale),
          borderTopLeftRadius: Math.round(6 * scale),
          borderTopRightRadius: Math.round(6 * scale),
          borderBottomLeftRadius: Math.round(2 * scale),
          borderBottomRightRadius: Math.round(2 * scale),
          backgroundColor: HAT_GREEN,
        }}
      />
      {/* Brim */}
      <View
        style={{
          width: Math.round(20 * scale),
          height: Math.round(3 * scale),
          borderRadius: Math.round(1.5 * scale),
          backgroundColor: HAT_GREEN,
          marginTop: -1,
        }}
      />
    </View>
  );
}

// ─── BrandMark ──────────────────────────────────────────────────────────────
// Cream card: green hat above the 'i' in "Stylia", wordmark in calligraphic
// Dancing Script, charcoal colour. size: sm=compact header, md=standard, lg=welcome.
interface BrandMarkProps {
  size?: 'sm' | 'md' | 'lg';
}

export const BrandMark: React.FC<BrandMarkProps> = ({ size = 'md' }) => {
  const [fontsLoaded] = useFonts({ DancingScript_400Regular });

  // Per-size constants
  const fontSize  = size === 'lg' ? 52 : size === 'sm' ? 36 : 44;
  const hatScale  = size === 'lg' ? 1.25 : size === 'sm' ? 0.85 : 1.05;
  const cardPH    = size === 'lg' ? Spacing.xl  : size === 'sm' ? Spacing.md   : Spacing.base;
  const cardPV    = size === 'lg' ? Spacing.md  : size === 'sm' ? Spacing.xs   : Spacing.sm;

  // Hat spacer: positions hat over the 'i' in "Stylia".
  // Dancing Script metrics: 'S'≈52%, 't'≈30%, 'y'≈38%, 'l'≈22%, 'i' starts here.
  // Empirically: left-offset ≈ fontSize * 1.42  from wordmark text start.
  // We subtract cardPH because the spacer is inside the card content (no padding offset).
  const hatSpacer = Math.max(0, Math.round(fontSize * 1.42));

  return (
    <View style={[styles.card, { paddingHorizontal: cardPH, paddingVertical: cardPV }]}>

      {/* Hat row — in flow, above wordmark */}
      <View style={styles.hatRow}>
        <View style={{ width: hatSpacer }} />
        <HatIcon scale={hatScale} />
      </View>

      {/* Wordmark — overlaps hat row via negative marginTop */}
      <Text
        style={[
          styles.wordmark,
          {
            fontSize,
            fontFamily: fontsLoaded ? 'DancingScript_400Regular' : undefined,
            fontStyle: fontsLoaded ? 'normal' : 'italic',
            marginTop: Math.round(-(6 * hatScale)),
          },
        ]}
        numberOfLines={1}
        adjustsFontSizeToFit
      >
        Stylia
      </Text>

      {/* Thin rule */}
      <View style={styles.rule} />
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#F3F0E8',
    borderRadius: Radius.lg,
    alignSelf: 'flex-start',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.18,
    shadowRadius: 6,
    elevation: 4,
    overflow: 'hidden', // ensures hat never clips outside card
  },
  hatRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
  },
  wordmark: {
    color: CHARCOAL,
    letterSpacing: 0.5,
    fontWeight: '400',
  },
  rule: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: CHARCOAL,
    opacity: 0.18,
    marginTop: 4,
    width: '80%',
  },
});
