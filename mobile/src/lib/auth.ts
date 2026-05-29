import AsyncStorage from '@react-native-async-storage/async-storage';

const tokenKey = 'aras_token';
const orgIdKey = 'org_id';

export async function getToken(): Promise<string | null> {
  return AsyncStorage.getItem(tokenKey);
}

export async function setToken(token: string): Promise<void> {
  await AsyncStorage.setItem(tokenKey, token);
}

export async function getOrgId(): Promise<string | null> {
  return AsyncStorage.getItem(orgIdKey);
}

export async function setOrgId(orgId: string): Promise<void> {
  await AsyncStorage.setItem(orgIdKey, orgId);
}

export async function logout(): Promise<void> {
  await Promise.all([
    AsyncStorage.removeItem(tokenKey),
    AsyncStorage.removeItem(orgIdKey),
  ]);
}
