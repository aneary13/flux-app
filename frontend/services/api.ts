import {
  GenerateSessionRequest,
  GeneratedSessionResponse,
  StartSessionRequest,
  CompleteSessionRequest,
  UserState,
  Exercise,
} from '../types/api';
import { LoggedSet } from '../store/useSessionStore';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper to enforce JSON headers and standard error handling.
 */
async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`API Error [${response.status}]: ${errorBody}`);
  }

  // Handle empty responses for void endpoints
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

/**
 * The FluxAPI object serves as the single source of truth for backend communication.
 * It strictly adheres to the backend_api_spec.md contracts.
 */
export const FluxAPI = {
  // --- A. System Initialization ---

  /** Retrieves the global exercise catalog and system configs */
  getBootstrap: () =>
    fetchApi<{ exercises: Exercise[]; configs: Record<string, unknown> }>('/bootstrap'),

  /** Retrieves the current user biological State Document */
  getUserState: () => fetchApi<UserState>('/user/state'),

  // --- B. The Generation Loop ---

  /** Sends biological state to generate a customized workout */
  generateSession: (payload: GenerateSessionRequest) =>
    fetchApi<GeneratedSessionResponse>('/sessions/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // --- C. Session Execution ---

  /** Initializes a session and returns a unique session_id */
  startSession: (payload: StartSessionRequest) =>
    fetchApi<{ session_id: string }>('/sessions/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  /** Logs an individual set atomically */
  logSet: (sessionId: string, exerciseName: string, setIndex: number, payload: LoggedSet) =>
    fetchApi<void>(`/sessions/${sessionId}/sets`, {
      method: 'POST',
      body: JSON.stringify({
        exercise_name: exerciseName,
        set_index: setIndex,
        ...payload,
      }),
    }),

  /** Finalizes the session and updates the user's permanent state */
  completeSession: (sessionId: string, payload: CompleteSessionRequest) =>
    fetchApi<void>(`/sessions/${sessionId}/complete`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
