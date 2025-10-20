import { useState, useRef, useCallback, useEffect } from 'react';

interface WebSocketConfig {
  url: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
  onOpen?: () => void;
}

export const useWebSocket = ({
  url,
  onMessage,
  onError,
  onClose,
  onOpen
}: WebSocketConfig) => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ws = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url);
      
      ws.current.binaryType = 'arraybuffer';  // Important for binary data

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        onOpen?.();
      };

      ws.current.onmessage = (event) => {
        onMessage?.(event.data);
      };

      ws.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket error occurred');
        onError?.(event);
      };

      ws.current.onclose = () => {
        console.log('WebSocket closed');
        setIsConnected(false);
        onClose?.();
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect to WebSocket');
    }
  }, [url, onMessage, onError, onClose, onOpen]);

  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.close();
      ws.current = null;
      setIsConnected(false);
    }
  }, []);

  const sendMessage = useCallback((data: Uint8Array) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(data);
      } catch (err) {
        console.error('Error sending data:', err);
        setError('Failed to send data');
      }
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    error,
    connect,
    disconnect,
    sendMessage
  };
};