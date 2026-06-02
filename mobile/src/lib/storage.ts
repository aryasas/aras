import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

const memory = new Map<string, string>();

function canUseWebStorage() {
  return Platform.OS === 'web' && typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

export async function getStoredValue(key: string): Promise<string | null> {
  if (canUseWebStorage()) {
    return window.localStorage.getItem(key);
  }
  try {
    const value = await SecureStore.getItemAsync(key);
    return value ?? memory.get(key) ?? null;
  } catch {
    return memory.get(key) ?? null;
  }
}

export async function setStoredValue(key: string, value: string): Promise<void> {
  memory.set(key, value);
  if (canUseWebStorage()) {
    window.localStorage.setItem(key, value);
    return;
  }
  try {
    await SecureStore.setItemAsync(key, value);
  } catch {
    // Keep the in-memory value so the current session still works.
  }
}

export async function removeStoredValue(key: string): Promise<void> {
  memory.delete(key);
  if (canUseWebStorage()) {
    window.localStorage.removeItem(key);
    return;
  }
  try {
    await SecureStore.deleteItemAsync(key);
  } catch {
    // Nothing else to clear.
  }
}
