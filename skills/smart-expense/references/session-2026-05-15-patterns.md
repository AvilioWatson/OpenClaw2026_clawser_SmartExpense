# Smart Expense - Session Patterns & Learnings

## Session: 2026-05-15 - LLM Receipt Parsing & Financial Advisor

### Key Achievements

1. **Receipt Parsing with LLM Vision**
   - Used Hermes LLM (kimi-k2.6) instead of Tesseract OCR
   - Extracts: merchant, date, items, discounts, payment method
   - Auto-categorizes transactions
   - Stores structured data in database

2. **Financial Advisor AI**
   - Generates personalized financial advice per transaction
   - Monthly spending insights
   - Multi-month trend analysis
   - Stores comments in `llm_comment` column

3. **Multi-User Support**
   - Added `telegram_id` column for user isolation
   - All scripts updated to filter by user
   - Default: 552378634 (current user)

---

## Migration Patterns Discovered

### V002: Table Naming Convention
**Problem:** Singular `category` table inconsistent with plural `transactions`

**Solution:**
```sql
ALTER TABLE category RENAME TO categories;
ALTER TABLE transactions 
  RENAME CONSTRAINT transactions_category_id_fkey 
  TO transactions_categories_id_fkey;
```

**Pitfall:** PostgreSQL does NOT auto-update constraint names - must be renamed explicitly.

### V003: LLM Comment Column
**Pattern:** Add AI insights column with timestamp and index

```sql
ALTER TABLE transactions ADD COLUMN llm_comment TEXT;
ALTER TABLE transactions ADD COLUMN llm_comment_at TIMESTAMPTZ;
CREATE INDEX idx_transactions_llm_comment
ON transactions(id) WHERE llm_comment IS NOT NULL;
```

**Why:** Enables fast filtering for transactions with AI advice.

### V004: Multi-User Support
**Pattern:** Add user identifier for data isolation

```sql
ALTER TABLE transactions ADD COLUMN telegram_id BIGINT;
CREATE INDEX idx_transactions_telegram_id
ON transactions(telegram_id) WHERE telegram_id IS NOT NULL;
```

**Default:** Set on INSERT (e.g., `telegram_id = 552378634`)

**Query Pattern:** Always filter by `telegram_id` in multi-user scenarios.

---

## Script Patterns

### 1. Receipt Parser (`parse_receipt_hermes_llm.py`)

**Flow:**
```
1. Load Hermes config from ~/.hermes/config.yaml
2. Create OpenAI client with configured model
3. Send receipt image to LLM with structured prompt
4. Parse JSON response (merchant, items, discounts, etc.)
5. Guess category based on merchant/items
6. Insert to database with telegram_id
```

**Key Code Pattern:**
```python
# Load config
config = load_hermes_config()
client, model = get_llm_client(config)

# Call LLM
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"}  # Forces JSON
)

# Insert with user ID
cursor.execute("""
    INSERT INTO transactions (..., telegram_id)
    VALUES (... , 552378634)
""")
```

### 2. Financial Advisor (`financial_advisor.py`)

**Commands:**
- `comment <tx_id>` - Single transaction analysis
- `analyze-month <year> <month>` - Monthly insights
- `analyze-trends --months 3` - Trend analysis
- `generate-all-comments` - Batch processing

**Query Pattern:**
```python
def get_transactions_by_month(year, month, telegram_id=552378634):
    cursor.execute("""
        SELECT * FROM transactions
        WHERE telegram_id = %s  # User filter
          AND transaction_date >= %s
          AND transaction_date < %s
    """, (telegram_id, start_date, end_date))
```

---

## Database Schema Evolution

### Before
```
transactions:
  id, transaction_date, amount, type, description,
  payment_method, merchant, notes, tags,
  created_at, updated_at
```

### After (Current)
```
transactions:
  id,
  telegram_id,              ← NEW: User identifier
  transaction_date,
  amount,
  type,
  description,
  payment_method,
  merchant,
  notes,
  tags,
  llm_comment,             ← NEW: AI advice
  llm_comment_at,          ← NEW: When generated
  created_at,
  updated_at
```

---

## Hermes LLM Integration

### Configuration
```yaml
# ~/.hermes/config.yaml
model:
  default: kimi-k2.6
  provider: custom
  base_url: https://ai.sumopod.com
  api_key: sk-...
```

### Benefits
- ✅ **Zero setup** - Uses existing Hermes config
- ✅ **No extra API keys** - Reuses same credentials
- ✅ **Consistent model** - Same model as agent
- ✅ **Local-first** - All processing respects user's setup

---

## Prompt Engineering Patterns

### Transaction Analysis Prompt
```text
You are a personal financial advisor. Analyze this transaction...

Return JSON:
{
  "comment": "Advice in Indonesian",
  "sentiment": "positive|neutral|negative",
  "action_items": ["action 1", "action 2"],
  "confidence": "high|medium|low"
}
```

### Monthly Insights Prompt
```text
You are a personal financial advisor. Analyze this month's spending...

Return JSON:
{
  "monthly_comment": "Summary",
  "savings_opportunity": "Specific tip",
  "spending_warning": "Red flag or null",
  "positive_notes": "What went well",
  "action_items": [...]
}
```

---

## Testing & Verification

### Database Verification
```sql
-- Check columns exist
\d transactions

-- Verify telegram_id is set
SELECT telegram_id, COUNT(*) 
FROM transactions 
GROUP BY telegram_id;

-- Check llm_comment is populated
SELECT merchant, llm_comment IS NOT NULL as has_comment
FROM transactions
LIMIT 5;
```

### Script Verification
```bash
# Test receipt parsing
python3 scripts/parse_receipt_hermes_llm.py test.jpg --no-insert

# Test financial advisor
python3 scripts/financial_advisor.py comment <tx_id>

# Test monthly analysis
python3 scripts/financial_advisor.py analyze-month 2016 9
```

---

## Common Pitfalls & Solutions

### 1. Constraint Name Mismatch
**Problem:** `category_id_fkey` doesn't exist after rename

**Solution:** Check actual constraint name first:
```sql
\d transactions | grep "Foreign-key"
-- Output: "transactions_category_id_fkey"
```

### 2. Index Creation
**Problem:** Index on nullable column is slow

**Solution:** Use partial index:
```sql
CREATE INDEX idx_name
ON table(column) WHERE column IS NOT NULL;
```

### 3. Multi-User Query
**Problem:** Queries return all users' data

**Solution:** Always add filter:
```sql
WHERE telegram_id = 552378634
```

### 4. LLM Timeout
**Problem:** Large receipts exceed token limits

**Solution:** Truncate notes in prompt:
```python
notes[:200] if notes else 'None'
```

---

## Future Enhancements

- [ ] Budget tracking feature
- [ ] Visual spending charts
- [ ] Investment recommendations
- [ ] Tax planning insights
- [ ] Goal-based savings suggestions
- [ ] Automated monthly reports (cron job)

---

## References

- [Migration V002](../../migrations/V002__rename_category_to_categories.sql)
- [Migration V003](../../migrations/V003__add_llm_comment_to_transactions.sql)
- [Migration V004](../../migrations/V004__add_telegram_id_to_transactions.sql)
- [Financial Advisor Script](../../scripts/financial_advisor.py)
- [Receipt Parser Script](../../scripts/parse_receipt_hermes_llm.py)

---

**Session Date:** 2026-05-15  
**Author:** zuzu  
**Status:** ✅ Complete
