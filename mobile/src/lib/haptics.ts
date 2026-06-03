import { Platform, Vibration } from 'react-native';

// claude-sonnet-4-6
export const haptic = {
  light: () => Vibration.vibrate(10),
  medium: () => Vibration.vibrate(30),
  success: () => (Platform.OS === 'ios' ? Vibration.vibrate([0, 10, 50, 10]) : Vibration.vibrate(50)),
  error: () => Vibration.vibrate(Platform.OS === 'ios' ? [0, 50, 30, 50] : 200),
};
