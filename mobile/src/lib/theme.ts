export const theme = {
  colors: {
    primary: '#4F46E5', // Indigo 600
    primaryLight: '#818CF8', // Indigo 400
    primaryDark: '#3730A3', // Indigo 800
    accent: '#F43F5E', // Rose 500
    background: '#F9FAFB', // Gray 50
    surface: '#FFFFFF', // White
    text: '#111827', // Gray 900
    textSecondary: '#6B7280', // Gray 500
    border: '#E5E7EB', // Gray 200
    error: '#EF4444', // Red 500
    success: '#10B981', // Emerald 500
    warning: '#F59E0B', // Amber 500
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  borderRadius: {
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
    round: 9999,
  },
  typography: {
    h1: {
      fontFamily: 'PlusJakartaSans_800ExtraBold',
      fontSize: 32,
      lineHeight: 40,
    },
    h2: {
      fontFamily: 'PlusJakartaSans_700Bold',
      fontSize: 24,
      lineHeight: 32,
    },
    h3: {
      fontFamily: 'PlusJakartaSans_600SemiBold',
      fontSize: 20,
      lineHeight: 28,
    },
    subtitle: {
      fontFamily: 'PlusJakartaSans_600SemiBold',
      fontSize: 16,
      lineHeight: 24,
    },
    body: {
      fontFamily: 'PlusJakartaSans_400Regular',
      fontSize: 14,
      lineHeight: 20,
    },
    caption: {
      fontFamily: 'PlusJakartaSans_500Medium',
      fontSize: 12,
      lineHeight: 16,
    },
  },
  shadows: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.05,
      shadowRadius: 2,
      elevation: 2,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.1,
      shadowRadius: 6,
      elevation: 4,
    },
  },
};
