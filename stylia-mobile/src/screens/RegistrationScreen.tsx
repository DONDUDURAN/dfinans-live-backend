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
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { BrandMark } from '../components/BrandMark';
import { MEMBERSHIP_PLANS, MembershipPlanId, STRIPE_PAYMENT_LINKS } from '../config/paymentLinks';
import { useUserStore } from '../store/userStore';
import { Colors, Radius, Shadow, Spacing, Typography } from '../theme';

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
    register({
      fullName: fullName.trim(),
      email: email.trim(),
      plan: selectedPlan,
    });
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <LinearGradient colors={['#041514', Colors.background]} style={[styles.header, { paddingTop: insets.top + Spacing.xl }]}>
        <BrandMark size="lg" />
        <Text style={styles.subtitle}>Kişisel stil kabininize hoş geldiniz</Text>
        <Text style={styles.trialTag}>7 gün ücretsiz deneme • Kart bilgisi uygulamada saklanmaz</Text>
      </LinearGradient>

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Hesap oluştur</Text>
          <TextInput
            value={fullName}
            onChangeText={setFullName}
            placeholder="Ad Soyad"
            placeholderTextColor={Colors.textMuted}
            style={styles.input}
          />
          <TextInput
            value={email}
            onChangeText={setEmail}
            placeholder="E-posta"
            placeholderTextColor={Colors.textMuted}
            keyboardType="email-address"
            autoCapitalize="none"
            style={styles.input}
          />
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Üyelik seçimi</Text>
          {PLAN_ORDER.map((planId) => {
            const plan = MEMBERSHIP_PLANS[planId];
            const selected = selectedPlan === planId;
            return (
              <TouchableOpacity
                key={planId}
                style={[styles.planCard, selected && styles.planCardSelected]}
                onPress={() => setSelectedPlan(planId)}
                activeOpacity={0.88}
              >
                <View style={styles.planHeader}>
                  <View>
                    <Text style={styles.planTitle}>{plan.title}</Text>
                    <Text style={styles.planSubtitle}>{plan.subtitle}</Text>
                  </View>
                  <Ionicons
                    name={selected ? 'radio-button-on' : 'radio-button-off'}
                    size={20}
                    color={selected ? Colors.gold : Colors.textMuted}
                  />
                </View>
                <Text style={styles.planPrice}>{plan.price}</Text>
                <Text style={styles.planTrial}>{plan.trial}</Text>
                <TouchableOpacity
                  style={styles.paymentButton}
                  onPress={() => openPaymentLink(planId)}
                >
                  <Ionicons name="card-outline" size={16} color={Colors.background} />
                  <Text style={styles.paymentButtonText}>Stripe ile öde</Text>
                </TouchableOpacity>
              </TouchableOpacity>
            );
          })}
        </View>

        <TouchableOpacity
          style={[styles.startButton, !canStart && styles.startButtonDisabled]}
          onPress={handleStartTrial}
          disabled={!canStart}
        >
          <Text style={styles.startButtonText}>7 günlük denemeyi başlat</Text>
        </TouchableOpacity>
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
    paddingBottom: Spacing.xl,
    paddingHorizontal: Spacing.base,
    gap: Spacing.sm,
  },
  subtitle: {
    color: Colors.textPrimary,
    fontSize: Typography.md,
    fontWeight: '600',
  },
  trialTag: {
    color: Colors.gold,
    fontSize: Typography.xs,
    textTransform: 'uppercase',
    letterSpacing: 0.7,
  },
  body: {
    padding: Spacing.base,
    paddingBottom: Spacing['3xl'],
    gap: Spacing.md,
  },
  card: {
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    gap: Spacing.md,
  },
  cardTitle: {
    color: Colors.textPrimary,
    fontSize: Typography.md,
    fontWeight: '700',
  },
  input: {
    backgroundColor: Colors.surfaceElevated,
    borderWidth: 1,
    borderColor: Colors.borderLight,
    borderRadius: Radius.md,
    color: Colors.textPrimary,
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.md,
    fontSize: Typography.base,
  },
  planCard: {
    backgroundColor: Colors.surfaceElevated,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: Radius.lg,
    padding: Spacing.md,
    gap: Spacing.sm,
  },
  planCardSelected: {
    borderColor: Colors.gold,
    ...Shadow.gold,
  },
  planHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  planTitle: {
    color: Colors.textPrimary,
    fontSize: Typography.base,
    fontWeight: '700',
  },
  planSubtitle: {
    color: Colors.textSecondary,
    fontSize: Typography.xs,
  },
  planPrice: {
    color: Colors.gold,
    fontWeight: '800',
    fontSize: Typography.lg,
  },
  planTrial: {
    color: Colors.textSecondary,
    fontSize: Typography.xs,
  },
  paymentButton: {
    marginTop: Spacing.xs,
    backgroundColor: Colors.gold,
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    borderRadius: Radius.full,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  paymentButtonText: {
    color: Colors.background,
    fontWeight: '700',
    fontSize: Typography.sm,
  },
  startButton: {
    backgroundColor: Colors.goldDark,
    borderRadius: Radius.full,
    paddingVertical: Spacing.base,
    alignItems: 'center',
    marginTop: Spacing.sm,
  },
  startButtonDisabled: {
    opacity: 0.45,
  },
  startButtonText: {
    color: Colors.textPrimary,
    fontSize: Typography.base,
    fontWeight: '800',
    letterSpacing: 0.2,
  },
});
