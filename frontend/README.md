# FLUX Frontend

React Native application built with Expo, TypeScript, Expo Router, NativeWind v4, TanStack Query, and Axios.

## Prerequisites

- Node.js 18+ and npm/yarn
- Expo CLI (install globally: `npm install -g expo-cli` or use `npx`)
- Backend API running on `http://localhost:8000`

## Installation

1. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

2. Start the development server:
   ```bash
   npm start
   # or
   yarn start
   ```

3. Run on iOS simulator:
   ```bash
   npm run ios
   ```

4. Run on Android emulator:
   ```bash
   npm run android
   ```

## Project Structure

```
frontend/
├── app/                 # Expo Router file-based routes
│   ├── _layout.tsx     # Root layout with providers
│   ├── index.tsx       # Home screen
│   └── check-in.tsx    # Check-in screen
├── src/
│   └── api/
│       └── client.ts   # Axios instance & QueryClient setup
├── global.css          # Tailwind CSS directives
├── tailwind.config.js  # Tailwind configuration
├── metro.config.js     # Metro bundler config with NativeWind
└── babel.config.js     # Babel config with NativeWind plugin
```

## Configuration

### API Client

The API client is configured in `src/api/client.ts`:
- **iOS Simulator**: Uses `http://localhost:8000`
- **Android Emulator**: Uses `http://10.0.2.2:8000` (Android emulator's localhost alias)

### NativeWind v4

- Metro config is wrapped with `withNativeWind()` from `nativewind/metro`
- Global CSS is imported in `app/_layout.tsx`
- Tailwind classes can be used directly in JSX with the `className` prop

### TanStack Query

- QueryClient is configured with sensible defaults
- Wrapped in `QueryProvider` in the root layout
- Use `useQuery` hook for data fetching

## Features

- ✅ Expo Router file-based routing
- ✅ NativeWind v4 for styling (Tailwind CSS)
- ✅ TanStack Query for data fetching
- ✅ Axios for HTTP requests
- ✅ Platform-aware API base URL
- ✅ TypeScript support
