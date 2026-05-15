#!/usr/bin/env python3
"""
Financial Advisor AI for Smart Expense

Generates financial insights and advice for transactions using Hermes LLM.
Supports:
- Single transaction analysis
- Multi-month transaction pattern analysis
- Budget recommendations
- Spending trend detection

Usage:
    python financial_advisor.py <transaction_id>
    python financial_advisor.py --analyze-month 2024-09
    python financial_advisor.py --generate-all-comments
"""

import sys
import os
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path

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
        sys.exit(1)


def get_llm_client(config: dict):
    """Create OpenAI-compatible client from Hermes config."""
    model_config = config.get('model', {})
    
    base_url = model_config.get('base_url', '')
    api_key = model_config.get('api_key', '')
    model = model_config.get('default', 'kimi-k2.6')
    
    if not base_url or not api_key:
        print("❌ Missing base_url or api_key in Hermes config")
        sys.exit(1)
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    return client, model


def get_transaction_data(tx_id: str):
    """Fetch transaction data from database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                t.id,
                t.transaction_date,
                t.amount,
                t.type,
                t.description,
                t.payment_method,
                t.merchant,
                t.notes,
                t.tags,
                t.llm_comment,
                t.llm_comment_at,
                c.name as category,
                c.type as category_type
            FROM transactions t
            JOIN categories c ON c.id = t.category_id
            WHERE t.id = %s
        """, (tx_id,))
        
        row = cursor.fetchone()
        if not row:
            print(f"❌ Transaction not found: {tx_id}")
            return None
        
        # Convert to dict
        columns = [desc[0] for desc in cursor.description]
        transaction = dict(zip(columns, row))
        
        conn.close()
        return transaction
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return None


def get_transactions_by_month(year: int, month: int):
    """Fetch all transactions for a specific month."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        
        cursor.execute("""
            SELECT 
                t.id,
                t.transaction_date,
                t.amount,
                t.type,
                t.description,
                t.payment_method,
                t.merchant,
                t.notes,
                t.tags,
                t.llm_comment,
                c.name as category,
                c.type as category_type
            FROM transactions t
            JOIN categories c ON c.id = t.category_id
            WHERE t.transaction_date >= %s 
              AND t.transaction_date < %s
            ORDER BY t.transaction_date DESC
        """, (start_date, end_date))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        transactions = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return transactions
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return []


def get_multi_month_data(months_back: int = 3):
    """Fetch transactions for multiple months for pattern analysis."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        cursor.execute("""
            SELECT 
                t.id,
                t.transaction_date,
                t.amount,
                t.type,
                t.description,
                t.payment_method,
                t.merchant,
                t.notes,
                t.tags,
                t.llm_comment,
                c.name as category,
                c.type as category_type
            FROM transactions t
            JOIN categories c ON c.id = t.category_id
            WHERE t.transaction_date >= %s
            ORDER BY t.transaction_date DESC
        """, (start_date.strftime('%Y-%m-%d'),))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        transactions = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return transactions
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return []


def generate_transaction_comment(client, model, transaction: dict) -> str:
    """Generate financial advisor comment for a single transaction."""
    
    prompt = f"""You are a personal financial advisor. Analyze this transaction and provide concise, actionable financial advice.

Transaction Details:
- Date: {transaction['transaction_date']}
- Merchant: {transaction['merchant']}
- Category: {transaction['category']}
- Amount: Rp{transaction['amount']:,.0f}
- Type: {transaction['type']}
- Payment: {transaction['payment_method']}
- Description: {transaction['description']}
- Notes: {transaction['notes'][:200] if transaction['notes'] else 'None'}

Provide advice in Indonesian (user's language). Keep it concise (max 3-4 sentences) and actionable.

Format your response as JSON:
{{
  "comment": "Your financial advice in Indonesian",
  "sentiment": "positive|neutral|negative",
  "action_items": ["action 1", "action 2"],
  "confidence": "high|medium|low"
}}

Rules:
- For expenses: Suggest budget tips, alternatives, or savings opportunities
- For income: Suggest investment or savings strategies
- Be practical and culturally appropriate for Indonesian context
- Reference specific amounts and categories
- Keep it encouraging but honest

Return ONLY valid JSON, no extra text."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"❌ LLM error: {e}")
        return None


def generate_monthly_insights(client, model, year: int, month: int, transactions: list) -> str:
    """Generate monthly financial insights and recommendations."""
    
    if not transactions:
        return {"comment": f"No transactions found for {year}-{month:02d}"}
    
    # Calculate statistics
    total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    net = total_income - total_expenses
    
    # Group by category
    by_category = {}
    for t in transactions:
        cat = t['category']
        if cat not in by_category:
            by_category[cat] = {'count': 0, 'total': 0}
        by_category[cat]['count'] += 1
        if t['type'] == 'expense':
            by_category[cat]['total'] += t['amount']
    
    # Find top spending category
    top_category = max(by_category.items(), key=lambda x: x[1]['total']) if by_category else None
    
    prompt = f"""You are a personal financial advisor. Analyze this month's spending pattern and provide insights.

Month: {year}-{month:02d}
Total Transactions: {len(transactions)}
Total Expenses: Rp{total_expenses:,.0f}
Total Income: Rp{total_income:,.0f}
Net (Income - Expenses): Rp{net:,.0f}

Top Spending Categories:
{chr(10).join(f"- {cat}: Rp{data['total']:,.0f} ({data['count']} transactions)" for cat, data in sorted(by_category.items(), key=lambda x: x[1]['total'], reverse=True)[:5])}

Top Merchants:
{chr(10).join(f"- {t['merchant']}: Rp{t['amount']:,.0f}" for t in sorted(transactions, key=lambda x: x['amount'], reverse=True)[:5])}

Provide insights in Indonesian (user's language). Keep it concise (max 5-6 sentences).

Format your response as JSON:
{{
  "monthly_comment": "Monthly financial summary and insights in Indonesian",
  "savings_opportunity": "Specific suggestion to save money",
  "spending_warning": "Red flag if spending is too high, null otherwise",
  "positive_notes": "What went well this month",
  "action_items": ["action 1", "action 2"],
  "confidence": "high|medium|low"
}}

Rules:
- Be encouraging but realistic
- Reference specific amounts and categories
- Suggest actionable improvements
- Consider Indonesian economic context
- If net is positive, suggest savings/investment strategies
- If net is negative, suggest budget cuts

Return ONLY valid JSON, no extra text."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"❌ LLM error: {e}")
        return None


def generate_multi_month_trends(client, model, transactions: list, months_back: int = 3) -> str:
    """Generate multi-month trend analysis."""
    
    if len(transactions) < 3:
        return {"comment": "Not enough data for trend analysis yet."}
    
    prompt = f"""You are a personal financial advisor. Analyze spending trends over {months_back} months.

Total Transactions Analyzed: {len(transactions)}

Provide trend analysis in Indonesian (user's language). Keep it concise (max 4-5 sentences).

Format your response as JSON:
{{
  "trend_comment": "Trend analysis in Indonesian",
  "spending_trend": "increasing|decreasing|stable",
  "pattern_insights": ["insight 1", "insight 2"],
  "recommendations": ["recommendation 1", "recommendation 2"],
  "confidence": "high|medium|low"
}}

Rules:
- Identify spending patterns (e.g., "increasing food costs")
- Point out concerning trends
- Suggest specific improvements
- Be data-driven and actionable
- Consider Indonesian economic context

Return ONLY valid JSON, no extra text."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"❌ LLM error: {e}")
        return None


def save_transaction_comment(tx_id: str, comment_data: dict):
    """Save LLM comment to transaction."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        comment_text = comment_data.get('comment', '')
        sentiment = comment_data.get('sentiment', 'neutral')
        action_items = comment_data.get('action_items', [])
        confidence = comment_data.get('confidence', 'high')
        
        # Format action items as string for storage
        actions_str = ", ".join(action_items) if action_items else ""
        
        cursor.execute("""
            UPDATE transactions
            SET 
                llm_comment = %s,
                llm_comment_at = NOW()
            WHERE id = %s
        """, (f"{comment_text} | Actions: {actions_str} | Sentiment: {sentiment} | Confidence: {confidence}", tx_id))
        
        conn.commit()
        print(f"✅ Comment saved for transaction {tx_id}")
        
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")


def save_monthly_insight(year: int, month: int, insight_data: dict):
    """Save monthly insights (stored as a special transaction or in a separate table)."""
    print(f"💾 Monthly insights for {year}-{month:02d}:")
    print(f"   {insight_data.get('monthly_comment', 'No comment')}")
    print(f"   Savings opportunity: {insight_data.get('savings_opportunity', 'N/A')}")
    if insight_data.get('spending_warning'):
        print(f"   ⚠️  {insight_data['spending_warning']}")


def save_trend_analysis(months_back: int, trend_data: dict):
    """Save trend analysis."""
    print(f"💾 {months_back}-month trend analysis:")
    print(f"   {trend_data.get('trend_comment', 'No comment')}")
    print(f"   Trend: {trend_data.get('spending_trend', 'unknown')}")
    for insight in trend_data.get('pattern_insights', []):
        print(f"   - {insight}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Financial Advisor AI for Smart Expense")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Transaction comment command
    tx_parser = subparsers.add_parser('comment', help='Generate comment for a transaction')
    tx_parser.add_argument('transaction_id', help='Transaction ID')
    
    # Monthly analysis command
    month_parser = subparsers.add_parser('analyze-month', help='Analyze a specific month')
    month_parser.add_argument('year', type=int, help='Year (e.g., 2024)')
    month_parser.add_argument('month', type=int, help='Month (1-12)')
    
    # Multi-month trends command
    trend_parser = subparsers.add_parser('analyze-trends', help='Analyze spending trends')
    trend_parser.add_argument('--months', type=int, default=3, help='Number of months to analyze')
    
    # Generate all comments command
    all_parser = subparsers.add_parser('generate-all-comments', help='Generate comments for all transactions without comments')
    
    args = parser.parse_args()
    
    # Load Hermes config
    print("📚 Loading Hermes configuration...")
    config = load_hermes_config()
    
    # Create LLM client
    client, model = get_llm_client(config)
    print(f"🔍 Using LLM: {model}")
    
    if args.command == 'comment':
        # Single transaction comment
        transaction = get_transaction_data(args.transaction_id)
        if not transaction:
            sys.exit(1)
        
        print(f"\n📊 Analyzing transaction: {transaction['merchant']} - Rp{transaction['amount']:,.0f}")
        
        comment_data = generate_transaction_comment(client, model, transaction)
        if comment_data:
            print(f"\n💬 Generated comment:")
            print(f"   {comment_data.get('comment', 'N/A')}")
            print(f"   Sentiment: {comment_data.get('sentiment', 'N/A')}")
            print(f"   Actions: {', '.join(comment_data.get('action_items', []))}")
            
            # Save to database
            save_transaction_comment(args.transaction_id, comment_data)
        
    elif args.command == 'analyze-month':
        # Monthly analysis
        print(f"\n📅 Analyzing {args.year}-{args.month:02d}...")
        transactions = get_transactions_by_month(args.year, args.month)
        
        if not transactions:
            print("❌ No transactions found for this month")
            sys.exit(0)
        
        insight_data = generate_monthly_insights(client, model, args.year, args.month, transactions)
        if insight_data:
            save_monthly_insight(args.year, args.month, insight_data)
            
    elif args.command == 'analyze-trends':
        # Multi-month trends
        print(f"\n📈 Analyzing {args.months}-month trends...")
        transactions = get_multi_month_data(args.months)
        
        if len(transactions) < 3:
            print("⚠️  Not enough data for trend analysis yet")
            sys.exit(0)
        
        trend_data = generate_multi_month_trends(client, model, transactions, args.months)
        if trend_data:
            save_trend_analysis(args.months, trend_data)
            
    elif args.command == 'generate-all-comments':
        # Generate comments for all transactions without comments
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id FROM transactions 
                WHERE llm_comment IS NULL
                ORDER BY transaction_date DESC
            """)
            
            transactions_to_process = [row[0] for row in cursor.fetchall()]
            print(f"\n📝 Found {len(transactions_to_process)} transactions without comments")
            
            for i, tx_id in enumerate(transactions_to_process, 1):
                print(f"\n[{i}/{len(transactions_to_process)}] Processing {tx_id}...")
                transaction = get_transaction_data(tx_id)
                if transaction:
                    comment_data = generate_transaction_comment(client, model, transaction)
                    if comment_data:
                        save_transaction_comment(tx_id, comment_data)
                        print(f"   ✅ Comment generated")
                    else:
                        print(f"   ❌ Failed to generate comment")
                else:
                    print(f"   ❌ Transaction not found")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
