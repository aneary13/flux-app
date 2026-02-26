import React, { useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import Slider from '@react-native-community/slider';

// State & API
import { useSessionStore } from '../../store/useSessionStore';
import { useUserStore } from '../../store/useUserStore';
import { FluxAPI } from '../../services/api';

// Core UI Components
import { Typography } from '../../components/core/Typography';
import { Card } from '../../components/core/Card';
import { Button } from '../../components/core/Button';
import { theme } from '../../theme';

export default function CheckInScreen() {
  const router = useRouter();
  
  // Zustand Stores
  const { stateDocument } = useUserStore();
  const { setReadiness, setSessionData } = useSessionStore();

  // Local UI State (1-10 Scale)
  const [kneePain, setKneePain] = useState<number>(2);
  const [energy, setEnergy] = useState<number>(7);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  // The Generation Loop
  const handleBuildSession = async () => {
    if (!stateDocument) return;

    setIsGenerating(true);
    try {
      // 1. Save local state
      setReadiness(kneePain, energy);

      // 2. Build the exact JSON payload the FastAPI engine expects
      const payload = {
        knee_pain: kneePain,
        energy: energy,
        pattern_debts: stateDocument.pattern_debts,
        conditioning_levels: stateDocument.conditioning_levels,
      };

      // 3. Hit the generation loop
      const generatedSession = await FluxAPI.generateSession(payload);
      
      // 4. Store the resulting workout blocks in Zustand
      setSessionData(generatedSession);
      
      // 5. Navigate to the Plan preview
      router.push('/(session)/plan');
    } catch (error) {
      console.error("Failed to generate session:", error);
      // In production, we'd trigger a toast or alert here
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* --- Header --- */}
      <View style={styles.header}>
        <Typography variant="h1">Check In</Typography>
      </View>

      {/* --- Knee Pain Card --- */}
      <Card style={styles.cardSpacing}>
        <View style={styles.cardHeader}>
          <Typography variant="h3">Knee Pain</Typography>
          <Typography variant="h1">{kneePain}</Typography>
        </View>
        
        <Slider
          style={styles.slider}
          minimumValue={1}
          maximumValue={10}
          step={1}
          value={kneePain}
          onValueChange={setKneePain}
          minimumTrackTintColor={theme.colors.stateGreen} // Sage
          maximumTrackTintColor={theme.colors.borderLight}
          thumbTintColor={theme.colors.actionPrimary} // Dark Charcoal
        />
        
        <View style={styles.sliderLabels}>
          <Typography variant="caption">None</Typography>
          <Typography variant="caption">Severe</Typography>
        </View>
      </Card>

      {/* --- Energy Level Card --- */}
      <Card style={styles.cardSpacing}>
        <View style={styles.cardHeader}>
          <Typography variant="h3">Energy Level</Typography>
          <Typography variant="h1">{energy}</Typography>
        </View>
        
        <Slider
          style={styles.slider}
          minimumValue={1}
          maximumValue={10}
          step={1}
          value={energy}
          onValueChange={setEnergy}
          minimumTrackTintColor={theme.colors.stateGreen}
          maximumTrackTintColor={theme.colors.borderLight}
          thumbTintColor={theme.colors.actionPrimary}
        />
        
        <View style={styles.sliderLabels}>
          <Typography variant="caption">Exhausted</Typography>
          <Typography variant="caption">Peak</Typography>
        </View>
      </Card>

      {/* --- Info Card --- */}
      <Card style={[styles.cardSpacing, styles.infoCard]} noShadow>
        <Typography variant="body" color={theme.colors.textPrimary}>
          This data is used to tailor today's session to your current state.
        </Typography>
      </Card>

      {/* --- Action --- */}
      <View style={styles.footer}>
        <Button 
          title="Build Session" 
          onPress={handleBuildSession} 
          loading={isGenerating}
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
    paddingTop: 80, // Accounts for the missing back button header for now
  },
  header: {
    marginBottom: theme.spacing.xxxl,
  },
  cardSpacing: {
    marginBottom: theme.spacing.xl,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  sliderLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: theme.spacing.xs,
  },
  infoCard: {
    backgroundColor: '#EBEBEB', // Slightly darker grey for the info card as seen in the design
    marginTop: theme.spacing.md,
  },
  footer: {
    marginTop: 'auto', // Pushes button to the bottom if the screen is tall
    paddingTop: theme.spacing.xl,
    marginBottom: theme.spacing.xl,
  }
});
