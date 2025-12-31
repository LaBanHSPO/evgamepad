/**
 * TypeScript types for KOL (Key Opinion Leader) message system.
 *
 * Feature: KOL Updates MVP
 * Created: 2025-12-31
 */

/**
 * KOL message displayed in the feed.
 *
 * Matches KOLMessageBroadcast from backend Socket.IO event.
 */
export interface KOLMessage {
  /** Message UUID */
  message_id: string;
  /** KOL identifier (e.g., "trader_pro_vn") */
  kol_id: string;
  /** KOL display name (e.g., "Trader Pro VN") */
  kol_name: string;
  /** Trading signal message content */
  message: string;
  /** Webhook receipt timestamp (ISO 8601 format) */
  received_at: string;
  /** Additional metadata from webhook */
  metadata?: Record<string, any>;
}

/**
 * Request payload for posting KOL messages.
 *
 * Matches KOLMessageRequest from backend API.
 */
export interface KOLMessageRequest {
  /** KOL identifier */
  kol_id: string;
  /** KOL display name */
  kol_name: string;
  /** Trading signal message */
  message: string;
  /** Message timestamp (ISO 8601) */
  timestamp: string;
  /** Optional Zalo message ID */
  zalo_message_id?: string;
  /** Optional metadata */
  metadata?: Record<string, any>;
}

/**
 * Response from KOL webhook endpoint.
 *
 * Matches KOLMessageResponse from backend API.
 */
export interface KOLMessageResponse {
  /** Success status */
  success: boolean;
  /** Created/existing message UUID */
  message_id: string;
  /** True if message was duplicate */
  deduplicated: boolean;
}
