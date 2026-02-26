import React from 'react';
import { Text, TextProps, StyleSheet } from 'react-native';
import { theme } from '../../theme';

interface TypographyProps extends TextProps {
  variant?: 'h1' | 'h2' | 'h3' | 'body' | 'label' | 'caption';
  color?: string;
  align?: 'auto' | 'left' | 'right' | 'center' | 'justify';
}

export function Typography({
  variant = 'body',
  color = theme.colors.textPrimary,
  align = 'left',
  style,
  children,
  ...rest
}: TypographyProps) {
  return (
    <Text
      style={[
        styles.base,
        styles[variant],
        { color, textAlign: align },
        style,
      ]}
      {...rest}
    >
      {children}
    </Text>
  );
}

const styles = StyleSheet.create({
  base: {
    fontFamily: 'System', // We can swap this for a custom font later
  },
  h1: {
    fontSize: 32,
    fontWeight: '700',
    letterSpacing: -0.5,
  },
  h2: {
    fontSize: 24,
    fontWeight: '600',
    letterSpacing: -0.5,
  },
  h3: {
    fontSize: 18,
    fontWeight: '600',
  },
  body: {
    fontSize: 16,
    fontWeight: '400',
    lineHeight: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.textMuted,
  },
  caption: {
    fontSize: 12,
    fontWeight: '400',
    color: theme.colors.textMuted,
  },
});
