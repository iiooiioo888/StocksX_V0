# 狀態管理 Store
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  username: string;
  display_name: string;
  email?: string;
  role: string;
  is_active: boolean;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  accessToken: string | null;
  refreshToken: string | null;
  
  login: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      accessToken: null,
      refreshToken: null,
      
      login: (user, accessToken, refreshToken) =>
        set({
          user,
          isAuthenticated: true,
          accessToken,
          refreshToken,
        }),
      
      logout: () =>
        set({
          user: null,
          isAuthenticated: false,
          accessToken: null,
          refreshToken: null,
        }),
      
      updateUser: (userData) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        })),
    }),
    {
      name: 'auth-storage',
    }
  )
);

interface BacktestState {
  currentTaskId: string | null;
  taskStatus: string | null;
  taskResult: any | null;
  
  setCurrentTask: (taskId: string) => void;
  setTaskStatus: (status: string) => void;
  setTaskResult: (result: any) => void;
  clearCurrentTask: () => void;
}

export const useBacktestStore = create<BacktestState>((set) => ({
  currentTaskId: null,
  taskStatus: null,
  taskResult: null,
  
  setCurrentTask: (taskId) => set({ currentTaskId: taskId }),
  setTaskStatus: (status) => set({ taskStatus: status }),
  setTaskResult: (result) => set({ taskResult: result }),
  clearCurrentTask: () => set({ currentTaskId: null, taskStatus: null, taskResult: null }),
}));

interface ThemeState {
  darkMode: boolean;
  toggleDarkMode: () => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  darkMode: true,
  toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
}));
