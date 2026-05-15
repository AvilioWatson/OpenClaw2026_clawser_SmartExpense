# Receipt Parsing JSON Schema

## Standard Output Format

All receipt parsing tools should return data in this standardized JSON format:

```json
{
  "merchant": "store/restaurant name (string)",
  "date": "YYYY-MM-DD or null if not found",
  "time": "HH:MM or null if not found",
  "amount_cents": 33900,  // integer, in rupiah (e.g. 33900 = Rp33,900)
  "payment_method": "cash|card|transfer|e-wallet|other|null",
  "items": [
    {
      "name": "item name",
      "qty": 1,
      "unit_price": 8500,
      "total": 8500
    }
  ],
  "subtotal": 35200,
  "discount": 1300,
  "discount_note": "optional description of discount",
  "cash_paid": 40000,
  "change": 6100,
  "you_saved": 1300,
  "confidence": "high|medium|low",
  "notes": "any additional info"
}
```

## Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `merchant` | string | ✅ | Store/restaurant name |
| `date` | string (YYYY-MM-DD) | ⚠️ | Transaction date, null if not found |
| `time` | string (HH:MM) | ⚠️ | Transaction time, null if not found |
| `amount_cents` | integer | ✅ | **TOTAL amount in rupiah** (not cents! e.g. 33900 = Rp33,900) |
| `payment_method` | string | ✅ | `cash`, `card`, `transfer`, `e-wallet`, `other`, or `null` |
| `items` | array | ✅ | List of purchased items |
| `items[].name` | string | ✅ | Item name/description |
| `items[].qty` | integer | ✅ | Quantity purchased |
| `items[].unit_price` | integer | ⚠️ | Price per unit in rupiah, null if unknown |
| `items[].total` | integer | ⚠️ | Total for this line item in rupiah, null if unknown |
| `subtotal` | integer | ⚠️ | Subtotal before discounts, null if unknown |
| `discount` | integer | ⚠️ | Total discount amount in rupiah, null if no discount |
| `discount_note` | string | ⚠️ | Description of discount (e.g., "DISKON FRISIAN FLAG") |
| `cash_paid` | integer | ⚠️ | Amount paid in cash, null if not cash payment |
| `change` | integer | ⚠️ | Change received, null if not applicable |
| `you_saved` | integer | ⚠️ | Total savings from discounts |
| `confidence` | string | ✅ | `high`, `medium`, or `low` - parser confidence level |
| `notes` | string | ⚠️ | Any additional information |

## Indonesian Receipt Patterns

### Currency Format
- Indonesian Rupiah (IDR) uses `Rp` prefix: `Rp 33,900`
- No decimal places for whole Rupiah
- Comma as thousands separator: `1,000,000`
- In JSON: always store as integer (e.g., `33900` for Rp33,900)

### Payment Methods
- **Tunai** → `cash`
- **Transfer** (BCA, Mandiri, BNI, BRI) → `transfer`
- **Gopay, OVO, Dana, ShopeePay, LinkAja** → `e-wallet`
- **Kartu, Visa, Mastercard** → `card`
- **QRIS** → `e-wallet` (or `other` if unsure)

### Common Discount Keywords
- `DISKON` - discount
- `PROMO` - promotion
- `BONUS` - bonus/gift
- `HEMAT` - savings
- `CASHBACK` - cashback

### Date Formats
- Indonesian: `14.09.16` (DD.MM.YY)
- Full: `14 September 2016`
- ISO: `2016-09-14`

## Category Guessing Logic

Based on merchant name and item descriptions:

```python
def guess_category(text: str, merchant: str) -> str:
    text_lower = (text + " " + merchant).lower()
    
    if any(word in text_lower for word in ['makan', 'restoran', 'warung', 'kopi', 'cafe', 'food', 'nasi', 'bakso', 'soto']):
        return 'Food & Drinks'
    elif any(word in text_lower for word in ['bensin', 'fuel', 'spbu', 'grab', 'gojek', 'parkir', 'tol']):
        return 'Transportation'
    elif any(word in text_lower for word in ['alfamart', 'indomaret', 'supermarket', 'sembako']):
        return 'Shopping'
    elif any(word in text_lower for word in ['bioskop', 'cinema', 'game', 'tiket']):
        return 'Entertainment'
    elif any(word in text_lower for word in ['pln', 'pdam', 'telkom', 'internet', 'bpjs']):
        return 'Bills & Utilities'
    elif any(word in text_lower for word in ['apotek', 'obat', 'klinik', 'dokter']):
        return 'Health'
    elif any(word in text_lower for word in ['buku', 'sekolah', 'kursus']):
        return 'Education'
    elif any(word in text_lower for word in ['sewa', 'hotel', 'kontrakan']):
        return 'Housing'
    else:
        return 'Other Expense'
```

## Example: Indomaret Receipt

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
  "you_saved": 1300,
  "confidence": "high",
  "notes": "Indomaret convenience store receipt"
}
```

## Example: Restaurant Receipt

```json
{
  "merchant": "RM Sederhana",
  "date": "2025-05-15",
  "time": "19:30",
  "amount_cents": 74750,
  "payment_method": "e-wallet",
  "items": [
    {"name": "Nasi Goreng", "qty": 2, "unit_price": 25000, "total": 50000},
    {"name": "Ayam Goreng", "qty": 1, "unit_price": 30000, "total": 30000},
    {"name": "Es Jeruk", "qty": 2, "unit_price": 10000, "total": 20000}
  ],
  "subtotal": 100000,
  "discount": 0,
  "cash_paid": 0,
  "change": 0,
  "you_saved": 0,
  "confidence": "high",
  "notes": "Pajak 10% (10,000), Service 5% (5,000), Total: Rp74,750"
}
```

## Validation Rules

1. **amount_cents** must be positive integer
2. **payment_method** must be one of: `cash`, `card`, `transfer`, `e-wallet`, `other`, `null`
3. **items** array must have at least one item if receipt has items
4. **date** should be in `YYYY-MM-DD` format if present
5. **time** should be in `HH:MM` format if present
6. **confidence** must be one of: `high`, `medium`, `low`
7. All monetary values in rupiah (no decimals, integer only)
8. **discount** cannot be greater than **subtotal**

## LLM Prompt Template

Use this prompt for best results:

```
You are a receipt parsing assistant. Extract ALL data from this receipt.

Return ONLY valid JSON in this EXACT format (no markdown, no extra text):
{
  "merchant": "store/restaurant name",
  "date": "YYYY-MM-DD or null",
  "time": "HH:MM or null",
  "amount_cents": 33900,
  "payment_method": "cash|card|transfer|e-wallet|other|null",
  "items": [
    {"name": "item name", "qty": 1, "unit_price": 8500, "total": 8500}
  ],
  "subtotal": 35200,
  "discount": 1300,
  "discount_note": "optional",
  "cash_paid": 40000,
  "change": 6100,
  "you_saved": 1300,
  "confidence": "high|medium|low",
  "notes": "additional info"
}

Rules:
- amount_cents is TOTAL amount in rupiah (integer, no decimals)
- If a field is missing, use null
- Focus on Indonesian receipts (Rp currency, Indonesian text)
- Be exact. Do not add extra fields or explanations.
```
