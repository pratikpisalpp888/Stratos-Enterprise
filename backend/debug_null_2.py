import json
from pathlib import Path

chunks = json.load(open(r"d:\2026\Stratos Enterprise\backend\app\ingestion\output\processed_chunks.json"))
null_chunks = [c for c in chunks if not c["metadata"].get("Sensitivity_Level")]
print(f"Null chunks: {len(null_chunks)}")
null_sources = set(c["source_file"] for c in null_chunks)
for s in sorted(null_sources):
    print(f"  {s}")
