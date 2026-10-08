import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

prompt = """You are an expert RAG faithfulness judge.
Grade the extent to which the claims in the ANSWER are supported by the SOURCE CONTEXT.

SOURCE CONTEXT:
Stratos Enterprises core working hours are 10:00 AM to 4:00 PM.

ANSWER:
The core working hours are 10 AM to 4 PM.

Output ONLY a JSON object: {"score": float_between_0_and_1, "reason": "short explanation"}
Do NOT include markdown formatting.
"""

try:
    res = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="qwen/qwen3.6-27b",
        temperature=0.0,
        max_tokens=80
    )
    print("QWEN OUTPUT:")
    print(res.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
