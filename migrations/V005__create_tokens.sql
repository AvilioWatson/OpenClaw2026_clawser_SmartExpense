-- ==============================================================
-- Migration: V005__create_tokens
-- Description: Create tokens table for API token authentication
-- Applied at: 2026-05-15
-- ==============================================================

-- ==============================================================
-- UP
-- ==============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS tokens (
    telegram_id BIGINT        NOT NULL,
    token       VARCHAR(255)  NOT NULL,
    created_at  TIMESTAMPTZ   DEFAULT NOW() NOT NULL,
    CONSTRAINT pk_tokens PRIMARY KEY (token)
);

CREATE INDEX IF NOT EXISTS idx_tokens_telegram_id ON tokens(telegram_id);

COMMENT ON TABLE tokens IS 'API tokens for web dashboard authentication';
COMMENT ON COLUMN tokens.telegram_id IS 'Telegram user ID linked to this token';
COMMENT ON COLUMN tokens.token IS 'Secret token pasted by user at login';

COMMIT;

-- ==============================================================
-- DOWN (rollback)
-- ==============================================================
/*
BEGIN;

DROP INDEX IF EXISTS idx_tokens_telegram_id;
DROP TABLE IF EXISTS tokens;

COMMIT;
*/

-- Dev seed (run manually after migration):
-- INSERT INTO tokens (telegram_id, token) VALUES (123456789, 'dev-token-change-me');
-- UPDATE transactions SET telegram_id = 123456789 WHERE telegram_id IS NULL;
