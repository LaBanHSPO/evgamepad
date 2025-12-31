# Phase 1: Database Layer - Testing Checklist

**Phase:** Database Layer
**Date:** 2025-12-31
**Status:** Ready for manual testing

---

## Prerequisites

- PostgreSQL installed and running
- Database `ev_gamepad` exists
- User `postgres` has access

---

## Manual Testing Steps

### 1. Run Migration

```bash
cd backend
psql -h localhost -U postgres -d ev_gamepad -f app/database/migrations/006_kol_messages.sql
```

**Expected Output:**
```
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE TRIGGER
COMMENT
COMMENT
COMMENT
```

**✓ Success:** No errors, all CREATE statements executed

---

### 2. Verify Table Schema

```bash
psql -h localhost -U postgres -d ev_gamepad -c "\d kol_messages"
```

**Expected Output:**
```
                                       Table "public.kol_messages"
     Column      |           Type           | Collation | Nullable |      Default
-----------------+--------------------------+-----------+----------+-------------------
 id              | uuid                     |           | not null | gen_random_uuid()
 kol_id          | character varying(100)   |           | not null |
 kol_name        | character varying(200)   |           | not null |
 message_text    | text                     |           | not null |
 message_hash    | character varying(32)    |           | not null |
 zalo_message_id | character varying(255)   |           |          |
 received_at     | timestamp with time zone |           | not null | now()
 created_at      | timestamp with time zone |           | not null | now()
 updated_at      | timestamp with time zone |           | not null | now()
 metadata        | jsonb                    |           |          |

Indexes:
    "kol_messages_pkey" PRIMARY KEY, btree (id)
    "kol_messages_message_hash_key" UNIQUE CONSTRAINT, btree (message_hash)
    "idx_kol_messages_hash" btree (message_hash)
    "idx_kol_messages_kol_id" btree (kol_id, received_at DESC)
    "idx_kol_messages_received_at" btree (received_at DESC)

Triggers:
    update_kol_messages_updated_at BEFORE UPDATE ON kol_messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
```

**✓ Verify:**
- All 9 columns present with correct types
- PRIMARY KEY on `id`
- UNIQUE constraint on `message_hash`
- 3 performance indexes created
- Trigger `update_kol_messages_updated_at` exists

---

### 3. Run Verification Script

```bash
psql -h localhost -U postgres -d ev_gamepad -f app/database/migrations/verify_006_kol_messages.sql
```

**Expected Output:**
- `table_exists = true`
- 9 columns listed
- 1 UNIQUE constraint
- 4 indexes (pkey + 3 custom)
- 1 trigger
- Table comment present

---

### 4. Test Insert (Deduplication)

```sql
-- Insert first message
INSERT INTO kol_messages (kol_id, kol_name, message_text, message_hash)
VALUES ('test_kol', 'Test KOL', 'Buy XAU 2650', 'abc123');

-- Verify insert
SELECT id, kol_id, kol_name, message_text, message_hash FROM kol_messages;

-- Try duplicate insert (should fail with UNIQUE constraint violation)
INSERT INTO kol_messages (kol_id, kol_name, message_text, message_hash)
VALUES ('test_kol', 'Test KOL', 'Buy XAU 2650', 'abc123');
```

**Expected Output:**
- First INSERT: Success (1 row inserted)
- SELECT: Shows 1 row with all fields populated
- Second INSERT: ERROR - duplicate key value violates unique constraint "kol_messages_message_hash_key"

**✓ Success:** Deduplication constraint working correctly

---

### 5. Test Auto-Update Trigger

```sql
-- Update a message
UPDATE kol_messages SET kol_name = 'Updated KOL' WHERE kol_id = 'test_kol';

-- Check updated_at changed
SELECT kol_id, kol_name, created_at, updated_at FROM kol_messages WHERE kol_id = 'test_kol';
```

**Expected Output:**
- `updated_at` timestamp is newer than `created_at`
- `kol_name` changed to 'Updated KOL'

**✓ Success:** Trigger auto-updates `updated_at` column

---

### 6. Test Index Performance

```sql
-- Explain query using index
EXPLAIN SELECT * FROM kol_messages WHERE message_hash = 'abc123';

-- Should use idx_kol_messages_hash
```

**Expected Output:**
```
Index Scan using idx_kol_messages_hash on kol_messages
```

**✓ Success:** Query uses hash index

---

### 7. Cleanup Test Data

```sql
DELETE FROM kol_messages WHERE kol_id = 'test_kol';
```

---

## Acceptance Criteria

- [x] Migration file created following existing pattern (005_recommendation_outcomes.sql)
- [ ] Table created with all columns + constraints
- [ ] Indexes created for performance
- [ ] No errors on migration execution
- [ ] Deduplication constraint prevents duplicate messages
- [ ] Auto-update trigger updates `updated_at` on row modification
- [ ] Indexes used by query planner

---

## Files Created

- `app/database/migrations/006_kol_messages.sql` - Migration script
- `app/database/migrations/verify_006_kol_messages.sql` - Verification queries

---

## Next Phase

After all tests pass, proceed to **Phase 2: Data Models** (Pydantic models for request/response validation)
