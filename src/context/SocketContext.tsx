
import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';

interface SocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  lastError: string | null;
}

const SocketContext = createContext<SocketContextType | undefined>(undefined);

// Defaults to localhost:8000 if not specified in env
const SOCKET_URL = import.meta.env.VITE_WS_URL || 'http://localhost:8000';

export const SocketProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  useEffect(() => {
    const newSocket = io(SOCKET_URL, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 10000,
      randomizationFactor: 0.5,
    });

    setSocket(newSocket);

    newSocket.on('connect', () => {
      console.log('Socket connected');
      setIsConnected(true);
      setLastError(null);
      setReconnectAttempt(0);
    });

    newSocket.on('disconnect', (reason) => {
      console.log('Socket disconnected:', reason);
      setIsConnected(false);

      // Auto-reconnect for client-side disconnects
      if (reason === 'io client disconnect') {
        newSocket.connect();
      }
    });

    newSocket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`Reconnection attempt ${attemptNumber}`);
      setReconnectAttempt(attemptNumber);
    });

    newSocket.on('reconnect_failed', () => {
      console.error('All reconnection attempts failed');
      setLastError('Failed to reconnect after maximum attempts');
    });

    newSocket.on('reconnect', (attemptNumber) => {
      console.log(`Reconnected after ${attemptNumber} attempts`);
      setReconnectAttempt(0);
    });

    newSocket.on('connect_error', (err) => {
      console.error('Socket connection error:', err);
      setIsConnected(false);
      setLastError(err.message);
    });

    newSocket.on('error', (data: unknown) => {
        console.error('Socket operational error:', data);
        // If data is an object with message, extract it, otherwise stringify
        const msg = (data && typeof data === 'object' && 'message' in data)
          ? (data as { message: string }).message
          : (typeof data === 'string' ? data : JSON.stringify(data));
        setLastError(msg);
    });

    return () => {
      newSocket.close();
    };
  }, []);

  return (
    <SocketContext.Provider value={{ socket, isConnected, lastError }}>
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
