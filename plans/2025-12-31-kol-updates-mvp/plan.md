# KOL Updates MVP - Implementation Plan

**Created:** 2025-12-31
**Status:** in-progress
**Estimated Duration:** 3.5 days
**Target:** Real-time KOL trading signals from Zalo messenger
**Last Updated:** 2025-12-31 10:15 UTC

---

## Overview

Implement real-time KOL (Key Opinion Leader) trading signal distribution system that receives messages via Zalo webhook and broadcasts to <100 concurrent users with <200ms latency.

**Brainstorm Report:** `docs/brainstorm-kol-updates-mvp-2025-12-31.md`

---

## Architecture Summary

```
Zalo Webhook
     ↓
POST /api/v1/kol/message (FastAPI)
     ↓
API Key Validation
     ↓
MD5 Deduplication Check
     ↓
PostgreSQL Insert (kol_messages table)
     ↓
Socket.IO Broadcast (kol:new_message)
     ↓
React Frontend (KOLUpdatesFeed component)
```

**Key Components:**
- Database: `kol_messages` table with hash-based deduplication
- REST API: FastAPI router with Bearer token auth
- Real-time: Socket.IO event broadcasting
- Frontend: React component with unread badge counter

---

## Implementation Phases

### Phase 1: Database Layer (0.5 days) - COMPLETE

**Status:** DONE
**Completion Date:** 2025-12-31
**Code Review Score:** 8.5/10 ✅

**Objective:** Create PostgreSQL schema for KOL messages with deduplication

**Tasks:**
1. **Create migration file: `app/database/migrations/006_kol_messages.sql`** ✅
   - Table: `kol_messages` (id, kol_id, kol_name, message_text, message_hash, zalo_message_id, received_at, created_at, metadata)
   - UNIQUE constraint on `message_hash`
   - Indexes: `idx_kol_messages_received_at`, `idx_kol_messages_kol_id`, `idx_kol_messages_hash`
   - Auto-update trigger for `updated_at` (reuse existing function)
   - Comments for documentation

2. **Run migration locally** ✅
   - Connect to PostgreSQL: `psql -U postgres -d ev_gamepad`
   - Execute: `\i app/database/migrations/006_kol_messages.sql`
   - Verify: `\d kol_messages`

**Acceptance Criteria:**
- [x] Migration file created following existing pattern (005_recommendation_outcomes.sql)
- [x] Table created with all columns + constraints
- [x] Indexes created for performance
- [x] No errors on migration execution

**Files Created:**
- ✅ `app/database/migrations/006_kol_messages.sql`
- ✅ `app/database/migrations/verify_006_kol_messages.sql` (verification script)
- ✅ `plans/2025-12-31-kol-updates-mvp/phase-1-testing-checklist.md` (testing checklist)

---

### Phase 2: Data Models (0.5 days)

**Objective:** Define Pydantic models for request/response validation

**Tasks:**
1. **Create `app/models/kol_models.py`**
   - `KOLMessageRequest`: Webhook request schema
     - Fields: kol_id, kol_name, message, timestamp, zalo_message_id, metadata
     - Validators: kol_id (alphanumeric + underscore, max 100), message (max 5000), timestamp (ISO 8601)

   - `KOLMessageResponse`: API response schema
     - Fields: success, message_id, deduplicated

   - `KOLMessage`: Internal model (matches DB schema)
     - Fields: id, kol_id, kol_name, message_text, message_hash, received_at, metadata

   - `KOLMessageBroadcast`: Socket.IO event payload
     - Fields: message_id, kol_id, kol_name, message, received_at, metadata

2. **Add to `app/models/__init__.py`**
   - Export: `KOLMessageRequest`, `KOLMessageResponse`, `KOLMessage`, `KOLMessageBroadcast`

**Acceptance Criteria:**
- [ ] All models defined with proper Pydantic validation
- [ ] Field constraints match database schema
- [ ] Models exported in __init__.py
- [ ] Type hints complete and accurate

**Files Created:**
- `app/models/kol_models.py`

**Files Modified:**
- `app/models/__init__.py`

---

### Phase 3: KOL Processor (0.75 days)

**Objective:** Implement business logic for KOL message processing

**Tasks:**
1. **Create `app/processors/kol_processor.py`**

   - `KOLProcessor` class with methods:
     - `__init__(db_pool_manager, sio)`: Constructor with dependencies
     - `calculate_message_hash(kol_id, timestamp, message)`: MD5 hash generation
     - `async def process_kol_message(request: KOLMessageRequest)`: Main processing logic
       - Calculate hash
       - Check for duplicate (query DB by hash)
       - If duplicate: return existing message_id with deduplicated=True
       - If new: INSERT into kol_messages table
       - Broadcast Socket.IO event `kol:new_message`
       - Return message_id with deduplicated=False
     - `async def _insert_message(...)`: Database insert helper
     - `async def _broadcast_message(message: KOLMessage)`: Socket.IO broadcast helper

2. **Error handling:**
   - Database connection errors → return 503 Service Unavailable
   - Validation errors → return 400 Bad Request
   - Socket.IO broadcast failures → log warning (don't fail request)

**Acceptance Criteria:**
- [ ] KOLProcessor class implements all methods
- [ ] Deduplication logic works correctly
- [ ] Socket.IO broadcast emits `kol:new_message` event
- [ ] Error handling covers all failure modes
- [ ] Async/await used properly throughout

**Files Created:**
- `app/processors/kol_processor.py`

---

### Phase 4: REST API Endpoint (0.75 days)

**Objective:** Create FastAPI endpoint for Zalo webhook with authentication

**Tasks:**
1. **Create `app/routers/kol_router.py`**

   - APIRouter setup:
     - Prefix: `/api/v1/kol`
     - Tags: `["kol"]`

   - Authentication dependency:
     - `async def verify_api_key(authorization: str = Header(...))`:
       - Parse `Bearer {token}` format
       - Compare with `config.KOL_WEBHOOK_API_KEY` (constant-time comparison using `secrets.compare_digest`)
       - Raise 401 Unauthorized if invalid

   - Endpoint: `POST /message`
     - Depends on: `verify_api_key`
     - Request: `KOLMessageRequest`
     - Response: `KOLMessageResponse`
     - Calls: `kol_processor.process_kol_message()`
     - Logging: Log all webhook requests with kol_id, message_id, deduplicated status

2. **Register router in `app/main.py`**
   - Import router
   - Include router in FastAPI app: `app.include_router(kol_router)`
   - Initialize `KOLProcessor` in lifespan
   - Inject dependencies into router

3. **Update `app/config.py`**
   - Add: `KOL_WEBHOOK_API_KEY: str = os.getenv('KOL_WEBHOOK_API_KEY', '')`
   - Add validation: Raise error if empty in production

**Acceptance Criteria:**
- [ ] POST /api/v1/kol/message endpoint created
- [ ] Bearer token authentication implemented
- [ ] Request validation via Pydantic models
- [ ] Proper error responses (401, 400, 503)
- [ ] All requests logged with structured logging

**Files Created:**
- `app/routers/kol_router.py`

**Files Modified:**
- `app/main.py` (register router + initialize processor)
- `app/config.py` (add KOL_WEBHOOK_API_KEY)

---

### Phase 5: Frontend - TypeScript Types (0.25 days)

**Objective:** Define TypeScript interfaces for KOL messages

**Tasks:**
1. **Create `src/types/kol.ts`**

   - Interfaces:
     ```typescript
     export interface KOLMessage {
       message_id: string;
       kol_id: string;
       kol_name: string;
       message: string;
       received_at: string;  // ISO 8601
       metadata?: Record<string, any>;
     }

     export interface KOLMessageRequest {
       kol_id: string;
       kol_name: string;
       message: string;
       timestamp: string;
       zalo_message_id?: string;
       metadata?: Record<string, any>;
     }
     ```

2. **Export from `src/types/index.ts`**
   - Add exports for KOLMessage, KOLMessageRequest

**Acceptance Criteria:**
- [ ] TypeScript interfaces match backend Pydantic models
- [ ] Types exported properly
- [ ] No type errors in IDE

**Files Created:**
- `src/types/kol.ts`

**Files Modified:**
- `src/types/index.ts`

---

### Phase 6: Frontend - KOL Feed Component (0.75 days)

**Objective:** Build React component to display real-time KOL messages

**Tasks:**
1. **Create `src/components/KOLUpdatesFeed.tsx`**

   - Props: None (uses global Socket.IO context)

   - State:
     - `messages: KOLMessage[]` - Message list (newest first)
     - `unreadCount: number` - Unread messages counter
     - `isExpanded: boolean` - Minimize/expand feed

   - Socket.IO subscription:
     - Subscribe to `kol:new_message` on mount
     - Prepend new message to list: `setMessages(prev => [msg, ...prev])`
     - Increment unread count
     - Cleanup on unmount

   - Features:
     - Message list with reverse chronological order
     - Each message shows: KOL name, relative timestamp ("2 min ago"), message text
     - Unread badge indicator (e.g., "🔴 3 new")
     - Click badge to mark all as read
     - Auto-scroll to top on new message
     - Minimize/expand toggle
     - Max 50 messages (trim old messages from state)

   - Styling:
     - Tailwind CSS classes
     - Card layout with shadow
     - Responsive (mobile-friendly)
     - Fixed height with scrollable content

2. **Add to main dashboard/portfolio page**
   - Import `KOLUpdatesFeed`
   - Place in sidebar or dedicated section
   - Ensure Socket.IO context is available

**Acceptance Criteria:**
- [ ] Component renders without errors
- [ ] Socket.IO event listener works
- [ ] Messages display in correct order
- [ ] Unread badge updates correctly
- [ ] Responsive layout on mobile
- [ ] Auto-scroll behavior works

**Files Created:**
- `src/components/KOLUpdatesFeed.tsx`

**Files Modified:**
- Main dashboard/portfolio page (integration)

---

### Phase 7: Testing (0.5 days)

**Objective:** Verify all functionality with automated tests

**Tasks:**
1. **Backend Unit Tests: `tests/test_kol_processor.py`**

   - Test `calculate_message_hash()`:
     - Same inputs → same hash
     - Different inputs → different hash

   - Test `process_kol_message()`:
     - New message → insert + broadcast
     - Duplicate message → return existing ID
     - Invalid input → validation error

   - Mock database and Socket.IO

2. **Backend Integration Test: `tests/test_kol_api.py`**

   - Test POST /api/v1/kol/message:
     - Valid request + auth → 200 OK
     - Invalid auth → 401 Unauthorized
     - Invalid payload → 400 Bad Request
     - Duplicate message → 200 OK with deduplicated=true

   - Use TestClient from FastAPI

3. **Frontend Component Test: `src/components/__tests__/KOLUpdatesFeed.test.tsx`**

   - Test rendering
   - Test Socket.IO event handling (mock socket)
   - Test unread count updates
   - Test mark as read functionality

   - Use React Testing Library + Jest

4. **Manual Testing Checklist:**
   - [ ] Generate API key: `openssl rand -base64 32`
   - [ ] Set environment variable: `KOL_WEBHOOK_API_KEY=<key>`
   - [ ] Start backend server
   - [ ] Send test webhook via curl:
     ```bash
     curl -X POST http://localhost:8686/api/v1/kol/message \
       -H "Authorization: Bearer <API_KEY>" \
       -H "Content-Type: application/json" \
       -d '{
         "kol_id": "test_kol",
         "kol_name": "Test KOL",
         "message": "Buy XAU 2650-2655 SL:2645",
         "timestamp": "2025-12-31T10:00:00Z"
       }'
     ```
   - [ ] Verify message appears in frontend feed
   - [ ] Send same message again → deduplicated
   - [ ] Open multiple browser tabs → all receive message
   - [ ] Check PostgreSQL: `SELECT * FROM kol_messages;`

**Acceptance Criteria:**
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Manual test checklist complete
- [ ] Code coverage >80% for new code

**Files Created:**
- `tests/test_kol_processor.py`
- `tests/test_kol_api.py`
- `src/components/__tests__/KOLUpdatesFeed.test.tsx`

---

### Phase 8: Documentation & Deployment (0.5 days)

**Objective:** Document API and deploy to production

**Tasks:**
1. **Update API Documentation**

   - Add to `docs/advisor-api-specification.md`:
     - Endpoint: `POST /api/v1/kol/message`
     - Authentication: Bearer token
     - Request/response schemas
     - Error codes
     - Example curl command

   - Add Socket.IO event: `kol:new_message`
     - Payload structure
     - Broadcast strategy (all clients)

2. **Update Codebase Summary**

   - Update `docs/codebase-summary.md`:
     - Add KOL Updates section
     - Document new files
     - Update data flow diagram

3. **Create Environment Setup Guide**

   - Add to `docs/deployment-guide.md` (or create if missing):
     - Generate API key: `openssl rand -base64 32`
     - Set `KOL_WEBHOOK_API_KEY` environment variable
     - Run database migration
     - Configure Zalo webhook URL
     - Monitoring: Track latency, deduplication rate

4. **Deployment Checklist:**
   - [ ] Database migration applied to production
   - [ ] Environment variables configured
   - [ ] API key generated and secured
   - [ ] Zalo webhook URL configured
   - [ ] Logging enabled for webhook requests
   - [ ] Monitoring alerts configured

**Acceptance Criteria:**
- [ ] API documentation complete
- [ ] Codebase summary updated
- [ ] Deployment guide created
- [ ] All deployment checklist items completed

**Files Modified:**
- `docs/advisor-api-specification.md`
- `docs/codebase-summary.md`
- `docs/deployment-guide.md` (create if needed)

---

## File Structure Summary

### New Files (10 total)
```
backend/app/
├── database/migrations/
│   └── 006_kol_messages.sql                    # Database schema
├── models/
│   └── kol_models.py                           # Pydantic models
├── processors/
│   └── kol_processor.py                        # Business logic
└── routers/
    └── kol_router.py                           # REST API endpoint

src/
├── types/
│   └── kol.ts                                  # TypeScript interfaces
└── components/
    └── KOLUpdatesFeed.tsx                      # React component

tests/
├── test_kol_processor.py                       # Backend unit tests
└── test_kol_api.py                             # Backend integration tests

src/components/__tests__/
└── KOLUpdatesFeed.test.tsx                     # Frontend tests

docs/
└── (updates to existing docs)
```

### Modified Files (5 total)
- `app/main.py` - Register router + initialize processor
- `app/config.py` - Add KOL_WEBHOOK_API_KEY
- `app/models/__init__.py` - Export KOL models
- `src/types/index.ts` - Export KOL types
- Main dashboard page - Integrate KOLUpdatesFeed component

---

## Dependencies

**No new dependencies required** - uses existing stack:
- FastAPI (REST API)
- PostgreSQL (database)
- Socket.IO (real-time)
- React + TypeScript (frontend)
- Pydantic (validation)

**Existing infrastructure leveraged:**
- `DatabasePoolManager` (PostgreSQL connection pooling)
- `sio` singleton (Socket.IO instance)
- Socket.IO context provider (frontend)
- Existing migration pattern
- Existing Pydantic model pattern

---

## Performance Targets

**Latency Breakdown:**
- Webhook → API: ~100ms (network)
- Authentication: ~1ms (hash comparison)
- Deduplication: ~5ms (indexed query)
- DB Insert: ~10ms (single row)
- Socket.IO Broadcast: ~5ms (100 clients)
- React Render: ~10ms
- **TOTAL: ~131ms** ✅ (target: <3s)

**Scalability:**
- Supports 1000+ concurrent users (tested Socket.IO capacity)
- PostgreSQL handles 10,000+ writes/sec
- Current load: ~50 messages/hour = 0.014/sec

---

## Security Checklist

- [ ] API key stored in environment variable (not in code)
- [ ] API key never committed to git (.env in .gitignore)
- [ ] Constant-time comparison for auth (prevents timing attacks)
- [ ] Input validation via Pydantic (prevents injection)
- [ ] Message length limit (5000 chars max)
- [ ] Frontend displays as plain text (prevents XSS)
- [ ] Rate limiting considered for future (100 req/min per KOL)

---

## Rollback Plan

If deployment fails:
1. **Database:** No data loss - table is append-only
2. **Backend:** Revert to previous commit - router not registered = no breaking changes
3. **Frontend:** Component can be hidden via feature flag if needed

**Rollback steps:**
```bash
# Database (if needed)
DROP TABLE kol_messages CASCADE;

# Backend
git revert <commit-hash>

# Frontend
# Remove/comment KOLUpdatesFeed import in dashboard
```

---

## Future Enhancements (Out of Scope for MVP)

**Phase 2.1: Message Parsing**
- Parse trading signals (BUY/SELL, symbol, entry, SL, TP)
- Store structured data in JSONB column
- Display formatted cards

**Phase 2.2: User Subscriptions**
- Room-based Socket.IO (subscribe to specific KOLs)
- Per-user notification preferences

**Phase 2.3: Message History API**
- `GET /api/v1/kol/messages?kol_id=...&limit=50`
- Pagination support
- Fetch missed messages on reconnect

**Phase 2.4: Admin Dashboard**
- Manual message posting
- Edit/delete messages
- KOL management

**Phase 2.5: Analytics & Performance Tracking**
- Track KOL signal accuracy
- Integration with Phase 5.2 accuracy tracking
- Popular signals dashboard

---

## Success Metrics

**MVP Acceptance Criteria:**
- [ ] Webhook endpoint accepts Zalo messages
- [ ] Messages appear in UI within 3 seconds (target: <200ms)
- [ ] Zero duplicate messages displayed
- [ ] Supports 100 concurrent users without lag
- [ ] Zero message loss (all webhooks persisted)

**Monitoring:**
- Message delivery latency (p50, p95, p99)
- Deduplication rate (expect <5%)
- Socket.IO connection stability
- Database table growth rate

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **Zalo webhook downtime** | Manual admin interface (Phase 2.4) |
| **Database growth** | Implement 90-day retention policy (future) |
| **API key leak** | Key rotation process + rate limiting |
| **Socket.IO drops** | Client auto-reconnect (already implemented) + history API (Phase 2.3) |

---

## Timeline

**Day 1: Backend Foundation**
- Phase 1: Database Layer (0.5d)
- Phase 2: Data Models (0.5d)
- Phase 3: KOL Processor (0.75d)
**Total:** 1.75 days

**Day 2: API & Frontend**
- Phase 4: REST API Endpoint (0.75d)
- Phase 5: TypeScript Types (0.25d)
- Phase 6: KOL Feed Component (0.75d)
**Total:** 1.75 days

**Day 3: Testing & Deployment**
- Phase 7: Testing (0.5d)
- Phase 8: Documentation & Deployment (0.5d)
**Total:** 1 day

**GRAND TOTAL: 3.5 days**

---

## Open Questions

Before implementation, clarify:
1. **Zalo webhook payload:** What exact JSON fields does Zalo send? (Adjust KOLMessageRequest schema)
2. **KOL onboarding:** How are KOL IDs assigned? Manual registration or auto-generated?
3. **Message moderation:** Auto-publish all messages or require admin approval?
4. **Multiple feeds:** Single feed for all KOLs, or separate feeds per KOL group?

---

## Implementation Order

Execute phases sequentially in order (1→8) for clean integration testing at each step.

**Start with:** Phase 1 (Database Layer)
**End with:** Phase 8 (Documentation & Deployment)

---

**Plan Status:** Ready for implementation
**Next Action:** Begin Phase 1 - Create database migration
**Estimated Completion:** 2026-01-03 (assuming start 2025-12-31)
