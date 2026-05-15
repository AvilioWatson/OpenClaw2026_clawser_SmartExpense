-- ==============================================================
-- Migration: V004__add_telegram_id_to_transactions
-- Description: Add telegram_id column to identify user ownership
--              for multi-user support
-- Applied at: 2026-05-15 19:30:00 UTC
-- ==============================================================

-- ==============================================================
-- UP
-- ==============================================================

BEGIN;

-- Add telegram_id column to transactions
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS telegram_id BIGINT;

-- Add index for faster filtering by user
CREATE INDEX IF NOT EXISTS idx_transactions_telegram_id
ON transactions(telegram_id) WHERE telegram_id IS NOT NULL;

-- Add foreign key constraint (optional - comment out if you have a users table)
-- ALTER TABLE transactions
-- ADD CONSTRAINT fk_transactions_telegram_user
-- FOREIGN KEY (telegram_id) REFERENCES users(id) ON DELETE SET NULL;

-- Add comment to column
COMMENT ON COLUMN transactions.telegram_id IS 'Telegram user ID for multi-user support';

COMMIT;

-- ==============================================================
-- DOWN (rollback)
-- ==============================================================
/*
BEGIN;

DROP INDEX IF EXISTS idx_transactions_telegram_id;

ALTER TABLE transactions
DROP COLUMN IF EXISTS telegram_id;

COMMIT;
*/
