import React, { useMemo, useState } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Linking,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { BrandMark } from '../components/BrandMark';
import { MEMBERSHIP_PLANS, MembershipPlanId, STRIPE_PAYMENT_LINKS } from '../config/paymentLinks';
import { useUserStore } from '../store/userStore';
import { Colors, Radius, Spacing, Typography } from '../theme';

const PLAN_ORDER: MembershipPlanId[] = ['aylik', 'yillik'];

export const RegistrationScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const register = useUserStore((s) => s.register);

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [selectedPlan, setSelectedPlan] = useState<MembershipPlanId>('yillik');

  const canStart = useMemo(
    () => fullName.trim().length > 2 && email.includes('@'),
    [email, fullName]
  );

  const openPaymentLink = async (plan: MembershipPlanId) => {
    const url = STRIPE_PAYMENT_LINKS[plan];
    const supported = await Linking.canOpenURL(url);
    if (!supported) {
      Alert.alert('Bağlantı açılamadı', 'Stripe ödeme bağlantısı şu an açılamıyor.');
      return;
    }
    await Linking.openURL(url);
  };

  const handleStartTrial = () => {
    if (!canStart) {
      Alert.alert('Eksik bilgi', 'Lütfen ad-soyad ve geçerli e-posta girin.');
      return;
    }
    register({ fullName: fullName.trim(), email: email.trim(), plan: selectedPlan });
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {/* ── Brand header ── */}
      <LinearGradient
        colors={['#050D08', Colors.background]}
        style={[styles.header, { paddingTop: insets.top + Spacing['2xl'] }]}
      >
        <BrandMark size="lg" />
        <Text style={styles.subtitle}>Kişisel stil kabininiz</Text>
      </LinearGradient>

      <ScrollView
        contentContainerStyle={styles.body}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* ── Account fields ── */}
        <View style={styles.fieldGroup}>
          <TextInput
            value={fullName}
            onChangeText={setFullName}
            placeholder="Ad Soyad"
            placeholderTextColor={Colors.textMuted}
            style={styles.field}
          />
          <View style={styles.fieldDivider} />
          <TextInput
            value={email}
            onChangeText={setEmail}
            placeholder="E-posta"
            placeholderTextColor={Colors.textMuted}
            keyboardType="email-address"
            autoCapitalize="none"
            style={styles.field}
          />
        </View>

        {/* ── Membership rows ── */}
        <View style={styles.planGroup}>
          <Text style={styles.planGroupLabel}>ÜYELİK</Text>
          {PLAN_ORDER.map((planId) => {
            const plan = MEMBERSHIP_PLANS[planId];
            const selected = selectedPlan === planId;
            return (
              <TouchableOpacity
                key={planId}
                style={styles.planRow}
                onPress={() => setSelectedPlan(planId)}
                activeOpacity={0.7}
              >
                <View style={[styles.planDot, selected && styles.planDotActive]} />
                <View style={styles.planInfo}>
                  <Text style={[styles.planTitle, selected && styles.planTitleActive]}>
                    {plan.title}
                  </Text>
                </View>
                <Text style={[styles.planPrice, selected && styles.planPriceActive]}>
                  {plan.price}
                </Text>
                <TouchableOpacity
                  style={styles.payBtn}
                  onPress={() => openPaymentLink(planId)}
                  hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                >
                  <Text style={styles.payBtnText}>Öde</Text>
                </TouchableOpacity>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* ── CTA ── */}
        <TouchableOpacity
          style={[styles.ctaBtn, !canStart && styles.ctaBtnDisabled]}
          onPress={handleStartTrial}
          disabled={!canStart}
          activeOpacity={0.85}
        >
          <Text style={styles.ctaBtnText}>Denemeyi başlat</Text>
        </TouchableOpacity>

        <Text style={styles.finePrint}>7 gün ücretsiz · kart bilgisi saklanmaz</Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    paddingBottom: Spacing['2xl'],
    paddingHorizontal: Spacing.base,
    gap: Spacing.md,
  },
  subtitle: {
    color: Colors.textSecondary,
    fontSize: Typography.base,
    fontWeight: '300',
    letterSpacing: 0.5,
  },
  body: {
    paddingHorizontal: Spacing.base,
    paddingTop: Spacing.lg,
    paddingBottom: Spacing['3xl'],
    gap: Spacing['2xl'],
  },
  // ── Fields ────────────────────────────────────────────────────────────────
  fieldGroup: {
    gap: 0,
  },
  field: {
    color: Colors.textPrimary,
    fontSize: Typography.base,
    paddingVertical: Spacing.base,
    letterSpacing: 0.2,
  },
  fieldDivider: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: Colors.border,
  },
  // ── Plan rows ─────────────────────────────────────────────────────────────
  planGroup: {
    gap: 0,
  },
  planGroupLabel: {
    color: Colors.textMuted,
    fontSize: Typography.xs,
    fontWeight: '600',
    letterSpacing: 1.5,
    marginBottom: Spacing.md,
  },
  planRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
    paddingVertical: Spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.border,
  },
  planDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: Colors.surfaceElevated,
    borderWidth: 1,
    borderColor: Colors.borderLight,
  },
  planDotActive: {
    backgroundColor: Colors.gold,
    borderColor: Colors.gold,
  },
  planInfo: {
    flex: 1,
  },
  planTitle: {
    color: Colors.textSecondary,
    fontSize: Typography.base,
    fontWeight: '400',
  },
  planTitleActive: {
    color: Colors.textPrimary,
    fontWeight: '500',
  },
  planPrice: {
    color: Colors.textMuted,
    fontSize: Typography.sm,
    fontWeight: '400',
  },
  planPriceActive: {
    color: Colors.goldLight,
    fontWeight: '500',
  },
  payBtn: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 5,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.borderLight,
    borderRadius: Radius.sm,
  },
  payBtnText: {
    color: Colors.textSecondary,
    fontSize: Typography.xs,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  // ── CTA ───────────────────────────────────────────────────────────────────
  ctaBtn: {
    backgroundColor: Colors.goldDark,
    borderRadius: Radius.md,
    paddingVertical: 14,
    alignItems: 'center',
  },
  ctaBtnDisabled: {
    opacity: 0.38,
  },
  ctaBtnText: {
    color: Colors.textPrimary,
    fontSize: Typography.base,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  finePrint: {
    color: Colors.textMuted,
    fontSize: Typography.xs,
    textAlign: 'center',
    letterSpacing: 0.5,
    marginTop: -Spacing.base,
  },
});

