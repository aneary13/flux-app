import axios from 'axios';
import { Platform } from 'react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Crypto from 'expo-crypto';

// TypeScript interfaces for API responses
export interface SessionPlan {
  archetype: string;
  session_name: string;
  exercises: string[];
  priority_score: number;
}

export interface ReadinessCheckInResponse {
  state: 'RED' | 'ORANGE' | 'GREEN';
}

// Determine base URL based on platform
// Android emulator uses 10.0.2.2 to access localhost
// iOS simulator uses localhost directly
const baseURL =
  Platform.OS === 'android'
    ? 'http://10.0.2.2:8000'
    : 'http://localhost:8000';

// User ID management
const USER_ID_STORAGE_KEY = 'user_id';

async function getOrCreateUserId(): Promise<string> {
  try {
    // Check if user ID exists in storage
    const storedUserId = await AsyncStorage.getItem(USER_ID_STORAGE_KEY);
    if (storedUserId) {
      return storedUserId;
    }

    // Generate new UUID if not found
    const newUserId = Crypto.randomUUID();
    await AsyncStorage.setItem(USER_ID_STORAGE_KEY, newUserId);
    return newUserId;
  } catch (error) {
    // Fallback: generate a new UUID if storage fails
    console.error('Error managing user ID:', error);
    return Crypto.randomUUID();
  }
}

// Create axios instance with base URL
export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Add request interceptor to inject X-User-Id header
apiClient.interceptors.request.use(
  async (config) => {
    const userId = await getOrCreateUserId();
    config.headers['X-User-Id'] = userId;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Create QueryClient with default options
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 10, // 10 minutes (formerly cacheTime)
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

// QueryClientProvider wrapper component
export function QueryProvider({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
