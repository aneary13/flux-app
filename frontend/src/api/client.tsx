import axios from 'axios';
import { Platform } from 'react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';

// Determine base URL based on platform
// Android emulator uses 10.0.2.2 to access localhost
// iOS simulator uses localhost directly
const baseURL =
  Platform.OS === 'android'
    ? 'http://10.0.2.2:8000'
    : 'http://localhost:8000';

// Create axios instance with base URL
export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

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
