import { create } from 'zustand';
import { MembershipPlanId } from '../config/paymentLinks';

interface BodyMeasurements {
  boyCm: string;
  kiloKg: string;
  gogusCm: string;
  belCm: string;
  kalcaCm: string;
}

interface UserState {
  registered: boolean;
  fullName: string;
  email: string;
  selectedPlan: MembershipPlanId;
  trialStartedAt?: string;
  trialEndsAt?: string;
  productLink: string;
  videoNoteUri?: string;
  measurements: BodyMeasurements;

  register: (payload: { fullName: string; email: string; plan: MembershipPlanId }) => void;
  switchPlan: (plan: MembershipPlanId) => void;
  setMeasurements: (measurements: BodyMeasurements) => void;
  setVideoNoteUri: (uri?: string) => void;
  setProductLink: (link: string) => void;
}

const nowIso = () => new Date().toISOString();
const addDaysIso = (days: number) => {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString();
};

export const useUserStore = create<UserState>((set) => ({
  registered: false,
  fullName: '',
  email: '',
  selectedPlan: 'yillik',
  trialStartedAt: undefined,
  trialEndsAt: undefined,
  productLink: '',
  videoNoteUri: undefined,
  measurements: {
    boyCm: '',
    kiloKg: '',
    gogusCm: '',
    belCm: '',
    kalcaCm: '',
  },

  register: ({ fullName, email, plan }) =>
    set({
      registered: true,
      fullName,
      email,
      selectedPlan: plan,
      trialStartedAt: nowIso(),
      trialEndsAt: addDaysIso(7),
    }),

  switchPlan: (plan) => set({ selectedPlan: plan }),

  setMeasurements: (measurements) => set({ measurements }),

  setVideoNoteUri: (uri) => set({ videoNoteUri: uri }),

  setProductLink: (link) => set({ productLink: link.trim() }),
}));
