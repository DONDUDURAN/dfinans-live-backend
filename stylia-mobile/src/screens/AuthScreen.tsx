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

type Mode = 'login' | 'register';
const PLAN_ORDER: MembershipPlanId[] = ['aylik', 'yillik'];

interface Props {
  /** Controls which tab opens first. Injected by AppNavigator based on `hasAccount`. */
  initialMode?: Mode;
}

export const AuthScreen: React.FC<Props> = ({ initialMode = 'register' }) => {
  const insets = useSafeAreaInsets();
  const hasAccount = useUserStore((s) => s.hasAccount);
  const register = useUserStore((s) => s.register);
  const login = useUserStore((s) => s.login);

  // Default to login if account exists, register otherwise
  const [mode, setMode] = useState<Mode>(hasAccount ? 'login' : initialMode);

  // ── Register fields ──────────────────────────────────────────────────────
  const [regName, setRegName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [selectedPlan, setSelectedPlan] = useState<MembershipPlanId>('yillik');

  // ── Login fields ─────────────────────────────────────────────────────────
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');

  const canRegister = useMemo(
    () => regName.trim().length > 2 && regEmail.includes('@') && regPassword.length >= 6,
    [regName, regEmail, regPassword]
  );

  const canLogin = useMemo(
    () => loginEmail.includes('@') && loginPassword.length >= 1,
    [loginEmail, loginPassword]
  );

  const openPaymentLink = async (planId: MembershipPlanId) => {
    const url = STRIPE_PAYMENT_LINKS[planId];
    const supported = await Linking.canOpenURL(url);
    if (!supported) {
      Alert.alert('Bağlantı açılamadı', 'Stripe ödeme sayfası açılamıyor.');
      return;
    }
    await Linking.openURL(url);
  };

  const handleRegister = () => {
    if (!canRegister) {
      Alert.alert('Eksik bilgi', 'Ad, e-posta ve en az 6 karakterli şifre gerekli.');
      return;
    }
    register({ fullName: regName.trim(), email: regEmail.trim(), password: regPassword, plan: selectedPlan });
  };

  const handleLogin = () => {
    if (!canLogin) return;
    setLoginError('');
    const result = login({ email: loginEmail.trim(), password: loginPassword });
    if (!result.ok) {
      setLoginError(result.error ?? 'Giriş başarısız.');
    }
  };

  const switchMode = (m: Mode) => {
    setLoginError('');
    setMode(m);
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <LinearGradient
        colors={['#040C07', Colors.background]}
        style={[styles.header, { paddingTop: insets.top + Spacing['2xl'] }]}
      >
        <BrandMark size="lg" />
        <Text style={styles.tagline}>Kişisel stil kabininiz</Text>
      </LinearGradient>

      {/* ── Mode tabs ───────────────────────────────────────────────────── */}
      <View style={styles.tabs}>
        <TouchableOpacity style={styles.tab} onPress={() => switchMode('login')} activeOpacity={0.7}>
          <Text style={[styles.tabText, mode === 'login' && styles.tabTextActive]}>Giriş Yap</Text>
          {mode === 'login' && <View style={styles.tabLine} />}
        </TouchableOpacity>
        <View style={styles.tabSep} />
        <TouchableOpacity style={styles.tab} onPress={() => switchMode('register')} activeOpacity={0.7}>
          <Text style={[styles.tabText, mode === 'register' && styles.tabTextActive]}>Kayıt Ol</Text>
          {mode === 'register' && <View style={styles.tabLine} />}
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.body}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* ── Login form ────────────────────────────────────────────────── */}
        {mode === 'login' && (
          <>
            <View style={styles.fieldGroup}>
              <TextInput
                value={loginEmail}
                onChangeText={(t) => { setLoginEmail(t); setLoginError(''); }}
                placeholder="E-posta"
                placeholderTextColor={Colors.textMuted}
                keyboardType="email-address"
                autoCapitalize="none"
                style={styles.field}
              />
              <View style={styles.fieldDivider} />
              <TextInput
                value={loginPassword}
                onChangeText={(t) => { setLoginPassword(t); setLoginError(''); }}
                placeholder="Şifre"
                placeholderTextColor={Colors.textMuted}
                secureTextEntry
                style={styles.field}
              />
            </View>

            {loginError ? <Text style={styles.errorText}>{loginError}</Text> : null}

            <TouchableOpacity
              style={[styles.ctaBtn, !canLogin && styles.ctaBtnDisabled]}
              onPress={handleLogin}
              disabled={!canLogin}
              activeOpacity={0.85}
            >
              <Text style={styles.ctaBtnText}>Giriş Yap</Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={() => switchMode('register')} activeOpacity={0.7}>
              <Text style={styles.switchLink}>Hesabın yok mu? <Text style={styles.switchLinkAccent}>Kayıt ol</Text></Text>
            </TouchableOpacity>
          </>
        )}

        {/* ── Register form ─────────────────────────────────────────────── */}
        {mode === 'register' && (
          <>
            <View style={styles.fieldGroup}>
              <TextInput
                value={regName}
                onChangeText={setRegName}
                placeholder="Ad Soyad"
                placeholderTextColor={Colors.textMuted}
                style={styles.field}
              />
              <View style={styles.fieldDivider} />
              <TextInput
                value={regEmail}
                onChangeText={setRegEmail}
                placeholder="E-posta"
                placeholderTextColor={Colors.textMuted}
                keyboardType="email-address"
                autoCapitalize="none"
                style={styles.field}
              />
              <View style={styles.fieldDivider} />
              <TextInput
                value={regPassword}
                onChangeText={setRegPassword}
                placeholder="Şifre (min. 6 karakter)"
                placeholderTextColor={Colors.textMuted}
                secureTextEntry
                style={styles.field}
              />
            </View>

            {/* Plan rows */}
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
                    <Text style={[styles.planTitle, selected && styles.planTitleActive]}>{plan.title}</Text>
                    <Text style={[styles.planPrice, selected && styles.planPriceActive]}>{plan.price}</Text>
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

            <TouchableOpacity
              style={[styles.ctaBtn, !canRegister && styles.ctaBtnDisabled]}
              onPress={handleRegister}
              disabled={!canRegister}
              activeOpacity={0.85}
            >
              <Text style={styles.ctaBtnText}>Denemeyi başlat</Text>
            </TouchableOpacity>

            <Text style={styles.finePrint}>7 gün ücretsiz · kart bilgisi saklanmaz</Text>

            {hasAccount && (
              <TouchableOpacity onPress={() => switchMode('login')} activeOpacity={0.7}>
                <Text style={styles.switchLink}>Zaten hesabın var mı? <Text style={styles.switchLinkAccent}>Giriş yap</Text></Text>
              </TouchableOpacity>
            )}
          </>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },

  header: {
    paddingBottom: Spacing.xl,
    paddingHorizontal: Spacing.base,
    gap: Spacing.sm,
  },
  tagline: {
    color: Colors.textSecondary,
    fontSize: Typography.base,
    fontWeight: '300',
    letterSpacing: 0.4,
  },

  // ── Tabs ──────────────────────────────────────────────────────────────────
  tabs: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.base,
    marginBottom: Spacing.lg,
    gap: Spacing.lg,
  },
  tab: { paddingBottom: Spacing.xs, gap: 4 },
  tabText: {
    color: Colors.textMuted,
    fontSize: Typography.sm,
    fontWeight: '500',
    letterSpacing: 0.4,
  },
  tabTextActive: { color: Colors.textPrimary },
  tabLine: {
    height: 1,
    backgroundColor: Colors.gold,
    borderRadius: 1,
  },
  tabSep: { width: StyleSheet.hairlineWidth, height: 14, backgroundColor: Colors.border },

  // ── Body ──────────────────────────────────────────────────────────────────
  body: {
    paddingHorizontal: Spacing.base,
    paddingBottom: Spacing['3xl'],
    gap: Spacing['2xl'],
  },

  // ── Fields ────────────────────────────────────────────────────────────────
  fieldGroup: { gap: 0 },
  field: {
    color: Colors.textPrimary,
    fontSize: Typography.base,
    paddingVertical: Spacing.base,
    letterSpacing: 0.2,
  },
  fieldDivider: { height: StyleSheet.hairlineWidth, backgroundColor: Colors.border },

  // ── Plan rows ─────────────────────────────────────────────────────────────
  planGroup: { gap: 0 },
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
  planDotActive: { backgroundColor: Colors.gold, borderColor: Colors.gold },
  planTitle: { flex: 1, color: Colors.textSecondary, fontSize: Typography.base, fontWeight: '400' },
  planTitleActive: { color: Colors.textPrimary, fontWeight: '500' },
  planPrice: { color: Colors.textMuted, fontSize: Typography.sm, fontWeight: '400' },
  planPriceActive: { color: Colors.goldLight, fontWeight: '500' },
  payBtn: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 5,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.borderLight,
    borderRadius: Radius.sm,
  },
  payBtnText: { color: Colors.textSecondary, fontSize: Typography.xs, fontWeight: '500', letterSpacing: 0.5 },

  // ── CTA ───────────────────────────────────────────────────────────────────
  ctaBtn: {
    backgroundColor: Colors.goldDark,
    borderRadius: Radius.md,
    paddingVertical: 14,
    alignItems: 'center',
  },
  ctaBtnDisabled: { opacity: 0.38 },
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

  // ── Switch prompt ─────────────────────────────────────────────────────────
  switchLink: {
    color: Colors.textMuted,
    fontSize: Typography.sm,
    textAlign: 'center',
    marginTop: -Spacing.sm,
  },
  switchLinkAccent: { color: Colors.goldLight },

  // ── Error ─────────────────────────────────────────────────────────────────
  errorText: {
    color: Colors.error,
    fontSize: Typography.sm,
    marginTop: -Spacing.base,
  },
});
