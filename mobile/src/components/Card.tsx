import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { theme } from '../lib/theme';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  variant?: 'elevated' | 'outline' | 'flat';
}

export const Card = ({ children, style, variant = 'elevated' }: CardProps) => {
  const getVariantStyles = (): ViewStyle => {
    switch (variant) {
      case 'outline':
        return {
          borderWidth: 1,
          borderColor: theme.colors.border,
          backgroundColor: theme.colors.surface,
        };
      case 'flat':
        return {
          backgroundColor: theme.colors.background,
        };
      case 'elevated':
      default:
        return {
          backgroundColor: theme.colors.surface,
          ...theme.shadows.sm,
        };
    }
  };

  return <View style={[styles.container, getVariantStyles(), style]}>{children}</View>;
};

const styles = StyleSheet.create({
  container: {
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing.lg,
  },
});
