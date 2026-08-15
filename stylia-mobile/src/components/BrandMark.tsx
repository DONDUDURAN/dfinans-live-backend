import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import {
  useFonts,
  DancingScript_400Regular,
} from '@expo-google-fonts/dancing-script';
import { Spacing } from '../theme';

// Warm ivory on dark — reads as premium/artisanal
const WORDMARK_CREAM = '#EDE5D0';
// Vivid emerald — richer and more distinct than prior #2C7A51
const HAT_GREEN = '#0F9B5E';
const HAT_BAND = '#07251A';   // near-black band — adds depth and elegance

// ─── Hat icon (top-hat silhouette with band detail) ──────────────────────────
function HatIcon({ scale = 1 }: { scale?: number }) {
  const crownW = Math.round(12 * scale);
  const crownH = Math.round(9 * scale);
  const brimW  = Math.round(20 * scale);
  const brimH  = Math.round(3  * scale);
  const bandH  = Math.round(2.5 * scale);
  const r      = Math.round(3 * scale);

  return (
    <View style={{ alignItems: 'center' }}>
      {/* Crown */}
      <View style={{
        width: crownW,
        height: crownH,
        borderTopLeftRadius: r + 2,
        borderTopRightRadius: r + 2,
        borderBottomLeftRadius: 1,
        borderBottomRightRadius: 1,
        backgroundColor: HAT_GREEN,
        overflow: 'hidden',
        justifyContent: 'flex-end',
      }}>
        {/* Band — sits at the base of the crown */}
        <View style={{ width: crownW, height: bandH, backgroundColor: HAT_BAND }} />
      </View>
      {/* Brim */}
      <View style={{
        width: brimW,
        height: brimH,
        borderRadius: Math.round(1.5 * scale),
        backgroundColor: HAT_GREEN,
        marginTop: -0.5,
      }} />
    </View>
  );
}

// ─── BrandMark ───────────────────────────────────────────────────────────────
interface BrandMarkProps {
  size?: 'sm' | 'md' | 'lg';
}

export const BrandMark: React.FC<BrandMarkProps> = ({ size = 'md' }) => {
  const [fontsLoaded] = useFonts({ DancingScript_400Regular });

  const fontSize = size === 'lg' ? 52 : size === 'sm' ? 34 : 44;
  const hatScale = size === 'lg' ? 1.2 : size === 'sm' ? 0.8 : 1.0;

  // Spacer approximates the x-position of the 'a' (last letter) in "Stylia"
  // Dancing Script: S≈0.38 t≈0.26 y≈0.34 l≈0.24 i≈0.14 → cumulative ≈ 1.36 × fontSize
  // Add slight overshoot so hat crown sits romantically over the 'a' centre
  const hatSpacer = Math.round(fontSize * 1.48);

  return (
    <View style={styles.wrap}>
      {/* Hat floats above the 'a' */}
      <View style={styles.hatRow}>
        <View style={{ width: hatSpacer }} />
        <HatIcon scale={hatScale} />
      </View>

      {/* Wordmark — tucked up under hat */}
      <Text
        style={[
          styles.wordmark,
          {
            fontSize,
            fontFamily: fontsLoaded ? 'DancingScript_400Regular' : undefined,
            fontStyle: fontsLoaded ? 'normal' : 'italic',
            marginTop: Math.round(-(5 * hatScale)),
            paddingLeft: size === 'lg' ? Spacing.xs : 0,
          },
        ]}
        numberOfLines={1}
        adjustsFontSizeToFit
      >
        Stylia
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  wrap: { alignSelf: 'flex-start' },
  hatRow: { flexDirection: 'row', alignItems: 'flex-end' },
  wordmark: {
    color: WORDMARK_CREAM,
    letterSpacing: 0.5,
    fontWeight: '400',
  },
});

