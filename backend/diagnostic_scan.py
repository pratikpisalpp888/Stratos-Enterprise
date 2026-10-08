import os
import glob
from app.ingestion.metadata_parser import parse_metadata

data_dir = r"d:\2026\Stratos Enterprise\data"
files = glob.glob(os.path.join(data_dir, "**", "*.txt"), recursive=True)

affected_files = []

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    
    metadata, clean_content = parse_metadata(content)
    
    if not clean_content or len(clean_content.strip()) < 50:
        affected_files.append((file, len(clean_content) if clean_content else 0))

print(f"Total files scanned: {len(files)}")
print(f"Files with empty or short content: {len(affected_files)}")
for f, length in affected_files:
    print(f"[{length} chars] {os.path.basename(f)}")
