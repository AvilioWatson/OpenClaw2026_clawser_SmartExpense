-- ==============================================================
-- Migration: V002__rename_category_to_categories
-- Description: Rename 'category' table to 'categories' for consistency
--              (plural naming convention)
-- Applied at: 2026-05-15 19:20:00 UTC
-- ==============================================================

-- ==============================================================
-- UP
-- ==============================================================

BEGIN;

-- Rename the table
ALTER TABLE category RENAME TO categories;

-- Rename foreign key constraint in transactions table
-- First, find the old constraint name
ALTER TABLE transactions
    RENAME CONSTRAINT transactions_category_id_fkey TO transactions_categories_id_fkey;

-- Update any indexes that reference the table
-- (PostgreSQL automatically updates index names when table is renamed)

COMMIT;

-- ==============================================================
-- DOWN (rollback)
-- Run this to revert the migration:
--   psql -h localhost -U postgres -d smart_expense -f V002__rollback.sql
-- ==============================================================
/*
BEGIN;

-- Rename the table back
ALTER TABLE categories RENAME TO category;

-- Rename foreign key constraint back
ALTER TABLE transactions
    RENAME CONSTRAINT transactions_categories_id_fkey TO transactions_category_id_fkey;

COMMIT;
*/
