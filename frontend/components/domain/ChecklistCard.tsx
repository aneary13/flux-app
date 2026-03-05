import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, Keyboard } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

// Types & State
import { GeneratedExercise } from '../../types/domain';
import { useSessionStore } from '../../store/useSessionStore';

// Core UI
import { Typography } from '../core/Typography';
import { theme } from '../../theme';

interface ChecklistCardProps {
  exercises: GeneratedExercise[];
  title?: string;
}

/**
 * Renders a single row for a checklist item.
 */
function ChecklistItem({ exercise }: { exercise: GeneratedExercise }) {
  const { logSet, loggedSets } = useSessionStore();
  const exerciseId = exercise.name; // Backend uses name as identifier
  const currentLog = loggedSets[exerciseId]?.[0] || {};
  const isChecked = !!currentLog.completed;

  const handleToggle = () => {
    logSet(exerciseId, 0, { completed: !isChecked });
    Keyboard.dismiss();
  };

  return (
    <TouchableOpacity style={styles.itemRow} activeOpacity={0.7} onPress={handleToggle}>
      <Ionicons
        name={isChecked ? 'checkmark-circle' : 'ellipse-outline'}
        size={28}
        color={isChecked ? theme.colors.stateGreen : theme.colors.borderLight}
      />
      <Typography variant="body" style={[styles.itemText, isChecked && styles.itemTextChecked]}>
        {exercise.name}
      </Typography>
    </TouchableOpacity>
  );
}

/**
 * The main Checklist Group Card
 * Now features a collapsible accordion state and completion summary.
 */
export function ChecklistCard({ exercises, title }: ChecklistCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const { loggedSets } = useSessionStore();

  if (!exercises || exercises.length === 0) return null;

  // Calculate how many items are checked for the summary text
  const completedCount = exercises.filter((ex) => !!loggedSets[ex.name]?.[0]?.completed).length;

  return (
    <View style={styles.cardContainer}>
      {/* Touchable Header for Toggling */}
      <TouchableOpacity
        style={styles.headerRow}
        activeOpacity={0.7}
        onPress={() => {
          setIsExpanded(!isExpanded);
          Keyboard.dismiss();
        }}
      >
        <View>
          {/* Show summary text ONLY when collapsed */}
          {title && <Typography variant="h3">{title}</Typography>}
          {!isExpanded && (
            <Typography variant="caption" color={theme.colors.textMuted}>
              {completedCount} / {exercises.length} completed
            </Typography>
          )}
        </View>
        <Ionicons
          name={isExpanded ? 'chevron-up' : 'chevron-down'}
          size={24}
          color={theme.colors.textMuted}
        />
      </TouchableOpacity>

      {/* Expandable List Content */}
      {isExpanded && (
        <View style={styles.listContainer}>
          {exercises.map((ex, index) => (
            <ChecklistItem key={`checklist-${ex.name}-${index}`} exercise={ex} />
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  cardContainer: {
    backgroundColor: theme.colors.background,
    borderRadius: theme.radii.md,
    padding: theme.spacing.lg,
    marginBottom: theme.spacing.lg,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    // We remove the bottom margin here so it sits flush when collapsed
  },
  listContainer: {
    marginTop: theme.spacing.md, // Add the spacing back only when expanded
    gap: theme.spacing.md,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  itemText: {
    marginLeft: theme.spacing.md,
    color: theme.colors.textPrimary,
    fontWeight: '500',
  },
  itemTextChecked: {
    color: theme.colors.textMuted,
    textDecorationLine: 'line-through',
  },
});
