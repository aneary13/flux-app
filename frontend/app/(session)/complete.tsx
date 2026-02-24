import React, { useState, useMemo } from 'react';
import { View, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { useSessionStore } from '../../store/useSessionStore';
import { FluxAPI } from '../../services/api';
import { Typography } from '../../components/core/Typography';
import { Button } from '../../components/core/Button';
import { Card } from '../../components/core/Card';
import { theme } from '../../theme';

// Helper to convert milliseconds to clean "Xm" strings
const formatTime = (ms: number | undefined) => {
  if (!ms) return "< 1m";
  const minutes = Math.round(ms / 60000);
  return minutes > 0 ? `${minutes}m` : "< 1m";
};

export default function CompleteSessionScreen() {
  const router = useRouter();
  const { sessionId, sessionData, loggedSets, clearSession, sessionStartTime, blockDurations } = useSessionStore();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // --- Calculate Summary Stats & Total Time ---
  const totalTimeMs = sessionStartTime ? Date.now() - sessionStartTime : 0;
  
  const { totalSets, completedExercises } = useMemo(() => {
    let setsCount = 0;
    let exercisesCount = 0;

    Object.values(loggedSets).forEach((setsArray) => {
      const completedSetsForExercise = setsArray.filter(set => set && set.completed).length;
      if (completedSetsForExercise > 0) {
        setsCount += completedSetsForExercise;
        exercisesCount += 1; // Only count the exercise if they did at least 1 set
      }
    });

    return { totalSets: setsCount, completedExercises: exercisesCount };
  }, [loggedSets]);

  const handleFinishSession = async () => {
    if (!sessionId) {
      clearSession();
      router.replace('/');
      return;
    }
    setIsSubmitting(true);
    try {
      await FluxAPI.completeSession(sessionId, { notes: "" });
      clearSession();
      router.replace('/'); 
    } catch (error) {
      console.error("Failed to complete session:", error);
      setIsSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        
        {/* Header */}
        <View style={styles.headerContainer}>
          <View style={styles.iconCircle}>
            <Ionicons name="checkmark" size={32} color={theme.colors.surface} />
          </View>
          <Typography variant="h1" style={styles.title}>Session Complete</Typography>
        </View>

        {/* Block Summary Cards */}
        {sessionData?.blocks.map((block, index) => {
          
          const checklistExercises = block.exercises.filter(ex => ex.tracking_unit === 'CHECKLIST');
          const standardExercises = block.exercises.filter(ex => ex.tracking_unit !== 'CHECKLIST');

          return (
            <Card key={block.id || `block-${index}`} style={styles.blockCard} padding={theme.spacing.lg}>
              
              {/* Block Header */}
              <View style={styles.blockHeader}>
                <View style={styles.blockHeaderLeft}>
                  <View style={styles.blockPill}>
                    <Typography variant="label" style={styles.blockPillText}>{block.type}</Typography>
                  </View>
                  {/* Dynamic Block Time! */}
                  <Typography variant="body" color={theme.colors.textMuted}>
                    {formatTime(blockDurations[block.type])}
                  </Typography>
                </View>
                <Ionicons name="checkmark-circle-outline" size={24} color={theme.colors.stateGreen} />
              </View>

              {/* Exercises List */}
              <View style={styles.exerciseList}>
                
                {/* 1. Visually Grouped Checklist Row */}
                {checklistExercises.length > 0 && (() => {
                  const title = block.type === 'PREP' ? 'Mobility & Activation' : block.type === 'POWER' ? 'Plyometrics' : 'Checklist';
                  
                  // Tally up completed checklist items
                  let completedChecklists = 0;
                  checklistExercises.forEach(ex => {
                     const exId = ex.id || ex.name;
                     if (loggedSets[exId]?.[0]?.completed) completedChecklists++;
                  });
                  
                  const totalChecklists = checklistExercises.length;
                  const isAllDone = completedChecklists === totalChecklists;
                  const statusText = isAllDone ? 'Completed' : `${completedChecklists}/${totalChecklists} done`;

                  return (
                    <View style={styles.exerciseRow}>
                      <Typography variant="body" style={styles.exerciseName}>{title}</Typography>
                      <Typography variant="body" color={theme.colors.textMuted}>{statusText}</Typography>
                    </View>
                  );
                })()}

                {/* 2. Standard Exercises */}
                {standardExercises.map((exercise, exIndex) => {
                  const exerciseId = exercise.id || exercise.name;
                  const setsLogged = loggedSets[exerciseId]?.filter(s => s && s.completed).length || 0;

                  return (
                    <View key={exerciseId || `ex-${exIndex}`} style={styles.exerciseRow}>
                      <Typography variant="body" style={styles.exerciseName}>{exercise.name}</Typography>
                      {/* Fixed Pluralization! */}
                      <Typography variant="body" color={theme.colors.textMuted}>
                        {setsLogged === 1 ? '1 set' : `${setsLogged} sets`}
                      </Typography>
                    </View>
                  );
                })}
              </View>

            </Card>
          );
        })}
      </ScrollView>

      {/* Footer Container */}
      <View style={styles.footerContainer}>
        <View style={styles.statsRow}>
          <View style={styles.statColumn}>
            {/* Dynamic Total Time! */}
            <Typography variant="h2">{formatTime(totalTimeMs)}</Typography>
            <Typography variant="caption" color={theme.colors.textMuted}>Total Time</Typography>
          </View>
          <View style={styles.statColumn}>
            <Typography variant="h2">{totalSets}</Typography>
            <Typography variant="caption" color={theme.colors.textMuted}>Total Sets</Typography>
          </View>
          <View style={styles.statColumn}>
            <Typography variant="h2">{completedExercises}</Typography>
            <Typography variant="caption" color={theme.colors.textMuted}>Exercises</Typography>
          </View>
        </View>

        {isSubmitting ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.colors.actionPrimary} />
          </View>
        ) : (
          <Button title="Back to Home" onPress={handleFinishSession} style={styles.homeButton} />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background, // F6F5F2
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: theme.spacing.xl,
    paddingTop: 80,
    paddingBottom: 40, // Extra padding so it doesn't collide with the footer
  },
  
  // Header
  headerContainer: {
    alignItems: 'center',
    marginBottom: theme.spacing.xl,
  },
  iconCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#8FA08A', // A muted sage green matching your mockup
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  title: {
    textAlign: 'center',
  },

  // Block Cards
  blockCard: {
    marginBottom: theme.spacing.md,
  },
  blockHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  blockHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
  },
  blockPill: {
    backgroundColor: theme.colors.actionPrimary, // Dark grey/black
    paddingVertical: 4,
    paddingHorizontal: 12,
    borderRadius: theme.radii.pill,
  },
  blockPillText: {
    color: theme.colors.surface,
    fontWeight: 'bold',
    fontSize: 12,
    letterSpacing: 0.5,
  },
  exerciseList: {
    gap: theme.spacing.sm,
  },
  exerciseRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  exerciseName: {
    color: theme.colors.textPrimary,
  },

  // Footer / Stats Area
  footerContainer: {
    backgroundColor: '#EBEBEB', // Slightly darker than background for contrast
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: theme.spacing.xl,
    paddingTop: theme.spacing.xl,
    paddingBottom: 40, // Safe area bottom
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.xl,
    paddingHorizontal: theme.spacing.md,
  },
  statColumn: {
    alignItems: 'center',
  },
  homeButton: {
    height: 56,
  },
  loadingContainer: {
    height: 56,
    justifyContent: 'center',
    alignItems: 'center',
  }
});
