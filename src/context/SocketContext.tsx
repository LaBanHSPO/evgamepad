
import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';

interface SocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  lastError: string | null;
  sessionId: string | null;
  sessionRecovered: boolean;
}

const SocketContext = createContext<SocketContextType | undefined>(undefined);

// Defaults to localhost:8686 (MT5 Trading Server) if not specified in env
const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:8686';

export const SocketProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionRecovered, setSessionRecovered] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  useEffect(() => {
    console.log('[SocketContext] Connecting to:', SOCKET_URL);

    const newSocket = io(SOCKET_URL, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 10000,
    });

    setSocket(newSocket);

    // Backend connection events
    newSocket.on('connected', (data: { session_id: string; message: string; server_time: string }) => {
      console.log('[SocketContext] Backend connected event:', data);
      setIsConnected(true);
      setSessionId(data.session_id);
      setSessionRecovered(false);
      setLastError(null);
      setReconnectAttempt(0);
    });

    newSocket.on('session_recovered', (data: { session_id: string; pending_orders: unknown[]; reconnected_at: string }) => {
      console.log('[SocketContext] Session recovered:', data);
      setIsConnected(true);
      setSessionId(data.session_id);
      setSessionRecovered(true);
      setLastError(null);
      setReconnectAttempt(0);
    });

    // Socket.IO native events
    newSocket.on('connect', () => {
      console.log('[SocketContext] Socket.IO connected');
      setIsConnected(true);
      setLastError(null);
    });

    newSocket.on('disconnect', (reason) => {
      console.log('[SocketContext] Socket disconnected:', reason);
      setIsConnected(false);
      setSessionId(null);
      setSessionRecovered(false);
    });

    newSocket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`[SocketContext] Reconnection attempt ${attemptNumber}`);
      setReconnectAttempt(attemptNumber);
    });

    newSocket.on('reconnect_failed', () => {
      console.error('[SocketContext] All reconnection attempts failed');
      setLastError('Failed to reconnect after maximum attempts');
    });

    newSocket.on('reconnect', (attemptNumber) => {
      console.log(`[SocketContext] Reconnected after ${attemptNumber} attempts`);
      setReconnectAttempt(0);
    });

    newSocket.on('connect_error', (err) => {
      console.error('[SocketContext] Connection error:', err);
      setIsConnected(false);
      setLastError(err.message);
    });

    // Trading error event
    newSocket.on('error', (data: { success: boolean; error_code: string; message: string }) => {
      console.error('[SocketContext] Trading error:', data);
      setLastError(data.message || 'Trading operation failed');
    });

    // Advisor error event
    newSocket.on('advisor:error', (data: { success: boolean; error_code: string; message: string }) => {
      console.error('[SocketContext] Advisor error:', data);
      setLastError(data.message || 'Advisor operation failed');
    });

    return () => {
      console.log('[SocketContext] Cleaning up socket connection');
      newSocket.close();
    };
  }, []);

  return (
    <SocketContext.Provider value={{ socket, isConnected, lastError, sessionId, sessionRecovered }}>
      {children}
    </SocketContext.Provider>
  );
};

export const useSocket = (): SocketContextType => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};
