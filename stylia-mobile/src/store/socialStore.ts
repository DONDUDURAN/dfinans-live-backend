import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface SocialFriend {
  id: string;
  name: string;
  username: string; // @kullanici
  avatarColor: string;
  createdAt: string;
}

export interface SharedLookMessage {
  id: string;
  senderLabel: string;
  recipientId: string;
  recipientName: string;
  recipientUsername: string;
  timestamp: string;
  lookTitle: string;
  previewImageUri?: string;
  note: string;
}

interface SocialState {
  friends: SocialFriend[];
  messages: SharedLookMessage[];

  addFriend: (payload: { name: string; username: string }) => { ok: boolean; error?: string };
  shareLookToFriends: (payload: {
    recipientIds: string[];
    lookTitle: string;
    previewImageUri?: string;
    note?: string;
    senderLabel?: string;
  }) => void;
}

const AVATAR_COLORS = ['#0F9B5E', '#2DC97E', '#4A7EC2', '#BD6BCE', '#CC6B7A', '#6BCEBD'];

const normalizeUsername = (raw: string) => {
  const clean = raw.trim().replace(/\s+/g, '').replace(/^@+/, '');
  return clean ? `@${clean.toLowerCase()}` : '';
};

export const useSocialStore = create<SocialState>()(
  persist(
    (set, get) => ({
      friends: [],
      messages: [],

      addFriend: ({ name, username }) => {
        const normalizedName = name.trim();
        const normalizedUsername = normalizeUsername(username);
        if (normalizedName.length < 2) {
          return { ok: false, error: 'İsim en az 2 karakter olmalı.' };
        }
        if (!normalizedUsername || normalizedUsername.length < 3) {
          return { ok: false, error: 'Geçerli kullanıcı adı girin.' };
        }

        const exists = get().friends.some((f) => f.username === normalizedUsername);
        if (exists) {
          return { ok: false, error: 'Bu kullanıcı zaten eklendi.' };
        }

        const friend: SocialFriend = {
          id: `f_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
          name: normalizedName,
          username: normalizedUsername,
          avatarColor: AVATAR_COLORS[get().friends.length % AVATAR_COLORS.length],
          createdAt: new Date().toISOString(),
        };
        set((state) => ({ friends: [friend, ...state.friends] }));
        return { ok: true };
      },

      shareLookToFriends: ({ recipientIds, lookTitle, previewImageUri, note, senderLabel }) => {
        if (recipientIds.length === 0) return;
        const byId = new Map(get().friends.map((f) => [f.id, f]));
        const now = new Date().toISOString();
        const safeTitle = lookTitle.trim() || 'Stil';
        const safeNote = note?.trim() || 'Yeni görünüm';

        const nextMessages: SharedLookMessage[] = recipientIds
          .map((id) => byId.get(id))
          .filter((friend): friend is SocialFriend => Boolean(friend))
          .map((friend) => ({
            id: `m_${Date.now()}_${friend.id}_${Math.random().toString(36).slice(2, 5)}`,
            senderLabel: senderLabel?.trim() || 'STYLIA',
            recipientId: friend.id,
            recipientName: friend.name,
            recipientUsername: friend.username,
            timestamp: now,
            lookTitle: safeTitle,
            previewImageUri,
            note: safeNote,
          }));

        if (nextMessages.length === 0) return;
        set((state) => ({ messages: [...nextMessages, ...state.messages] }));
      },
    }),
    {
      name: 'stylia-social-store',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        friends: state.friends,
        messages: state.messages,
      }),
    }
  )
);

