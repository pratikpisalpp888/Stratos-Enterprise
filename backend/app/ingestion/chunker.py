from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict
import logging

logger = logging.getLogger("app.ingestion.chunker")

def chunk_document(clean_content: str, metadata: Dict, source_file: str) -> List[Dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len
    )
    
    chunks_text = splitter.split_text(clean_content)
    chunk_objects = []
    
    filename = source_file.split('\\')[-1].split('/')[-1]
    
    doc_type_clean = (metadata.get("Document_Type") or "doc").replace(" ", "_")
    for i, text in enumerate(chunks_text):
        chunk_id = f"{doc_type_clean}_{filename}_chunk_{i}"
        
        # Carry forward metadata
        chunk_objects.append({
            "chunk_id": chunk_id,
            "content": text,
            "metadata": metadata,
            "source_file": source_file
        })
        
    return chunk_objects
