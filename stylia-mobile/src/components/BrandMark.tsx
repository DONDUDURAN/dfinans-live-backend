import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import {
  useFonts,
  DancingScript_400Regular,
} from '@expo-google-fonts/dancing-script';
import { Spacing } from '../theme';

// Warm ivory on dark — reads as premium/artisanal, not digital
const WORDMARK_CREAM = '#EDE5D0';
// Forest green — matches app accent and reference hat
const HAT_GREEN = '#2C7A51';

// ─── Hat icon ────────────────────────────────────────────────────────────────
function HatIcon({ scale = 1 }: { scale?: number }) {
  return (
    <View style={{ alignItems: 'center' }}>
      {/* Crown — tapers at bottom for a hat silhouette */}
      <View style={{
        width: Math.round(11 * scale),
        height: Math.round(8 * scale),
        borderTopLeftRadius: Math.round(6 * scale),
        borderTopRightRadius: Math.round(6 * scale),
        borderBottomLeftRadius: Math.round(2 * scale),
        borderBottomRightRadius: Math.round(2 * scale),
        backgroundColor: HAT_GREEN,
      }} />
      {/* Brim */}
      <View style={{
        width: Math.round(18 * scale),
        height: Math.round(3 * scale),
        borderRadius: Math.round(2 * scale),
        backgroundColor: HAT_GREEN,
        marginTop: -1,
      }} />
    </View>
  );
}

// ─── BrandMark ───────────────────────────────────────────────────────────────
// Floats directly on dark background — no card box.
// Hat is positioned in-flow above the 'i' in "Stylia".
interface BrandMarkProps {
  size?: 'sm' | 'md' | 'lg';
}

export const BrandMark: React.FC<BrandMarkProps> = ({ size = 'md' }) => {
  const [fontsLoaded] = useFonts({ DancingScript_400Regular });

  const fontSize  = size === 'lg' ? 52 : size === 'sm' ? 34 : 44;
  const hatScale  = size === 'lg' ? 1.2 : size === 'sm' ? 0.8 : 1.0;
  // Spacer width ≈ 'S' + 't' + 'y' + 'l' in Dancing Script at fontSize
  const hatSpacer = Math.round(fontSize * 1.42);

  return (
    <View style={styles.wrap}>
      {/* Hat row — above wordmark, hat offset to sit over the 'i' */}
      <View style={styles.hatRow}>
        <View style={{ width: hatSpacer }} />
        <HatIcon scale={hatScale} />
      </View>

      {/* Wordmark — pulled up slightly under the hat */}
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
  wrap: {
    alignSelf: 'flex-start',
  },
  hatRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
  },
  wordmark: {
    color: WORDMARK_CREAM,
    letterSpacing: 0.5,
    fontWeight: '400',
  },
});

