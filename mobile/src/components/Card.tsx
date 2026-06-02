import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { theme } from '../lib/theme';
import { useDesignOverride } from '../lib/designOverrides';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  variant?: 'elevated' | 'outline' | 'flat';
}

export const Card = ({ children, style, variant = 'elevated' }: CardProps) => {
  const cardOverride = useDesignOverride('mobile:card', `mobile:card:${variant}`);
  if (cardOverride.hidden) return null;

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

  return <View style={[styles.container, getVariantStyles(), cardOverride.style, style]}>{children}</View>;
};

const styles = StyleSheet.create({
  container: {
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing.lg,
  },
});
