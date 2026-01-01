-- Verification script for 006_kol_messages migration
-- Run this after executing 006_kol_messages.sql

-- 1. Verify table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'kol_messages'
) AS table_exists;

-- 2. Verify columns
SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns
WHERE table_name = 'kol_messages'
ORDER BY ordinal_position;

-- 3. Verify UNIQUE constraint on message_hash
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'kol_messages'
AND constraint_type = 'UNIQUE';

-- 4. Verify indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'kol_messages'
ORDER BY indexname;

-- 5. Verify trigger exists
SELECT trigger_name, event_manipulation, action_statement
FROM information_schema.triggers
WHERE event_object_table = 'kol_messages';

-- 6. Verify comments
SELECT obj_description('kol_messages'::regclass) AS table_comment;

-- Expected results:
-- ✓ table_exists = true
-- ✓ 9 columns: id (uuid), kol_id (varchar 100), kol_name (varchar 200), message_text (text),
--              message_hash (varchar 32), zalo_message_id (varchar 255),
--              received_at, created_at, updated_at (timestamptz), metadata (jsonb)
-- ✓ 1 UNIQUE constraint on message_hash
-- ✓ 4 indexes: kol_messages_pkey, idx_kol_messages_received_at, idx_kol_messages_kol_id, idx_kol_messages_hash
-- ✓ 1 trigger: update_kol_messages_updated_at
-- ✓ Table comment: 'Stores KOL trading signals received via Zalo webhook with deduplication'
