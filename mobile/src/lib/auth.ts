import { getStoredValue, removeStoredValue, setStoredValue } from './storage';

const tokenKey = 'aras_token';
const orgIdKey = 'org_id';
let sessionToken: string | null = null;

// claude-sonnet-4-6
export async function getToken(): Promise<string | null> {
  return sessionToken ?? getStoredValue(tokenKey);
}

// claude-sonnet-4-6
export async function setToken(token: string, rememberMe: boolean = true): Promise<void> {
  sessionToken = token;
  if (rememberMe) {
    await setStoredValue(tokenKey, token);
    return;
  }
  await removeStoredValue(tokenKey);
}

// claude-sonnet-4-6
export async function getOrgId(): Promise<string | null> {
  return getStoredValue(orgIdKey);
}

// claude-sonnet-4-6
export async function setOrgId(orgId: string): Promise<void> {
  await setStoredValue(orgIdKey, orgId);
}

// claude-sonnet-4-6
export async function logout(): Promise<void> {
  sessionToken = null;
  await Promise.all([
    removeStoredValue(tokenKey),
    removeStoredValue(orgIdKey),
  ]);
}
