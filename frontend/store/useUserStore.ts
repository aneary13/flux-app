import { create } from 'zustand';
import { UserState } from '../types/api';

interface UserStoreState {
  // Authentication
  userId: string | null; // Defaults to null, will hold our test UUID
  
  // Global Biological State
  stateDocument: UserState | null; // Holds pattern_debts and conditioning_levels
  
  // App Readiness
  isHydrated: boolean; // Useful for showing a loading spinner while fetching the initial state
}

interface UserStoreActions {
  // Auth Actions
  login: (uuid: string) => void;
  logout: () => void;
  
  // State Document Actions
  setUserState: (state: UserState) => void;
  
  // Initialization
  setHydrated: (status: boolean) => void;
}

type UserStore = UserStoreState & UserStoreActions;

export const useUserStore = create<UserStore>((set) => ({
  // Initial State
  userId: null,
  stateDocument: null,
  isHydrated: false,

  // Actions
  login: (uuid) => 
    set({ userId: uuid }),

  logout: () => 
    set({ userId: null, stateDocument: null, isHydrated: false }),

  setUserState: (state) => 
    set({ stateDocument: state }),

  setHydrated: (status) => 
    set({ isHydrated: status }),
}));
