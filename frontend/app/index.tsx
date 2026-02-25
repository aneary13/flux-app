import React, { useCallback, useState, useMemo } from 'react';
import { View, StyleSheet, ActivityIndicator, ScrollView } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';

// State & Services
import { useUserStore } from '../store/useUserStore';
import { FluxAPI } from '../services/api';

// Core UI Components
import { Typography } from '../components/core/Typography';
import { Card } from '../components/core/Card';
import { Button } from '../components/core/Button';
import { theme } from '../theme';

// --- HYBRID UI HELPERS ---

const getReadinessVisuals = (debt: number) => {
  if (debt === 0) return { color: theme.colors.stateRed, width: '30%', label: 'Fatigued' }; 
  if (debt === 1) return { color: theme.colors.stateOrange, width: '60%', label: 'Recovering' };
  return { color: theme.colors.stateGreen, width: '100%', label: 'Fully Primed' };
};

const generateDynamicGreeting = (debts: Record<string, number>) => {
  const maxDebt = Math.max(...Object.values(debts));
  const primedPatterns = Object.entries(debts)
    .filter(([_, value]) => value === maxDebt)
    .map(([pattern]) => pattern);

  if (maxDebt === 0) {
    return {
      headline: "Engine Cooling.",
      sub: "You've trained every pattern recently. Time to recover or focus on conditioning."
    };
  }

  const patternString = primedPatterns.join(' and ');
  
  return {
    headline: `Your ${patternString} is fully primed`,
    sub: `It's been ${maxDebt} session${maxDebt > 1 ? 's' : ''} since you trained ${primedPatterns.length > 1 ? 'these patterns' : 'this pattern'}`
  };
};

// Map backend acronyms to premium frontend labels
const PROTOCOL_NAMES: Record<string, string> = {
  'HIIT': 'High Intensity Interval Training',
  'SIT': 'Sprint Interval Training',
};

export default function HomeDashboard() {
  const router = useRouter();
  const { stateDocument, setUserState } = useUserStore();
  const [isInitialLoad, setIsInitialLoad] = useState(!stateDocument); 

  useFocusEffect(
    useCallback(() => {
      let isActive = true;
      async function loadUserState() {
        try {
          const data = await FluxAPI.getUserState();
          if (isActive) {
            setUserState(data);
            setIsInitialLoad(false);
          }
        } catch (error) {
          console.error("Failed to fetch user state:", error);
          if (isActive) setIsInitialLoad(false);
        }
      }
      loadUserState();
      return () => { isActive = false; };
    }, [setUserState])
  );

  const greeting = useMemo(() => {
    if (!stateDocument) return { headline: '', sub: '' };
    return generateDynamicGreeting(stateDocument.pattern_debts);
  }, [stateDocument]);


  if (isInitialLoad && !stateDocument) {
    return (
      <View style={[styles.container, styles.centered]}>
        <ActivityIndicator size="large" color={theme.colors.actionPrimary} />
        <Typography variant="label" style={{ marginTop: theme.spacing.md }}>
          Syncing Biological State...
        </Typography>
      </View>
    );
  }

  if (!stateDocument) return null;

  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      
      {/* --- Header & Dynamic Greeting --- */}
      <View style={styles.header}>
        <Typography variant="h1" style={styles.brandTitle}>FLUX</Typography>
        <Typography variant="h2" style={styles.dynamicHeadline}>
          {greeting.headline}
        </Typography>
        <Typography variant="body" color={theme.colors.textMuted} style={styles.dynamicSub}>
          {greeting.sub}
        </Typography>
      </View>

      {/* --- Readiness Bars --- */}
      <Card style={styles.cardSpacing} padding={theme.spacing.lg}>
        <View style={styles.cardHeader}>
          <Typography variant="h3">Movement Readiness</Typography>
        </View>
        
        <View style={styles.readinessList}>
          {Object.entries(stateDocument.pattern_debts).map(([pattern, debt]) => {
            const visual = getReadinessVisuals(debt as number);
            return (
              <View key={pattern} style={styles.readinessRow}>
                <View style={styles.readinessLabels}>
                  <Typography variant="label" style={styles.patternName}>{pattern}</Typography>
                  <Typography variant="caption" color={theme.colors.textMuted}>{visual.label}</Typography>
                </View>
                
                <View style={styles.barTrack}>
                  <View style={[
                    styles.barFill, 
                    { width: visual.width as any, backgroundColor: visual.color }
                  ]} />
                </View>
              </View>
            );
          })}
        </View>
      </Card>

      {/* --- Engine Capacity (Stacked Protocols) --- */}
      <Card style={styles.cardSpacing} padding={theme.spacing.lg}>
        <View style={styles.cardHeader}>
          <Typography variant="h3">Engine Capacity</Typography>
          <Typography variant="caption" color={theme.colors.textMuted}>
            Current protocol stages
          </Typography>
        </View>
        
        <View style={styles.protocolList}>
          {Object.entries(stateDocument.conditioning_levels)
            .filter(([protocol]) => protocol !== 'SS') // Hide Steady State
            .map(([protocol, level]) => {
              const fullName = PROTOCOL_NAMES[protocol] || protocol; // Fallback to acronym if not found

              return (
                <View key={protocol} style={styles.engineRow}>
                  <Typography variant="label" style={styles.protocolName}>{fullName}</Typography>
                  <View style={styles.pillBadge}>
                    <Typography variant="caption" style={styles.pillLevel}>Level {level as number}</Typography>
                  </View>
                </View>
              );
          })}
        </View>
      </Card>

      {/* --- Massive Action Button --- */}
      <View style={styles.footer}>
        <Button 
          title="Check-In & Generate Session" 
          onPress={() => router.push('/(session)/check-in')} 
        />
      </View>
      
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: theme.colors.background, 
    paddingHorizontal: theme.spacing.xl,
    paddingTop: 80,
    paddingBottom: 40,
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    marginBottom: theme.spacing.xxxl,
  },
  brandTitle: {
    fontSize: 14,
    letterSpacing: 2,
    color: theme.colors.textMuted,
    marginBottom: theme.spacing.lg,
  },
  dynamicHeadline: {
    marginBottom: theme.spacing.sm,
    color: theme.colors.textPrimary,
  },
  dynamicSub: {
    lineHeight: 22,
  },
  cardSpacing: {
    marginBottom: theme.spacing.xl,
  },
  cardHeader: {
    marginBottom: theme.spacing.lg,
  },
  
  // Readiness Bars Styles
  readinessList: {
    gap: theme.spacing.md,
  },
  readinessRow: {
    marginBottom: theme.spacing.xs,
  },
  readinessLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    marginBottom: theme.spacing.xs,
  },
  patternName: {
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  barTrack: {
    height: 12,
    backgroundColor: '#EBEBEB',
    borderRadius: theme.radii.pill,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: theme.radii.pill,
  },

  // Engine Capacity Styles
  protocolList: {
    gap: theme.spacing.sm, // Vertical spacing between rows
  },
  engineRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between', // Pushes the text to the left and badge to the right
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.borderLight,
    borderRadius: theme.radii.pill,
    paddingLeft: 16,
    paddingRight: 6,
    paddingVertical: 6,
  },
  protocolName: {
    fontWeight: '600',
  },
  pillBadge: {
    backgroundColor: '#F0F0F0',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: theme.radii.pill,
  },
  pillLevel: {
    fontWeight: 'bold',
    color: theme.colors.textPrimary,
  },

  footer: {
    marginTop: 'auto', 
    paddingTop: theme.spacing.xxl,
  }
});
