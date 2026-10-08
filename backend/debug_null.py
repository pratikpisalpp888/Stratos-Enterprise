import json
from pathlib import Path

chunks = json.load(open(r"d:\2026\Stratos Enterprise\backend\app\ingestion\output\processed_chunks.json"))

# Find null sensitivity chunks and their source files
null_chunks = [c for c in chunks if not c["metadata"].get("Sensitivity_Level")]
print(f"Null sensitivity chunks: {len(null_chunks)}")
null_sources = set(c["source_file"] for c in null_chunks)
print(f"From {len(null_sources)} unique files:")
for s in sorted(null_sources)[:5]:
    print(f"  {s}")

print()

# Read one of the null files to see format
sample = sorted(null_sources)[0]
print(f"=== Sample null file header (first 15 lines) ===")
lines = open(sample, encoding="utf-8").read().split("\n")[:15]
for l in lines:
    print(repr(l))
