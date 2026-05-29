import { create } from 'zustand';
import api from '../lib/api';
import { getToken, logout as clearAuthStorage, setToken } from '../lib/auth';

interface User {
  id: string | number;
  username: string;
  full_name?: string;
  email?: string;
  is_admin?: boolean;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  token: null,
  login: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    const { access_token } = response.data;
    await setToken(access_token);
    
    const me = await api.get('/auth/me');
    set({ isAuthenticated: true, user: me.data, token: access_token });
  },
  logout: async () => {
    await clearAuthStorage();
    set({ isAuthenticated: false, user: null, token: null });
  },
  checkAuth: async () => {
    const token = await getToken();
    if (token) {
      try {
        const me = await api.get('/auth/me');
        set({ isAuthenticated: true, user: me.data, token });
      } catch (err) {
        await clearAuthStorage();
        set({ isAuthenticated: false, user: null, token: null });
      }
    }
  },
}));
