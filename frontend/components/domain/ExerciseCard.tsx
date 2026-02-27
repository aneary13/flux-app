import React, { useState, useEffect } from 'react';
import { View, StyleSheet, TouchableOpacity, TextInput, Keyboard } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

// Types & State
import { Exercise } from '../../types/api';
import { useSessionStore } from '../../store/useSessionStore';
import { FluxAPI } from '../../services/api';

// Core UI
import { Typography } from '../core/Typography';
import { theme } from '../../theme';

interface SetRowProps {
  exercise: Exercise;
  setIndex: number;
  isConditioning: boolean;
}

/**
 * --- INTERNAL COMPONENT: SetRow ---
 * Handles the Active (Editing) vs Collapsed (Logged) state machine.
 */
function SetRow({ exercise, setIndex, isConditioning }: SetRowProps) {
    // Grab sessionId to make the atomic API call
    const { logSet, loggedSets, sessionId } = useSessionStore();
    
    const exerciseId = exercise.id || exercise.name;
    const currentLog = loggedSets[exerciseId]?.[setIndex] || {};
    
    const [isEditing, setIsEditing] = useState(!currentLog.completed);
  
    // Standard Inputs
    const [weightValue, setWeightValue] = useState(currentLog.weight?.toString() || '');
    const [metricValue, setMetricValue] = useState(currentLog.reps?.toString() || currentLog.seconds?.toString() || '');
    const [rpeValue, setRpeValue] = useState(currentLog.rpe?.toString() || '');
    const [isWarmup, setIsWarmup] = useState(!!currentLog.is_warmup);
  
    // Conditioning Inputs
    const [avgWatts, setAvgWatts] = useState(currentLog.avg_watts?.toString() || '');
    const [peakWatts, setPeakWatts] = useState(currentLog.peak_watts?.toString() || '');
    const [avgHr, setAvgHr] = useState(currentLog.avg_hr?.toString() || '');
    const [peakHr, setPeakHr] = useState(currentLog.peak_hr?.toString() || '');
  
    let metricLabel = 'reps';
    if (exercise.tracking_unit === 'SECS') metricLabel = 'secs';
    if (exercise.tracking_unit === 'DISTANCE') metricLabel = 'meters';
    if (exercise.is_unilateral) metricLabel += ' / side';
  
    const isBodyweight = exercise.load_type === 'BODYWEIGHT';
  
    // --- ATOMIC LOGGING TRIGGER ---
    const handleCompleteSet = async () => {
      // Base payload
      const payload: any = { 
        completed: true 
      };

      if (isConditioning) {
        payload.is_benchmark = !!exercise.is_benchmark;
        payload.is_warmup = false; 
  
        // Parse "SIT (Level 1)" into protocol and level using Regex
        let parsedProtocol = 'UNKNOWN';
        let parsedLevel = 1;
        
        if (exercise.description) {
          // Matches letters before a space, then "(Level X)"
          const match = exercise.description.match(/([A-Z]+)\s*\(Level\s*(\d+)\)/i);
          if (match) {
            parsedProtocol = match[1].toUpperCase(); // e.g., "SIT"
            parsedLevel = parseInt(match[2], 10);    // e.g., 1
          }
        }

        // Build the exact nested metadata object your backend expects
        payload.metadata = {
          protocol: parsedProtocol,
          level: parsedLevel,
          work_seconds: exercise.work_seconds,
          rest_seconds: exercise.rest_seconds,
          avg_watts: avgWatts ? parseFloat(avgWatts) : undefined,
          peak_watts: peakWatts ? parseFloat(peakWatts) : undefined,
          avg_hr: avgHr ? parseFloat(avgHr) : undefined,
          peak_hr: peakHr ? parseFloat(peakHr) : undefined,
        };
      } else {
        // Standard Lifting Payload
        payload.is_warmup = isWarmup;
        payload.rpe = rpeValue ? parseFloat(rpeValue) : undefined;
        payload.weight = weightValue ? parseFloat(weightValue) : 0;
      
        const numericMetric = metricValue ? parseFloat(metricValue) : 0;
        if (exercise.tracking_unit === 'REPS') payload.reps = numericMetric;
        if (exercise.tracking_unit === 'SECS') payload.seconds = numericMetric;
      }

      // 1. Optimistic UI Update (Save to Zustand)
      logSet(exerciseId, setIndex, payload);
      setIsEditing(false); 
      Keyboard.dismiss(); // Explicitly drop the native keyboard

      // 2. Background API Call
      if (sessionId) {
        try {
          await FluxAPI.logSet(sessionId, exercise.name, setIndex, payload);
        } catch (error) {
          console.error("Atomic logging failed:", error);
        }
      }
    };
  
    // --- RENDER COLLAPSED STATE ---
    if (!isEditing) {
      return (
        <TouchableOpacity style={styles.collapsedRow} activeOpacity={0.7} onPress={() => setIsEditing(true)}>
          <Typography variant="label" style={styles.setNumber}>Set {setIndex + 1}</Typography>
          
          <View style={styles.collapsedData}>
            {isConditioning ? (
               <Typography variant="body" style={styles.collapsedText}>
                 {avgWatts ? `${avgWatts}W avg ` : ''} 
                 {peakWatts ? `| ${peakWatts}W peak ` : ''}
                 {avgHr ? `| ${avgHr}bpm` : ''}
               </Typography>
            ) : (
               <Typography variant="body" style={styles.collapsedText}>
                 {isWarmup ? '(W) ' : ''}
                 {isBodyweight ? `BW + ${weightValue || 0}kg` : `${weightValue || 0}kg`} 
                 {' x '} 
                 {metricValue || 0} {metricLabel} 
                 {rpeValue ? ` @ RPE ${rpeValue}` : ''}
               </Typography>
            )}
          </View>
  
          <Ionicons name="checkmark-circle" size={24} color={theme.colors.stateGreen} />
        </TouchableOpacity>
      );
    }
  
    // --- RENDER ACTIVE STATE (CONDITIONING) ---
    if (isConditioning) {
        // Determine how to format the target string
        const targetText = exercise.target_intensity === 'MAX' 
          ? 'MAX Effort' 
          : exercise.target_intensity 
            ? `${exercise.target_intensity}W Target` 
            : null;
    
        return (
          <View style={styles.activeRowContainer}>
            {/* Header Row: Round Number & Metadata */}
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: theme.spacing.sm }}>
               <Typography variant="label" style={styles.activeSetHeader}>Round {setIndex + 1}</Typography>
               
               {/* Right-Aligned Metadata Container */}
               <View style={{ alignItems: 'flex-end' }}>
                 <Typography variant="caption" color={theme.colors.stateOrange}>
                   Work: {exercise.work_seconds}s | Rest: {exercise.rest_seconds}s
                 </Typography>
                 
                 {/* Conditionally render the target intensity if the backend provides it */}
                 {targetText && (
                   <Typography variant="caption" style={{ marginTop: 2, fontWeight: 'bold', color: theme.colors.textPrimary }}>
                     {targetText}
                   </Typography>
                 )}
               </View>
            </View>
  
          {/* Conditioning Row 1: Watts */}
          <View style={styles.inputRow}>
            <View style={styles.inputGroup}>
              <TextInput style={styles.input} keyboardType="numeric" placeholder="Avg" placeholderTextColor={theme.colors.borderLight} value={avgWatts} onChangeText={setAvgWatts} />
              <Typography variant="caption" style={styles.unitText}>W (Avg)</Typography>
            </View>
            <View style={styles.inputGroup}>
              <TextInput style={styles.input} keyboardType="numeric" placeholder="Peak" placeholderTextColor={theme.colors.borderLight} value={peakWatts} onChangeText={setPeakWatts} />
              <Typography variant="caption" style={styles.unitText}>W (Peak)</Typography>
            </View>
          </View>
  
          {/* Conditioning Row 2: Heart Rate & Complete Action */}
          <View style={[styles.inputRow, styles.bottomInputRow]}>
            <View style={styles.inputGroup}>
              <TextInput style={[styles.input, {minWidth: 45}]} keyboardType="numeric" placeholder="Avg" placeholderTextColor={theme.colors.borderLight} value={avgHr} onChangeText={setAvgHr} />
              <Typography variant="caption" style={styles.unitText}>bpm</Typography>
            </View>
            <View style={styles.inputGroup}>
              <TextInput style={[styles.input, {minWidth: 45}]} keyboardType="numeric" placeholder="Peak" placeholderTextColor={theme.colors.borderLight} value={peakHr} onChangeText={setPeakHr} />
              <Typography variant="caption" style={styles.unitText}>bpm</Typography>
            </View>
            
            <TouchableOpacity style={styles.completeButton} onPress={handleCompleteSet}>
              <Ionicons name="checkmark" size={20} color={theme.colors.surface} />
            </TouchableOpacity>
          </View>
        </View>
      );
    }
  
    // --- RENDER ACTIVE STATE (STANDARD LIFTING) ---
    return (
      <View style={styles.activeRowContainer}>
        {/* ... (Keep your existing standard lifting UI here) ... */}
        <Typography variant="label" style={styles.activeSetHeader}>Set {setIndex + 1}</Typography>
        
        {/* Row 1: Load and Volume */}
        <View style={styles.inputRow}>
          <View style={styles.inputGroup}>
            {isBodyweight && <Typography variant="caption" style={styles.prefix}>BW +</Typography>}
            <TextInput style={styles.input} keyboardType="numeric" placeholder="0" placeholderTextColor={theme.colors.borderLight} value={weightValue} onChangeText={setWeightValue} />
            <Typography variant="caption" style={styles.unitText}>kg</Typography>
          </View>
          <View style={styles.inputGroup}>
            <TextInput style={styles.input} keyboardType="numeric" placeholder="0" placeholderTextColor={theme.colors.borderLight} value={metricValue} onChangeText={setMetricValue} />
            <Typography variant="caption" style={styles.unitText}>{metricLabel}</Typography>
          </View>
        </View>
  
        {/* Row 2: RPE, Warmup, and Complete Action */}
        <View style={[styles.inputRow, styles.bottomInputRow]}>
          <TouchableOpacity style={styles.warmupToggle} activeOpacity={0.7} onPress={() => setIsWarmup(!isWarmup)}>
            <Ionicons name={isWarmup ? "checkbox" : "square-outline"} size={20} color={isWarmup ? theme.colors.stateOrange : theme.colors.textMuted} />
            <Typography variant="caption" style={{ marginLeft: 4 }}>Warmup</Typography>
          </TouchableOpacity>
          <View style={styles.inputGroup}>
            <Typography variant="caption" style={styles.prefix}>RPE</Typography>
            <TextInput style={[styles.input, styles.rpeInput]} keyboardType="numeric" placeholder="-" placeholderTextColor={theme.colors.borderLight} value={rpeValue} onChangeText={setRpeValue} maxLength={4} />
          </View>
          <TouchableOpacity style={styles.completeButton} onPress={handleCompleteSet}>
            <Ionicons name="checkmark" size={20} color={theme.colors.surface} />
          </TouchableOpacity>
        </View>
      </View>
    );
  }

/**
 * --- MAIN COMPONENT: ExerciseCard ---
 */
interface ExerciseCardProps {
  exercise: Exercise;
}

export function ExerciseCard({ exercise }: ExerciseCardProps) {
  const { loggedSets, exerciseNotes, setExerciseNote } = useSessionStore();
  const exerciseId = exercise.id || exercise.name;
  
  const isConditioning = !!exercise.is_conditioning;
  
  // Local state to manage how many set rows to render
  const [rowCount, setRowCount] = useState<number>(1);

  // Initialization Logic
  useEffect(() => {
    // If conditioning, pre-populate the exact number of sets
    if (isConditioning && exercise.rounds) {
      setRowCount(exercise.rounds);
    } else {
      // Otherwise, see if Zustand already has sets saved
      const existingSets = Object.keys(loggedSets[exerciseId] || {}).length;
      if (existingSets > 0) {
        setRowCount(existingSets);
      }
    }
  }, [exercise, isConditioning, exerciseId, loggedSets]);

  return (
    <View style={styles.cardContainer}>
      {/* Header */}
      <View style={styles.header}>
        <Typography variant="h3">{exercise.name}</Typography>
        {isConditioning && exercise.description && (
          <Typography variant="caption" color={theme.colors.stateOrange} style={{ marginTop: 4 }}>
            {exercise.description}
          </Typography>
        )}
      </View>

      {/* Sets List */}
      <View style={styles.setsContainer}>
        {Array.from({ length: rowCount }).map((_, index) => (
          <SetRow 
            key={`${exerciseId}-set-${index}`} 
            exercise={exercise} 
            setIndex={index} 
            isConditioning={isConditioning}
          />
        ))}
      </View>

      {/* Add Set Button (Hidden for Conditioning) */}
      {!isConditioning && (
        <TouchableOpacity 
          style={styles.addSetButton} 
          onPress={() => setRowCount(prev => prev + 1)}
          activeOpacity={0.7}
        >
          <Ionicons name="add" size={16} color={theme.colors.textMuted} />
          <Typography variant="label" style={{ marginLeft: 4 }}>Add Set</Typography>
        </TouchableOpacity>
      )}

      {/* Notes Section */}
      <View style={styles.notesContainer}>
        <TextInput
          style={styles.notesInput}
          placeholder="Add exercise notes..."
          placeholderTextColor={theme.colors.borderLight}
          value={exerciseNotes[exerciseId] || ''}
          onChangeText={(text) => setExerciseNote(exerciseId, text)}
          multiline
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  cardContainer: {
    backgroundColor: theme.colors.background, // F6F5F2
    borderRadius: theme.radii.md,
    padding: theme.spacing.lg,
    marginBottom: theme.spacing.lg,
  },
  header: {
    marginBottom: theme.spacing.md,
  },
  setsContainer: {
    gap: theme.spacing.sm,
  },
  
  // --- Collapsed State Styles ---
  collapsedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EBEBEB',
    padding: theme.spacing.md,
    borderRadius: theme.radii.sm,
  },
  setNumber: {
    width: 45,
    color: theme.colors.textMuted,
  },
  collapsedData: {
    flex: 1,
  },
  collapsedText: {
    fontWeight: '500',
  },

  // --- Active State Styles ---
  activeRowContainer: {
    backgroundColor: theme.colors.surface, // Pure white to pop out from the grey card
    padding: theme.spacing.md,
    borderRadius: theme.radii.sm,
    borderWidth: 1,
    borderColor: theme.colors.borderLight,
  },
  activeSetHeader: {
    marginBottom: theme.spacing.sm,
    color: theme.colors.textPrimary,
  },
  inputRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  bottomInputRow: {
    marginTop: theme.spacing.md,
  },
  inputGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  prefix: {
    marginRight: 6,
    color: theme.colors.textMuted,
  },
  input: {
    backgroundColor: theme.colors.background,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 6,
    minWidth: 50,
    textAlign: 'center',
    fontSize: 16,
    color: theme.colors.textPrimary,
  },
  rpeInput: {
    minWidth: 40,
  },
  unitText: {
    marginLeft: 6,
    color: theme.colors.textMuted,
  },
  warmupToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  completeButton: {
    backgroundColor: theme.colors.actionPrimary,
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },

  // --- Actions & Notes ---
  addSetButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.spacing.md,
    marginTop: theme.spacing.xs,
  },
  notesContainer: {
    marginTop: theme.spacing.sm,
    borderTopWidth: 1,
    borderTopColor: theme.colors.borderLight,
    paddingTop: theme.spacing.md,
  },
  notesInput: {
    fontSize: 14,
    color: theme.colors.textPrimary,
    minHeight: 40,
  }
});
