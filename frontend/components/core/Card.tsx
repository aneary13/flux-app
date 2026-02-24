import React from 'react';
import { View, ViewProps, StyleSheet } from 'react-native';
import { theme } from '../../theme';

interface CardProps extends ViewProps {
  padding?: number;
  noShadow?: boolean;
}

export function Card({ 
  style, 
  children, 
  padding = theme.spacing.lg, // Standard 20px padding
  noShadow = false,
  ...rest 
}: CardProps) {
  return (
    <View
      style={[
        styles.card,
        { padding },
        !noShadow && styles.shadow,
        style,
      ]}
      {...rest}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: theme.colors.surface, // Pure white
    borderRadius: theme.radii.md, // Soft 16px corners
  },
  shadow: {
    ...theme.shadows.card, // 4px vertical offset, 0.03 opacity
  },
});
