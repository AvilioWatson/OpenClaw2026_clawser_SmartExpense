from openai import OpenAI

# Initialize client with SumoPod AI
client = OpenAI(
    api_key="sk-TQ0kXDpEgEXK4Tb2qq8SDg",
    base_url="https://ai.sumopod.com/v1"
)

# Make a chat completion request
response = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[
        {"role": "user", "content": "Who are you"}
    ],
    max_tokens=150,
    temperature=0.7
)

print(response.choices[0].message.content)