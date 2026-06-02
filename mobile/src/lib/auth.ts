import { getStoredValue, removeStoredValue, setStoredValue } from './storage';

const tokenKey = 'aras_token';
const orgIdKey = 'org_id';

export async function getToken(): Promise<string | null> {
  return getStoredValue(tokenKey);
}

export async function setToken(token: string): Promise<void> {
  await setStoredValue(tokenKey, token);
}

export async function getOrgId(): Promise<string | null> {
  return getStoredValue(orgIdKey);
}

export async function setOrgId(orgId: string): Promise<void> {
  await setStoredValue(orgIdKey, orgId);
}

export async function logout(): Promise<void> {
  await Promise.all([
    removeStoredValue(tokenKey),
    removeStoredValue(orgIdKey),
  ]);
}
