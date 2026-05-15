-- ==============================================================
-- Migration: V003__add_llm_comment_to_transactions
-- Description: Add llm_comment column to transactions table
--              for storing AI financial advisor insights
-- Applied at: 2026-05-15 19:25:00 UTC
-- ==============================================================

-- ==============================================================
-- UP
-- ==============================================================

BEGIN;

-- Add llm_comment column to transactions
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS llm_comment TEXT;

-- Add index for faster filtering on llm_comment (non-null comments)
CREATE INDEX IF NOT EXISTS idx_transactions_llm_comment
ON transactions(id) WHERE llm_comment IS NOT NULL;

-- Add column to track when comment was generated
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS llm_comment_at TIMESTAMPTZ;

COMMIT;

-- ==============================================================
-- DOWN (rollback)
-- ==============================================================
/*
BEGIN;

DROP INDEX IF EXISTS idx_transactions_llm_comment;

ALTER TABLE transactions
DROP COLUMN IF EXISTS llm_comment;

ALTER TABLE transactions
DROP COLUMN IF EXISTS llm_comment_at;

COMMIT;
*/
