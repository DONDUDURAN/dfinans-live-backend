export const STRIPE_PAYMENT_LINKS = {
  aylik: 'https://buy.stripe.com/test_00g6oH8hB2YV6YI8ww',
  yillik: 'https://buy.stripe.com/test_aEU6oH3Xld7va34fYZ',
};

export const MEMBERSHIP_PLANS = {
  aylik: {
    id: 'aylik',
    title: 'Aylık STYLIA Plus',
    subtitle: 'Esnek aylık üyelik',
    price: '₺699 / ay',
    trial: '7 gün ücretsiz deneme',
  },
  yillik: {
    id: 'yillik',
    title: 'Yıllık STYLIA Elite',
    subtitle: 'Yıllık peşin, daha uygun fiyat',
    price: '₺4.990 / yıl',
    trial: 'Aylık plana göre %40 tasarruf',
  },
} as const;

export type MembershipPlanId = keyof typeof MEMBERSHIP_PLANS;
