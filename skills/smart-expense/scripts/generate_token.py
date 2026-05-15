#!/usr/bin/env python3
"""
Smart Expense — Token Generator

Generate a secure random authentication token for a Telegram user and
insert it into the `tokens` table.

Usage:
    python generate_token.py                              # Uses default Telegram ID (552378634)
    python generate_token.py 123456789                     # Generate for a specific Telegram ID
    python generate_token.py 123456789 --length 64        # Custom token length (default: 32)
    python generate_token.py 123456789 --quiet            # Just print the token, no extra output
"""

import sys
import secrets
import string
import argparse
import psycopg2
from datetime import datetime, timezone

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "postgres",
    "password": "pg123",
    "database": "smart_expense",
    "port": 5432,
}

DEFAULT_TELEGRAM_ID = 552378634
DEFAULT_TOKEN_LENGTH = 32


def generate_token(length: int = DEFAULT_TOKEN_LENGTH) -> str:
    """Generate a cryptographically secure random token."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def insert_token(telegram_id: int, token: str) -> bool:
    """Insert a token into the tokens table. Returns True if successful."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tokens (telegram_id, token, created_at) VALUES (%s, %s, %s)",
            (telegram_id, token, datetime.now(timezone.utc)),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except psycopg2.errors.UniqueViolation:
        print(f"⚠️  Token collision! This shouldn't happen with secure random. Retry.")
        return False
    except Exception as e:
        print(f"❌ Database error: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate auth token for Smart Expense")
    parser.add_argument("telegram_id", nargs="?", type=int, default=DEFAULT_TELEGRAM_ID,
                        help=f"Telegram user ID (default: {DEFAULT_TELEGRAM_ID})")
    parser.add_argument("--length", type=int, default=DEFAULT_TOKEN_LENGTH,
                        help=f"Token length in characters (default: {DEFAULT_TOKEN_LENGTH})")
    parser.add_argument("--quiet", action="store_true",
                        help="Only print the generated token")
    args = parser.parse_args()

    # Validate
    if args.length < 16:
        print("❌ Token length must be at least 16 characters for security.", file=sys.stderr)
        sys.exit(1)
    if args.length > 128:
        print("❌ Token length cannot exceed 128 characters.", file=sys.stderr)
        sys.exit(1)

    # Generate
    token = generate_token(args.length)

    # Insert
    if not insert_token(args.telegram_id, token):
        sys.exit(1)

    if args.quiet:
        print(token)
    else:
        print(f"✅ Token generated and saved!")
        print(f"   Telegram ID : {args.telegram_id}")
        print(f"   Token       : {token}")
        print(f"   Length      : {args.length} chars")
        print(f"   Created at  : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print()
        print(f"🔐 Use this token for API authentication:")
        print(f"   Authorization: Bearer {token}")


if __name__ == "__main__":
    main()
