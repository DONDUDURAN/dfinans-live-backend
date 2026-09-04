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
  // ── Auth ──────────────────────────────────────────────────────────────────
  hasAccount: boolean;       // account ever created on this device
  isAuthenticated: boolean;  // currently logged in
  password: string;          // local mock credential

  // ── Profile ───────────────────────────────────────────────────────────────
  fullName: string;
  email: string;
  selectedPlan: MembershipPlanId;
  trialStartedAt?: string;
  trialEndsAt?: string;
  productLink: string;
  videoNoteUri?: string;
  measurements: BodyMeasurements;

  // ── Actions ───────────────────────────────────────────────────────────────
  register: (payload: { fullName: string; email: string; password: string; plan: MembershipPlanId }) => void;
  login: (payload: { email: string; password: string }) => { ok: boolean; error?: string };
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
    (set, get) => ({
      hasAccount: false,
      isAuthenticated: false,
      password: '',
      fullName: '',
      email: '',
      selectedPlan: 'yillik' as MembershipPlanId,
      trialStartedAt: undefined,
      trialEndsAt: undefined,
      productLink: '',
      videoNoteUri: undefined,
      measurements: { ...EMPTY_MEASUREMENTS },

      register: ({ fullName, email, password, plan }) =>
        set({
          hasAccount: true,
          isAuthenticated: true,
          password,
          fullName,
          email,
          selectedPlan: plan,
          trialStartedAt: nowIso(),
          trialEndsAt: addDaysIso(7),
        }),

      login: ({ email, password }) => {
        const state = get();
        if (!state.hasAccount) {
          return { ok: false, error: 'Hesap bulunamadı.' };
        }
        if (email.trim().toLowerCase() !== state.email.toLowerCase()) {
          return { ok: false, error: 'E-posta adresi eşleşmiyor.' };
        }
        if (password !== state.password) {
          return { ok: false, error: 'Şifre hatalı.' };
        }
        set({ isAuthenticated: true });
        return { ok: true };
      },

      switchPlan: (plan) => set({ selectedPlan: plan }),
      setMeasurements: (measurements) => set({ measurements }),
      setVideoNoteUri: (uri) => set({ videoNoteUri: uri }),
      setProductLink: (link) => set({ productLink: link.trim() }),

      logout: () => set({ isAuthenticated: false }),
    }),
    {
      name: 'stylia-user-store',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        hasAccount: state.hasAccount,
        isAuthenticated: state.isAuthenticated,
        password: state.password,
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
