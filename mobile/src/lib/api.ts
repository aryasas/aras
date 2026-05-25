import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

if (!__DEV__ && API_BASE_URL.startsWith('http://')) {
  console.warn('SECURITY WARNING: Production mobile build is using an insecure HTTP endpoint. HTTPS is required for production.');
}

interface ApiEnvelope<T = unknown> {
  success: boolean;
  data: T;
  message?: string | null;
  error?: string | { message?: string; detail?: unknown } | null;
  detail?: string | null;
}

function getEnvelopeErrorMessage(value: ApiEnvelope | Record<string, any>): string {
  const error = value.error;
  if (typeof error === 'string') return error;
  if (error && typeof error === 'object' && typeof error.message === 'string') return error.message;
  if (typeof value.detail === 'string') return value.detail;
  if (typeof value.message === 'string') return value.message;
  return 'Request failed';
}

function isApiEnvelope(value: unknown): value is ApiEnvelope {
  return (
    typeof value === 'object' &&
    value !== null &&
    'success' in value &&
    typeof (value as { success?: unknown }).success === 'boolean'
  );
}

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync('aras_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  const orgId = await SecureStore.getItemAsync('org_id');
  if (orgId && orgId !== '-1') {
    config.headers['X-Org-ID'] = orgId;
  }

  return config;
});

api.interceptors.response.use(
  (response) => {
    if (isApiEnvelope(response.data)) {
      if (!response.data.success) {
        const errorMessage = getEnvelopeErrorMessage(response.data);
        const errorData = {
          ...response.data,
          message: errorMessage,
          detail: response.data.detail || errorMessage,
          error: response.data.error || errorMessage,
        };
        const error = new Error(errorMessage) as Error & { response?: typeof response };
        error.response = { ...response, data: errorData };
        return Promise.reject(error);
      }
      response.data = response.data.data;
    }
    return response;
  },
  async (error) => {
    if (error.response?.data) {
      const d = error.response.data;
      let errorMessage = 'Request failed';
      if (isApiEnvelope(d)) {
        errorMessage = getEnvelopeErrorMessage(d);
      } else if (typeof d === 'object') {
        errorMessage = getEnvelopeErrorMessage(d);
      } else if (typeof d === 'string') {
        errorMessage = d;
      }
      error.message = errorMessage;
      error.response.data = {
        ...d,
        error: d.error || errorMessage,
        detail: d.detail || errorMessage,
        message: d.message || errorMessage,
      };
    }
    if (error.response?.status === 401) {
      await SecureStore.deleteItemAsync('aras_token');
    }
    return Promise.reject(error);
  }
);

export default api;
