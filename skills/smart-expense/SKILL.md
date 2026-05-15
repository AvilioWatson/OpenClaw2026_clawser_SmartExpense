---
name: smart-expense
description: "Use when managing a Smart Expense PostgreSQL database — CRUD transactions, categories, reports, and budget tracking. Covers connection, queries, and best practices."
version: 1.3.0
author: zuzu
license: MIT
metadata:
  hermes:
    tags: [finance, expense-tracking, postgresql, database, smart-expense, receipt-parsing, authentication, token, login-token]
    related_skills: []
---

# Smart Expense — Hermes Agent Skill

Manage your personal expense tracking database (`smart_expense`) on local PostgreSQL. This skill covers connection setup, CRUD operations for transactions & categories, and reporting queries.

---

## Overview

The `smart_expense` database tracks income & expense transactions organized by categories. It runs on **PostgreSQL 17** via Docker/OrbStack on macOS. The schema uses UUID primary keys, foreign key constraints, check constraints, GIN indexes on tags, and auto-updating timestamps.

---

## When to Use

- User sends **`/login-token`** → generate a new auth token and return it immediately
- User asks to **add / view / edit / delete** a transaction or category
- User wants a **spending report** (monthly, by category, by merchant)
- User wants to **manage categories** (add, rename, archive)
- User wants to **export data** or analyze spending patterns
- User asks about **database schema** or **connection details**

> **Don't use for:** general PostgreSQL administration unrelated to smart_expense.

---

## `/login-token` Handler

When the user sends the slash command `/login-token`, generate a **new** cryptographically secure token and return it immediately.

### Steps

1. **Determine the Telegram ID** from the conversation context (available in message metadata on Telegram gateway). For this user (zuzu), the Telegram ID is `552378634`.

2. **Run** the token generation script:
   ```
   python3 ~/.hermes/skills/productivity/smart-expense/scripts/generate_token.py <telegram_id>
   ```

3. **Capture the output** and return the token to the user.

4. **Bilingual response**: respond in both English and Indonesian when returning the token.

### Response Template

```
🔑 Token baru berhasil dibuat!

Token     : `{token}`
User ID   : {telegram_id}
Created   : {timestamp}

📌 Gunakan untuk autentikasi API:
   Authorization: Bearer {token}
```

### Important Rules

- **Always generate a NEW token each time** — never reuse an existing one
- **Don't list existing tokens** — only return the newly generated one
- **Token is stored** in the `tokens` table automatically by the script

---

## Database Connection

```bash
# Connection string
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense

# One-shot query
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "SELECT * FROM categories;"

# Execute SQL file
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -f migrations/V002__something.sql
```

### Connection Details

| Key | Value |
|-----|-------|
| Host | `localhost` |
| Port | `5432` |
| User | `postgres` |
| Password | `pg123` |
| Database | `smart_expense` |

> ⚠️ PostgreSQL runs via Docker/OrbStack (`gvproxy`), not natively on macOS. Always use `-h localhost` (TCP), not the default Unix socket.

### Database Path

Migrations live at:
```
/Users/apple/projects/smart-expense/migrations/
```

---

## Schema Reference

### Table: `categories`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | Auto-generated via uuid-ossp |
| name | VARCHAR(100) | Category name |
| type | VARCHAR(20) | `'income'` or `'expense'` |
| icon | VARCHAR(50) | Emoji icon |
| color | VARCHAR(7) | Hex colour (e.g. `#e74c3c`) |
| description | TEXT | Optional |
| is_active | BOOLEAN | Default `TRUE` |
| display_order | INT | Sort order |
| created_at | TIMESTAMPTZ | Auto-set |
| updated_at | TIMESTAMPTZ | Auto-updated |

**Unique:** `(name, type)` — no duplicate category name for the same type.

### Table: `transactions`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | Auto-generated |
| category_id | UUID (FK → category) | `ON DELETE RESTRICT` |
| amount | DECIMAL(15,2) | Must be > 0 |
| type | VARCHAR(10) | `'income'` or `'expense'` |
| description | VARCHAR(255) | Short description |
| transaction_date | DATE | Defaults to today |
| payment_method | VARCHAR(50) | `cash` / `card` / `transfer` / `e-wallet` / `other` |
| merchant | VARCHAR(100) | Merchant name |
| notes | TEXT | Long notes |
| is_recurring | BOOLEAN | Default `FALSE` |
| recurring_period | VARCHAR(20) | `daily` / `weekly` / `monthly` / `yearly` |
| tags | TEXT[] | PostgreSQL array |
| created_at | TIMESTAMPTZ | Auto-set |
| updated_at | TIMESTAMPTZ | Auto-updated |

### Default Categories

**Income (5):** Salary, Freelance, Investment, Gift, Other Income
**Expense (10):** Food & Drinks, Transportation, Shopping, Entertainment, Bills & Utilities, Health, Education, Housing, Travel, Other Expense

### Table: `tokens`

| Column | Type | Notes |
|--------|------|-------|
| telegram_id | BIGINT | Telegram user ID (not null) |
| token | VARCHAR(255) | Authentication token (PK, not null) |
| created_at | TIMESTAMPTZ | Auto-set via default `now()` |

**PK:** `token` (unique token string)
**Index:** `idx_tokens_telegram_id` on `telegram_id`

---

## Authentication Token Management

The `tokens` table stores API authentication tokens linked to Telegram user IDs. Each token is a cryptographically secure random string used for Bearer token authentication.

### Generate a Token

Use the bundled script to generate and insert a token in one step:

```bash
# Generate a 32-char token for your Telegram ID (default: 552378634)
python3 ~/.hermes/skills/productivity/smart-expense/scripts/generate_token.py

# Generate for a specific Telegram ID
python3 ~/.hermes/skills/productivity/smart-expense/scripts/generate_token.py 123456789

# Custom token length (64 chars)
python3 ~/.hermes/skills/productivity/smart-expense/scripts/generate_token.py 123456789 --length 64

# Quiet mode — just print the token (useful for scripts)
python3 ~/.hermes/skills/productivity/smart-expense/scripts/generate_token.py --quiet
```

**Sample output:**
```
✅ Token generated and saved!
   Telegram ID : 552378634
   Token       : aB3xK9mN2pQ5rT7vW1yZ4cE6fH8jL0sD
   Length      : 32 chars
   Created at  : 2026-05-15 19:30:00 UTC

🔐 Use this token for API authentication:
   Authorization: Bearer aB3xK9mN2pQ5rT7vW1yZ4cE6fH8jL0sD
```

### Manual SQL Approach

```bash
# Generate a 32-char random token and insert
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
INSERT INTO tokens (telegram_id, token)
VALUES (
  552378634,
  encode(gen_random_bytes(24), 'hex')
);
"

# List all tokens
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
SELECT telegram_id, LEFT(token, 16) || '...' AS token_preview,
       created_at
FROM tokens
ORDER BY created_at DESC;
"

# Verify a token exists
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -tAc "
SELECT telegram_id FROM tokens
WHERE token = 'your-token-here';
"

# Delete a token (revoke access)
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
DELETE FROM tokens WHERE token = 'your-token-here';
"
```

### Security Notes

- **Minimum token length:** 16 characters (script enforces this)
- **Maximum token length:** 128 characters (script enforces this)
- **Default length:** 32 characters (128 bits of entropy — sufficient for most use cases)
- **Token format:** Alphanumeric (`[a-zA-Z0-9]+`) — URL-safe, no special chars
- **Uniqueness:** `token` is the primary key; collisions are rejected by the DB
- **Revocation:** Delete the row from `tokens` to invalidate a token

### Reference

See [`references/token-authentication.md`](references/token-authentication.md) for script internals, manual SQL equivalents, exit codes, and scripting patterns.

---

## Common Queries & Operations

For detailed JSON schema and examples, see [`references/receipt-json-schema.md`](references/receipt-json-schema.md).

### Transactions — CRUD

**Add a transaction:**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
INSERT INTO transactions (category_id, amount, type, description, transaction_date, payment_method, merchant, tags)
VALUES (
  (SELECT id FROM categories WHERE name = 'Food & Drinks' LIMIT 1),
  150000.00,
  'expense',
  'Lunch at Sederhana',
  CURRENT_DATE,
  'e-wallet',
  'Sederhana Restaurant',
  ARRAY['lunch', 'padang']
);"
```

**View recent transactions:**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
SELECT t.transaction_date, t.amount, t.type, c.name AS category, 
       t.description, t.payment_method, t.merchant
FROM transactions t
JOIN categories c ON c.id = t.category_id
ORDER BY t.transaction_date DESC, t.created_at DESC
LIMIT 20;"
```

**View transactions for a specific month:**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
SELECT t.transaction_date, t.amount, c.name AS category, 
       t.description, t.merchant
FROM transactions t
JOIN categories c ON c.id = t.category_id
WHERE t.transaction_date >= '2025-01-01'
  AND t.transaction_date < '2025-02-01'
  AND t.type = 'expense'
ORDER BY t.transaction_date DESC;"
```

**Update a transaction:**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
UPDATE transactions 
SET amount = 180000.00, notes = 'Updated: added tip'
WHERE id = 'some-uuid-here';"
```

**Delete a transaction:**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
DELETE FROM transactions WHERE id = 'some-uuid-here';"
```

### Categories — CRUD

**Add a category:**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
INSERT INTO categories (name, type, icon, color, description, display_order)
VALUES ('Pet Supplies', 'expense', '🐾', '#e67e22', 'Pet food, vet, accessories', 
  (SELECT COALESCE(MAX(display_order), 0) + 1 FROM categories WHERE type = 'expense'));"
```

**Rename / edit category:**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
UPDATE category SET name = 'Pets', icon = '🐶' WHERE name = 'Pet Supplies';"
```

**Archive a category (soft-delete):**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
UPDATE category SET is_active = FALSE WHERE name = 'Travel' AND type = 'expense';"
```

### Reports & Analysis

**Monthly spending summary:**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
SELECT TO_CHAR(transaction_date, 'YYYY-MM') AS month,
       SUM(amount) AS total_spent,
       COUNT(*) AS transaction_count
FROM transactions
WHERE type = 'expense'
GROUP BY TO_CHAR(transaction_date, 'YYYY-MM')
ORDER BY month DESC
LIMIT 12;"
```

**Spending by category (current month):**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
SELECT c.name AS category,
       c.icon,
       COUNT(*) AS tx_count,
       SUM(t.amount) AS total,
       ROUND(100.0 * SUM(t.amount) / (SELECT SUM(amount) FROM transactions 
               WHERE type = 'expense' 
                 AND DATE_TRUNC('month', transaction_date) = DATE_TRUNC('month', CURRENT_DATE)), 1) AS pct
FROM transactions t
JOIN categories c ON c.id = t.category_id
WHERE t.type = 'expense'
  AND DATE_TRUNC('month', t.transaction_date) = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY c.name, c.icon
ORDER BY total DESC;"
```

**Income vs Expense summary:**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
SELECT type,
       COUNT(*) AS count,
       SUM(amount) AS total,
       ROUND(AVG(amount), 2) AS average
FROM transactions
WHERE DATE_TRUNC('month', transaction_date) = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY type;"
```

**Top merchants:**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
SELECT merchant, COUNT(*) AS visits, SUM(amount) AS total_spent
FROM transactions
WHERE type = 'expense' AND merchant IS NOT NULL
GROUP BY merchant
ORDER BY total_spent DESC
LIMIT 10;"
```

**Find transactions by tag:**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
SELECT transaction_date, amount, category.name, description, tags
FROM transactions
JOIN categories ON categories.id = transactions.category_id
WHERE tags @> ARRAY['lunch'::TEXT]
ORDER BY transaction_date DESC;"
```

**Daily balance (running total):**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
WITH daily AS (
  SELECT transaction_date,
         SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS income,
         SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expense
  FROM transactions
  GROUP BY transaction_date
)
SELECT transaction_date, income, expense,
       SUM(income - expense) OVER (ORDER BY transaction_date) AS balance
FROM daily
ORDER BY transaction_date DESC
LIMIT 30;"
```

### Recurring Transactions

**Find recurring transactions:**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
SELECT t.description, t.amount, c.name AS category,
       t.recurring_period, t.transaction_date AS last_date
FROM transactions t
JOIN categories c ON c.id = t.category_id
WHERE t.is_recurring = TRUE
ORDER BY t.recurring_period, c.name;"
```

---

## Database Migration Workflow

Migrations follow Flyway-style versioning:

```
/Users/apple/projects/smart-expense/migrations/
├── V001__create_category_and_transactions.sql
├── V002__rename_category_to_categories.sql
├── V003__add_llm_comment_to_transactions.sql
└── V004__...sql  # future
```

**Apply a migration:**
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense \
  -f /Users/apple/projects/smart-expense/migrations/V003__add_llm_comment_to_transactions.sql
```

**Rollback a migration:**
```bash
# Check migration history
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "\dv"

# Manually rollback (if no migration tracking table exists)
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense \
  -f /Users/apple/projects/smart-expense/migrations/V003__rollback.sql
```

### Migration Best Practices

1. **Always include rollback script** - Commented `-- DOWN` section in migration file
2. **Use descriptive names** - `V002__rename_category_to_categories` not `V002__fix.sql`
3. **Test before applying** - Run migration in a test database first
4. **Document changes** - Add header comment with description and date
5. **Use transactions** - Wrap migration in `BEGIN; ... COMMIT;` for atomicity
6. **Index carefully** - Add indexes for frequently queried columns (e.g., `llm_comment`)
7. **Follow naming conventions** - Use plural for tables (`categories`), singular for columns where appropriate (`category_id`)

### Schema Evolution Pattern

This project follows these conventions:

- **Plural table names**: `categories`, `transactions` (not `category`, `transaction`)
- **Foreign key naming**: `{table}_{column}_fkey` → `transactions_categories_id_fkey`
- **Index naming**: `idx_{table}_{column}` or `idx_{table}_{column}_where` for partial indexes
- **Timestamp columns**: `created_at`, `updated_at` (TIMESTAMPTZ)
- **UUID primary keys**: Auto-generated via `uuid-ossp` extension

---

## Hermes LLM Integration Pattern

**Key learning**: Use your configured Hermes LLM directly instead of the `vision_analyze` tool for receipt parsing and financial analysis.

### Why This Pattern?

| Approach | Setup | Integration | Cost |
|----------|-------|-------------|------|
| `vision_analyze` tool | ✅ Zero | ⚠️ Separate tool | ✅ Free |
| **Hermes LLM directly** | ✅ Zero | ✅ **Fully integrated** | ✅ Uses existing quota |

### Implementation Pattern

```python
# 1. Load Hermes config automatically
config = load_hermes_config()  # From ~/.hermes/config.yaml

# 2. Create OpenAI-compatible client
client, model = get_llm_client(config)
# Uses: model.default, base_url, api_key from config

# 3. Use with any task
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"}
)
```

### Benefits

- ✅ **Zero extra setup** - Uses your existing Hermes configuration
- ✅ **Auto-updates** - Changes to config automatically apply
- ✅ **Fully integrated** - Part of your Hermes workflow
- ✅ **No API key management** - Securely loaded from config
- ✅ **Same endpoint** - Works with your configured model (kimi-k2.6, etc.)

### Common Pitfalls

1. **Don't hardcode API keys** - Always load from `~/.hermes/config.yaml`
2. **Don't use `vision_analyze` tool** - Use the LLM client directly instead
3. **Don't forget `response_format`** - Always use `{"type": "json_object"}` for structured output
4. **Don't assume model capabilities** - Check if your model supports vision (image input)

---

## Financial Advisor AI

Generate AI-powered financial insights using your Hermes LLM configuration.

### Quick Start

```bash
# Analyze single transaction
python3 scripts/financial_advisor.py comment <transaction_id>

# Monthly analysis
python3 scripts/financial_advisor.py analyze-month <year> <month>

# Trend analysis
python3 scripts/financial_advisor.py analyze-trends --months 3

# Batch generate comments
python3 scripts/financial_advisor.py generate-all-comments
```

### Features

| Feature | Command | Description |
|---------|---------|-------------|
| **Transaction Comment** | `comment <id>` | Personalized advice for single transaction |
| **Monthly Summary** | `analyze-month <y> <m>` | Monthly spending insights & budget recommendations |
| **Trend Analysis** | `analyze-trends` | Multi-month pattern detection |
| **Batch Processing** | `generate-all-comments` | Process all un-commented transactions |

### Examples

```bash
# Comment on Indomaret receipt
python3 scripts/financial_advisor.py comment f9a0be93-a0ea-4d6e-b3aa-dcbcbc2f0f7e

# September 2024 analysis
python3 scripts/financial_advisor.py analyze-month 2024 9

# 3-month trend
python3 scripts/financial_advisor.py analyze-trends --months 3
```

### Sample Output

**Transaction Comment:**
```
Transaksi senilai Rp75.200 ini mencampur belanja makanan dan kebutuhan rumah 
tangga di minimarket. Untuk barang seperti pembersih, lebih hemat membelinya di 
supermarket besar dengan harga lebih murah. Selalu bawa tas 
belanja sendiri untuk menghindari biaya kantong plastik sekaligus mendapat 
potongan harga.

Actions: 
- Beli kebutuhan rumah tangga di supermarket besar alih-alih minimarket
- Selalu bawa tas belanja sendiri untuk hemat biaya plastik

Sentiment: neutral
Confidence: high
```

**Monthly Insights:**
```
Pada bulan September 2016, total pengeluaran Anda mencapai Rp67.800 dengan 
pemasukan Rp0, sehingga terjadi defisit sebesar Rp67.800. Belanja dan makanan/minuman masing-masing 
menghabiskan Rp33.900. Meskipun jumlah transaksi hanya 2, pola ini menunjukkan perlunya 
perencanaan keuangan yang lebih baik.

Savings opportunity: Anda bisa menghemat dengan mengurangi frekuensi belanja di Indomaret, 
misalnya memasak di rumah untuk menggantikan makanan/minuman yang dibeli.

⚠️  Pengeluaran Rp67.800 tanpa pemasukan sangat berisiko.
```

### Database Integration

Comments are stored in `llm_comment` column:

```bash
# Check transactions with comments
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
SELECT merchant, amount, llm_comment 
FROM transactions 
WHERE llm_comment IS NOT NULL 
LIMIT 3;"
```

### When to Use

- ✅ After adding new receipts/transactions
- ✅ At month-end for budget review
- ✅ Quarterly for trend analysis
- ✅ When user asks "How am I doing financially?"

---

## Verification Checklist

- [ ] Connection works: `PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "SELECT 1;"`
- [ ] Can list categories: `SELECT COUNT(*) FROM categories;` → should return 15
- [ ] Can insert a test transaction and verify it appears
- [ ] Can generate monthly report without errors
- [ ] Can clean up test data after verification
- [ ] **Receipt parsing**: LLM endpoint accessible and vision-capable
- [ ] **Receipt parsing**: `parse_receipt_hermes_llm.py` works with test image
- [ ] **Financial advisor**: `llm_comment` column exists in transactions table
- [ ] **Financial advisor**: Script runs and generates valid JSON output
- [ ] **Hermes integration**: Config loaded from `~/.hermes/config.yaml`

1. **Forgetting `-h localhost`.** PostgreSQL runs via Docker/OrbStack. The default Unix socket doesn't exist — always connect via TCP.

2. **Using `ON DELETE CASCADE` for categories.** The schema uses `ON DELETE RESTRICT` — you can't delete a category that still has transactions. Either reassign or delete the transactions first.

3. **Inserting duplicate categories.** The `(name, type)` unique constraint prevents this. Use `ON CONFLICT (name, type) DO NOTHING` in seed scripts.

4. **Hardcoding UUIDs.** UUIDs are generated by the database. Always retrieve the ID first when you need it for a related operation:
   ```bash
   # Get the category ID
   PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -tAc "
   SELECT id FROM categories WHERE name = 'Food & Drinks' LIMIT 1;"
   ```

5. **Rounding errors with DECIMAL.** PostgreSQL handles DECIMAL precisely, but floating-point operations in application code can introduce errors. Keep calculations in SQL when possible.

6. **Missing tags array syntax.** Always cast string literals: `ARRAY['tag1'::TEXT, 'tag2'::TEXT]` or simply `ARRAY['tag1', 'tag2']` which defaults to TEXT.

7. **Date filtering off-by-one.** Use half-open intervals for month queries:
   ```sql
   WHERE transaction_date >= '2025-01-01' AND transaction_date < '2025-02-01'
   ```
---

## Receipt / Nota Scanning

Detect and extract transaction data from photos of receipts (struk belanja, nota restoran, invoice, dll.). **Uses your Hermes LLM configuration directly** — no extra API keys needed!

### 🚀 Primary Method: Hermes LLM (Recommended)

**This script uses your EXACT Hermes LLM configuration** from `~/.hermes/config.yaml`:
- Automatically reads `model`, `base_url`, `api_key` from config
- Works with **kimi-k2.6** (your configured model)
- **No additional API keys** required
- **Fully local** to your Hermes setup

**Usage:**
```bash
# Parse receipt using your Hermes LLM
python3 ~/.hermes/skills/productivity/smart-expense/scripts/parse_receipt_hermes_llm.py \
  /path/to/receipt.jpg

# Just parse (don't insert to database)
python3 parse_receipt_hermes_llm.py receipt.jpg --no-insert

# Override auto-detected category
python3 parse_receipt_hermes_llm.py receipt.jpg --category "Food & Drinks"

# See full LLM response
python3 parse_receipt_hermes_llm.py receipt.jpg --verbose
```

**Configuration (from `~/.hermes/config.yaml`):**
```yaml
model:
  default: kimi-k2.6
  provider: custom
  base_url: https://ai.sumopod.com
  api_key: sk-...  # Your API key
  api_mode: chat_completions
```

The script automatically uses:
- **Model**: `kimi-k2.6`
- **Endpoint**: `https://ai.sumopod.com`
- **API Key**: From your config file (securely loaded)

**What it extracts:**
```json
{
  "merchant": "Indomaret Jatinangor KM.20",
  "date": "2016-09-14",
  "time": "06:46",
  "amount_cents": 33900,
  "payment_method": "cash",
  "items": [
    {"name": "S/ROTI KRIM KEJU 72G", "qty": 4, "unit_price": 4500, "total": 18000},
    {"name": "CIMORY MIX BERRY 225", "qty": 1, "unit_price": 8500, "total": 8500},
    {"name": "CAFELA ESPRESO 200ML", "qty": 1, "unit_price": 3500, "total": 3500},
    {"name": "FF LOW FAT VAN 225", "qty": 1, "unit_price": 5200, "total": 5200},
    {"name": "PLASTIK SDG", "qty": 1, "unit_price": 1, "total": 1}
  ],
  "subtotal": 35200,
  "discount": 1300,
  "discount_note": "DISKON FRISIAN FLAG",
  "cash_paid": 40000,
  "change": 6100,
  "confidence": "high"
}
```

Then **auto-inserts** into `smart_expense` with:
- ✅ Auto-guessed category (Food & Drinks, Shopping, etc.)
- ✅ All fields properly mapped
- ✅ Tags: `["receipt", "hermes-llm", "high"]`

---

### 🔄 Alternative: Tesseract OCR (Offline Fallback)

For offline use or when LLM is unavailable:

```bash
# Scan receipt with Indonesian + English OCR
tesseract /path/to/struk.jpg stdout -l ind+eng 2>/dev/null

# Or use the OCR parser
python3 ~/.hermes/skills/productivity/smart-expense/scripts/parse_receipt.py \
  /path/to/receipt.jpg
```

---

### 🇮🇩 Indonesian Receipt Patterns

Local Indonesian receipts (struk) often have these patterns:

```
# Struk Minimarket
TOKO ABC
Jl. Merdeka No. 123
Telp: 021-123456
15/05/25 14:30
# Struk Retail / Bill
Indomie Goreng    1 x 3,500 =   3,500
Telur            1 x 2,000 =   2,000
                              --------
TOTAL                       Rp 5,500
TUNAI                        Rp 10,000
KEMBALI                      Rp 4,500
-----
# Kasir: Ani
# Terima Kasih

# Struk Restoran
RM SEDERHANA
Jl. Pahlawan No. 45
Nasi Goreng                25,000
Ayam Goreng                30,000
Es Jeruk                   10,000
Pajak 10%                   6,500
Service 5%                  3,250
                            -------+
TOTAL                      Rp74,750
```

---

### 📊 Receipt Scanning Workflow

```
User sends receipt photo
        │
        ▼
  [Hermes LLM] ─── or ─── [Tesseract OCR]
        │                          │
        ▼                          ▼
  Extract structured JSON      Extract raw text
  (merchant, date, amount,   → parse with regex
   items, payment, discount)
        │
        ▼
  Guess category from merchant/items
        │
        ▼
  Insert into smart_expense DB
        │
        ▼
  Show user: "✅ Added: Rp33,900 at Indomaret (Shopping)"
```

### 🎯 Why Hermes LLM is Best

**This approach uses YOUR configured LLM** — no extra setup needed!

| Feature | Hermes LLM | Tesseract OCR |
|---------|------------|---------------|
| **Accuracy** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Discount detection** | ✅ Automatic | ❌ Manual |
| **Item-level extraction** | ✅ Detailed | ⚠️ Basic |
| **Multi-language** | ✅ Excellent | ⚠️ Limited |
| **Setup** | ✅ Zero (uses your config) | ✅ Zero |
| **Offline** | ❌ Needs internet | ✅ Yes |
| **Cost** | ✅ Uses your existing quota | ✅ Free |

**Key advantages:**
- ✅ **No extra API keys** — uses your Hermes config
- ✅ **Works with your model** (kimi-k2.6, etc.)
- ✅ **Same endpoint** as your Hermes agent
- ✅ **Fully integrated** — no separate setup
- ✅ **Auto-updates** when you change Hermes config

---

## Migration Patterns

### V002: Table Naming Convention
**Pattern:** Rename singular tables to plural for consistency.

```sql
ALTER TABLE category RENAME TO categories;
ALTER TABLE transactions 
  RENAME CONSTRAINT transactions_category_id_fkey 
  TO transactions_categories_id_fkey;
```

**Pitfall:** PostgreSQL constraint names must be explicitly renamed (not auto-updated).

### V003: LLM Comment Column
**Pattern:** Add `llm_comment` + `llm_comment_at` for AI-generated insights.

```sql
ALTER TABLE transactions ADD COLUMN llm_comment TEXT;
ALTER TABLE transactions ADD COLUMN llm_comment_at TIMESTAMPTZ;
CREATE INDEX idx_transactions_llm_comment
ON transactions(id) WHERE llm_comment IS NOT NULL;
```

**Why:** Enables fast filtering for transactions with AI advice.

### V004: Multi-User Support
**Pattern:** Add `telegram_id` for user isolation.

```sql
ALTER TABLE transactions ADD COLUMN telegram_id BIGINT;
CREATE INDEX idx_transactions_telegram_id
ON transactions(telegram_id) WHERE telegram_id IS NOT NULL;
```

**Default:** Set to user's Telegram ID (e.g., 552378634) on insert.

**Query Pattern:** Always filter by `telegram_id` in multi-user scenarios.

### UP/DOWN Migration Template

```sql
-- ==============================================================
-- Migration: VXXX__description
-- Description: What changed and why
-- Applied at: YYYY-MM-DD HH:MM:SS UTC
-- ==============================================================

BEGIN;

-- UP changes here

COMMIT;

/*
-- DOWN (rollback)
BEGIN;

-- Rollback changes here

COMMIT;
*/
```

### Receipt Parsing with Hermes LLM (Recommended)

```bash
# Install dependencies (if needed)
pip install openai pyyaml psycopg2-binary

# Parse receipt using your Hermes LLM
python3 ~/.hermes/skills/productivity/smart-expense/scripts/parse_receipt_hermes_llm.py \
  /path/to/receipt.jpg

# Parse without inserting (just see what it extracts)
python3 parse_receipt_hermes_llm.py receipt.jpg --no-insert

# Override category
python3 parse_receipt_hermes_llm.py receipt.jpg --category "Food & Drinks"
```

### Quick Balance Check
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
SELECT type, SUM(amount) FROM transactions
WHERE DATE_TRUNC('month', transaction_date) = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY type;"
```

### Add Today's Expense
```bash
read -p "Amount: " AMOUNT
read -p "Category: " CAT
read -p "Description: " DESC
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense -c "
INSERT INTO transactions (category_id, amount, type, description, transaction_date)
VALUES (
  (SELECT id FROM categories WHERE name ILIKE '%$CAT%' AND type='expense' LIMIT 1),
  $AMOUNT, 'expense', '$DESC', CURRENT_DATE
);"
```

### Export Current Month as CSV
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense \
  --csv -c "
SELECT t.transaction_date, t.type, c.name AS kategori,
       t.amount, t.description, t.payment_method, t.merchant, t.tags
FROM transactions t
JOIN categories c ON c.id = t.category_id
WHERE DATE_TRUNC('month', t.transaction_date) = DATE_TRUNC('month', CURRENT_DATE)
ORDER BY t.transaction_date DESC;" > ~/Desktop/smart_expense_$(date +%Y%m).csv
```
