import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
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
  logout: () => void;
}

const EMPTY_MEASUREMENTS: BodyMeasurements = {
  boyCm: '', kiloKg: '', gogusCm: '', belCm: '', kalcaCm: '',
};

const nowIso = () => new Date().toISOString();
const addDaysIso = (days: number) => {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString();
};

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      registered: false,
      fullName: '',
      email: '',
      selectedPlan: 'yillik' as MembershipPlanId,
      trialStartedAt: undefined,
      trialEndsAt: undefined,
      productLink: '',
      videoNoteUri: undefined,
      measurements: { ...EMPTY_MEASUREMENTS },

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

      logout: () =>
        set({
          registered: false,
          fullName: '',
          email: '',
          selectedPlan: 'yillik',
          trialStartedAt: undefined,
          trialEndsAt: undefined,
          productLink: '',
          videoNoteUri: undefined,
          measurements: { ...EMPTY_MEASUREMENTS },
        }),
    }),
    {
      name: 'stylia-user-store',
      storage: createJSONStorage(() => AsyncStorage),
      // Only persist data fields — not actions
      partialize: (state) => ({
        registered: state.registered,
        fullName: state.fullName,
        email: state.email,
        selectedPlan: state.selectedPlan,
        trialStartedAt: state.trialStartedAt,
        trialEndsAt: state.trialEndsAt,
        productLink: state.productLink,
        videoNoteUri: state.videoNoteUri,
        measurements: state.measurements,
      }),
    }
  )
);
