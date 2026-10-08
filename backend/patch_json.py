import re
import os

FILES_TO_PATCH = [
    "app/guardrails/input_guardrails.py",
    "app/guardrails/output_guardrails.py"
]

def patch_file(filepath):
    if not os.path.exists(filepath):
        print(f"Skipping {filepath}")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # robust json parser snippet
    parser_code = """
        import re
        match = re.search(r"\\{.*\\}|\\[.*\\]", text, re.DOTALL)
        if match:
            text = match.group(0)
        else:
            text = text.strip()
"""

    if "if text.startswith(" in content:
        # replace old markdown stripping
        content = re.sub(
            r' *if text\.startswith\("```"\):.*?text = text\.split\("```"\)\[1\]\.replace\("json", ""\)\.strip\(\)\n',
            parser_code,
            content,
            flags=re.DOTALL
        )
    
    if "if content.startswith(" in content:
        # replace old markdown stripping
        content = re.sub(
            r' *if content\.startswith\("```"\):.*?content = content\.strip\(\)\n',
            parser_code.replace("text", "content"),
            content,
            flags=re.DOTALL
        )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Patched {filepath}")

for f in FILES_TO_PATCH:
    patch_file(f)
