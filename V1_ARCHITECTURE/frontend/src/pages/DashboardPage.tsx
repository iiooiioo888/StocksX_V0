// 主頁儀表板
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Menu, Card, Row, Col, Statistic, Typography, Button } from 'antd';
import {
  DashboardOutlined,
  LineChartOutlined,
  HistoryOutlined,
  SettingOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/store';
import { dataApi } from '@/api';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuthStore();
  const [fearGreed, setFearGreed] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    // 載入恐懼貪婪指數
    const loadFearGreed = async () => {
      try {
        const response = await dataApi.getFearGreed();
        setFearGreed(response.data);
      } catch (error) {
        console.error('Failed to load fear greed:', error);
      }
    };
    
    loadFearGreed();
  }, [isAuthenticated, navigate]);
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  const menuItems = [
    { key: 'dashboard', icon: <DashboardOutlined />, label: '儀表板' },
    { key: 'backtest', icon: <LineChartOutlined />, label: '回測' },
    { key: 'history', icon: <HistoryOutlined />, label: '歷史' },
    { key: 'settings', icon: <SettingOutlined />, label: '設定' },
  ];
  
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        theme="dark"
        width={200}
        style={{
          background: 'linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%)',
        }}
      >
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}>
          <Title level={4} style={{ color: '#6ea8fe', margin: 0 }}>
            📊 StocksX
          </Title>
        </div>
        
        <Menu
          theme="dark"
          mode="inline"
          defaultSelectedKeys={['dashboard']}
          items={menuItems}
          style={{ marginTop: 16 }}
        />
        
        <div style={{ position: 'absolute', bottom: 0, width: '100%', padding: 16 }}>
          <Button
            type="text"
            icon={<LogoutOutlined />}
            onClick={handleLogout}
            style={{ color: '#94a3b8', width: '100%', textAlign: 'left' }}
          >
            登出
          </Button>
        </div>
      </Sider>
      
      <Layout>
        <Header
          style={{
            background: 'rgba(26,26,46,0.7)',
            backdropFilter: 'blur(20px)',
            borderBottom: '1px solid rgba(110,168,254,0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 24px',
          }}
        >
          <Title level={4} style={{ color: '#f0f0ff', margin: 0 }}>
            儀表板
          </Title>
          <div style={{ color: '#94a3b8' }}>
            👤 {user?.display_name || user?.username}
          </div>
        </Header>
        
        <Content style={{ padding: 24 }}>
          {/* 恐懼貪婪指數 */}
          <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
              <Card
                style={{
                  borderRadius: 16,
                  background: 'linear-gradient(135deg, rgba(42,26,58,0.8), rgba(53,37,69,0.8))',
                  border: '1px solid rgba(90,58,124,0.4)',
                }}
              >
                <div style={{ textAlign: 'center' }}>
                  <Typography.Text style={{ color: '#94a3b8', textTransform: 'uppercase' }}>
                    恐懼貪婪指數
                  </Typography.Text>
                  <div
                    style={{
                      fontSize: 48,
                      fontWeight: 800,
                      color: fearGreed?.value > 50 ? '#00cc96' : '#ef553b',
                      margin: '16px 0',
                    }}
                  >
                    {fearGreed?.value ?? '-'}
                  </div>
                  <div style={{ color: '#94a3b8' }}>
                    {fearGreed?.classification ?? '載入中...'}
                  </div>
                </div>
              </Card>
            </Col>
            
            <Col xs={24} md={8}>
              <Card
                style={{
                  borderRadius: 16,
                  background: 'linear-gradient(135deg, rgba(30,30,58,0.6), rgba(37,37,69,0.6))',
                  border: '1px solid rgba(58,58,92,0.4)',
                }}
              >
                <Statistic
                  title="我的回測"
                  value={12}
                  suffix="次"
                  valueStyle={{ color: '#6ea8fe' }}
                />
              </Card>
            </Col>
            
            <Col xs={24} md={8}>
              <Card
                style={{
                  borderRadius: 16,
                  background: 'linear-gradient(135deg, rgba(30,30,58,0.6), rgba(37,37,69,0.6))',
                  border: '1px solid rgba(58,58,92,0.4)',
                }}
              >
                <Statistic
                  title="勝率"
                  value={55}
                  suffix="%"
                  valueStyle={{ color: '#00cc96' }}
                />
              </Card>
            </Col>
          </Row>
          
          {/* 快速操作 */}
          <div style={{ marginTop: 24 }}>
            <Title level={5} style={{ color: '#f0f0ff' }}>快速操作</Title>
            <Row gutter={[16, 16]}>
              <Col xs={24} md={12}>
                <Card
                  hoverable
                  style={{
                    borderRadius: 16,
                    background: 'linear-gradient(135deg, rgba(30,30,58,0.8), rgba(37,37,69,0.8))',
                    border: '1px solid rgba(58,58,92,0.5)',
                  }}
                  onClick={() => navigate('/backtest')}
                >
                  <div style={{ fontSize: 24, marginBottom: 8 }}>₿</div>
                  <Title level={5} style={{ color: '#f0f0ff', margin: 0 }}>
                    加密貨幣回測
                  </Title>
                  <Typography.Text style={{ color: '#94a3b8' }}>
                    支援 11 個交易所、主流幣/DeFi/Meme
                  </Typography.Text>
                </Card>
              </Col>
              
              <Col xs={24} md={12}>
                <Card
                  hoverable
                  style={{
                    borderRadius: 16,
                    background: 'linear-gradient(135deg, rgba(30,30,58,0.8), rgba(37,37,69,0.8))',
                    border: '1px solid rgba(58,58,92,0.5)',
                  }}
                  onClick={() => navigate('/backtest', { state: { marketType: 'traditional' } })}
                >
                  <div style={{ fontSize: 24, marginBottom: 8 }}>🏛️</div>
                  <Title level={5} style={{ color: '#f0f0ff', margin: 0 }}>
                    傳統市場回測
                  </Title>
                  <Typography.Text style={{ color: '#94a3b8' }}>
                    美股、台股、ETF、期貨、指數
                  </Typography.Text>
                </Card>
              </Col>
            </Row>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default DashboardPage;
