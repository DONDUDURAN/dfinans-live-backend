import React, { useMemo, useState } from 'react';
import {
  Alert,
  Image,
  Linking,
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
import { BrandMark } from '../components/BrandMark';
import { useWardrobeStore } from '../store/wardrobeStore';
import { useUserStore } from '../store/userStore';
import { useSocialStore } from '../store/socialStore';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';
import { MEMBERSHIP_PLANS, MembershipPlanId, STRIPE_PAYMENT_LINKS } from '../config/paymentLinks';

const PLAN_ORDER: MembershipPlanId[] = ['aylik', 'yillik'];

export const ProfileScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const items = useWardrobeStore((s) => s.items);
  const outfits = useWardrobeStore((s) => s.outfits);

  const fullName = useUserStore((s) => s.fullName);
  const email = useUserStore((s) => s.email);
  const selectedPlan = useUserStore((s) => s.selectedPlan);
  const switchPlan = useUserStore((s) => s.switchPlan);
  const trialEndsAt = useUserStore((s) => s.trialEndsAt);
  const measurements = useUserStore((s) => s.measurements);
  const setMeasurements = useUserStore((s) => s.setMeasurements);
  const videoNoteUri = useUserStore((s) => s.videoNoteUri);
  const setVideoNoteUri = useUserStore((s) => s.setVideoNoteUri);

  const logout = useUserStore((s) => s.logout);
  const friends = useSocialStore((s) => s.friends);
  const messages = useSocialStore((s) => s.messages);
  const addFriend = useSocialStore((s) => s.addFriend);

  const [draft, setDraft] = useState(measurements);
  const [showFriendForm, setShowFriendForm] = useState(false);
  const [friendName, setFriendName] = useState('');
  const [friendUsername, setFriendUsername] = useState('');

  const totalWorn = items.reduce((acc, i) => acc + i.timesWorn, 0);
  const trialDaysLeft = useMemo(() => {
    if (!trialEndsAt) return 0;
    const diff = new Date(trialEndsAt).getTime() - Date.now();
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
  }, [trialEndsAt]);
  const latestShares = useMemo(() => messages.slice(0, 8), [messages]);

  const openPlanPayment = async (planId: MembershipPlanId) => {
    const url = STRIPE_PAYMENT_LINKS[planId];
    if (!(await Linking.canOpenURL(url))) {
      Alert.alert('Bağlantı açılamadı', 'Stripe ödeme bağlantısı şu an açılamıyor.');
      return;
    }
    switchPlan(planId);
    await Linking.openURL(url);
  };

  const saveMeasurements = () => {
    setMeasurements(draft);
    Alert.alert('Kaydedildi', 'Vücut ölçülerin güncellendi.');
  };

  const recordVideoNote = async () => {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) {
      Alert.alert('İzin gerekli', 'Video notu için kamera izni gereklidir.');
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
      quality: 0.6,
      videoMaxDuration: 45,
    });
    if (!result.canceled) {
      setVideoNoteUri(result.assets[0].uri);
      Alert.alert('Video notu eklendi');
    }
  };

  const handleAddFriend = () => {
    const result = addFriend({ name: friendName, username: friendUsername });
    if (!result.ok) {
      Alert.alert('Eklenemedi', result.error ?? 'Tekrar deneyin.');
      return;
    }
    setFriendName('');
    setFriendUsername('');
    setShowFriendForm(false);
    Alert.alert('Arkadaş eklendi');
  };

  const formatShareTime = (iso: string) =>
    new Date(iso).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' });

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <LinearGradient colors={['#050D08', Colors.background]} style={[styles.profileHeader, { paddingTop: insets.top + Spacing.base }]}>
        <BrandMark size="sm" />
        <Text style={styles.profileName}>{fullName || 'Üye Profil'}</Text>
        <Text style={styles.profileHandle}>{email || 'premium@stylia.app'}</Text>
        <View style={styles.planBadge}>
          <Ionicons name="diamond-outline" size={14} color={Colors.goldLight} />
          <Text style={styles.planBadgeText}>
            {MEMBERSHIP_PLANS[selectedPlan].title} • {trialDaysLeft} gün deneme
          </Text>
        </View>
      </LinearGradient>

      <View style={styles.statsGrid}>
        {[
          { icon: 'shirt-outline', label: 'Parça', value: items.length },
          { icon: 'layers-outline', label: 'Stil', value: outfits.length },
          { icon: 'repeat-outline', label: 'Kullanım', value: totalWorn },
          { icon: 'heart-outline', label: 'Favori', value: items.filter((i) => i.isFavorite).length },
        ].map((stat) => (
          <View key={stat.label} style={styles.statCard}>
            <Ionicons name={stat.icon as any} size={18} color={Colors.gold} />
            <Text style={styles.statValue}>{stat.value}</Text>
            <Text style={styles.statLabel}>{stat.label}</Text>
          </View>
        ))}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Üyelik planı</Text>
        <View style={styles.stack}>
          {PLAN_ORDER.map((planId) => {
            const plan = MEMBERSHIP_PLANS[planId];
            const active = selectedPlan === planId;
            return (
              <View key={planId} style={[styles.planCard, active && styles.planCardActive]}>
                <View style={styles.planRow}>
                  <View>
                    <Text style={styles.planTitle}>{plan.title}</Text>
                    <Text style={styles.planSubtitle}>{plan.subtitle}</Text>
                  </View>
                  {active ? <Text style={styles.currentPlanTag}>Aktif Plan</Text> : null}
                </View>
                <Text style={styles.planPrice}>{plan.price}</Text>
                <Text style={styles.planHint}>{plan.trial}</Text>
                <TouchableOpacity style={styles.paymentButton} onPress={() => openPlanPayment(planId)}>
                  <Ionicons name="card-outline" size={16} color={Colors.background} />
                  <Text style={styles.paymentButtonText}>Öde</Text>
                </TouchableOpacity>
              </View>
            );
          })}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Vücut ölçüleri</Text>
        <View style={styles.measurementsCard}>
          <View style={styles.measureGrid}>
            <TextInput style={styles.measureInput} placeholder="Boy (cm)" placeholderTextColor={Colors.textMuted} value={draft.boyCm} onChangeText={(v) => setDraft((p) => ({ ...p, boyCm: v }))} keyboardType="numeric" />
            <TextInput style={styles.measureInput} placeholder="Kilo (kg)" placeholderTextColor={Colors.textMuted} value={draft.kiloKg} onChangeText={(v) => setDraft((p) => ({ ...p, kiloKg: v }))} keyboardType="numeric" />
            <TextInput style={styles.measureInput} placeholder="Göğüs (cm)" placeholderTextColor={Colors.textMuted} value={draft.gogusCm} onChangeText={(v) => setDraft((p) => ({ ...p, gogusCm: v }))} keyboardType="numeric" />
            <TextInput style={styles.measureInput} placeholder="Bel (cm)" placeholderTextColor={Colors.textMuted} value={draft.belCm} onChangeText={(v) => setDraft((p) => ({ ...p, belCm: v }))} keyboardType="numeric" />
            <TextInput style={styles.measureInput} placeholder="Kalça (cm)" placeholderTextColor={Colors.textMuted} value={draft.kalcaCm} onChangeText={(v) => setDraft((p) => ({ ...p, kalcaCm: v }))} keyboardType="numeric" />
          </View>
          <TouchableOpacity style={styles.secondaryButton} onPress={saveMeasurements}>
            <Text style={styles.secondaryButtonText}>Ölçüleri kaydet</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Video notu</Text>
        <View style={styles.videoCard}>
          <Text style={styles.videoText}>20–45 sn ayna videosu</Text>
          <TouchableOpacity style={styles.secondaryButton} onPress={recordVideoNote}>
            <Ionicons name={videoNoteUri ? 'checkmark-circle-outline' : 'videocam-outline'} size={16} color={videoNoteUri ? Colors.goldLight : Colors.gold} />
            <Text style={styles.secondaryButtonText}>{videoNoteUri ? 'Yenile' : 'Video notu çek'}</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.section}>
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>Arkadaşlar</Text>
          <TouchableOpacity style={styles.sectionActionBtn} onPress={() => setShowFriendForm((v) => !v)}>
            <Ionicons name="person-add-outline" size={14} color={Colors.gold} />
            <Text style={styles.sectionActionText}>Arkadaş ekle</Text>
          </TouchableOpacity>
        </View>

        {showFriendForm && (
          <View style={styles.friendFormCard}>
            <TextInput
              style={styles.friendInput}
              placeholder="İsim"
              placeholderTextColor={Colors.textMuted}
              value={friendName}
              onChangeText={setFriendName}
            />
            <TextInput
              style={styles.friendInput}
              placeholder="@kullaniciAdi"
              placeholderTextColor={Colors.textMuted}
              value={friendUsername}
              onChangeText={setFriendUsername}
              autoCapitalize="none"
            />
            <TouchableOpacity style={styles.sectionActionBtn} onPress={handleAddFriend}>
              <Text style={styles.sectionActionText}>Ekle</Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.stack}>
          {friends.length === 0 ? (
            <Text style={styles.emptyText}>Henüz arkadaş yok</Text>
          ) : (
            friends.slice(0, 8).map((friend) => (
              <View key={friend.id} style={styles.friendRow}>
                <View style={[styles.friendAvatar, { backgroundColor: friend.avatarColor }]}>
                  <Text style={styles.friendAvatarText}>{friend.name.charAt(0).toUpperCase()}</Text>
                </View>
                <View style={styles.friendInfo}>
                  <Text style={styles.friendName}>{friend.name}</Text>
                  <Text style={styles.friendUsername}>{friend.username}</Text>
                </View>
              </View>
            ))
          )}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Paylaşılanlar</Text>
        <View style={styles.stack}>
          {latestShares.length === 0 ? (
            <Text style={styles.emptyText}>Henüz paylaşım yok</Text>
          ) : (
            latestShares.map((share) => (
              <View key={share.id} style={styles.shareRow}>
                {share.previewImageUri ? (
                  <Image source={{ uri: share.previewImageUri }} style={styles.sharePreview} />
                ) : (
                  <View style={styles.sharePreviewFallback}>
                    <Ionicons name="images-outline" size={14} color={Colors.textMuted} />
                  </View>
                )}
                <View style={styles.shareContent}>
                  <Text style={styles.shareTitle}>{share.lookTitle}</Text>
                  <Text style={styles.shareMeta}>→ {share.recipientUsername} · {formatShareTime(share.timestamp)}</Text>
                </View>
              </View>
            ))
          )}
        </View>
      </View>

      <TouchableOpacity
        style={styles.resetBtn}
        onPress={() =>
          Alert.alert('Çıkış Yap', 'Oturumunuz kapatılacak.', [
            { text: 'Vazgeç', style: 'cancel' },
            { text: 'Çıkış Yap', style: 'destructive', onPress: logout },
          ])
        }
      >
        <Text style={styles.resetText}>Çıkış yap</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { paddingBottom: Spacing['4xl'] },
  profileHeader: {
    paddingBottom: Spacing.xl,
    paddingHorizontal: Spacing.base,
    gap: Spacing.sm,
  },
  wordmark: {
    // removed — replaced by BrandMark component
  },
  wordmarkRule: {
    // removed — replaced by BrandMark component
  },
  profileName: { color: Colors.textPrimary, fontSize: Typography.xl, fontWeight: '800' },
  profileHandle: { color: Colors.textSecondary, fontSize: Typography.sm },
  planBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
  },
  planBadgeText: { color: Colors.goldLight, fontSize: Typography.xs, fontWeight: '600' },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: Spacing.base,
    gap: Spacing.md,
    marginTop: Spacing.base,
  },
  statCard: {
    width: '47%',
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    alignItems: 'center',
    gap: Spacing.xs,
  },
  statValue: { color: Colors.textPrimary, fontSize: Typography['2xl'], fontWeight: '700' },
  statLabel: { color: Colors.textSecondary, fontSize: Typography.xs },
  section: { paddingHorizontal: Spacing.base, marginTop: Spacing.xl, gap: Spacing.md },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sectionTitle: {
    color: Colors.textMuted,
    fontSize: Typography.xs,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1.5,
  },
  stack: { gap: Spacing.md },
  planCard: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    gap: Spacing.xs,
    borderLeftWidth: 2,
    borderLeftColor: 'transparent',
  },
  planCardActive: { borderLeftColor: Colors.gold },
  planRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  planTitle: { color: Colors.textPrimary, fontWeight: '500', fontSize: Typography.base },
  planSubtitle: { color: Colors.textSecondary, fontSize: Typography.xs },
  currentPlanTag: {
    color: Colors.goldLight,
    fontSize: 10,
    fontWeight: '500',
  },
  planPrice: { color: Colors.goldLight, fontWeight: '600', fontSize: Typography.base },
  planHint: { color: Colors.textSecondary, fontSize: Typography.xs },
  paymentButton: {
    marginTop: Spacing.xs,
    alignSelf: 'flex-start',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.gold,
    borderRadius: Radius.sm,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  paymentButtonText: { color: Colors.gold, fontWeight: '500', fontSize: Typography.xs },
  measurementsCard: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    gap: Spacing.md,
  },
  measureGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  measureInput: {
    width: '47%',
    borderRadius: Radius.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.borderLight,
    backgroundColor: 'transparent',
    color: Colors.textPrimary,
    paddingHorizontal: 0,
    paddingVertical: Spacing.sm,
    fontSize: Typography.sm,
  },
  secondaryButton: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: Spacing.sm,
  },
  secondaryButtonText: { color: Colors.gold, fontWeight: '500', fontSize: Typography.xs },
  videoCard: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    gap: Spacing.sm,
  },
  videoText: { color: Colors.textSecondary, fontSize: Typography.sm, lineHeight: 20 },
  videoStatus: { color: Colors.textPrimary, fontSize: Typography.xs, fontWeight: '700' },
  sectionActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderRadius: Radius.sm,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.borderLight,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 6,
  },
  sectionActionText: {
    color: Colors.gold,
    fontSize: Typography.xs,
    fontWeight: '500',
  },
  friendFormCard: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.md,
    padding: Spacing.base,
    gap: Spacing.sm,
  },
  friendInput: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.borderLight,
    color: Colors.textPrimary,
    paddingVertical: Spacing.sm,
    fontSize: Typography.sm,
  },
  friendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    backgroundColor: Colors.surface,
    borderRadius: Radius.md,
    padding: Spacing.sm,
  },
  friendAvatar: {
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },
  friendAvatarText: {
    color: Colors.background,
    fontWeight: '700',
    fontSize: Typography.xs,
  },
  friendInfo: { gap: 1 },
  friendName: { color: Colors.textPrimary, fontSize: Typography.sm, fontWeight: '500' },
  friendUsername: { color: Colors.textSecondary, fontSize: Typography.xs },
  emptyText: {
    color: Colors.textSecondary,
    fontSize: Typography.sm,
  },
  shareRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    backgroundColor: Colors.surface,
    borderRadius: Radius.md,
    padding: Spacing.sm,
  },
  sharePreview: {
    width: 42,
    height: 42,
    borderRadius: Radius.sm,
  },
  sharePreviewFallback: {
    width: 42,
    height: 42,
    borderRadius: Radius.sm,
    backgroundColor: Colors.surfaceElevated,
    alignItems: 'center',
    justifyContent: 'center',
  },
  shareContent: { flex: 1, gap: 2 },
  shareTitle: { color: Colors.textPrimary, fontSize: Typography.sm, fontWeight: '500' },
  shareMeta: { color: Colors.textSecondary, fontSize: Typography.xs },
  resetBtn: {
    alignSelf: 'center',
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.xl,
    marginTop: Spacing.xl,
    marginBottom: Spacing['3xl'],
  },
  resetText: {
    color: Colors.textMuted,
    fontSize: Typography.xs,
    letterSpacing: 0.3,
  },
});
