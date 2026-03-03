# API 客戶端配置
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// 建立 axios 實例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 請求攔截器 - 添加 JWT 令牌
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 響應攔截器 - 處理令牌過期
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 如果是 401 且尚未重試
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token');
        }

        // 嘗試刷新令牌
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, null, {
          headers: { Authorization: `Bearer ${refreshToken}` },
        });

        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        // 重試原始請求
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // 刷新失敗，清除令牌並跳轉到登入頁
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// API 服務
export const authApi = {
  login: (username: string, password: string) =>
    apiClient.post('/auth/login', { username, password }),
  
  register: (data: { username: string; password: string; display_name?: string; email?: string }) =>
    apiClient.post('/auth/register', data),
  
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
  
  getCurrentUser: () => apiClient.get('/auth/me'),
  
  changePassword: (oldPassword: string, newPassword: string) =>
    apiClient.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword }),
};

export const backtestApi = {
  run: (data: {
    symbol: string;
    exchange: string;
    timeframe: string;
    strategy: string;
    params: Record<string, any>;
    start_date: string;
    end_date: string;
    initial_equity?: number;
    leverage?: number;
    fee_rate?: number;
  }) => apiClient.post('/backtest/run', data),
  
  getStatus: (taskId: string) => apiClient.get(`/backtest/status/${taskId}`),
  
  getResult: (taskId: string) => apiClient.get(`/backtest/result/${taskId}`),
  
  getHistory: (page = 1, pageSize = 20, strategy?: string, symbol?: string) =>
    apiClient.get('/backtest/history', { params: { page, page_size: pageSize, strategy, symbol } }),
  
  deleteHistory: (recordId: number) => apiClient.delete(`/backtest/history/${recordId}`),
  
  optimize: (data: {
    symbol: string;
    exchange: string;
    timeframe: string;
    strategy: string;
    param_grid: Record<string, any[]>;
    start_date: string;
    end_date: string;
    metric?: string;
    n_best?: number;
  }) => apiClient.post('/backtest/optimize', data),
};

export const dataApi = {
  getSymbols: (marketType = 'crypto', category?: string, exchange?: string) =>
    apiClient.get('/data/symbols', { params: { market_type: marketType, category, exchange } }),
  
  getCategories: (marketType = 'crypto') =>
    apiClient.get('/data/symbols/categories', { params: { market_type: marketType } }),
  
  getKline: (params: {
    symbol: string;
    exchange?: string;
    timeframe?: string;
    start_date: string;
    end_date: string;
    limit?: number;
  }) => apiClient.get('/data/kline', { params }),
  
  getFearGreed: () => apiClient.get('/data/fear-greed'),
  
  getStrategies: (category?: string) =>
    apiClient.get('/data/strategies', { params: { category } }),
  
  getStrategyInfo: (strategyName: string) =>
    apiClient.get(`/data/strategies/${strategyName}`),
};

export const monitorApi = {
  getSubscriptions: () => apiClient.get('/monitor/subscriptions'),
};

export default apiClient;
