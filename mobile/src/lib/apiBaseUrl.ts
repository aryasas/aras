import api from './api';
import { getStoredValue } from './storage';

const workspaceUrlKey = 'aras_workspace_url';

// claude-sonnet-4-6
function normalizeApiBaseUrl(url: string): string {
  return `${url.replace(/\/$/, '')}/api/v1`;
}

// claude-sonnet-4-6
export async function setApiBaseUrl(url: string): Promise<void> {
  api.defaults.baseURL = normalizeApiBaseUrl(url);
}

// claude-sonnet-4-6
export async function loadApiBaseUrl(): Promise<void> {
  const workspaceUrl = await getStoredValue(workspaceUrlKey);
  if (workspaceUrl) {
    api.defaults.baseURL = normalizeApiBaseUrl(workspaceUrl);
  }
}
