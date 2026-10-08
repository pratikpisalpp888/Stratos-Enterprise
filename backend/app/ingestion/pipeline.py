import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple
from app.config.settings import settings
from app.ingestion.document_loader import load_documents
from app.ingestion.metadata_parser import parse_metadata
from app.ingestion.chunker import chunk_document

logger = logging.getLogger("app.ingestion.pipeline")

def merge_employee_roster() -> Tuple[Set[str], Set[str]]:
    valid_ids = set()
    valid_names = set()
    
    roster_dir = settings.EMPLOYEE_ROSTER_DIR
    if not roster_dir.exists():
        logger.warning(f"Employee roaster directory not found: {roster_dir}")
        return valid_ids, valid_names
        
    for root, _, files in os.walk(roster_dir):
        for file in files:
            if file.endswith('.json'):
                try:
                    with open(Path(root) / file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for emp in data:
                            if 'employee_id' in emp:
                                valid_ids.add(emp['employee_id'])
                            if 'full_name' in emp:
                                valid_names.add(emp['full_name'])
                except Exception as e:
                    logger.error(f"Error reading roster file {file}: {e}")
                    
    return valid_ids, valid_names

def run_ingestion_pipeline() -> Dict:
    docs = load_documents()
    
    valid_ids, valid_names = merge_employee_roster()
    
    all_chunks = []
    errors = []
    mismatches = []
    
    stats = {
        "total_documents_processed": len(docs),
        "total_chunks_created": 0,
        "metadata_parsing_errors": 0,
        "mismatches": 0,
        "docs_by_category": {
            "department_docs": 0,
            "appraisal": 0,
            "leave_record": 0,
            "salary_slip": 0
        },
        "chunks_by_department": {},
        "chunks_by_sensitivity": {},
        "unique_sensitivity_levels": [],
        "unique_departments": {},
        "unique_document_types": []
    }
    
    unique_sens = set()
    unique_depts = {}
    unique_doc_types = set()
    
    for doc in docs:
        cat = doc.get("source_category")
        if cat in stats["docs_by_category"]:
            stats["docs_by_category"][cat] += 1
            
        metadata, clean_content = parse_metadata(doc["raw_content"])
        
        if not metadata:
            errors.append(doc["file_path"])
            stats["metadata_parsing_errors"] += 1
            continue
            
        owner_id = metadata.get('Owner_Employee_ID') or metadata.get('Owner_Employee_ID_')
        if owner_id and owner_id not in valid_ids:
            mismatches.append(f"{doc['file_path']}: Invalid Owner_Employee_ID '{owner_id}'")
            stats["mismatches"] += 1
            
        author = metadata.get('Author')
        if author:
            author_name = author.split(',')[0].strip()
            if author_name not in valid_names:
                mismatches.append(f"{doc['file_path']}: Invalid Author name '{author_name}'")
                stats["mismatches"] += 1
        
        sens = metadata.get('Sensitivity_Level')
        if sens:
            unique_sens.add(sens)
            
        dept = metadata.get('Department')
        if dept:
            if dept not in unique_depts:
                unique_depts[dept] = []
            unique_depts[dept].append(doc["file_path"])
            
        doc_type = metadata.get('Document_Type')
        if doc_type:
            unique_doc_types.add(doc_type)
            
        chunks = chunk_document(clean_content, metadata, doc["file_path"])
        
        for chunk in chunks:
            chunk['metadata']['source_category'] = cat
            all_chunks.append(chunk)
            
        stats["chunks_by_department"][dept] = stats["chunks_by_department"].get(dept, 0) + len(chunks)
        stats["chunks_by_sensitivity"][sens] = stats["chunks_by_sensitivity"].get(sens, 0) + len(chunks)
        
    stats["total_chunks_created"] = len(all_chunks)
    stats["unique_sensitivity_levels"] = list(unique_sens)
    stats["unique_departments"] = unique_depts
    stats["unique_document_types"] = list(unique_doc_types)
    
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "processed_chunks.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2)
        
    return {
        "stats": stats,
        "errors": errors,
        "mismatches": mismatches,
        "output_file": str(output_file)
    }
