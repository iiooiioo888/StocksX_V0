// 主應用程式
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, theme } from 'antd';
import zhTW from 'antd/locale/zh_TW';

import { useAuthStore } from '@/store';

import LoginPage from '@/pages/LoginPage';
import DashboardPage from '@/pages/DashboardPage';

// 路由守衛
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={zhTW}
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#4a6cf7',
          borderRadius: 8,
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <DashboardPage />
              </PrivateRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
