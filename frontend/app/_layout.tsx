import '../global.css';
import { Stack } from 'expo-router';
import { QueryProvider } from '@/src/api/client';

export default function RootLayout() {
  return (
    <QueryProvider>
      <Stack>
        <Stack.Screen name="index" options={{ title: 'Home' }} />
        <Stack.Screen name="check-in" options={{ title: 'Check In' }} />
      </Stack>
    </QueryProvider>
  );
}
