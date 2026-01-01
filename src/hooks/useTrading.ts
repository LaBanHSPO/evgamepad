/**
 * Trading operations hook for MT5 Socket.IO integration
 * Provides login, buy, sell, modify, and close position functionality
 */

import { useState, useEffect, useCallback } from 'react';
import { useSocket } from '@/context/SocketContext';

// ============================================================================
// Types
// ============================================================================

interface LoginCredentials {
  account: number;
  password: string;
  server: string;
}

interface AccountInfo {
  login: number;
  name: string;
  server: string;
  currency: string;
  balance: number;
  equity: number;
  leverage: number;
}

interface OrderRequest {
  symbol: string;
  volume: number;
  sl?: number;
  tp?: number;
}

interface OrderResult {
  command_id: string;
  ticket: number;
  symbol: string;
  volume: number;
  price: number;
  sl?: number;
  tp?: number;
  timestamp: string;
}

interface ModifyRequest {
  ticket: number;
  sl?: number;
  tp?: number;
}

interface ModifyResult {
  command_id: string;
  ticket: number;
  sl: number;
  tp: number;
  modified_at: string;
}

interface CloseRequest {
  ticket: number;
  volume?: number;
}

interface CloseResult {
  command_id: string;
  ticket: number;
  close_ticket: number;
  close_price: number;
  volume_closed: number;
  profit: number;
  closed_at: string;
}

interface TradingError {
  success: false;
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
}

// ============================================================================
// Hook
// ============================================================================

export const useTrading = () => {
  const { socket, isConnected } = useSocket();

  // State
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ============================================================================
  // Event Handlers
  // ============================================================================

  useEffect(() => {
    if (!socket) return;

    // Login result
    socket.on('login_result', (data: { success: boolean; data?: AccountInfo }) => {
      console.log('[useTrading] Login result:', data);
      if (data.success && data.data) {
        setAccountInfo(data.data);
        setIsLoggedIn(true);
        setError(null);
      }
      setLoading(false);
    });

    // Order result (buy/sell)
    socket.on('order_result', (data: { success: boolean; data?: OrderResult }) => {
      console.log('[useTrading] Order result:', data);
      setLoading(false);
      if (!data.success) {
        setError('Order failed');
      }
    });

    // Modify result
    socket.on('modify_result', (data: { success: boolean; data?: ModifyResult }) => {
      console.log('[useTrading] Modify result:', data);
      setLoading(false);
      if (!data.success) {
        setError('Modify failed');
      }
    });

    // Close result
    socket.on('close_result', (data: { success: boolean; data?: CloseResult }) => {
      console.log('[useTrading] Close result:', data);
      setLoading(false);
      if (!data.success) {
        setError('Close failed');
      }
    });

    // Error handling
    socket.on('error', (data: TradingError) => {
      console.error('[useTrading] Error:', data);
      setError(data.message);
      setLoading(false);
    });

    return () => {
      socket.off('login_result');
      socket.off('order_result');
      socket.off('modify_result');
      socket.off('close_result');
      socket.off('error');
    };
  }, [socket]);

  // ============================================================================
  // Operations
  // ============================================================================

  const login = useCallback(
    (credentials: LoginCredentials): Promise<AccountInfo> => {
      return new Promise((resolve, reject) => {
        if (!socket || !isConnected) {
          reject(new Error('Socket not connected'));
          return;
        }

        setLoading(true);
        setError(null);

        const handleResult = (data: { success: boolean; data?: AccountInfo }) => {
          socket.off('login_result', handleResult);
          socket.off('error', handleError);

          if (data.success && data.data) {
            resolve(data.data);
          } else {
            reject(new Error('Login failed'));
          }
        };

        const handleError = (data: TradingError) => {
          socket.off('login_result', handleResult);
          socket.off('error', handleError);
          reject(new Error(data.message));
        };

        socket.once('login_result', handleResult);
        socket.once('error', handleError);

        socket.emit('login', credentials);
      });
    },
    [socket, isConnected]
  );

  const buy = useCallback(
    (order: OrderRequest): Promise<OrderResult> => {
      return new Promise((resolve, reject) => {
        if (!socket || !isConnected) {
          reject(new Error('Socket not connected'));
          return;
        }

        setLoading(true);
        setError(null);

        const handleResult = (data: { success: boolean; data?: OrderResult }) => {
          socket.off('order_result', handleResult);
          socket.off('error', handleError);

          if (data.success && data.data) {
            resolve(data.data);
          } else {
            reject(new Error('Buy order failed'));
          }
        };

        const handleError = (data: TradingError) => {
          socket.off('order_result', handleResult);
          socket.off('error', handleError);
          reject(new Error(data.message));
        };

        socket.once('order_result', handleResult);
        socket.once('error', handleError);

        socket.emit('buy', order);
      });
    },
    [socket, isConnected]
  );

  const sell = useCallback(
    (order: OrderRequest): Promise<OrderResult> => {
      return new Promise((resolve, reject) => {
        if (!socket || !isConnected) {
          reject(new Error('Socket not connected'));
          return;
        }

        setLoading(true);
        setError(null);

        const handleResult = (data: { success: boolean; data?: OrderResult }) => {
          socket.off('order_result', handleResult);
          socket.off('error', handleError);

          if (data.success && data.data) {
            resolve(data.data);
          } else {
            reject(new Error('Sell order failed'));
          }
        };

        const handleError = (data: TradingError) => {
          socket.off('order_result', handleResult);
          socket.off('error', handleError);
          reject(new Error(data.message));
        };

        socket.once('order_result', handleResult);
        socket.once('error', handleError);

        socket.emit('sell', order);
      });
    },
    [socket, isConnected]
  );

  const modify = useCallback(
    (request: ModifyRequest): Promise<ModifyResult> => {
      return new Promise((resolve, reject) => {
        if (!socket || !isConnected) {
          reject(new Error('Socket not connected'));
          return;
        }

        setLoading(true);
        setError(null);

        const handleResult = (data: { success: boolean; data?: ModifyResult }) => {
          socket.off('modify_result', handleResult);
          socket.off('error', handleError);

          if (data.success && data.data) {
            resolve(data.data);
          } else {
            reject(new Error('Modify failed'));
          }
        };

        const handleError = (data: TradingError) => {
          socket.off('modify_result', handleResult);
          socket.off('error', handleError);
          reject(new Error(data.message));
        };

        socket.once('modify_result', handleResult);
        socket.once('error', handleError);

        socket.emit('modify', request);
      });
    },
    [socket, isConnected]
  );

  const close = useCallback(
    (request: CloseRequest): Promise<CloseResult> => {
      return new Promise((resolve, reject) => {
        if (!socket || !isConnected) {
          reject(new Error('Socket not connected'));
          return;
        }

        setLoading(true);
        setError(null);

        const handleResult = (data: { success: boolean; data?: CloseResult }) => {
          socket.off('close_result', handleResult);
          socket.off('error', handleError);

          if (data.success && data.data) {
            resolve(data.data);
          } else {
            reject(new Error('Close failed'));
          }
        };

        const handleError = (data: TradingError) => {
          socket.off('close_result', handleResult);
          socket.off('error', handleError);
          reject(new Error(data.message));
        };

        socket.once('close_result', handleResult);
        socket.once('error', handleError);

        socket.emit('close', request);
      });
    },
    [socket, isConnected]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    // State
    isConnected,
    isLoggedIn,
    accountInfo,
    loading,
    error,

    // Operations
    login,
    buy,
    sell,
    modify,
    close,
    clearError,
  };
};
