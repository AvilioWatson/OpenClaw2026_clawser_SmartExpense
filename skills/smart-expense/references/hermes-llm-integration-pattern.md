# Hermes LLM Integration Pattern

**Session-specific detail**: Pattern for using Hermes LLM configuration directly instead of `vision_analyze` tool for receipt parsing and financial analysis.

---

## Why This Pattern?

During the Smart Expense receipt parsing session, we discovered that using the **Hermes LLM configuration directly** is superior to the `vision_analyze` tool for several reasons:

### Comparison

| Approach | Setup | Integration | Flexibility |
|----------|-------|-------------|-------------|
| `vision_analyze` tool | ✅ Zero | ⚠️ Separate tool | ⚠️ Limited |
| **Hermes LLM directly** | ✅ Zero | ✅ **Fully integrated** | ✅ **Maximum** |

### Key Benefits

1. **Zero extra setup** - Uses your existing `~/.hermes/config.yaml`
2. **Auto-updates** - Changes to config automatically apply
3. **Fully integrated** - Part of your Hermes workflow
4. **No API key management** - Securely loaded from config
5. **Same endpoint** - Works with your configured model (kimi-k2.6, etc.)
6. **Maximum flexibility** - Can use any LLM feature (vision, text, JSON mode)

---

## Implementation Pattern

### Step 1: Load Hermes Config

```python
import yaml
import os

HERMES_CONFIG_PATH = os.path.expanduser("~/.hermes/config.yaml")

def load_hermes_config():
    """Load Hermes configuration from config.yaml."""
    with open(HERMES_CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    return config
```

### Step 2: Create OpenAI-Compatible Client

```python
from openai import OpenAI

def get_llm_client(config: dict):
    """Create OpenAI-compatible client from Hermes config."""
    model_config = config.get('model', {})
    
    base_url = model_config.get('base_url', '')
    api_key = model_config.get('api_key', '')
    model = model_config.get('default', 'kimi-k2.6')
    
    if not base_url or not api_key:
        raise ValueError("Missing base_url or api_key in Hermes config")
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    return client, model
```

### Step 3: Use with Any Task

```python
# Example: Receipt parsing
client, model = get_llm_client(load_hermes_config())

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
                {"type": "text", "text": "Extract receipt data as JSON..."}
            ]
        }
    ],
    response_format={"type": "json_object"}  # Forces JSON output
)

data = json.loads(response.choices[0].message.content)
```

---

## Configuration Format

Your `~/.hermes/config.yaml` should have:

```yaml
model:
  default: kimi-k2.6
  provider: custom
  base_url: https://ai.sumopod.com
  api_key: sk-...  # Your API key
  api_mode: chat_completions
```

**Note**: The script automatically uses:
- `model.default` → model name
- `model.base_url` → API endpoint
- `model.api_key` → API key (securely loaded)

---

## Common Use Cases

### 1. Receipt Parsing

```python
# Parse receipt image with LLM vision
client, model = get_llm_client(load_hermes_config())

response = client.chat.completions.create(
    model=model,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": image_base64}},
            {"type": "text", "text": PROMPT}
        ]
    }],
    response_format={"type": "json_object"}
)

receipt_data = json.loads(response.choices[0].message.content)
```

### 2. Financial Advisor Comments

```python
# Generate financial advice for transaction
client, model = get_llm_client(load_hermes_config())

response = client.chat.completions.create(
    model=model,
    messages=[{
        "role": "user",
        "content": "Analyze this transaction and provide financial advice..."
    }],
    response_format={"type": "json_object"}
)

advice = json.loads(response.choices[0].message.content)
```

### 3. Monthly Insights

```python
# Generate monthly spending analysis
client, model = get_llm_client(load_hermes_config())

response = client.chat.completions.create(
    model=model,
    messages=[{
        "role": "user",
        "content": f"Analyze {year}-{month:02d} spending: {transactions}..."
    }],
    response_format={"type": "json_object"}
)

insights = json.loads(response.choices[0].message.content)
```

---

## Error Handling

```python
try:
    client, model = get_llm_client(load_hermes_config())
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)
    
except ValueError as e:
    print(f"❌ Config error: {e}")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ LLM error: {e}")
    return None
```

---

## Testing

### Verify Config Loading

```python
config = load_hermes_config()
print(f"Model: {config['model']['default']}")
print(f"Base URL: {config['model']['base_url']}")
print(f"API Key: {config['model']['api_key'][:10]}...")
```

### Verify LLM Connection

```python
client, model = get_llm_client(load_hermes_config())

# Simple test
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Respond with: OK"}]
)

assert response.choices[0].message.content == "OK"
print("✅ LLM connection verified")
```

---

## Migration to This Pattern

If you're currently using `vision_analyze` tool:

### Before (vision_analyze tool)

```python
# This approach requires the vision_analyze tool
vision_analyze(
    image_url="receipt.jpg",
    question="Extract receipt data..."
)
```

### After (direct LLM client)

```python
# This approach uses your Hermes config directly
client, model = get_llm_client(load_hermes_config())

response = client.chat.completions.create(
    model=model,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": base64_image}},
            {"type": "text", "text": "Extract receipt data..."}
        ]
    }],
    response_format={"type": "json_object"}
)
```

### Benefits of Migration

- ✅ **More control** - You manage the entire flow
- ✅ **Better error handling** - Catch and handle LLM errors
- ✅ **Reusable** - Same pattern for any LLM task
- ✅ **Testable** - Easy to mock and test
- ✅ **Flexible** - Can switch models/endpoints easily

---

## Security Considerations

1. **Never hardcode API keys** - Always load from config
2. **Never commit config.yaml** - Add to `.gitignore`
3. **Use environment variables** - For production deployments
4. **Validate config** - Check required fields before use
5. **Log carefully** - Never log full API keys

---

## References

- [Smart Expense SKILL.md](../SKILL.md) - Main expense tracking skill
- [Financial Advisor Script](../scripts/financial_advisor.py) - Example implementation
- [Receipt Parser Script](../scripts/parse_receipt_hermes_llm.py) - Example implementation
- [Hermes Agent Config Docs](https://hermes-agent.nousresearch.com/docs/config) - Config reference

---

**Created**: 2026-05-15  
**Session**: Smart Expense receipt parsing and financial advisor implementation  
**Status**: ✅ Tested and working
