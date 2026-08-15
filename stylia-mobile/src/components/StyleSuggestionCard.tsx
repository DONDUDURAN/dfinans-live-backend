import React from 'react';
import {
  Alert,
  Share,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { StyleSuggestion } from '../types';
import { useWardrobeStore } from '../store/wardrobeStore';
import { useSocialStore } from '../store/socialStore';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';
import { trOccasion } from '../utils/translations';

interface Props {
  suggestion: StyleSuggestion;
  onPress?: () => void;
  compact?: boolean;
}

export const StyleSuggestionCard: React.FC<Props> = ({
  suggestion,
  onPress,
  compact = false,
}) => {
  const getItemById = useWardrobeStore((s) => s.getItemById);
  const friends = useSocialStore((s) => s.friends);
  const shareLookToFriends = useSocialStore((s) => s.shareLookToFriends);
  const items = suggestion.outfit.items
    .slice(0, 3)
    .map((id) => getItemById(id))
    .filter(Boolean);
  const previewImageUri = items[0]?.imageUri;

  const shareText = `${suggestion.title}\n${trOccasion(suggestion.outfit.occasion)} · ${suggestion.mood}\n#STYLIA`;

  const handleShare = async () => {
    try {
      const payload: { message: string; url?: string } = { message: shareText };
      if (previewImageUri) payload.url = previewImageUri;
      await Share.share(payload);
    } catch {
      Alert.alert('Paylaşım açılamadı');
    }
  };

  const handleSendToFriend = () => {
    if (friends.length === 0) {
      Alert.alert('Arkadaş yok', 'Önce profilde arkadaş ekleyin.');
      return;
    }

    Alert.alert(
      'Arkadaşa gönder',
      'Kime gönderilsin?',
      [
        {
          text: 'Tüm arkadaşlar',
          onPress: () => {
            shareLookToFriends({
              recipientIds: friends.map((f) => f.id),
              lookTitle: suggestion.title,
              previewImageUri,
              note: `${trOccasion(suggestion.outfit.occasion)} · ${suggestion.mood}`,
            });
            Alert.alert('Gönderildi', 'Tüm arkadaşlara paylaşıldı.');
          },
        },
        ...friends.slice(0, 8).map((friend) => ({
          text: `${friend.name} (${friend.username})`,
          onPress: () => {
            shareLookToFriends({
              recipientIds: [friend.id],
              lookTitle: suggestion.title,
              previewImageUri,
              note: `${trOccasion(suggestion.outfit.occasion)} · ${suggestion.mood}`,
            });
            Alert.alert('Gönderildi', `${friend.name} için paylaşıldı.`);
          },
        })),
        { text: 'Vazgeç', style: 'cancel' as const },
      ]
    );
  };

  return (
    <TouchableOpacity
      style={[styles.card, Shadow.gold, compact && styles.cardCompact]}
      onPress={onPress}
      activeOpacity={0.88}
    >
      <LinearGradient
        colors={['#001412', '#0D0D0D']}
        style={StyleSheet.absoluteFill}
      />

      {/* Confidence arc */}
      <View style={styles.confidenceBadge}>
        <Text style={styles.confidenceValue}>{suggestion.confidence}%</Text>
        <Text style={styles.confidenceLabel}>Eşleşme</Text>
      </View>

      {/* Item thumbnails */}
      <View style={styles.thumbnails}>
        {items.map((item, idx) => (
          <View
            key={item!.id}
            style={[
              styles.thumbnail,
              { marginLeft: idx > 0 ? -16 : 0, zIndex: items.length - idx },
            ]}
          >
            <Image
              source={{ uri: item!.imageUri }}
              style={styles.thumbnailImage}
              resizeMode="cover"
            />
          </View>
        ))}
      </View>

      <View style={styles.content}>
        <Text style={styles.mood}>{suggestion.mood}</Text>
        <Text style={styles.title}>{suggestion.title}</Text>

        <View style={styles.footer}>
          <View style={styles.outfitOccasion}>
            <Ionicons name="calendar-outline" size={12} color={Colors.textSecondary} />
            <Text style={styles.outfitOccasionText}>{trOccasion(suggestion.outfit.occasion)}</Text>
          </View>
          <View style={styles.actionRow}>
            <TouchableOpacity style={styles.ghostBtn} onPress={handleShare}>
              <Ionicons name="share-social-outline" size={13} color={Colors.gold} />
              <Text style={styles.ghostBtnText}>Paylaş</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.ghostBtn} onPress={handleSendToFriend}>
              <Ionicons name="paper-plane-outline" size={13} color={Colors.gold} />
              <Text style={styles.ghostBtnText}>Arkadaşa gönder</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.tryBtn} onPress={onPress}>
              <Text style={styles.tryBtnText}>Kabinde Dene</Text>
              <Ionicons name="arrow-forward" size={12} color={Colors.background} />
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    borderRadius: Radius.xl,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: Colors.gold + '33',
    padding: Spacing.base,
    gap: Spacing.md,
  },
  cardCompact: {
    padding: Spacing.md,
  },
  confidenceBadge: {
    position: 'absolute',
    top: Spacing.base,
    right: Spacing.base,
    alignItems: 'center',
    backgroundColor: Colors.gold + '22',
    borderRadius: Radius.md,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: Colors.gold + '44',
  },
  confidenceValue: {
    fontSize: Typography.base,
    fontWeight: '800',
    color: Colors.gold,
  },
  confidenceLabel: {
    fontSize: 9,
    color: Colors.gold,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  thumbnails: {
    flexDirection: 'row',
    marginBottom: Spacing.xs,
  },
  thumbnail: {
    width: 52,
    height: 52,
    borderRadius: Radius.md,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: Colors.background,
  },
  thumbnailImage: {
    width: '100%',
    height: '100%',
  },
  content: {
    gap: Spacing.xs,
  },
  mood: {
    fontSize: Typography.sm,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  title: {
    fontSize: Typography.lg,
    fontWeight: '800',
    color: Colors.textPrimary,
    letterSpacing: -0.3,
  },
  description: {
    fontSize: Typography.sm,
    color: Colors.textSecondary,
    lineHeight: 20,
  },
  reasons: { gap: 4, marginTop: Spacing.xs },
  reasonRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  reasonText: { fontSize: Typography.xs, color: Colors.textSecondary, flex: 1 },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: Spacing.sm,
  },
  outfitOccasion: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  outfitOccasionText: {
    fontSize: Typography.xs,
    color: Colors.textSecondary,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
  },
  ghostBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    borderRadius: Radius.sm,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.borderLight,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 6,
  },
  ghostBtnText: {
    fontSize: 10,
    color: Colors.gold,
    fontWeight: '500',
  },
  tryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.gold,
    borderRadius: Radius.sm,
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  tryBtnText: {
    fontSize: Typography.xs,
    fontWeight: '700',
    color: Colors.background,
  },
});
