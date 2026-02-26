// services/api.ts
import {
    GenerateSessionRequest,
    GeneratedSessionResponse,
    StartSessionRequest,
    CompleteSessionRequest,
    UserState,
  } from '../types/api';
  
  const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';
  
  /**
   * Generic fetch wrapper to enforce JSON headers and standard error handling.
   */
  async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;
    
    const headers = {
      'Content-Type': 'application/json',
      // In the future, we will inject our Auth token / Test UUID here
      // 'X-User-ID': useUserStore.getState().userId, 
      ...options.headers,
    };
  
    const response = await fetch(url, { ...options, headers });
  
    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`API Error [${response.status}]: ${errorBody}`);
    }
  
    return response.json();
  }
  
  export const FluxAPI = {
    // --- A. System Initialization ---
    
    getBootstrap: () => 
      fetchApi<any>('/bootstrap'), // Caches global configs & exercise catalog
  
    getUserState: () => 
      fetchApi<UserState>('/user/state'), // Retrieves current State Document
  
    // --- B. The Generation Loop ---
  
    generateSession: (payload: GenerateSessionRequest) => 
      fetchApi<GeneratedSessionResponse>('/sessions/generate', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  
    // --- C. Session Execution ---
  
    startSession: (payload: StartSessionRequest) => 
      fetchApi<{ session_id: string }>('/sessions/start', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  
      logSet: (sessionId: string, exerciseName: string, setIndex: number, payload: any) => 
        fetchApi<void>(`/sessions/${sessionId}/sets`, {
          method: 'POST',
          body: JSON.stringify({
            exercise_name: exerciseName,
            set_index: setIndex,
            ...payload
          }), 
        }),
  
      completeSession: (sessionId: string, payload: {
        exercise_notes?: Record<string, string>;
        summary_notes?: string | null;
        anchor_pattern?: string | null;
        completed_conditioning_protocol?: string | null;
      }) => 
        fetchApi<void>(`/sessions/${sessionId}/complete`, {
          method: 'POST',
          body: JSON.stringify(payload),
        }),
  };
