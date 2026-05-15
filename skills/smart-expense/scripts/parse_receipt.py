#!/usr/bin/env python3
"""
Receipt Parser for Smart Expense

Parse receipt images (struk/nota) using Tesseract OCR and auto-insert into
smart_expense PostgreSQL database.

Usage:
    python parse_receipt.py /path/to/receipt.jpg [--merchant "Optional name"]
    python parse_receipt.py /path/to/receipt.jpg --vision  # Use vision AI instead

Requires:
    - tesseract CLI installed
    - pytesseract, Pillow
    - psycopg2
    - PostgreSQL connection: PGPASSWORD=pg123 psql -h localhost -U postgres -d smart_expense

Indonesian language support: ind.traineddata
"""

import sys
import os
import re
import json
from pathlib import Path

# Try to import dependencies
try:
    import pytesseract
    from PIL import Image
    import psycopg2
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Install with: pip install pytesseract Pillow psycopg2-binary")
    sys.exit(1)

# Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "postgres",
    "password": "pg123",
    "database": "smart_expense",
    "port": 5432
}


def guess_category(text: str, merchant_name: str = None) -> str:
    """Guess category based on receipt text and merchant name."""
    text_lower = (text + " " + (merchant_name or "")).lower()
    
    # Food & Drinks
    if any(w in text_lower for w in [
        'makan', 'restoran', 'warung', 'kopi', 'cafe', 'food', 'nasi', 'bakso', 
        'soto', 'mie', 'ayam', 'sate', 'goreng', 'burger', 'pizza', 'pizza',
        'indofood', 'minuman', 'drink', 'beverage', 'coffee', 'tea', 'ice cream'
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
        'clothing', 'baju', 'pakaian', 'toko', 'shop', 'store'
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
        'buku', 'sekolah', 'kursus', 'bimbel', 'seminar', 'workshop', 'kopi',
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


def parse_receipt_ocr(image_path: str) -> dict:
    """Parse receipt using Tesseract OCR."""
    print(f"🔍 Scanning receipt: {image_path}")
    
    # Run Tesseract OCR
    result = os.popen(f'tesseract "{image_path}" stdout -l ind+eng 2>/dev/null').read()
    
    if not result.strip():
        print("❌ No text found. Try a clearer image or use --vision instead.")
        sys.exit(1)
    
    # Extract merchant (first non-empty line)
    lines = [l.strip() for l in result.strip().split('\n') if l.strip()]
    merchant = lines[0] if lines else "Unknown"
    
    # Extract date (various Indonesian formats)
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # 15/5/25, 15-05-2025
        r'(\d{2}\s+\w+\s+\d{4})',             # 15 Mei 2025
        r'(\d{4}-\d{2}-\d{2})'                # 2025-05-15
    ]
    date = None
    for pattern in date_patterns:
        match = re.search(pattern, result)
        if match:
            date = match.group(1)
            break
    
    # Extract amount (various formats)
    amount_patterns = [
        r'(?:total|jumlah|TOTAL|JUMLAH|amount|Amount)\s*[:=]?\s*Rp?\.?\s*([\d.,]+)',
        r'Rp\s*([\d.,]+)',
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:IDR|rupiah|Rp)\b',
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*IDR\b'
    ]
    amount = None
    for pattern in amount_patterns:
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            amount = float(match.group(1).replace('.', '').replace(',', '.'))
            break
    
    # Extract payment method
    payment_patterns = [
        (r'(?:tunai|cash)', 'cash'),
        (r'(?:transfer|bca|mandiri|bni|bri)', 'transfer'),
        (r'(?:gopay|ovo|dana|shopeepay|linkaja)', 'e-wallet'),
        (r'(?:kartu|card|visa|mastercard)', 'card')
    ]
    payment_method = 'other'
    for pattern, method in payment_patterns:
        if re.search(pattern, result, re.IGNORECASE):
            payment_method = method
            break
    
    # Extract items (lines with price)
    item_patterns = [
        r'^(.+?)\s+x\s+([\d.,]+)\s*=\s*([\d.,]+)$',  # Item x 1 = 10,000
        r'^(.+?)\s+([\d.,]+)$'  # Item 10,000
    ]
    items = []
    for line in lines[1:]:  # Skip first line (merchant)
        for pattern in item_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    items.append(f"{match.group(1)} x{match.group(2)} = Rp{match.group(3).replace('.', '').replace(',', '.')}")
                else:
                    items.append(f"{match.group(1)} Rp{match.group(2).replace('.', '').replace(',', '.')}")
                break
    
    # Parse full text for notes
    full_text = "\n".join(items[:10]) if items else result[:200]
    
    return {
        "merchant": merchant,
        "date": date,
        "amount": amount,
        "payment_method": payment_method,
        "items": items[:5],
        "notes": full_text,
        "raw_text": result[:500]
    }


def insert_transaction(data: dict, category: str = None) -> bool:
    """Insert parsed receipt data into smart_expense database."""
    
    if category is None:
        category = guess_category(data["notes"], data["merchant"])
    
    print(f"📊 Guessing category: {category}")
    
    # Get category ID
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
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
        
        # Insert transaction
        cursor.execute("""
            INSERT INTO transactions (category_id, amount, type, description, 
                                     transaction_date, payment_method, merchant, notes, tags)
            VALUES (%s, %s, 'expense', %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            category_id,
            data["amount"],
            data["merchant"][:200],
            data["date"],
            data["payment_method"],
            data["merchant"][:100],
            data["notes"][:500],
            ["receipt", "scanned"]
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
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python parse_receipt.py /path/to/receipt.jpg [--merchant 'Optional name']")
        print("  python parse_receipt.py /path/to/receipt.jpg --vision")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        sys.exit(1)
    
    # Parse receipt
    data = parse_receipt_ocr(image_path)
    
    print("\n📄 Parsed receipt data:")
    print(f"  Merchant: {data['merchant']}")
    print(f"  Date: {data['date'] or '(not detected)'}")
    print(f"  Amount: Rp{data['amount']:,.0f}" if data['amount'] else "  Amount: (not detected)")
    print(f"  Payment: {data['payment_method']}")
    print(f"  Items: {', '.join(data['items'][:3])}..." if data['items'] else "  Items: (none detected)")
    
    # Insert into database
    if data["amount"]:
        insert_transaction(data)
    else:
        print("⚠️  No amount detected. Skipping insertion.")


if __name__ == "__main__":
    main()
