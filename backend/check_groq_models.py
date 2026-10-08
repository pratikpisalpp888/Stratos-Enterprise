"""Check available Groq models and current rate limit status."""
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("Available Groq models:")
print("=" * 60)
try:
    models = client.models.list()
    for m in sorted(models.data, key=lambda x: x.id):
        print(f"  {m.id}")
except Exception as e:
    print(f"Error: {e}")

print()
print("Testing which models accept a tiny test call:")
print("=" * 60)

test_models = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile", 
    "llama3-8b-8192",
    "llama3-70b-8192",
    "gemma-7b-it",
    "llama-3.2-3b-preview",
    "llama-3.2-1b-preview",
]

for model in test_models:
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": "Say OK"}],
            model=model,
            max_tokens=5,
            temperature=0.0
        )
        print(f"  OK   {model} -> '{res.choices[0].message.content.strip()}'")
    except Exception as e:
        err = str(e)[:120]
        print(f"  FAIL {model}: {err}")
