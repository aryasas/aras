// claude-opus-4-7
// ARC (ArasStudio) theme port for React Native. Palette/radius/spacing mirror
// ui/src/index.css ARC tokens. Font family stays on Plus Jakarta (already
// installed via @expo-google-fonts) — Geist is web-only until a Geist font
// package is added to expo. Replace fontFamily values to swap.
const ARC = {
  light: {
    bg:        '#FBFAF7',
    bg2:       '#F4F2EC',
    surface:   '#FFFFFF',
    surface2:  '#F7F5EF',
    line:      '#E7E3D9',
    line2:     '#D3CEC0',
    text:      '#1A1D23',
    text2:     '#5A6373',
    text3:     '#8B95A6',
    mute:      '#BDC3CC',
  },
  dark: {
    bg:        '#0E1116',
    bg2:       '#11151B',
    surface:   '#161B23',
    surface2:  '#1C2330',
    line:      '#262E3B',
    line2:     '#323B4B',
    text:      '#E7E9EE',
    text2:     '#98A0AE',
    text3:     '#5E6877',
    mute:      '#3B4452',
  },
  accent:     '#E89B6C',  // coral
  accentDark: '#D5874F',
  accentInk:  '#FFFFFF',
  warn:       '#F2C56C',
  danger:     '#FF6B7A',
  info:       '#7AB6FF',
} as const;

const palette = ARC.light;

export const theme = {
  arc: ARC,
  colors: {
    primary:        ARC.accent,
    primaryLight:   '#F2B58E',
    primaryDark:    ARC.accentDark,
    accent:         ARC.accent,
    background:     palette.bg,
    surface:        palette.surface,
    surfaceAlt:     palette.surface2,
    text:           palette.text,
    textSecondary:  palette.text2,
    textTertiary:   palette.text3,
    border:         palette.line,
    borderStrong:   palette.line2,
    error:          ARC.danger,
    success:        '#10B981',
    warning:        ARC.warn,
    info:           ARC.info,
    onPrimary:      ARC.accentInk,
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 18,
    xl: 24,
    xxl: 36,
  },
  borderRadius: {
    sm: 5,
    md: 8,
    lg: 14,
    xl: 20,
    round: 9999,
  },
  rowHeight: 36,
  typography: {
    h1:        { fontFamily: 'PlusJakartaSans_700Bold',     fontSize: 28, lineHeight: 34, letterSpacing: -0.4 },
    h2:        { fontFamily: 'PlusJakartaSans_700Bold',     fontSize: 22, lineHeight: 28, letterSpacing: -0.3 },
    h3:        { fontFamily: 'PlusJakartaSans_600SemiBold', fontSize: 18, lineHeight: 24, letterSpacing: -0.2 },
    subtitle:  { fontFamily: 'PlusJakartaSans_600SemiBold', fontSize: 15, lineHeight: 22 },
    body:      { fontFamily: 'PlusJakartaSans_400Regular',  fontSize: 14, lineHeight: 20 },
    bodyStrong:{ fontFamily: 'PlusJakartaSans_500Medium',   fontSize: 14, lineHeight: 20 },
    caption:   { fontFamily: 'PlusJakartaSans_500Medium',   fontSize: 11, lineHeight: 14, letterSpacing: 0.6 },
    mono:      { fontFamily: 'Menlo',                       fontSize: 12, lineHeight: 16 },
  },
  shadows: {
    sm: { shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.04, shadowRadius: 2, elevation: 1 },
    md: { shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.08, shadowRadius: 8, elevation: 3 },
    lg: { shadowColor: '#000', shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.12, shadowRadius: 20, elevation: 6 },
  },
};

export type Theme = typeof theme;
