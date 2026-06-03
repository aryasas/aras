import { create } from 'zustand';
import api from '../lib/api';
import { logout as clearAuthStorage, setToken } from '../lib/auth';
import { loadApiBaseUrl } from '../lib/apiBaseUrl';
import * as SecureStore from 'expo-secure-store';

interface User {
  id: string | number;
  username: string;
  name?: string;
  email?: string;
  is_admin?: boolean;
}

type LogoutReason = 'session_expired' | 'manual' | null;

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  rememberMe: boolean;
  logoutReason: LogoutReason;
  login: (username: string, password: string, rememberMe?: boolean) => Promise<void>;
  logout: (reason?: Exclude<LogoutReason, null>) => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  token: null,
  rememberMe: true,
  logoutReason: null,
  login: async (username, password, rememberMe = true) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    const { access_token } = response.data;
    await setToken(access_token, rememberMe);
    
    const me = await api.get('/auth/me');
    set({ isAuthenticated: true, user: me.data, token: access_token, rememberMe, logoutReason: null });
  },
  logout: async (reason = 'manual') => {
    await clearAuthStorage();
    set({ isAuthenticated: false, user: null, token: null, logoutReason: reason });
  },
  checkAuth: async () => {
    await loadApiBaseUrl();
    const token = await SecureStore.getItemAsync('aras_token');
    if (!token) {
      set({ isAuthenticated: false, user: null, token: null, logoutReason: null });
      return;
    }

    try {
      await setToken(token, true);
      const me = await api.get('/auth/me');
      set({ isAuthenticated: true, user: me.data, token, logoutReason: null });
    } catch (err) {
      await clearAuthStorage();
      set({ isAuthenticated: false, user: null, token: null, logoutReason: 'session_expired' });
    }
  },
}));
