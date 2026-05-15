#!/usr/bin/env python3
"""
LLM-Based Receipt Parser for Smart Expense

Parse receipt images using an OpenAI-compatible vision LLM (GPT-4o, Claude, LLaVA, etc.)
and auto-insert into smart_expense PostgreSQL database.

This is the RECOMMENDED approach - LLMs are far more accurate than regex-based OCR.

Usage:
    python parse_receipt_llm.py /path/to/receipt.jpg [--model gpt-4o]
    python parse_receipt_llm.py /path/to/receipt.jpg --base-url https://api.openai.com/v1
    python parse_receipt_llm.py /path/to/receipt.jpg --prompt "custom prompt here"

Requires:
    - openai Python SDK: pip install openai
    - psycopg2: pip install psycopg2-binary
    - An OpenAI-compatible LLM endpoint with vision support

Configuration:
    - Set OPENAI_API_KEY and OPENAI_BASE_URL in environment variables, OR
    - Pass --api-key and --base-url on command line
"""

import sys
import os
import re
import json
from pathlib import Path

# Try to import dependencies
try:
    from openai import OpenAI
    import psycopg2
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Install with: pip install openai psycopg2-binary")
    sys.exit(1)

# Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "postgres",
    "password": "pg123",
    "database": "smart_expense",
    "port": 5432
}

# Default LLM endpoint (can be overridden)
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o"

# Default prompt for best results
DEFAULT_PROMPT = """You are a receipt parsing assistant. Extract data from this receipt image.

Return ONLY valid JSON in this exact format:
{{
  "merchant": "store/restaurant name (string)",
  "date": "YYYY-MM-DD or null if not found",
  "amount_cents": 75000,  // integer, in rupiah (e.g. 75000 = Rp75,000)
  "payment_method": "cash|card|transfer|e-wallet|other|null",
  "items": [
    {{"name": "item name", "price": 25000}}
  ],
  "confidence": "high|medium|low",
  "notes": "any additional info"
}}

Rules:
- If a field is missing, use null
- amount_cents should be the TOTAL amount (integer, in rupiah)
- payment_method: guess based on keywords (tunai=cash, transfer=transfer, gopay/ovo/dana=e-wallet, card=card)
- Be exact. Do not add extra fields or explanations.
- Focus on Indonesian receipts (Rp currency, Indonesian text)
"""


def guess_category(text: str, merchant_name: str = None) -> str:
    """Guess category based on receipt text and merchant name."""
    text_lower = (text + " " + (merchant_name or "")).lower()
    
    if any(w in text_lower for w in ['makan', 'restoran', 'warung', 'kopi', 'cafe', 'food', 'nasi', 'bakso', 'soto', 'mie', 'ayam', 'sate', 'goreng', 'burger', 'pizza', 'indofood', 'minuman', 'drink', 'beverage', 'coffee', 'tea', 'ice cream']):
        return 'Food & Drinks'
    elif any(w in text_lower for w in ['bensin', 'fuel', 'bahan bakar', 'spbu', 'pertamina', 'shell', 'bp', 'parkir', 'tol', 'grab', 'gojek', 'ojek', 'taksi', 'taxi', 'bus', 'kereta', 'train', 'bandara', 'airport']):
        return 'Transportation'
    elif any(w in text_lower for w in ['alfamart', 'indomaret', 'supermarket', 'sembako', 'minimarket', 'ritel', 'clothing', 'baju', 'pakaian', 'toko', 'shop', 'store']):
        return 'Shopping'
    elif any(w in text_lower for w in ['bioskop', 'cinema', 'film', 'teater', 'game', 'arcade', 'biliar', 'karaoke', 'nonton', 'tiket', 'event', 'konser', 'musik']):
        return 'Entertainment'
    elif any(w in text_lower for w in ['listrik', 'pln', 'pdam', 'air', 'telkom', 'internet', 'wifi', 'bpjs', 'telepon', 'hp', 'pulsa', 'token', 'tagihan', 'bill']):
        return 'Bills & Utilities'
    elif any(w in text_lower for w in ['apotek', 'obat', 'klinik', 'dokter', 'rumah sakit', 'hospital', 'kesehatan', 'medis', 'farmasi', 'vitamin', 'suplemen']):
        return 'Health'
    elif any(w in text_lower for w in ['buku', 'sekolah', 'kursus', 'bimbel', 'seminar', 'workshop', 'stationery', 'alat tulis', 'toko buku']):
        return 'Education'
    elif any(w in text_lower for w in ['sewa', 'rent', 'kontrakan', 'kos', 'hotel', 'homestay', 'sewa rumah', 'maintenance', 'perbaikan', 'tukang', 'service']):
        return 'Housing'
    else:
        return 'Other Expense'


def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return "data:" + get_image_mime_type(image_path) + ";base64," + base64.b64encode(image_file.read()).decode()


def get_image_mime_type(image_path: str) -> str:
    """Get MIME type for image file."""
    ext = Path(image_path).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.gif': 'image/gif'
    }
    return mime_types.get(ext, 'image/jpeg')


def parse_receipt_llm(image_path: str, api_key: str, base_url: str, model: str, prompt: str) -> dict:
    """Parse receipt using LLM vision API."""
    print(f"🔍 Analyzing receipt with LLM: {image_path}")
    print(f"   Model: {model}")
    print(f"   Endpoint: {base_url}")
    
    # Convert image to base64
    try:
        image_base64 = image_to_base64(image_path)
    except Exception as e:
        print(f"❌ Error reading image: {e}")
        sys.exit(1)
    
    # Initialize client
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
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
                            "image_url": {"url": image_base64}
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        content = response.choices[0].message.content
        data = json.loads(content)
        
        print(f"✅ LLM parsed receipt:")
        print(f"   Merchant: {data.get('merchant', 'Unknown')}")
        print(f"   Date: {data.get('date', 'Not found')}")
        print(f"   Amount: Rp{data.get('amount_cents', 0):,.0f}" if data.get('amount_cents') else "   Amount: Not found")
        print(f"   Payment: {data.get('payment_method', 'Unknown')}")
        print(f"   Items: {len(data.get('items', []))} items detected")
        print(f"   Confidence: {data.get('confidence', 'Unknown')}")
        
        return data
        
    except Exception as e:
        print(f"❌ LLM error: {e}")
        sys.exit(1)


def insert_transaction(data: dict, category: str = None) -> bool:
    """Insert parsed receipt data into smart_expense database."""
    
    if category is None:
        # Build text from items and notes
        items_text = " ".join([item.get('name', '') for item in data.get('items', [])])
        notes_text = data.get('notes', '') or ''
        category = guess_category(items_text + " " + notes_text, data.get('merchant'))
    
    print(f"📊 Guessing category: {category}")
    
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
        
        # Build notes from items
        items_str = ", ".join([f"{item.get('name', 'Unknown')} Rp{item.get('price', 0):,.0f}" for item in data.get('items', [])])
        notes = f"{items_str}" if items_str else data.get('notes', '')
        
        # Insert transaction
        cursor.execute("""
            INSERT INTO transactions (category_id, amount, type, description, 
                                     transaction_date, payment_method, merchant, notes, tags)
            VALUES (%s, %s, 'expense', %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            category_id,
            data.get('amount_cents', 0) / 100.0,  # Convert from cents to rupiah
            data.get('merchant', 'Unknown')[:200],
            data.get('date'),
            data.get('payment_method', 'other'),
            data.get('merchant', 'Unknown')[:100],
            notes[:500],
            ["receipt", "llm-parsed"]
        ))
        conn.commit()
        print(f"✅ Transaction added (ID: {cursor.fetchone()[0]})")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse receipt with LLM and insert into smart_expense")
    parser.add_argument("image", help="Path to receipt image")
    parser.add_argument("--api-key", env="OPENAI_API_KEY", help="API key for LLM endpoint")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="LLM API base URL")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="LLM model to use")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Custom prompt for LLM")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.api_key:
        print("❌ API key required. Set OPENAI_API_KEY env var or use --api-key")
        sys.exit(1)
    
    if not os.path.exists(args.image):
        print(f"❌ File not found: {args.image}")
        sys.exit(1)
    
    # Parse receipt
    data = parse_receipt_llm(args.image, args.api_key, args.base_url, args.model, args.prompt)
    
    # Insert into database
    if data.get('amount_cents'):
        insert_transaction(data)
    else:
        print("⚠️  No amount detected. Skipping insertion.")


if __name__ == "__main__":
    main()
