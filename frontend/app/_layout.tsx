// app/_layout.tsx
import { Stack } from 'expo-router';

export default function RootLayout() {
  return (
    // This tells Expo Router to render child routes normally
    <Stack screenOptions={{ headerShown: false }} />
  );
}
