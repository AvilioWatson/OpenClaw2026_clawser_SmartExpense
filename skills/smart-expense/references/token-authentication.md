# Token Authentication — Reference

API authentication tokens for the Smart Expense database, stored in the `tokens` table and generated via `scripts/generate_token.py`.

---

## Database Schema

```sql
CREATE TABLE tokens (
    telegram_id BIGINT       NOT NULL,
    token       VARCHAR(255) NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    PRIMARY KEY (token)
);

CREATE INDEX idx_tokens_telegram_id ON tokens(telegram_id);
```

## Script: `scripts/generate_token.py`

| Aspect | Detail |
|--------|--------|
| **Language** | Python 3 |
| **Dependencies** | `psycopg2-binary` (DB), no external crypto libs |
| **RNG** | `secrets.choice()` — cryptographically secure |
| **Default length** | 32 chars (128 bits entropy) |
| **Min/Max** | 16 / 128 characters |
| **Alphabet** | `[a-zA-Z0-9]` — URL-safe, no special chars |
| **DB config** | Hardcoded: localhost:5432, user=postgres, pass=pg123, db=smart_expense |

### Arguments

```
positional:
  telegram_id    User's Telegram ID (default: 552378634)

optional:
  --length N     Token length in characters (default: 32)
  --quiet        Only print the token, no extra output
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success — token generated and inserted |
| 1 | DB error, token collision, or invalid arguments |

### Sample Output (default mode)

```
✅ Token generated and saved!
   Telegram ID : 552378634
   Token       : aB3xK9mN2pQ5rT7vW1yZ4cE6fH8jL0sD
   Length      : 32 chars
   Created at  : 2026-05-15 19:30:00 UTC

🔐 Use this token for API authentication:
   Authorization: Bearer aB3xK9mN2pQ5rT7vW1yZ4cE6fH8jL0sD
```

### Quiet Mode (for scripting)

```
python3 generate_token.py 552378634 --quiet
# Output: aB3xK9mN2pQ5rT7vW1yZ4cE6fH8jL0sD
```

## Manual SQL Equivalents

**Generate and insert a 48-char hex token:**
```sql
INSERT INTO tokens (telegram_id, token)
VALUES (552378634, encode(gen_random_bytes(24), 'hex'));
```

**Look up a user by token:**
```sql
SELECT telegram_id FROM tokens WHERE token = '<token>';
```

**Revoke a token:**
```sql
DELETE FROM tokens WHERE token = '<token>';
```

**List all tokens (preview only — never expose full tokens):**
```sql
SELECT telegram_id,
       LEFT(token, 8) || '...' || RIGHT(token, 4) AS masked_token,
       created_at
FROM tokens ORDER BY created_at DESC;
```

## Use Cases

| Use Case | Script Command |
|----------|---------------|
| User types `/login-token` | `python3 generate_token.py <telegram_id>` |
| Script wants a fresh token | `python3 generate_token.py <id> --quiet` |
| Generate a 64-char token | `python3 generate_token.py <id> --length 64` |
| Revoke compromised token | `DELETE FROM tokens WHERE token = '...'` |
| Check all tokens for a user | `SELECT * FROM tokens WHERE telegram_id = <id>` |
