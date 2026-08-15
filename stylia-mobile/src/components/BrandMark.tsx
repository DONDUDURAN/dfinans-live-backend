import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import {
  useFonts,
  DancingScript_700Bold,
} from '@expo-google-fonts/dancing-script';
import { Spacing } from '../theme';

const WORDMARK_CREAM = '#EDE5D0';
const HAT_GREEN  = '#0F9B5E';
const HAT_BAND   = '#061510';   // very deep, near-black — crisp band detail

// ─── Hat ─────────────────────────────────────────────────────────────────────
// Top-hat silhouette: narrower crown, wider brim, prominent band.
function HatIcon({ scale = 1 }: { scale?: number }) {
  const crownW  = Math.round(13 * scale);
  const crownH  = Math.round(11 * scale);
  const brimW   = Math.round(22 * scale);
  const brimH   = Math.round(2.5 * scale);
  const bandH   = Math.round(3 * scale);
  const topR    = Math.round(4 * scale);

  return (
    <View style={{ alignItems: 'center' }}>
      {/* Crown with band inset at bottom */}
      <View style={{
        width: crownW,
        height: crownH,
        borderTopLeftRadius: topR,
        borderTopRightRadius: topR,
        borderBottomLeftRadius: 0,
        borderBottomRightRadius: 0,
        backgroundColor: HAT_GREEN,
        overflow: 'hidden',
        justifyContent: 'flex-end',
      }}>
        <View style={{ width: crownW, height: bandH, backgroundColor: HAT_BAND }} />
      </View>
      {/* Brim — slightly thicker on bottom */}
      <View style={{
        width: brimW,
        height: brimH,
        borderRadius: 1,
        backgroundColor: HAT_GREEN,
      }} />
    </View>
  );
}

// ─── BrandMark ───────────────────────────────────────────────────────────────
interface BrandMarkProps {
  size?: 'sm' | 'md' | 'lg';
}

export const BrandMark: React.FC<BrandMarkProps> = ({ size = 'md' }) => {
  const [fontsLoaded] = useFonts({ DancingScript_700Bold });

  const fontSize  = size === 'lg' ? 54 : size === 'sm' ? 36 : 46;
  const hatScale  = size === 'lg' ? 1.25 : size === 'sm' ? 0.85 : 1.05;

  // 700Bold is wider than 400Regular; re-calibrate spacer for 'a' position.
  // S≈0.42 t≈0.28 y≈0.37 l≈0.25 i≈0.16 → ~1.48 × fontSize to reach start of 'a'
  // Centre of 'a' ≈ 1.48 + 0.18 = 1.66; aim for romantic overlap, pull back a touch.
  const hatSpacer = Math.round(fontSize * 1.52);

  return (
    <View style={styles.wrap}>
      <View style={styles.hatRow}>
        <View style={{ width: hatSpacer }} />
        <HatIcon scale={hatScale} />
      </View>
      <Text
        style={[
          styles.wordmark,
          {
            fontSize,
            fontFamily: fontsLoaded ? 'DancingScript_700Bold' : undefined,
            fontStyle: fontsLoaded ? 'normal' : 'italic',
            marginTop: Math.round(-(6 * hatScale)),
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
    letterSpacing: 1,
    fontWeight: '700',
  },
});

