import json
from app.ingestion.pipeline import run_ingestion_pipeline

result = run_ingestion_pipeline()
s = result["stats"]

print("=== FINAL INGESTION SUMMARY ===")
print("Total Documents:", s["total_documents_processed"])
print("Total Chunks:", s["total_chunks_created"])
print("Parsing Errors:", s["metadata_parsing_errors"])
print("Mismatches:", s["mismatches"])
print()
print("Docs by Category:", json.dumps(s["docs_by_category"], indent=2))
print()
print("Chunks by Department:", json.dumps(s["chunks_by_department"], indent=2))
print()
print("Chunks by Sensitivity:", json.dumps(s["chunks_by_sensitivity"], indent=2))
print()
print("Document Types:", s["unique_document_types"])
print()
print("Errors:", result["errors"])
print("Output file:", result["output_file"])
