import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Typography } from './Typography';
import { theme } from '../../theme';

interface PillProps {
  label: string;
}

export function Pill({ label }: PillProps) {
  return (
    <View style={styles.pill}>
      <Typography variant="caption" style={styles.text}>
        {label}
      </Typography>
    </View>
  );
}

const styles = StyleSheet.create({
  pill: {
    backgroundColor: theme.colors.background, // F6F5F2
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: theme.radii.pill, // 999px
    alignSelf: 'flex-start',
  },
  text: {
    fontWeight: '500',
    color: theme.colors.textPrimary,
  }
});
