# KOL Updates Feature - Brainstorming Report

**Date:** 2025-12-31
**Feature:** KOL Updates Integration with Zalo Messenger
**Status:** Brainstorming Complete
**Target:** MVP with <100 concurrent users, 1-3s latency

---

## Problem Statement

**Business Need:**
Display trading signals from KOLs (Key Opinion Leaders) received via Zalo messenger to platform users in near real-time (1-3 seconds).

**Example Signal:**
```
"Canh Buy XAU ET 13-15 SL: 09, Buy XAU entry 14-16 SL:10 1/2 vol, Sell XAU ET 31-33 SL:38"
```

**MVP Requirements:**
- REST API endpoint accepting Zalo webhook calls for each new KOL message
- Display raw messages (no parsing for MVP)
- Prevent duplicate messages (webhook retries)
- Near real-time delivery (<3s from webhook to UI)
- Support <100 concurrent users viewing feed
- API key authentication for webhook security

---

## Current System Context

**Backend Stack:**
- FastAPI + Starlette (async Python)
- Socket.IO (real-time push to frontend)
- PostgreSQL (existing: recommendation_outcomes table)
- Redis (caching + pub/sub capable)
- React/TypeScript frontend

**Existing Architecture:**
- Event-driven: Socket.IO handlers in `app/events/`
- Processors: Business logic in `app/processors/`
- Database: PostgreSQL pool manager available
- Real-time: Already pushing advisor results via Socket.IO

**Key Advantage:**
Infrastructure for real-time push already exists (Socket.IO), no polling needed.

---

## Evaluated Approaches

### Approach 1: Simple Database + Socket.IO Push (Recommended)

**Architecture:**
```
Zalo → REST API → Validate + Dedupe → PostgreSQL Insert → Socket.IO Broadcast
                                                              ↓
                                                        Frontend (React)
```

**Flow:**
1. **Webhook Receiver:** FastAPI endpoint `/api/v1/kol/message` (POST)
2. **Authentication:** Verify `Authorization: Bearer {API_KEY}` header
3. **Deduplication:** Check message hash (MD5 of: KOL ID + timestamp + content)
4. **Storage:** Insert into `kol_messages` table (PostgreSQL)
5. **Broadcast:** Emit Socket.IO event `kol:new_message` to all connected clients
6. **Frontend:** Display in real-time feed with timestamp + KOL name

**Pros:**
✅ Simple architecture (1 endpoint, 1 table, 1 Socket.IO event)
✅ Uses existing Socket.IO infrastructure (no new tech)
✅ <500ms latency (direct broadcast)
✅ Scales to 1000+ users (Socket.IO handles concurrency)
✅ PostgreSQL durability (messages never lost)
✅ Easy debugging (all messages in DB)

**Cons:**
❌ All users receive all KOL messages (no filtering)
❌ Database grows indefinitely (needs retention policy)
❌ No message prioritization (FIFO only)

**Complexity:** Low (2-3 days implementation)
**Risk:** Low (proven patterns, existing infra)

---

### Approach 2: Redis Pub/Sub + Database Backup

**Architecture:**
```
Zalo → REST API → Redis Pub/Sub → Socket.IO Server → Clients
                       ↓
                  PostgreSQL (async backup)
```

**Flow:**
1. Webhook receives message
2. Publish to Redis channel `kol_updates`
3. Socket.IO server subscribes to channel
4. Broadcast to clients immediately
5. Async task writes to PostgreSQL for history

**Pros:**
✅ Fastest latency (<100ms, no DB wait)
✅ Redis pub/sub built for real-time messaging
✅ Decouples persistence from delivery
✅ Can add multiple subscribers (analytics, notifications)

**Cons:**
❌ Risk of message loss if Redis crashes before DB write
❌ More complex error handling (retry logic needed)
❌ Two sources of truth (Redis + PostgreSQL)
❌ Over-engineered for <100 users

**Complexity:** Medium (4-5 days)
**Risk:** Medium (Redis failure scenarios)

---

### Approach 3: Server-Sent Events (SSE) Instead of Socket.IO

**Architecture:**
```
Zalo → REST API → PostgreSQL → Trigger → SSE Stream
                                           ↓
                                      Frontend (EventSource)
```

**Flow:**
1. Webhook writes to PostgreSQL
2. PostgreSQL trigger/NOTIFY sends event
3. FastAPI SSE endpoint streams to clients
4. React uses EventSource API

**Pros:**
✅ HTTP-based (simpler than WebSocket for one-way push)
✅ Auto-reconnect built into EventSource
✅ No Socket.IO dependency (lighter)

**Cons:**
❌ Requires replacing existing Socket.IO architecture
❌ One-way only (no client → server events)
❌ Less mature in your codebase (advisor already uses Socket.IO)
❌ PostgreSQL LISTEN/NOTIFY adds complexity

**Complexity:** High (requires refactor)
**Risk:** High (architectural change)

---

## Recommended Solution: Approach 1 (Simple Database + Socket.IO)

**Rationale:**
1. **Fits existing architecture** - Socket.IO already in use for advisor events
2. **Meets latency target** - Direct broadcast achieves <1s easily
3. **Simple to implement** - Minimal new code, reuses patterns
4. **Reliable** - PostgreSQL ensures no message loss
5. **Scales adequately** - 100 users well within Socket.IO capacity
6. **Debuggable** - All messages queryable in database

**Trade-offs Accepted:**
- No per-user message filtering (future: add user subscriptions)
- Need retention policy (future: archive messages >30 days)
- No parsing logic (as requested for MVP)

---

## Technical Design (Approach 1)

### 1. Database Schema

**Table: `kol_messages`**
```sql
CREATE TABLE kol_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kol_id VARCHAR(100) NOT NULL,           -- KOL identifier (e.g., "kol_trader_123")
    kol_name VARCHAR(200) NOT NULL,         -- Display name (e.g., "Trader Pro VN")
    message_text TEXT NOT NULL,             -- Raw message content
    message_hash VARCHAR(32) NOT NULL UNIQUE, -- MD5 for deduplication
    zalo_message_id VARCHAR(255),           -- Zalo's message ID (if provided)
    received_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB                          -- Additional fields (zalo user ID, etc.)
);

-- Indexes
CREATE INDEX idx_kol_messages_received_at ON kol_messages(received_at DESC);
CREATE INDEX idx_kol_messages_kol_id ON kol_messages(kol_id, received_at DESC);
CREATE INDEX idx_kol_messages_hash ON kol_messages(message_hash);
```

**Retention Policy (Future):**
```sql
-- Delete messages older than 90 days (run daily via cron)
DELETE FROM kol_messages WHERE received_at < NOW() - INTERVAL '90 days';
```

---

### 2. REST API Endpoint

**Endpoint:** `POST /api/v1/kol/message`

**Authentication:**
```
Authorization: Bearer {API_KEY}
```
- API key stored in environment: `KOL_WEBHOOK_API_KEY`
- Verify with constant-time comparison (prevent timing attacks)

**Request Body:**
```json
{
  "kol_id": "trader_pro_vn",
  "kol_name": "Trader Pro VN",
  "message": "Canh Buy XAU ET 13-15 SL: 09, Buy XAU entry 14-16 SL:10 1/2 vol",
  "timestamp": "2025-12-31T10:15:30Z",
  "zalo_message_id": "msg_abc123",
  "metadata": {
    "zalo_user_id": "123456",
    "source": "zalo_group"
  }
}
```

**Response (Success):**
```json
{
  "success": true,
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "deduplicated": false
}
```

**Response (Duplicate):**
```json
{
  "success": true,
  "message_id": "existing-uuid",
  "deduplicated": true
}
```

**Response (Auth Error):**
```json
{
  "success": false,
  "error": "UNAUTHORIZED",
  "message": "Invalid API key"
}
```

---

### 3. Deduplication Strategy

**Hash Calculation:**
```python
import hashlib

def calculate_message_hash(kol_id: str, timestamp: str, message: str) -> str:
    """Generate unique hash for deduplication."""
    content = f"{kol_id}|{timestamp}|{message}"
    return hashlib.md5(content.encode()).hexdigest()
```

**Database Constraint:**
- `message_hash` column has UNIQUE constraint
- Duplicate INSERT attempts return existing row

**Webhook Retry Handling:**
- If hash exists → return success + existing message_id
- No error thrown (idempotent operation)

---

### 4. Socket.IO Event

**Event Name:** `kol:new_message`

**Payload:**
```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "kol_id": "trader_pro_vn",
  "kol_name": "Trader Pro VN",
  "message": "Canh Buy XAU ET 13-15 SL: 09...",
  "received_at": "2025-12-31T10:15:30Z",
  "metadata": {...}
}
```

**Broadcast Strategy:**
- Emit to **all connected clients** (no room filtering for MVP)
- Future: Add room-based subscriptions (e.g., join room `kol:trader_pro_vn`)

---

### 5. Frontend Integration

**React Component:** `KOLUpdatesFeed.tsx`

**Features:**
- Subscribe to `kol:new_message` event on mount
- Display messages in reverse chronological order (newest first)
- Show: KOL name, timestamp (relative: "2 minutes ago"), message text
- Auto-scroll to top on new message
- Badge notification for unread messages

**State Management:**
```typescript
const [messages, setMessages] = useState<KOLMessage[]>([]);
const [unreadCount, setUnreadCount] = useState(0);

useEffect(() => {
  socket.on('kol:new_message', (msg: KOLMessage) => {
    setMessages(prev => [msg, ...prev]);
    setUnreadCount(prev => prev + 1);
  });

  return () => socket.off('kol:new_message');
}, []);
```

**UI Layout:**
```
┌─────────────────────────────────┐
│ KOL Updates Feed (🔴 3 new)    │
├─────────────────────────────────┤
│ Trader Pro VN · 2 min ago       │
│ Canh Buy XAU ET 13-15 SL: 09... │
├─────────────────────────────────┤
│ Gold Master · 15 min ago        │
│ Sell XAU entry 31-33 SL:38      │
└─────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Backend (2 days)
1. **Database Migration**
   - Create `kol_messages` table + indexes
   - Add `KOL_WEBHOOK_API_KEY` to environment config

2. **REST API Endpoint**
   - Create `app/events/kol_events.py` (FastAPI router)
   - Implement authentication middleware
   - Implement deduplication logic
   - Implement PostgreSQL insert
   - Emit Socket.IO `kol:new_message` event

3. **Testing**
   - Unit tests for deduplication
   - Integration test for webhook → broadcast flow
   - Load test with 100 concurrent Socket.IO clients

### Phase 2: Frontend (1 day)
1. **KOL Feed Component**
   - Create `src/components/KOLUpdatesFeed.tsx`
   - Subscribe to Socket.IO event
   - Display messages with timestamps
   - Unread badge counter

2. **Integration**
   - Add to main dashboard/portfolio page
   - Mobile responsive layout

### Phase 3: Deployment & Monitoring (0.5 days)
1. **Configuration**
   - Generate secure API key (32-byte random)
   - Configure Zalo webhook URL
   - Set up database retention job (future)

2. **Monitoring**
   - Log all webhook requests (success/failure)
   - Track message delivery latency (webhook → client)
   - Alert on duplicate rate >10% (indicates Zalo retry issues)

**Total Estimate:** 3.5 days

---

## Performance Analysis

### Latency Breakdown (Target: 1-3s)

```
Zalo → REST API:           ~100ms (network)
Authentication:            ~1ms (constant-time comparison)
Deduplication Check:       ~5ms (indexed hash lookup)
PostgreSQL Insert:         ~10ms (single row write)
Socket.IO Broadcast:       ~5ms (100 clients)
Client Render:             ~10ms (React update)
────────────────────────────────────────
TOTAL:                     ~131ms ✅
```

**Result:** Achieves <200ms latency (well under 3s target)

### Throughput Analysis

**Expected Load:**
- KOL messages: ~50/hour (peak)
- Concurrent users: <100
- Messages/second: ~0.014 (very low)

**Database Capacity:**
- PostgreSQL handles 10,000+ writes/sec
- Headroom: 700,000x ✅

**Socket.IO Capacity:**
- Tested up to 10,000 concurrent connections
- Headroom: 100x ✅

**Bottleneck:** None for <100 users

---

## Security Considerations

### 1. API Key Management
- Store in environment variable (`.env`)
- Never commit to git
- Rotate every 90 days
- Use 32-byte random key: `openssl rand -base64 32`

### 2. Rate Limiting (Future Enhancement)
```python
# Limit: 100 requests/minute per KOL
from slowapi import Limiter
limiter = Limiter(key_func=lambda: request.json.get("kol_id"))

@app.post("/api/v1/kol/message")
@limiter.limit("100/minute")
async def receive_kol_message(...):
    ...
```

### 3. Input Validation
- `kol_id`: Alphanumeric + underscore (max 100 chars)
- `message`: Max 5000 chars (prevent abuse)
- `timestamp`: ISO 8601 format validation

### 4. XSS Prevention
- Frontend displays messages as plain text (no HTML rendering)
- Escape special characters in React

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Zalo webhook downtime** | Messages not received | Medium | Manual admin interface to post messages |
| **Database grows too large** | Slow queries | Low | Implement 90-day retention policy |
| **API key leaked** | Spam messages | Low | Key rotation + rate limiting |
| **Message parsing issues** | (N/A for MVP - raw display) | N/A | Future: Add parsing with validation |
| **Socket.IO connection drops** | Users miss messages | Medium | Client auto-reconnect + message history API |

---

## Future Enhancements (Post-MVP)

### Phase 2.1: Message Parsing
- Extract trading signals (BUY/SELL, symbol, entry, SL, TP)
- Store structured data in JSONB column
- Display formatted cards instead of raw text

### Phase 2.2: User Subscriptions
- Allow users to follow specific KOLs
- Room-based Socket.IO (join `kol:{kol_id}`)
- Per-user notification preferences

### Phase 2.3: Message History API
- REST endpoint: `GET /api/v1/kol/messages?kol_id=...&limit=50`
- Pagination support
- Allow clients to fetch missed messages on reconnect

### Phase 2.4: Admin Dashboard
- Manually post messages (if Zalo webhook fails)
- Edit/delete inappropriate messages
- KOL management (add/remove, enable/disable)

### Phase 2.5: Analytics
- Track message engagement (views, clicks)
- KOL performance metrics (accuracy tracking integration)
- Popular trading signals

---

## Dependencies & Integration Points

**New Dependencies:**
- None (uses existing FastAPI, PostgreSQL, Socket.IO)

**Integration with Existing Features:**
- **Accuracy Tracking (Phase 5.2):** Future integration to track KOL signal performance
- **Portfolio Analysis:** Users can compare KOL signals vs. AI advisor recommendations
- **Socket.IO Infrastructure:** Reuses existing connection management

---

## Success Metrics

**MVP Success Criteria:**
- [ ] Webhook endpoint accepts Zalo messages
- [ ] Messages appear in UI within 3 seconds
- [ ] Zero duplicate messages displayed (deduplication works)
- [ ] Supports 100 concurrent users without lag
- [ ] Zero message loss (all webhooks persisted)

**Key Metrics to Track:**
- Message delivery latency (p50, p95, p99)
- Deduplication rate (should be <5% under normal operation)
- Socket.IO connection stability (reconnects/hour)
- Database table growth rate (rows/day)

---

## Open Questions

1. **KOL Onboarding:** How will KOL IDs be assigned? Manual registration or auto-generated from Zalo user ID?
2. **Message Moderation:** Do you need admin approval before messages are broadcast, or auto-publish all KOL messages?
3. **Zalo Webhook Payload:** What exact fields does Zalo send? (Adjust request schema to match)
4. **Multi-Tenant:** Will you have multiple groups/channels, or single KOL feed for all users?

---

## Recommendation

**Start with Approach 1 (Simple Database + Socket.IO Push)**

**Why:**
- Meets all MVP requirements with minimal complexity
- Leverages existing infrastructure (Socket.IO, PostgreSQL)
- Achieves <200ms latency (6x faster than 1-3s target)
- Easy to extend with parsing, subscriptions, history API later
- Low risk, proven patterns

**Next Steps:**
1. Confirm Zalo webhook payload format
2. Generate API key and configure environment
3. Create database migration for `kol_messages` table
4. Implement REST endpoint + Socket.IO broadcast
5. Build React component for KOL feed
6. Test with mock Zalo webhook calls
7. Deploy and configure Zalo webhook URL

**Estimated Timeline:** 3.5 days (backend 2d, frontend 1d, deployment 0.5d)

---

## Appendix: Alternative Parsing Strategy (Future)

**Trading Signal Format (Observed):**
```
"Canh Buy XAU ET 13-15 SL: 09, Buy XAU entry 14-16 SL:10 1/2 vol, Sell XAU ET 31-33 SL:38"
```

**Extracted Structure:**
```json
{
  "signals": [
    {
      "action": "BUY",
      "symbol": "XAU",
      "entry": {"min": 13, "max": 15},
      "stop_loss": 9,
      "volume": "full"
    },
    {
      "action": "BUY",
      "symbol": "XAU",
      "entry": {"min": 14, "max": 16},
      "stop_loss": 10,
      "volume": "half"
    },
    {
      "action": "SELL",
      "symbol": "XAU",
      "entry": {"min": 31, "max": 33},
      "stop_loss": 38,
      "volume": "full"
    }
  ]
}
```

**Parser Implementation (Regex + NLP):**
- Use regex for structured parts (numbers, SL, TP)
- Use Claude/DeepSeek to extract intent from Vietnamese text
- Validation: Cross-check extracted values make sense (SL < entry for buy)

**Complexity:** Medium (2-3 days for robust parser)

**Defer to Phase 2.1** (post-MVP)

---

**Document Status:** Complete
**Next Action:** User approval → Create implementation plan
**Author:** Solution Brainstormer
**Review Date:** 2025-12-31
