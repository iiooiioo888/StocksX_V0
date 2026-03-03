// 登入頁面
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Form, Input, Button, Card, message, Typography } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { authApi } from '@/api';
import { useAuthStore } from '@/store';

const { Title } = Typography;

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const [loading, setLoading] = useState(false);
  
  const onFinish = async (values: { username: string; password: string }) => {
    try {
      setLoading(true);
      const response = await authApi.login(values.username, values.password);
      const { access_token, refresh_token } = response.data;
      
      // 取得用戶資訊
      const userResponse = await authApi.getCurrentUser();
      
      // 儲存令牌和用戶資訊
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      login(userResponse.data, access_token, refresh_token);
      
      message.success('登入成功！');
      navigate('/');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '登入失敗，請檢查帳號密碼');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
    }}>
      <Card
        style={{
          width: 400,
          borderRadius: 16,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
        }}
        bodyStyle={{ padding: 32 }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ color: '#6ea8fe', margin: 0 }}>
            📊 StocksX
          </Title>
          <Title level={5} style={{ color: '#94a3b8', margin: '8px 0 0' }}>
            通用回測平台
          </Title>
        </div>
        
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '請輸入帳號' },
              { min: 3, message: '帳號至少 3 個字元' }
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="帳號"
              style={{ borderRadius: 8 }}
            />
          </Form.Item>
          
          <Form.Item
            name="password"
            rules={[
              { required: true, message: '請輸入密碼' },
              { min: 6, message: '密碼至少 6 個字元' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密碼"
              style={{ borderRadius: 8 }}
            />
          </Form.Item>
          
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
              style={{
                borderRadius: 8,
                background: 'linear-gradient(135deg, #4a6cf7, #6366f1)',
              }}
            >
              登入
            </Button>
          </Form.Item>
          
          <div style={{ textAlign: 'center', color: '#94a3b8' }}>
            還沒有帳號？{' '}
            <Link to="/register">立即註冊</Link>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default LoginPage;
