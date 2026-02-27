import { create } from 'zustand';
import { UserState, GenerateSessionRequest, MovementPattern } from '../types/api';

interface UserStoreState {
  userId: string | null;
  stateDocument: UserState | null;
  isHydrated: boolean;
}

interface UserStoreActions {
  login: (uuid: string) => void;
  logout: () => void;
  setUserState: (state: UserState) => void;
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

    // Extract just the datetimes for the engine
    const last_trained = Object.entries(stateDocument.patterns).reduce(
      (acc, [pattern, data]) => ({
        ...acc,
        [pattern]: data.last_trained_datetime,
      }),
      {} as Record<MovementPattern, string | null>
    );

    return {
      knee_pain: kneePain,
      energy: energy,
      last_trained,
      conditioning_levels: stateDocument.conditioning_levels,
    };
  },
}));
