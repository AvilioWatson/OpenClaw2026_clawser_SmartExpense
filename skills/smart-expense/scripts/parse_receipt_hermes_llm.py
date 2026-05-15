#!/usr/bin/env python3
"""
Hermes LLM Receipt Parser for Smart Expense

Parse receipt images using the EXACT Hermes LLM configuration from config.yaml.
This script reads the Hermes config directly and uses your configured LLM
(kimi-k2.6 via https://ai.sumopod.com) for receipt parsing.

Advantages:
- Uses your existing Hermes LLM (no extra API key needed)
- No dependency on vision_analyze tool
- Fully integrated with your Hermes setup
- Respects your LLM provider choice

Usage:
    python parse_receipt_hermes_llm.py /path/to/receipt.jpg
    python parse_receipt_hermes_llm.py /path/to/receipt.jpg --no-insert  # Just parse, don't insert

Configuration:
    Reads from: ~/.hermes/config.yaml
    Section: model
"""

import sys
import os
import re
import json
import yaml
from pathlib import Path
import base64

# Try to import dependencies
try:
    from openai import OpenAI
    import psycopg2
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Install with: pip install openai pyyaml psycopg2-binary")
    sys.exit(1)

# Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "postgres",
    "password": "pg123",
    "database": "smart_expense",
    "port": 5432
}

HERMES_CONFIG_PATH = os.path.expanduser("~/.hermes/config.yaml")


def load_hermes_config() -> dict:
    """Load Hermes configuration from config.yaml."""
    try:
        with open(HERMES_CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"❌ Failed to load Hermes config: {e}")
        print(f"   Looking for: {HERMES_CONFIG_PATH}")
        sys.exit(1)


def get_llm_client(config: dict) -> tuple[OpenAI, str]:
    """Create OpenAI-compatible client from Hermes config."""
    model_config = config.get('model', {})
    
    base_url = model_config.get('base_url', '')
    api_key = model_config.get('api_key', '')
    model = model_config.get('default', 'kimi-k2.6')
    
    if not base_url:
        print("❌ No base_url found in Hermes config")
        sys.exit(1)
    
    if not api_key:
        print("❌ No api_key found in Hermes config")
        sys.exit(1)
    
    print(f"🔍 Using Hermes LLM configuration:")
    print(f"   Model: {model}")
    print(f"   Base URL: {base_url}")
    print(f"   API Key: {api_key[:10]}...")
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    return client, model


def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 data URL."""
    ext = Path(image_path).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.gif': 'image/gif'
    }
    mime = mime_types.get(ext, 'image/jpeg')
    
    with open(image_path, "rb") as image_file:
        base64_data = base64.b64encode(image_file.read()).decode('utf-8')
    
    return f"data:{mime};base64,{base64_data}"


def parse_receipt_with_hermes_llm(client: OpenAI, model: str, image_path: str) -> dict:
    """Parse receipt using Hermes-configured LLM."""
    print(f"\n🚀 Parsing receipt with Hermes LLM: {model}")
    print(f"   Image: {image_path}")
    
    # Convert image to base64
    try:
        image_url = image_to_base64(image_path)
    except Exception as e:
        print(f"❌ Error reading image: {e}")
        sys.exit(1)
    
    # Receipt parsing prompt
    prompt = """You are a receipt parsing assistant. Analyze this receipt image carefully.

Extract ALL transaction data and return ONLY valid JSON in this exact format:

{
  "merchant": "Store or restaurant name",
  "date": "YYYY-MM-DD or null",
  "time": "HH:MM or null",
  "amount_cents": 33900,  // Total amount in rupiah (integer, no decimals)
  "payment_method": "cash|card|transfer|e-wallet|other|null",
  "items": [
    {"name": "item name", "qty": 1, "unit_price": 4500, "total": 4500}
  ],
  "subtotal": 35200,  // Before discounts
  "discount": 1300,  // Total discounts
  "discount_note": "Description of discount",
  "cash_paid": 40000,  // If cash payment
  "change": 6100,  // Change returned
  "tax": null,  // Tax amount if any
  "notes": "Any additional info",
  "confidence": "high|medium|low"
}

Rules:
- If a field is missing or unclear, use null
- amount_cents is the FINAL total (after discounts)
- For Indonesian receipts: Rp amounts are in rupiah
- Items should include ALL line items if visible
- Be precise with numbers. Don't guess amounts.
- payment_method: 'cash' for TUNAI, 'e-wallet' for GoPay/OVO/DANA, 'card' for debit/credit
- Focus on accuracy. If unsure, set confidence to "low" and note in notes field.

Return ONLY the JSON. No markdown, no explanation, no ```json code blocks."""

    # Call LLM
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse response
        content = response.choices[0].message.content
        data = json.loads(content)
        
        print(f"\n✅ Receipt parsed successfully!")
        print(f"   Merchant: {data.get('merchant', 'Unknown')}")
        print(f"   Date: {data.get('date', 'Not found')}")
        print(f"   Time: {data.get('time', 'Not found')}")
        print(f"   Amount: Rp{data.get('amount_cents', 0):,.0f}")
        print(f"   Payment: {data.get('payment_method', 'Unknown')}")
        print(f"   Items: {len(data.get('items', []))} items")
        print(f"   Discount: Rp{data.get('discount', 0):,.0f}")
        print(f"   Confidence: {data.get('confidence', 'Unknown')}")
        
        return data
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        print(f"   Raw response: {content[:500]}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ LLM API error: {e}")
        sys.exit(1)


def guess_category(text: str, merchant_name: str = None) -> str:
    """Guess expense category based on receipt content."""
    text_lower = (text + " " + (merchant_name or "")).lower()
    
    # Food & Drinks
    if any(w in text_lower for w in [
        'makan', 'restoran', 'warung', 'kopi', 'cafe', 'food', 'nasi', 'bakso',
        'soto', 'mie', 'ayam', 'sate', 'goreng', 'burger', 'pizza', 'indofood',
        'minuman', 'drink', 'beverage', 'coffee', 'tea', 'ice cream', 'roti',
        'susu', 'yogurt', 'espresso', 'cafe'
    ]):
        return 'Food & Drinks'
    
    # Transportation
    elif any(w in text_lower for w in [
        'bensin', 'fuel', 'bahan bakar', 'spbu', 'pertamina', 'shell', 'bp',
        'parkir', 'tol', 'grab', 'gojek', 'ojek', 'taksi', 'taxi', 'bus',
        'kereta', 'train', 'bandara', 'airport'
    ]):
        return 'Transportation'
    
    # Shopping
    elif any(w in text_lower for w in [
        'alfamart', 'indomaret', 'supermarket', 'sembako', 'minimarket', 'ritel',
        'clothing', 'baju', 'pakaian', 'toko', 'shop', 'store', 'plastik'
    ]):
        return 'Shopping'
    
    # Entertainment
    elif any(w in text_lower for w in [
        'bioskop', 'cinema', 'film', 'teater', 'game', 'arcade', 'biliar',
        'karaoke', 'nonton', 'tiket', 'event', 'konser', 'musik'
    ]):
        return 'Entertainment'
    
    # Bills & Utilities
    elif any(w in text_lower for w in [
        'listrik', 'pln', 'pdam', 'air', 'telkom', 'internet', 'wifi', 'bpjs',
        'telepon', 'hp', 'pulsa', 'token', 'tagihan', 'bill'
    ]):
        return 'Bills & Utilities'
    
    # Health
    elif any(w in text_lower for w in [
        'apotek', 'obat', 'klinik', 'dokter', 'rumah sakit', 'hospital',
        'kesehatan', 'medis', 'farmasi', 'vitamin', 'suplemen'
    ]):
        return 'Health'
    
    # Education
    elif any(w in text_lower for w in [
        'buku', 'sekolah', 'kursus', 'bimbel', 'seminar', 'workshop',
        'stationery', 'alat tulis', 'toko buku'
    ]):
        return 'Education'
    
    # Housing
    elif any(w in text_lower for w in [
        'sewa', 'rent', 'kontrakan', 'kos', 'hotel', 'homestay', 'sewa rumah',
        'maintenance', 'perbaikan', 'tukang', 'service'
    ]):
        return 'Housing'
    
    else:
        return 'Other Expense'


def insert_transaction(data: dict, category: str = None, dry_run: bool = False) -> bool:
    """Insert parsed receipt data into smart_expense database."""
    
    # Build text for category guessing
    items_text = " ".join([item.get('name', '') for item in data.get('items', [])])
    notes_text = data.get('notes', '') or ''
    merchant = data.get('merchant', '')
    
    if category is None:
        category = guess_category(items_text + " " + notes_text, merchant)
    
    print(f"\n📊 Guessing category: {category}")
    
    if dry_run:
        print("💾 DRY RUN - Not inserting to database")
        return True
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get category ID
        cursor.execute(
            "SELECT id FROM categories WHERE name = %s AND type = 'expense' LIMIT 1",
            (category,)
        )
        row = cursor.fetchone()
        if not row:
            print(f"❌ Category '{category}' not found. Available categories:")
            cursor.execute("SELECT name FROM categories WHERE type = 'expense'")
            for r in cursor.fetchall():
                print(f"  - {r[0]}")
            return False
        category_id = row[0]
        
        # Build notes from items and receipt details
        items_lines = []
        for item in data.get('items', []):
            name = item.get('name', 'Unknown')
            qty = item.get('qty', 1)
            price = item.get('unit_price', 0)
            total = item.get('total', 0)
            items_lines.append(f"{name} x{qty} @ Rp{price:,.0f} = Rp{total:,.0f}")
        
        items_str = "; ".join(items_lines) if items_lines else data.get('notes', '')
        
        # Add discount info to notes
        discount = data.get('discount', 0)
        discount_note = data.get('discount_note', '')
        cash_paid = data.get('cash_paid')
        change = data.get('change')
        
        extra_notes = []
        if discount and discount > 0:
            extra_notes.append(f"Discount: Rp{discount:,.0f} ({discount_note})")
        if cash_paid:
            extra_notes.append(f"Cash: Rp{cash_paid:,.0f}")
        if change:
            extra_notes.append(f"Change: Rp{change:,.0f}")
        
        notes = items_str
        if extra_notes:
            notes += " | " + " | ".join(extra_notes)
        
        # Insert transaction
        cursor.execute("""
            INSERT INTO transactions (category_id, amount, type, description,
                                     transaction_date, payment_method, merchant, notes, tags)
            VALUES (%s, %s, 'expense', %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            category_id,
            data.get('amount_cents', 0),  # Already in rupiah
            merchant[:200] if merchant else 'Unknown',
            data.get('date'),
            data.get('payment_method', 'other'),
            merchant[:100] if merchant else 'Unknown',
            notes[:500],
            ["receipt", "hermes-llm", data.get('confidence', 'unknown')]
        ))
        conn.commit()
        tx_id = cursor.fetchone()[0]
        print(f"✅ Transaction added (ID: {tx_id})")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse receipt with Hermes LLM and insert into smart_expense")
    parser.add_argument("image", help="Path to receipt image")
    parser.add_argument("--category", help="Override auto-detected category")
    parser.add_argument("--no-insert", action="store_true", help="Parse only, don't insert to database")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full LLM response")
    
    args = parser.parse_args()
    
    # Validate image path
    if not os.path.exists(args.image):
        print(f"❌ File not found: {args.image}")
        sys.exit(1)
    
    # Load Hermes config
    print("📚 Loading Hermes configuration...")
    config = load_hermes_config()
    
    # Create LLM client from Hermes config
    client, model = get_llm_client(config)
    
    # Parse receipt
    data = parse_receipt_with_hermes_llm(client, model, args.image)
    
    # Show full response if verbose
    if args.verbose:
        print(f"\n📋 Full parsed data:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # Insert to database
    if data.get('amount_cents'):
        insert_transaction(data, category=args.category, dry_run=args.no_insert)
    else:
        print("⚠️  No amount detected. Skipping insertion.")


if __name__ == "__main__":
    main()
