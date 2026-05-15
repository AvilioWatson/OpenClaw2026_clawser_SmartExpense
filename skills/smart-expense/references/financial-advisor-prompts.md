# Financial Advisor Prompts

## Prompt Engineering for Expense Analysis

### 1. Transaction Analysis Prompt

**Purpose:** Generate personalized financial advice for a single transaction

**Template:**
```text
You are a personal financial advisor. Analyze this transaction and provide 
concise, actionable financial advice.

Transaction Details:
- Date: {date}
- Merchant: {merchant}
- Category: {category}
- Amount: Rp{amount}
- Type: {type}
- Payment: {payment_method}

Provide advice in Indonesian. Keep it concise (max 3-4 sentences).

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

Return ONLY valid JSON, no extra text.
```

**Key Features:**
- Forces JSON output via `response_format={"type": "json_object"}`
- Context-aware (different advice for expense vs income)
- Culturally localized (Indonesian language)
- Actionable items included

---

### 2. Monthly Insights Prompt

**Purpose:** Generate comprehensive monthly spending analysis

**Template:**
```text
You are a personal financial advisor. Analyze this month's spending pattern.

Month: {year}-{month}
Total Transactions: {count}
Total Expenses: Rp{expenses}
Total Income: Rp{income}
Net (Income - Expenses): Rp{net}

Top Spending Categories:
{category_list}

Top Merchants:
{merchant_list}

Provide insights in Indonesian. Keep it concise (max 5-6 sentences).

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

Return ONLY valid JSON, no extra text.
```

**Key Features:**
- Monthly aggregation
- Top categories and merchants
- Deficit/surplus analysis
- Risk warnings when spending exceeds income

---

### 3. Trend Analysis Prompt

**Purpose:** Identify spending patterns over multiple months

**Template:**
```text
You are a personal financial advisor. Analyze spending trends over {months} months.

Total Transactions Analyzed: {count}

Provide trend analysis in Indonesian. Keep it concise (max 4-5 sentences).

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

Return ONLY valid JSON, no extra text.
```

**Key Features:**
- Multi-month pattern detection
- Trend classification (increasing/decreasing/stable)
- Specific insight extraction
- Actionable recommendations

---

### 4. Receipt Parsing Prompt

**Purpose:** Extract structured data from receipt images

**Template:**
```text
You are a receipt parsing assistant. Extract ALL data from this receipt.

Return ONLY valid JSON in this EXACT format (no markdown, no extra text):
{{
  "merchant": "Store name",
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "amount_cents": 33900,
  "payment_method": "cash|card|transfer|e-wallet",
  "items": [
    {{"name": "Item name", "qty": 1, "unit_price": 10000, "total": 10000}}
  ],
  "subtotal": 35200,
  "discount": 1300,
  "discount_note": "DISKON description",
  "cash_paid": 40000,
  "change": 6100,
  "tax": null,
  "notes": "Additional notes",
  "confidence": "high|medium|low"
}}

Extract ALL data accurately. If any field is missing, use null.
Rules:
- Amounts are in Rupiah (Indonesian currency)
- Parse Indonesian date formats (DD.MM.YY, DD/MM/YYYY)
- Handle discounts as negative values
- Extract itemized list if present
- Payment methods: cash, card, e-wallet, transfer
- Confidence: high (clear), medium (ambiguous), low (unclear)

Return ONLY valid JSON, no extra text.
```

**Key Features:**
- Strict JSON output
- Indonesian date format support
- Item-level extraction
- Discount handling
- Confidence scoring

---

## Prompt Engineering Best Practices

### 1. **Force JSON Output**
```python
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"}  # ← Forces JSON
)
```

### 2. **Truncate Long Content**
```python
notes[:200] if notes else 'None'  # Prevent token overflow
```

### 3. **Include Examples in Prompt**
```text
Format your response as JSON:
{{"example": "value"}}
```

### 4. **Specify Language**
```text
Provide advice in Indonesian (user's language).
```

### 5. **Set Confidence Thresholds**
```text
Confidence: high (clear), medium (ambiguous), low (unclear)
```

---

## Response Handling

### Error Handling Pattern
```python
try:
    response = client.chat.completions.create(...)
    return json.loads(response.choices[0].message.content)
except json.JSONDecodeError:
    print("Failed to parse JSON, retrying...")
except Exception as e:
    print(f"LLM API error: {e}")
    return None
```

### Result Validation
```python
def validate_comment(comment_data: dict) -> bool:
    required = ['comment', 'sentiment', 'confidence']
    return all(key in comment_data for key in required)
```

---

## Tips for Better Results

1. **Be Specific:** Include exact amounts, dates, and categories
2. **Provide Context:** Include payment method, merchant, and notes
3. **Use Indonesian:** User prefers Indonesian language
4. **Keep Concise:** Limit to 3-6 sentences for readability
5. **Be Actionable:** Always include specific action items
6. **Add Confidence:** Helps filter low-quality responses
7. **Cultural Context:** Reference Indonesian economic context

---

**Version:** 1.0  
**Date:** 2026-05-15  
**Author:** zuzu
