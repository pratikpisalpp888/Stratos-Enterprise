import os
from pathlib import Path
from typing import List, Dict
import logging
from app.config.settings import settings

logger = logging.getLogger("app.ingestion.document_loader")

def load_documents() -> List[Dict]:
    docs = []
    
    def read_files(dir_path: Path, source_category: str):
        if not dir_path.exists():
            logger.warning(f"Directory not found: {dir_path}")
            return
            
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(".txt"):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            docs.append({
                                "file_path": str(file_path),
                                "raw_content": content,
                                "source_category": source_category
                            })
                    except Exception as e:
                        logger.error(f"Failed to read file {file_path}: {e}")
                        
    # a) department_docs
    read_files(settings.DEPARTMENT_DOCS_DIR, "department_docs")
    
    # b) Appraisals
    read_files(settings.EMPLOYEE_DOCS_DIR / "Appraisals", "appraisal")
    
    # c) Leave Records
    read_files(settings.EMPLOYEE_DOCS_DIR / "Leave Records", "leave_record")
    
    # d) Salary_slips
    read_files(settings.EMPLOYEE_DOCS_DIR / "Salary_slips", "salary_slip")
    
    return docs
