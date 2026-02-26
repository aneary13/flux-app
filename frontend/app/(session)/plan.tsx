import React, { useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';

// State & API
import { useSessionStore } from '../../store/useSessionStore';
import { FluxAPI } from '../../services/api';

// Core UI Components
import { Typography } from '../../components/core/Typography';
import { Card } from '../../components/core/Card';
import { Button } from '../../components/core/Button';
import { Pill } from '../../components/core/Pill';
import { theme } from '../../theme';

export default function PlanScreen() {
  const router = useRouter();
  const { sessionData, readiness, startSession } = useSessionStore();
  const [isStarting, setIsStarting] = useState(false);

  if (!sessionData || !readiness) {
    return (
      <View style={styles.center}>
        <Typography>No active session found.</Typography>
      </View>
    );
  }

  // --- State Mapping Logic ---
  const sessionState = sessionData.metadata.state; // "GREEN", "ORANGE", or "RED"

  const stateConfig = {
    GREEN: {
      text: "Full Intensity Training",
      color: theme.colors.stateGreen,
    },
    ORANGE: {
      text: "Modified Training",
      color: theme.colors.stateOrange || '#E9C46A', // Fallback if theme not updated
    },
    RED: {
      text: "Rehab and Recovery",
      color: theme.colors.stateRed,
    },
  };

  const currentConfig = stateConfig[sessionState as keyof typeof stateConfig] || stateConfig.GREEN;
  const archetypeText = currentConfig.text;
  const archetypeColor = currentConfig.color;

  const handleStartWorkout = async () => {
    setIsStarting(true);
    try {
      const response = await FluxAPI.startSession({ readiness });
      startSession(response.session_id);
      router.push('/(session)/active'); 
    } catch (error) {
      console.error("Failed to start session on backend:", error);
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Typography variant="h1">Today's Plan</Typography>
      </View>

      {/* Dynamic State Banner */}
      <Card style={styles.bannerCard} padding={theme.spacing.md} noShadow>
        <View style={styles.bannerContent}>
          <View style={[styles.indicatorDot, { backgroundColor: archetypeColor }]} />
          <Typography variant="h3">{archetypeText}</Typography>
        </View>
      </Card>

      {/* Workout Blocks List */}
      <View style={styles.blocksContainer}>
        {sessionData.blocks.map((block, index) => (
          <Card key={block.id || `block-${index}`} style={styles.blockCard}>
            <View style={styles.blockHeader}>
              <View style={styles.numberCircle}>
                <Typography variant="caption" style={styles.numberText}>
                  {index + 1}
                </Typography>
              </View>
              
              <View style={styles.blockTitle}>
                <Typography variant="h3">{block.type}</Typography>
                {/* Fixed: Only renders if block.name exists, no "Overview" fallback */}
                {block.label ? (
                  <Typography variant="caption">{block.label}</Typography>
                ) : null}
              </View>
            </View>

            <View style={styles.pillsContainer}>
              {block.exercises.map((ex, exIndex) => (
                <Pill key={ex.id || `ex-${index}-${exIndex}`} label={ex.name} />
              ))}
            </View>
          </Card>
        ))}
      </View>

      {/* Action Footer */}
      <View style={styles.footer}>
        <Button 
          title="Let's Go" 
          onPress={handleStartWorkout}
          loading={isStarting}
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { 
    flexGrow: 1, 
    backgroundColor: theme.colors.background, 
    padding: theme.spacing.xl, 
    paddingTop: 80 
  },
  center: { 
    flex: 1, 
    justifyContent: 'center', 
    alignItems: 'center' 
  },
  header: { 
    marginBottom: theme.spacing.xl 
  },
  bannerCard: { 
    marginBottom: theme.spacing.xl, 
    backgroundColor: '#EBEBEB' 
  },
  bannerContent: { 
    flexDirection: 'row', 
    alignItems: 'center' 
  },
  indicatorDot: { 
    width: 16, 
    height: 16, 
    borderRadius: 8, 
    marginRight: theme.spacing.md 
  },
  blocksContainer: { 
    gap: theme.spacing.md 
  },
  blockCard: { 
    marginBottom: theme.spacing.xs 
  },
  blockHeader: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    marginBottom: theme.spacing.md 
  },
  numberCircle: { 
    width: 32, 
    height: 32, 
    borderRadius: 16, 
    backgroundColor: theme.colors.actionPrimary, 
    justifyContent: 'center', 
    alignItems: 'center', 
    marginRight: theme.spacing.md 
  },
  numberText: { 
    color: theme.colors.surface, 
    fontWeight: 'bold', 
    fontSize: 14 
  },
  blockTitle: { 
    flex: 1 
  },
  pillsContainer: { 
    flexDirection: 'row', 
    flexWrap: 'wrap', 
    gap: theme.spacing.sm, 
    marginLeft: 48 
  },
  footer: { 
    marginTop: theme.spacing.xxl, 
    marginBottom: theme.spacing.xl 
  }
});
