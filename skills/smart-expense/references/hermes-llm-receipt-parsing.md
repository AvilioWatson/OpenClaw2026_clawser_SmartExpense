# Hermes LLM Receipt Parsing

## Overview

This guide explains how to parse receipt images using **your Hermes LLM configuration** — no extra API keys needed!

## How It Works

The script `parse_receipt_hermes_llm.py` automatically:

1. **Reads your Hermes config** from `~/.hermes/config.yaml`
2. **Extracts LLM settings**: model, base_url, api_key
3. **Creates OpenAI-compatible client** with your config
4. **Parses receipt image** using your configured LLM (kimi-k2.6)
5. **Returns structured JSON** with merchant, date, amount, items, discounts
6. **Auto-inserts** to `smart_expense` database

## Configuration

Your Hermes config (from `~/.hermes/config.yaml`):

```yaml
model:
  default: kimi-k2.6
  provider: custom
  base_url: https://ai.sumopod.com
  api_key: sk-1Ol...RpSw  # Your API key
  api_mode: chat_completions
```

The script uses these exact values — no configuration needed!

## Usage

### Basic Usage

```bash
# Parse and insert to database
python3 ~/.hermes/skills/productivity/smart-expense/scripts/parse_receipt_hermes_llm.py \
  /path/to/receipt.jpg
```

### Options

```bash
# Just parse (don't insert)
python3 parse_receipt_hermes_llm.py receipt.jpg --no-insert

# Override category
python3 parse_receipt_hermes_llm.py receipt.jpg --category "Food & Drinks"

# See full LLM response
python3 parse_receipt_hermes_llm.py receipt.jpg --verbose
```

## Example Output

```
📚 Loading Hermes configuration...
🔍 Using Hermes LLM configuration:
   Model: kimi-k2.6
   Base URL: https://ai.sumopod.com
   API Key: sk-1OlO62a...

🚀 Parsing receipt with Hermes LLM: kimi-k2.6
   Image: /path/to/receipt.jpg

✅ Receipt parsed successfully!
   Merchant: Indomaret Jatinangor KM.20
   Date: 2016-09-14
   Time: 06:46
   Amount: Rp33,900
   Payment: cash
   Items: 5 items
   Discount: Rp1,300
   Confidence: high

📊 Guessing category: Shopping
✅ Transaction added (ID: 550e8400-...)
```

## What Gets Extracted

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

## Dependencies

Install these once:

```bash
pip install openai pyyaml psycopg2-binary
```

## Advantages

✅ **Zero setup** — uses your existing Hermes config  
✅ **No extra API keys** — automatically reads from `~/.hermes/config.yaml`  
✅ **Works with your model** — kimi-k2.6 (or whatever you configured)  
✅ **Fully integrated** — same endpoint as your Hermes agent  
✅ **Auto-updates** — changes to Hermes config are automatically used  

## Troubleshooting

### "No api_key found in Hermes config"

Make sure `~/.hermes/config.yaml` has:

```yaml
model:
  api_key: sk-...
  base_url: https://...
```

### "Failed to parse JSON"

The LLM might not have returned valid JSON. Try:
- Using `--verbose` to see raw response
- Checking if image is clear and readable
- Ensuring receipt text is visible

### "Category not found"

Available categories:
```bash
PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense \
  -c "SELECT name FROM category WHERE type='expense';"
```

Or use `--category` to override.

## Files

- `parse_receipt_hermes_llm.py` — Main script
- `parse_receipt_llm.py` — Alternative (requires manual API key)
- `parse_receipt.py` — Tesseract OCR fallback
- `test_receipt_llm.py` — Test script

## See Also

- [SKILL.md](../SKILL.md) — Full documentation
- [smart_expense schema](../references/schema.md) — Database structure
- [Migrations](../../migrations/) — Database migrations
