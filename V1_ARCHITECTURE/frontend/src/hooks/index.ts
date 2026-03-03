# 自訂 Hooks
import { useState, useEffect, useRef, useCallback } from 'react';

// WebSocket Hook
export function useWebSocket(url: string, options?: { reconnect?: boolean; reconnectInterval?: number }) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<NodeJS.Timeout | null>(null);
  
  const { reconnect = true, reconnectInterval = 5000 } = options || {};
  
  const connect = useCallback(() => {
    try {
      wsRef.current = new WebSocket(url);
      
      wsRef.current.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket connected');
      };
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      };
      
      wsRef.current.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected');
        
        if (reconnect) {
          reconnectRef.current = setTimeout(connect, reconnectInterval);
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }, [url, reconnect, reconnectInterval]);
  
  useEffect(() => {
    connect();
    
    return () => {
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);
  
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);
  
  const disconnect = useCallback(() => {
    if (reconnectRef.current) {
      clearTimeout(reconnectRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
    }
    setIsConnected(false);
  }, []);
  
  return { isConnected, lastMessage, sendMessage, disconnect, connect };
}

// 輪詢 Hook
export function usePolling<T>(
  fetchFn: () => Promise<T>,
  interval: number,
  enabled: boolean = true
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  
  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      const result = await fetchFn();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [fetchFn]);
  
  useEffect(() => {
    if (enabled) {
      fetch();
      timerRef.current = setInterval(fetch, interval);
    }
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [enabled, interval, fetch]);
  
  return { data, loading, error, refetch: fetch };
}

// 本地存儲 Hook
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(error);
      return initialValue;
    }
  });
  
  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(error);
    }
  };
  
  return [storedValue, setValue] as const;
}

// 防抖 Hook
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  
  return debouncedValue;
}
