import { create } from 'zustand';
import { UserStateResponse, GenerateSessionRequest } from '../types/domain';

interface UserStoreState {
  userId: string | null;
  stateDocument: UserStateResponse | null;
  isHydrated: boolean;
}

interface UserStoreActions {
  login: (uuid: string) => void;
  logout: () => void;
  setUserState: (state: UserStateResponse) => void;
  setHydrated: (status: boolean) => void;

  // Maps the View Model into the exact payload the backend expects
  buildSessionPayload: (kneePain: number, energy: number) => GenerateSessionRequest | null;
}

type UserStore = UserStoreState & UserStoreActions;

export const useUserStore = create<UserStore>((set, get) => ({
  userId: null,
  stateDocument: null,
  isHydrated: false,

  login: (uuid) => set({ userId: uuid }),
  logout: () => set({ userId: null, stateDocument: null, isHydrated: false }),
  setUserState: (state) => set({ stateDocument: state }),
  setHydrated: (status) => set({ isHydrated: status }),

  buildSessionPayload: (kneePain, energy) => {
    const { stateDocument } = get();
    if (!stateDocument) return null;

    // Extract just the datetimes for the engine.
    // We map keys as strings here to satisfy the backend dictionary.
    const last_trained = Object.entries(stateDocument.patterns).reduce(
      (acc, [pattern, data]) => ({
        ...acc,
        [pattern]: data.last_trained_datetime,
      }),
      {} as Record<string, string | null>
    );

    return {
      knee_pain: kneePain,
      energy: energy,
      last_trained,
      conditioning_levels: stateDocument.conditioning_levels,
    };
  },
}));
