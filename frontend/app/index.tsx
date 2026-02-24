// app/(tabs)/index.tsx
import React, { useEffect } from 'react';
import { View, StyleSheet, ActivityIndicator, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';

// State & Services
import { useUserStore } from '../store/useUserStore';
import { FluxAPI } from '../services/api';

// Core UI Components
import { Typography } from '../components/core/Typography';
import { Card } from '../components/core/Card';
import { Button } from '../components/core/Button';
import { theme } from '../theme';

export default function HomeDashboard() {
  const router = useRouter();
  
  // Pull what we need from our Zustand store
  const { stateDocument, isHydrated, setUserState, setHydrated } = useUserStore();

  // Hydrate the "State Document" on load
  useEffect(() => {
    async function loadUserState() {
      if (isHydrated) return; // Don't refetch if we already have it
      
      try {
        const data = await FluxAPI.getUserState();
        setUserState(data);
        setHydrated(true);
      } catch (error) {
        console.error("Failed to fetch user state:", error);
        // In a full production app, we would set an error state here
      }
    }
    
    loadUserState();
  }, [isHydrated, setUserState, setHydrated]);

  // Show a loading spinner if the API hasn't returned the state yet
  if (!isHydrated || !stateDocument) {
    return (
      <View style={[styles.container, styles.centered]}>
        <ActivityIndicator size="large" color={theme.colors.actionPrimary} />
        <Typography variant="label" style={{ marginTop: theme.spacing.md }}>
          Syncing Biological State...
        </Typography>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* --- Header --- */}
      <View style={styles.header}>
        <Typography variant="h1">FLUX</Typography>
        <Typography variant="body" color={theme.colors.textMuted}>
          Your biological training engine.
        </Typography>
      </View>

      {/* --- Pattern Debts Card --- */}
      <Card style={styles.cardSpacing}>
        <Typography variant="h3" style={styles.cardTitle}>Pattern Debts</Typography>
        <Typography variant="caption" style={styles.cardSubtitle}>
          The engine prioritizes patterns with the highest debt.
        </Typography>
        
        <View style={styles.row}>
          {Object.entries(stateDocument.pattern_debts).map(([pattern, debt]) => (
            <View key={pattern} style={styles.statBox}>
              <Typography variant="h2">{debt}</Typography>
              <Typography variant="label">{pattern}</Typography>
            </View>
          ))}
        </View>
      </Card>

      {/* --- Conditioning Levels Card --- */}
      <Card style={styles.cardSpacing}>
        <Typography variant="h3" style={styles.cardTitle}>Conditioning Levels</Typography>
        <Typography variant="caption" style={styles.cardSubtitle}>
          Linear progression for metabolic protocols.
        </Typography>
        
        <View style={styles.row}>
          {Object.entries(stateDocument.conditioning_levels).map(([protocol, level]) => (
            <View key={protocol} style={styles.statBox}>
              <Typography variant="h2">Lvl {level}</Typography>
              <Typography variant="label">{protocol}</Typography>
            </View>
          ))}
        </View>
      </Card>

      {/* --- The Action Button --- */}
      <View style={styles.footer}>
        <Button 
          title="Start Check-In" 
          onPress={() => router.push('/(session)/check-in')} // Navigates to the session flow
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.background, // F6F5F2
    padding: theme.spacing.xl,
    paddingTop: 80, // Safe area top offset
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    marginBottom: theme.spacing.xxxl,
  },
  cardSpacing: {
    marginBottom: theme.spacing.lg,
  },
  cardTitle: {
    marginBottom: theme.spacing.xs,
  },
  cardSubtitle: {
    marginBottom: theme.spacing.lg,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statBox: {
    alignItems: 'center',
  },
  footer: {
    marginTop: theme.spacing.xxl,
    marginBottom: theme.spacing.xl,
  }
});
