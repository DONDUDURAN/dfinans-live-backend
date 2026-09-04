import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import {
  useFonts,
  DancingScript_600SemiBold,
} from '@expo-google-fonts/dancing-script';
import { Spacing } from '../theme';

const WORDMARK_CREAM = '#EDE5D0';
const HAT_GREEN  = '#0F9B5E';
const HAT_BAND   = '#061510';   // very deep, near-black — crisp band detail

// ─── Hat ─────────────────────────────────────────────────────────────────────
// Mini top-hat used as the "i" dot symbol.
function HatIcon({ scale = 1 }: { scale?: number }) {
  const crownW  = Math.round(12.5 * scale);
  const crownH  = Math.round(10.5 * scale);
  const brimW   = Math.round(24 * scale);
  const brimH   = Math.round(2.6 * scale);
  const bandH   = Math.round(2.8 * scale);
  const topR    = Math.round(4 * scale);

  return (
    <View style={{ alignItems: 'center', transform: [{ rotate: '-6deg' }] }}>
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
        borderRadius: 2,
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
  const [fontsLoaded] = useFonts({ DancingScript_600SemiBold });

  const fontSize  = size === 'lg' ? 56 : size === 'sm' ? 36 : 48;
  const hatScale  = size === 'lg' ? 0.56 : size === 'sm' ? 0.38 : 0.48;
  const joinShift = size === 'lg' ? -3 : size === 'sm' ? -2 : -2.5;
  const iStemWidth = Math.round(fontSize * 0.18);
  const hatTop = -Math.round(fontSize * 0.52);

  return (
    <View style={[styles.wrap, size === 'sm' ? styles.wrapSm : size === 'lg' ? styles.wrapLg : styles.wrapMd]}>
      <View
        style={[
          styles.wordRow,
          { paddingLeft: size === 'lg' ? Spacing.xs : 0 },
        ]}
      >
        <Text
          style={[
            styles.wordmark,
            {
              fontSize,
              fontFamily: fontsLoaded ? 'DancingScript_600SemiBold' : undefined,
              fontStyle: fontsLoaded ? 'normal' : 'italic',
            },
          ]}
          numberOfLines={1}
          adjustsFontSizeToFit
        >
          Styl
        </Text>

        {/* Dotless ı removes the default dot; mini hat becomes the i-dot symbol */}
        <View style={[styles.iStemWrap, { width: iStemWidth, marginLeft: joinShift, marginRight: joinShift }]}>
          <Text
            style={[
              styles.wordmark,
              styles.iStem,
              {
                fontSize,
                fontFamily: fontsLoaded ? 'DancingScript_600SemiBold' : undefined,
                fontStyle: fontsLoaded ? 'normal' : 'italic',
              },
            ]}
          >
            ı
          </Text>
          <View style={[styles.iDotSymbol, { top: hatTop }]}>
            <HatIcon scale={hatScale} />
          </View>
        </View>

        <Text
          style={[
            styles.wordmark,
            {
              fontSize,
              fontFamily: fontsLoaded ? 'DancingScript_600SemiBold' : undefined,
              fontStyle: fontsLoaded ? 'normal' : 'italic',
            },
          ]}
          numberOfLines={1}
          adjustsFontSizeToFit
        >
          a
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  wrap: {
    alignSelf: 'flex-start',
    paddingTop: 2,
    overflow: 'visible',
  },
  wrapSm: {
    paddingRight: 8,
  },
  wrapMd: {
    paddingRight: 10,
  },
  wrapLg: {
    paddingRight: 12,
  },
  wordRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    overflow: 'visible',
  },
  iStemWrap: {
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'flex-end',
    overflow: 'visible',
  },
  iStem: {
    textAlign: 'center',
  },
  iDotSymbol: {
    position: 'absolute',
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  wordmark: {
    color: WORDMARK_CREAM,
    letterSpacing: 0.4,
    fontWeight: '600',
    textShadowColor: 'rgba(0,0,0,0.35)',
    textShadowOffset: { width: 0.6, height: 0.6 },
    textShadowRadius: 1.2,
  },
});
