import json
import logging
import re
from pathlib import Path
from typing import Optional, List, Dict
from rank_bm25 import BM25Okapi
from app.ingestion.payload_builder import build_payload

logger = logging.getLogger("app.retrieval.sparse_retriever")

# Singleton in-memory state
_bm25_index: Optional[BM25Okapi] = None
_bm25_chunks: List[Dict] = []
_bm25_payloads: List[Dict] = []

def _tokenize(text: str) -> List[str]:
    """Simple alphanumeric tokenizer for BM25."""
    return re.findall(r"\w+", text.lower())

def build_bm25_index(force_rebuild: bool = False) -> BM25Okapi:
    """
    Loads processed_chunks.json, tokenizes content, and builds the BM25 index.
    Caches index and chunk payloads in memory.
    """
    global _bm25_index, _bm25_payloads
    
    if _bm25_index is not None and not force_rebuild:
        return _bm25_index

    # Locate processed_chunks.json
    chunks_path = Path(__file__).parent.parent / "ingestion" / "output" / "processed_chunks.json"
    if not chunks_path.exists():
        logger.error(f"processed_chunks.json not found at {chunks_path}")
        raise FileNotFoundError(f"Could not locate processed_chunks.json at {chunks_path}")

    logger.info(f"Building BM25 index from {chunks_path}...")
    with open(chunks_path, "r", encoding="utf-8") as f:
        raw_chunks = json.load(f)

    corpus = []
    _bm25_payloads = []
    
    for chunk in raw_chunks:
        payload = build_payload(chunk)
        _bm25_payloads.append(payload)
        tokens = _tokenize(chunk.get("content", ""))
        corpus.append(tokens)

    # Free raw_chunks memory immediately
    del raw_chunks

    _bm25_index = BM25Okapi(corpus)
    del corpus
    import gc
    gc.collect()

    logger.info(f"BM25 index built successfully with {len(_bm25_payloads)} documents.")
    return _bm25_index

def sparse_search(query: str, limit: int = 20) -> List[Dict]:
    """
    Performs BM25 keyword search over cached corpus.
    Returns list of candidate dicts with score, chunk_id, and payload.
    """
    index = build_bm25_index()
    tokenized_query = _tokenize(query)
    
    if not tokenized_query:
        return []

    scores = index.get_scores(tokenized_query)
    
    # Pair scores with indexes and sort descending
    scored_indices = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    
    results = []
    for idx, score in scored_indices[:limit]:
        if score <= 0:
            continue
        payload = _bm25_payloads[idx]
        results.append({
            "bm25_score": float(score),
            "chunk_id": payload["chunk_id"],
            "payload": payload
        })
        
    logger.info(f"BM25 search for '{query[:30]}' returned {len(results)} candidate chunks.")
    return results
