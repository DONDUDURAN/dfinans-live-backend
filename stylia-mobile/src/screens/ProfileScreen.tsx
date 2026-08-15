import React, { useMemo, useState } from 'react';
import {
  Alert,
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
import { useWardrobeStore } from '../store/wardrobeStore';
import { useUserStore } from '../store/userStore';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';
import { MEMBERSHIP_PLANS, MembershipPlanId, STRIPE_PAYMENT_LINKS } from '../config/paymentLinks';

const PLAN_ORDER: MembershipPlanId[] = ['aylik', 'yillik'];

export const ProfileScreen: React.FC = () => {
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

  const [draft, setDraft] = useState(measurements);

  const totalWorn = items.reduce((acc, i) => acc + i.timesWorn, 0);
  const trialDaysLeft = useMemo(() => {
    if (!trialEndsAt) return 0;
    const diff = new Date(trialEndsAt).getTime() - Date.now();
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
  }, [trialEndsAt]);

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
      Alert.alert('Video notu eklendi', 'Stil danışmanı bu videoyu referans alacak.');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <LinearGradient colors={['#171103', Colors.background]} style={styles.profileHeader}>
        <View style={styles.wordmarkWrap}>
          <Text style={styles.wordmark} numberOfLines={1} adjustsFontSizeToFit>STYLIA</Text>
          <View style={styles.wordmarkRule} />
        </View>
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
          { icon: 'layers-outline', label: 'Kombin', value: outfits.length },
          { icon: 'repeat-outline', label: 'Kullanım', value: totalWorn },
          { icon: 'heart-outline', label: 'Favori', value: items.filter((i) => i.isFavorite).length },
        ].map((stat) => (
          <View key={stat.label} style={[styles.statCard, Shadow.sm]}>
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
                  <Text style={styles.paymentButtonText}>Stripe Payment Link ile öde</Text>
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
        <Text style={styles.sectionTitle}>Video notu akışı</Text>
        <View style={styles.videoCard}>
          <Text style={styles.videoText}>
            Stil danışmanı için 20-45 saniyelik kısa bir ayna videosu kaydet.
          </Text>
          <Text style={styles.videoStatus}>
            {videoNoteUri ? 'Video notu mevcut' : 'Henüz video notu yok'}
          </Text>
          <TouchableOpacity style={styles.secondaryButton} onPress={recordVideoNote}>
            <Ionicons name="videocam-outline" size={16} color={Colors.gold} />
            <Text style={styles.secondaryButtonText}>Video notu çek</Text>
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { paddingBottom: Spacing['4xl'] },
  profileHeader: {
    paddingTop: Spacing['2xl'],
    paddingBottom: Spacing.xl,
    paddingHorizontal: Spacing.base,
    gap: Spacing.sm,
  },
  wordmarkWrap: {
    alignSelf: 'flex-start',
    marginBottom: 2,
  },
  wordmark: {
    color: Colors.goldLight,
    letterSpacing: 12,
    fontWeight: '100',
    fontSize: 40,
  },
  wordmarkRule: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: Colors.gold,
    marginTop: 4,
    width: '80%',
    opacity: 0.65,
  },
  profileName: { color: Colors.textPrimary, fontSize: Typography.xl, fontWeight: '800' },
  profileHandle: { color: Colors.textSecondary, fontSize: Typography.sm },
  planBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
    borderRadius: Radius.full,
    borderWidth: 1,
    borderColor: Colors.gold + '66',
    backgroundColor: Colors.gold + '1F',
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
  },
  planBadgeText: { color: Colors.goldLight, fontSize: Typography.xs, fontWeight: '700' },
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
    borderWidth: 1,
    borderColor: Colors.border,
  },
  statValue: { color: Colors.textPrimary, fontSize: Typography['2xl'], fontWeight: '800' },
  statLabel: { color: Colors.textSecondary, fontSize: Typography.xs },
  section: { paddingHorizontal: Spacing.base, marginTop: Spacing.xl, gap: Spacing.md },
  sectionTitle: { color: Colors.textPrimary, fontSize: Typography.md, fontWeight: '700' },
  stack: { gap: Spacing.md },
  planCard: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.base,
    gap: Spacing.xs,
  },
  planCardActive: { borderColor: Colors.gold, ...Shadow.gold },
  planRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  planTitle: { color: Colors.textPrimary, fontWeight: '700', fontSize: Typography.base },
  planSubtitle: { color: Colors.textSecondary, fontSize: Typography.xs },
  currentPlanTag: {
    color: Colors.goldLight,
    borderWidth: 1,
    borderColor: Colors.gold + '66',
    borderRadius: Radius.full,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    fontSize: 10,
    fontWeight: '700',
  },
  planPrice: { color: Colors.gold, fontWeight: '800', fontSize: Typography.lg },
  planHint: { color: Colors.textSecondary, fontSize: Typography.xs },
  paymentButton: {
    marginTop: Spacing.xs,
    backgroundColor: Colors.gold,
    borderRadius: Radius.full,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  paymentButtonText: { color: Colors.background, fontWeight: '700', fontSize: Typography.xs },
  measurementsCard: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.base,
    gap: Spacing.md,
  },
  measureGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  measureInput: {
    width: '47%',
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.borderLight,
    backgroundColor: Colors.surfaceElevated,
    color: Colors.textPrimary,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.sm,
    fontSize: Typography.sm,
  },
  secondaryButton: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderRadius: Radius.full,
    borderWidth: 1,
    borderColor: Colors.gold,
    backgroundColor: Colors.gold + '1D',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
  },
  secondaryButtonText: { color: Colors.gold, fontWeight: '700', fontSize: Typography.xs },
  videoCard: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.base,
    gap: Spacing.sm,
  },
  videoText: { color: Colors.textSecondary, fontSize: Typography.sm, lineHeight: 20 },
  videoStatus: { color: Colors.textPrimary, fontSize: Typography.xs, fontWeight: '700' },
});
