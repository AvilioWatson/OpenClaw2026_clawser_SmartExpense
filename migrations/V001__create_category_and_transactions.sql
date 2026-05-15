-- ==============================================================
-- Migration: V001__create_category_and_transactions
-- Description: Create smart_expense schema with category &
--              transactions tables, indexes, triggers, and seed data
-- Applied at: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
-- ==============================================================

-- ==============================================================
-- UP
-- ==============================================================

BEGIN;

-- -----------------------------------------------------------------
-- 1. Extension
-- -----------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------
-- 2. Trigger function (shared)
-- -----------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------
-- 3. Table: category
-- -----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS category (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name         VARCHAR(100) NOT NULL,
    type         VARCHAR(20)  NOT NULL CHECK (type IN ('income', 'expense')),
    icon         VARCHAR(50),
    color        VARCHAR(7),                                       -- hex colour e.g. #FF5733
    description  TEXT,
    is_active    BOOLEAN      DEFAULT TRUE NOT NULL,
    display_order INT         DEFAULT 0,
    created_at   TIMESTAMPTZ  DEFAULT NOW() NOT NULL,
    updated_at   TIMESTAMPTZ  DEFAULT NOW() NOT NULL,

    CONSTRAINT uq_category_name_type UNIQUE (name, type)
);

CREATE INDEX idx_category_type   ON category(type);
CREATE INDEX idx_category_active ON category(is_active);
CREATE INDEX idx_category_order  ON category(display_order);

CREATE TRIGGER trigger_category_updated_at
    BEFORE UPDATE ON category
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------------------------
-- 4. Table: transactions
-- -----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id      UUID        NOT NULL REFERENCES category(id) ON DELETE RESTRICT,
    amount           DECIMAL(15,2) NOT NULL CHECK (amount > 0),
    type             VARCHAR(10) NOT NULL CHECK (type IN ('income', 'expense')),
    description      VARCHAR(255),
    transaction_date DATE        NOT NULL DEFAULT CURRENT_DATE,
    payment_method   VARCHAR(50) CHECK (payment_method IN ('cash', 'card', 'transfer', 'e-wallet', 'other')),
    merchant         VARCHAR(100),
    notes            TEXT,
    is_recurring     BOOLEAN     DEFAULT FALSE NOT NULL,
    recurring_period VARCHAR(20) CHECK (recurring_period IN ('daily', 'weekly', 'monthly', 'yearly')),
    tags             TEXT[],
    created_at       TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at       TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_transactions_date       ON transactions(transaction_date DESC);
CREATE INDEX idx_transactions_category   ON transactions(category_id);
CREATE INDEX idx_transactions_type       ON transactions(type);
CREATE INDEX idx_transactions_date_type  ON transactions(transaction_date DESC, type);
CREATE INDEX idx_transactions_merchant   ON transactions(merchant);
CREATE INDEX idx_transactions_tags       ON transactions USING GIN(tags);

CREATE TRIGGER trigger_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------------------------
-- 5. Seed data: default categories
-- -----------------------------------------------------------------
INSERT INTO category (name, type, icon, color, description, display_order) VALUES
    -- Income
    ('Salary',         'income',  '💰', '#2ecc71', 'Monthly salary / wages',                         1),
    ('Freelance',      'income',  '💻', '#27ae60', 'Freelance project income',                       2),
    ('Investment',     'income',  '📈', '#27ae60', 'Dividends, interest, capital gains',             3),
    ('Gift',           'income',  '🎁', '#27ae60', 'Received gifts or bonuses',                      4),
    ('Other Income',   'income',  '💵', '#27ae60', 'Miscellaneous income',                           5),
    -- Expense
    ('Food & Drinks',  'expense', '🍽️', '#e74c3c', 'Meals, groceries, beverages',                   10),
    ('Transportation', 'expense', '🚗', '#e67e22', 'Fuel, public transport, ride-hailing',           11),
    ('Shopping',       'expense', '🛍️', '#f39c12', 'Clothing, electronics, accessories',             12),
    ('Entertainment',  'expense', '🎬', '#9b59b6', 'Movies, games, streaming subscriptions',         13),
    ('Bills & Utilities','expense','💡', '#3498db', 'Electricity, water, internet, phone',           14),
    ('Health',         'expense', '💊', '#1abc9c', 'Medical, pharmacy, fitness',                     15),
    ('Education',      'expense', '📚', '#2980b9', 'Courses, books, training',                       16),
    ('Housing',        'expense', '🏠', '#34495e', 'Rent, mortgage, maintenance, property tax',      17),
    ('Travel',         'expense', '✈️', '#16a085', 'Flights, hotels, vacations',                     18),
    ('Other Expense',  'expense', '📝', '#95a5a6', 'Miscellaneous expenses',                         19)
ON CONFLICT (name, type) DO NOTHING;

COMMIT;

-- ==============================================================
-- DOWN (rollback)
-- Run this to revert the migration:
--   psql -h localhost -U postgres -d smart_expense -c "\i V001__rollback.sql"
-- ==============================================================
/*
BEGIN;

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS category;
DROP FUNCTION IF EXISTS update_updated_at_column();
-- Note: uuid-ossp extension is left in place to avoid affecting
-- other tables that may depend on it.

COMMIT;
*/
