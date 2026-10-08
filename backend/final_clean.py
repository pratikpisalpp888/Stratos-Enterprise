from pathlib import Path

# Fix Rohan Pillai leave record - prepend metadata
rp = Path(r"D:\2026\Stratos Enterprise\data\Employee_docs\Leave Records\Legal\Rohan Pillai.txt")
content = rp.read_text(encoding="utf-8")

header = (
    "---METADATA---\n"
    "Owner_Employee_ID: STX-L-003\n"
    "Owner_Name: Rohan Pillai\n"
    "Department: Legal\n"
    "Document_Type: Leave History Record\n"
    "Sensitivity_Level: Internal\n"
    "Access_Roles: STX-L-003, STX-L-001, HR-Admin\n"
    "---END METADATA---\n\n"
)
rp.write_text(header + content, encoding="utf-8")
print("Fixed Rohan Pillai.txt")

# Run final ingestion
import json, sys
sys.path.insert(0, r"d:\2026\Stratos Enterprise\backend")
from app.ingestion.pipeline import run_ingestion_pipeline

result = run_ingestion_pipeline()
s = result["stats"]

print("\n=== FINAL CLEAN INGESTION SUMMARY ===")
print("Total Documents:", s["total_documents_processed"])
print("Total Chunks:", s["total_chunks_created"])
print("Parsing Errors:", s["metadata_parsing_errors"])
print("Mismatches:", s["mismatches"])
print("Errors:", result["errors"])
print("\nDocs by Category:", s["docs_by_category"])
print("\nChunks by Department:", s["chunks_by_department"])
print("\nChunks by Sensitivity:", s["chunks_by_sensitivity"])
print("\nDocument Types:", s["unique_document_types"])

# Check for remaining nulls
chunks = json.load(open(r"d:\2026\Stratos Enterprise\backend\app\ingestion\output\processed_chunks.json"))
null_chunks = [c for c in chunks if not c["metadata"].get("Sensitivity_Level")]
print(f"\nNull sensitivity chunks remaining: {len(null_chunks)}")
