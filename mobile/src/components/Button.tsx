import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ActivityIndicator, ViewStyle, TextStyle } from 'react-native';
import { theme } from '../lib/theme';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  size?: 'small' | 'medium' | 'large';
  isLoading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
  icon?: React.ReactNode;
}

export const Button = ({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  isLoading = false,
  disabled = false,
  style,
  textStyle,
  icon,
}: ButtonProps) => {
  const getVariantStyles = (): ViewStyle => {
    switch (variant) {
      case 'secondary':
        return { backgroundColor: theme.colors.primaryLight };
      case 'outline':
        return { 
          backgroundColor: 'transparent', 
          borderWidth: 1.5, 
          borderColor: theme.colors.border 
        };
      case 'danger':
        return { backgroundColor: theme.colors.error };
      case 'primary':
      default:
        return { backgroundColor: theme.colors.primary };
    }
  };

  const getTextVariantStyles = (): TextStyle => {
    switch (variant) {
      case 'outline':
        return { color: theme.colors.text };
      default:
        return { color: theme.colors.surface };
    }
  };

  const getSizeStyles = (): ViewStyle => {
    switch (size) {
      case 'small':
        return { paddingVertical: theme.spacing.sm, paddingHorizontal: theme.spacing.md };
      case 'large':
        return { paddingVertical: theme.spacing.lg, paddingHorizontal: theme.spacing.xl };
      case 'medium':
      default:
        return { paddingVertical: theme.spacing.md, paddingHorizontal: theme.spacing.lg };
    }
  };

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || isLoading}
      activeOpacity={0.8}
      style={[
        styles.container,
        getVariantStyles(),
        getSizeStyles(),
        disabled && styles.disabled,
        style,
      ]}
    >
      {isLoading ? (
        <ActivityIndicator color={variant === 'outline' ? theme.colors.primary : theme.colors.surface} />
      ) : (
        <>
          {icon && <React.Fragment>{icon}</React.Fragment>}
          <Text style={[styles.text, getTextVariantStyles(), textStyle, icon ? { marginLeft: theme.spacing.sm } : null]}>
            {title}
          </Text>
        </>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: theme.borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    ...theme.shadows.sm,
  },
  text: {
    ...theme.typography.subtitle,
  },
  disabled: {
    opacity: 0.6,
  },
});
