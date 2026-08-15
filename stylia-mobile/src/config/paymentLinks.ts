export const STRIPE_PAYMENT_LINKS = {
  aylik: 'https://buy.stripe.com/test_00g6oH8hB2YV6YI8ww',
  yillik: 'https://buy.stripe.com/test_aEU6oH3Xld7va34fYZ',
};

export const MEMBERSHIP_PLANS = {
  aylik: {
    id: 'aylik',
    title: 'Aylik STYLIA Plus',
    subtitle: 'Esnek aylik üyelik',
    price: '₺699 / ay',
    trial: '7 gün ücretsiz deneme',
  },
  yillik: {
    id: 'yillik',
    title: 'Yillik STYLIA Elite',
    subtitle: 'Yillik peşin, daha uygun fiyat',
    price: '₺4.990 / yil',
    trial: 'Aylik plana göre %40 tasarruf',
  },
} as const;

export type MembershipPlanId = keyof typeof MEMBERSHIP_PLANS;
