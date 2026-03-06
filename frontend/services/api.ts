import {
  GenerateSessionRequest,
  GeneratedSessionResponse,
  StartSessionRequest,
  CompleteSessionRequest,
  UserStateResponse,
  LoggedSet,
  LogSetRequest,
  GeneratedExercise,
} from '../types/domain';

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
    // Providing clear error context for the Elite Product Engineer
    throw new Error(`API Error [${response.status}]: ${errorBody}`);
  }

  // Handle empty responses or 200/201 responses that return confirmation strings
  if (response.status === 204 || response.headers.get('content-length') === '0') {
    return {} as T;
  }

  return response.json();
}

/**
 * The FluxAPI object serves as the single source of truth for backend communication.
 * It strictly adheres to the auto-generated api.d.ts contracts.
 */
export const FluxAPI = {
  // --- A. System Initialization ---

  /** Retrieves the global exercise catalog and system configs */
  getBootstrap: () =>
    fetchApi<{ exercises: GeneratedExercise[]; configs: Record<string, unknown> }>('/bootstrap'),

  /** Retrieves the current user biological State Document formatted as a View Model */
  getUserState: () => fetchApi<UserStateResponse>('/user/state'),

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

  /** * Logs an individual set atomically.
   * Maps local LoggedSet to the backend LogSetRequest schema.
   */
  logSet: (sessionId: string, exerciseName: string, setIndex: number, payload: LoggedSet) => {
    const requestBody: LogSetRequest = {
      exercise_name: exerciseName,
      set_index: setIndex,
      weight: payload.weight,
      reps: payload.reps,
      seconds: payload.seconds,
      is_warmup: payload.is_warmup ?? false,
      is_benchmark: payload.is_benchmark ?? false,
      metadata: {
        ...payload.metadata,
        rpe: payload.rpe,
        avg_watts: payload.avg_watts,
        peak_watts: payload.peak_watts,
        avg_hr: payload.avg_hr,
        peak_hr: payload.peak_hr,
      },
    };

    return fetchApi<{ message: string }>(`/sessions/${sessionId}/sets`, {
      method: 'POST',
      body: JSON.stringify(requestBody),
    });
  },

  /** Finalizes the session and updates the user's permanent state */
  completeSession: (sessionId: string, payload: CompleteSessionRequest) =>
    fetchApi<{ message: string }>(`/sessions/${sessionId}/complete`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
