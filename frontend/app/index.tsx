import React, { useState, useCallback, useMemo } from 'react';
import { View, ScrollView, StyleSheet, ActivityIndicator, Text, TouchableOpacity } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useUserStore } from '../store/useUserStore';
import { FluxAPI } from '../services/api';
import { PatternReadiness } from '../types/api';
import { theme } from '../theme';

// --- HYBRID UI HELPERS ---

const getPatternColor = (statusText: string) => {
  switch (statusText) {
    case 'Fatigued': 
      return theme.colors.stateRed;
    case 'Recovering': 
      return theme.colors.stateOrange;
    case 'Fully Primed': 
    default:
      return theme.colors.stateGreen;
  }
};

const getStatusIcon = (statusText: string) => {
  switch (statusText) {
    case 'Fatigued': 
      return 'alert-circle-outline';
    case 'Recovering': 
      return 'time-outline';
    case 'Fully Primed': 
    default:
      return 'checkmark-circle-outline';
  }
};

const generateDynamicGreeting = (patterns: Record<string, PatternReadiness>) => {
  const primedPatterns = Object.entries(patterns)
    .filter(([_, data]) => data.status_text === 'Fully Primed')
    .map(([pattern]) => pattern);

  if (primedPatterns.length === 0) {
    return {
      headline: "Engine Cooling",
      subHeadlineStart: "Your movement patterns are ",
      highlightedPatterns: "recovering",
      subHeadlineEnd: ". Focus on conditioning."
    };
  }

  // Formatting "PULL, PUSH, and HINGE" beautifully for the new UI
  let highlightedPatterns = primedPatterns.join(', ');
  if (primedPatterns.length > 1) {
    const last = primedPatterns.pop();
    highlightedPatterns = `${primedPatterns.join(', ')}, and ${last}`;
  } else if (primedPatterns.length === 1) {
    highlightedPatterns = primedPatterns[0];
  }
  
  return {
    headline: "Ready to Train",
    subHeadlineStart: "Your ",
    highlightedPatterns: highlightedPatterns,
    subHeadlineEnd: ` pattern${primedPatterns.length >= 1 ? 's are' : ' is'} fully primed.`
  };
};

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
    if (!stateDocument) return null;
    return generateDynamicGreeting(stateDocument.patterns);
  }, [stateDocument]);

  const primedCount = useMemo(() => {
    if (!stateDocument) return 0;
    return Object.values(stateDocument.patterns).filter(p => p.status_text === 'Fully Primed').length;
  }, [stateDocument]);

  if (isInitialLoad || !stateDocument || !greeting) {
    return (
      <View style={[styles.container, styles.centered]}>
        <ActivityIndicator size="large" color={theme.colors.actionPrimary} />
        <Text style={styles.loadingText}>Syncing Biological State...</Text>
      </View>
    );
  }

  const totalPatterns = Object.keys(stateDocument.patterns).length;

  return (
    <View style={styles.container}>
      <ScrollView 
        contentContainerStyle={styles.scrollContent} 
        showsVerticalScrollIndicator={false}
      >
        
        {/* --- Header Section --- */}
        <View style={styles.header}>
          <Text style={styles.headline}>{greeting.headline}</Text>
          <Text style={styles.subHeadline}>
            {greeting.subHeadlineStart}
            <Text style={styles.subHeadlineHighlight}>{greeting.highlightedPatterns}</Text>
            {greeting.subHeadlineEnd}
          </Text>
        </View>

        {/* --- Movement Readiness Section --- */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Movement Readiness</Text>
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{primedCount}/{totalPatterns} Primed</Text>
            </View>
          </View>
          
          <View style={styles.cardList}>
            {Object.entries(stateDocument.patterns).map(([pattern, data]) => {
              const { status_text, days_since } = data;
              const color = getPatternColor(status_text);
              const iconName = getStatusIcon(status_text);
              const daysDisplay = days_since === null ? 'Untrained' : `${days_since} days ago`;

              return (
                <View key={pattern} style={styles.readinessCard}>
                  <View style={styles.cardLeft}>
                    <View style={[styles.pillIndicator, { backgroundColor: color }]} />
                    <View>
                      <Text style={styles.patternName}>{pattern}</Text>
                      <Text style={[styles.statusText, { color }]}>{status_text}</Text>
                    </View>
                  </View>

                  <View style={styles.cardRight}>
                    <Ionicons name={iconName} size={20} color={color} />
                    <Text style={styles.daysText}>{daysDisplay}</Text>
                  </View>
                </View>
              );
            })}
          </View>
        </View>

        {/* --- Engine Capacity Section --- */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Engine Capacity</Text>
          </View>
          
          <View style={styles.cardList}>
            {Object.entries(stateDocument.conditioning_levels)
              .filter(([protocol]) => protocol !== 'SS') // Hide Steady State
              .map(([protocol, level]) => {
                const fullName = PROTOCOL_NAMES[protocol] || protocol; 

                return (
                  <View key={protocol} style={styles.engineCard}>
                    <View style={styles.cardLeft}>
                      <View style={styles.iconCircle}>
                        <Ionicons name="pulse-outline" size={16} color={theme.colors.textPrimary} />
                      </View>
                      <Text style={styles.protocolName}>{fullName}</Text>
                    </View>
                    <View style={styles.badge}>
                      <Text style={styles.badgeText}>Level {level as number}</Text>
                    </View>
                  </View>
                );
            })}
          </View>
        </View>

        {/* Padding for sticky button */}
        <View style={{ height: 100 }} />
      </ScrollView>

      {/* --- Sticky Bottom Action Button --- */}
      <View style={styles.stickyFooter}>
        <TouchableOpacity 
          style={styles.primaryButton}
          activeOpacity={0.9}
          onPress={() => router.push('/(session)/check-in')}
        >
          <Text style={styles.buttonText}>Check-In & Generate Session</Text>
          <Ionicons name="arrow-forward" size={20} color={theme.colors.surface} />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: theme.spacing.md,
    color: theme.colors.textMuted,
    fontWeight: '500',
  },
  scrollContent: {
    paddingHorizontal: theme.spacing.lg,
    paddingTop: 80,
    paddingBottom: 40,
  },
  
  // Header
  header: {
    marginBottom: theme.spacing.xxl,
  },
  headline: {
    fontSize: 28,
    fontWeight: '800',
    color: theme.colors.textPrimary,
    letterSpacing: -0.5,
    marginBottom: theme.spacing.xs,
  },
  subHeadline: {
    fontSize: 16,
    color: theme.colors.textMuted,
    lineHeight: 24,
  },
  subHeadlineHighlight: {
    color: theme.colors.textPrimary,
    fontWeight: '600',
  },

  // Sections
  section: {
    marginBottom: theme.spacing.xxl,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
    paddingHorizontal: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    letterSpacing: -0.5,
  },
  badge: {
    backgroundColor: '#E5E5EA', // Slightly darker than background for contrast
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: theme.radii.sm,
  },
  badgeText: {
    fontSize: 13,
    fontWeight: '600',
    color: theme.colors.textPrimary,
  },

  // Cards
  cardList: {
    gap: theme.spacing.sm,
  },
  readinessCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radii.lg,
    padding: theme.spacing.lg,
    ...theme.shadows.card,
  },
  engineCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radii.md,
    padding: theme.spacing.md,
    ...theme.shadows.card,
  },
  cardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
  },
  cardRight: {
    alignItems: 'flex-end',
    gap: 4,
  },
  
  // Card Specific Internals
  pillIndicator: {
    width: 6,
    height: 48,
    borderRadius: theme.radii.pill,
  },
  patternName: {
    fontSize: 17,
    fontWeight: '700',
    color: theme.colors.textPrimary,
    letterSpacing: -0.5,
  },
  statusText: {
    fontSize: 13,
    fontWeight: '600',
    marginTop: 2,
  },
  daysText: {
    fontSize: 12,
    fontWeight: '500',
    color: theme.colors.textMuted,
  },
  iconCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: theme.colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  protocolName: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.colors.textPrimary,
  },

  // Sticky Footer Button
  stickyFooter: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: theme.spacing.xl,
    paddingBottom: 40, // Extra padding for safe area / home indicator
    backgroundColor: 'rgba(246, 245, 242, 0.95)', // theme.colors.background with opacity
  },
  primaryButton: {
    backgroundColor: theme.colors.actionPrimary,
    flexDirection: 'row',
    height: 56,
    borderRadius: theme.radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 4,
  },
  buttonText: {
    color: theme.colors.surface,
    fontSize: 16,
    fontWeight: '700',
  },
});
