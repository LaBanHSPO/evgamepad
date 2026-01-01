/**
 * KOL Updates Feed Component
 *
 * Real-time display of KOL trading signals received via Socket.IO.
 *
 * Feature: KOL Updates MVP
 * Created: 2025-12-31
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Users, MessageCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { useSocket } from '../context/SocketContext';
import type { KOLMessage } from '../types/kol';

const MAX_MESSAGES = 50; // Keep only last 50 messages in state

export const KOLUpdatesFeed: React.FC = () => {
  const { socket, isConnected } = useSocket();
  const [messages, setMessages] = useState<KOLMessage[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isExpanded, setIsExpanded] = useState(true);

  // Subscribe to Socket.IO 'kol:new_message' event
  useEffect(() => {
    if (!socket) return;

    const handleNewMessage = (msg: KOLMessage) => {
      console.log('Received KOL message:', msg);

      // Prepend new message (newest first)
      setMessages(prev => {
        const updated = [msg, ...prev];
        // Trim to max messages
        return updated.slice(0, MAX_MESSAGES);
      });

      // Increment unread count
      setUnreadCount(prev => prev + 1);
    };

    socket.on('kol:new_message', handleNewMessage);

    // Cleanup on unmount
    return () => {
      socket.off('kol:new_message', handleNewMessage);
    };
  }, [socket]);

  // Mark all messages as read
  const handleMarkAsRead = useCallback(() => {
    setUnreadCount(0);
  }, []);

  // Toggle expand/collapse
  const toggleExpand = useCallback(() => {
    setIsExpanded(prev => !prev);
  }, []);

  // Format timestamp to relative time
  const formatRelativeTime = (isoTimestamp: string): string => {
    const date = new Date(isoTimestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) return `${diffSecs}s ago`;
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  return (
    <div className="panel">
      {/* Header */}
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-primary" />
          <h2 className="panel-title">KOL UPDATES</h2>
          {unreadCount > 0 && (
            <span
              className="text-xs px-2 py-0.5 rounded-full bg-danger-red text-white font-semibold cursor-pointer animate-pulse"
              onClick={handleMarkAsRead}
              title="Click to mark all as read"
            >
              {unreadCount} new
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {isConnected ? (
            <div className="flex items-center gap-2">
              <MessageCircle className="w-3 h-3 text-terminal-green animate-pulse" />
              <span className="text-xs text-terminal-green">LIVE</span>
            </div>
          ) : (
            <span className="text-xs text-danger-red">DISCONNECTED</span>
          )}
          <button
            onClick={toggleExpand}
            className="text-muted-foreground hover:text-primary transition-colors"
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Message Feed (Collapsible) */}
      {isExpanded && (
        <>
          {messages.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground">
              <MessageCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No KOL messages yet</p>
              <p className="text-xs mt-1">Waiting for trading signals...</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[400px] overflow-y-auto scrollbar-thin scrollbar-thumb-primary/20">
              {messages.map((msg) => (
                <div
                  key={msg.message_id}
                  className="p-3 rounded border-l-2 border-l-primary bg-primary/5 transition-all hover:bg-primary/10"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center text-xs font-bold text-primary">
                        {msg.kol_name.substring(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <span className="text-sm font-semibold text-foreground">
                          {msg.kol_name}
                        </span>
                        <span className="text-xs text-muted-foreground ml-2">
                          {formatRelativeTime(msg.received_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-foreground/90 mt-2 leading-relaxed whitespace-pre-wrap">
                    {msg.message}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Footer Stats */}
          <div className="mt-3 pt-3 border-t border-border/30 flex items-center justify-between text-xs text-muted-foreground">
            <span>Total messages: {messages.length}</span>
            {unreadCount > 0 && (
              <span
                className="text-primary cursor-pointer hover:underline"
                onClick={handleMarkAsRead}
              >
                Mark all as read
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
};
