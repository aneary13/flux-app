import { create } from 'zustand';
import { 
  GeneratedSessionResponse, 
  ConditioningProtocol,
} from '../types/api';

export interface LoggedSet {
  weight?: number;
  reps?: number;
  seconds?: number;
  avg_watts?: number;
  peak_watts?: number;
  avg_hr?: number;
  peak_hr?: number;
  completed?: boolean;
  is_warmup?: boolean;
  rpe?: number;
}

interface SessionState {
  readiness: { knee_pain: number; energy: number; } | null;
  sessionData: GeneratedSessionResponse | null;
  sessionId: string | null;
  loggedSets: Record<string, LoggedSet[]>;
  exerciseNotes: Record<string, string>;
  summaryNotes: string;
  completedConditioningProtocol?: ConditioningProtocol; 
  sessionStartTime: number | null; 
  blockDurations: Record<string, number>; // Maps Block Type to milliseconds
}

interface SessionActions {
  setReadiness: (knee_pain: number, energy: number) => void;
  setSessionData: (data: GeneratedSessionResponse) => void;
  startSession: (sessionId: string) => void;
  logSet: (exerciseId: string, setIndex: number, setData: LoggedSet) => void;
  setExerciseNote: (exerciseId: string, note: string) => void;
  setSummaryNote: (note: string) => void;
  setCompletedConditioning: (protocol: ConditioningProtocol) => void;
  addBlockTime: (blockType: string, timeMs: number) => void; 
  clearSession: () => void;
}

type SessionStore = SessionState & SessionActions;

export const useSessionStore = create<SessionStore>((set) => ({
  readiness: null,
  sessionData: null,
  sessionId: null,
  loggedSets: {},
  exerciseNotes: {},
  summaryNotes: '',
  completedConditioningProtocol: undefined,
  
  // Initialize Timers
  sessionStartTime: null, 
  blockDurations: {},

  setReadiness: (knee_pain, energy) => set({ readiness: { knee_pain, energy } }),
  setSessionData: (data) => set({ sessionData: data }),
  
  startSession: (id) => 
    set({ 
      sessionId: id, 
      sessionStartTime: Date.now(), // Start the master clock
      blockDurations: {} // Reset block clocks
    }), 

  logSet: (exerciseId, setIndex, setData) => 
    set((state) => {
      const currentSets = state.loggedSets[exerciseId] || [];
      const updatedSets = [...currentSets];
      updatedSets[setIndex] = { ...updatedSets[setIndex], ...setData };
      return { loggedSets: { ...state.loggedSets, [exerciseId]: updatedSets } };
    }),

  setExerciseNote: (exerciseId, note) =>
    set((state) => ({ exerciseNotes: { ...state.exerciseNotes, [exerciseId]: note } })),
  setSummaryNote: (note) => set({ summaryNotes: note }),
  setCompletedConditioning: (protocol) => set({ completedConditioningProtocol: protocol }),

  // Accumulate time for the specific block
  addBlockTime: (blockType, timeMs) =>
    set((state) => ({
      blockDurations: {
        ...state.blockDurations,
        [blockType]: (state.blockDurations[blockType] || 0) + timeMs
      }
    })),

  clearSession: () => 
    set({
      readiness: null,
      sessionData: null,
      sessionId: null,
      loggedSets: {},
      exerciseNotes: {},
      summaryNotes: '',
      completedConditioningProtocol: undefined,
      sessionStartTime: null,
      blockDurations: {},
    }),
}));
