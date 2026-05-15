#!/usr/bin/env python3
"""
Test receipt parsing with LLM vision API
"""
import sys
import os
import json
import base64

# Try to import required packages
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

# Get API key - check environment or ask user
api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENROUTER_API_KEY')

if not api_key:
    print("❌ No API key found. Please set OPENAI_API_KEY or OPENROUTER_API_KEY environment variable.")
    sys.exit(1)

# Use OpenRouter as fallback if no OpenAI key
base_url = "https://openrouter.ai/api/v1" if "OPENROUTER" in os.environ else "https://api.openai.com/v1"
model = "google/palm-2" if "OPENROUTER" in os.environ else "gpt-4o"

print(f"🔍 Using LLM: {model}")
print(f"   Base URL: {base_url}")

# Read and encode image
image_path = '/Users/apple/.hermes/image_cache/img_f87b00c64cd8.jpg'
with open(image_path, 'rb') as f:
    img_base64 = base64.b64encode(f.read()).decode('utf-8')

image_data_url = f"data:image/jpeg;base64,{img_base64}"

# Prompt for receipt parsing
prompt = """You are a receipt parsing assistant. Extract ALL data from this Indomaret receipt.

Return ONLY valid JSON in this EXACT format (no markdown, no extra text):
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
  "notes": "Additional notes about the receipt"
}

Extract ALL data accurately. If any field is missing, use null."""

print("\n📸 Analyzing receipt with LLM...")
print(f"   Image size: {len(img_base64)} base64 chars")
print(f"   Prompt length: {len(prompt)} chars")

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
                        "image_url": {"url": image_data_url}
                    },
                    {"type": "text", "text": prompt}
                ]
            }
        ],
        response_format={"type": "json_object"}
    )
    
    # Parse response
    content = response.choices[0].message.content
    print(f"\n✅ LLM response received!")
    print(f"   Response length: {len(content)} chars")
    
    # Try to parse JSON
    try:
        data = json.loads(content)
        print(f"\n📊 Parsed JSON successfully!")
        print(f"\nExtracted data:")
        print(f"  Merchant: {data.get('merchant', 'Unknown')}")
        print(f"  Date: {data.get('date', 'Unknown')}")
        print(f"  Time: {data.get('time', 'Unknown')}")
        print(f"  Amount: Rp{data.get('amount_cents', 0):,.0f}")
        print(f"  Payment: {data.get('payment_method', 'Unknown')}")
        print(f"  Items: {len(data.get('items', []))} items")
        print(f"  Subtotal: Rp{data.get('subtotal', 0):,.0f}")
        print(f"  Discount: Rp{data.get('discount', 0):,.0f}")
        print(f"  Cash Paid: Rp{data.get('cash_paid', 0):,.0f}")
        print(f"  Change: Rp{data.get('change', 0):,.0f}")
        print(f"  You Saved: Rp{data.get('you_saved', 0):,.0f}")
        
        # Store for next step
        with open('/tmp/parsed_receipt.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n💾 Saved to /tmp/parsed_receipt.json")
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        print(f"\nRaw response:\n{content}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ LLM API error: {e}")
    sys.exit(1)
