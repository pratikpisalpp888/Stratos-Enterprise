import logging
from typing import Any
from app.config.settings import settings

logger = logging.getLogger("app.ingestion.embedder")

# Lazy loading of model to prevent early PyTorch memory allocation
_model: Any = None

def _get_model():
    global _model
    if _model is None:
        import torch
        torch.set_num_threads(1)
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info(f"Model {settings.EMBEDDING_MODEL} loaded successfully.")
    return _model

def generate_embeddings(texts: list[str]) -> list[list[float]]:
    import torch
    model = _get_model()
    embeddings = []
    batch_size = 64
    
    total_texts = len(texts)
    logger.info(f"Generating embeddings for {total_texts} chunks in batches of {batch_size}...")
    
    with torch.inference_mode():
        for idx in range(0, total_texts, batch_size):
            batch = texts[idx:idx + batch_size]
            # model.encode generates numpy arrays, convert to list[float]
            batch_embeddings = model.encode(batch, show_progress_bar=False).tolist()
            embeddings.extend(batch_embeddings)
            
            # Log progress every 200 items (or close to it)
            if len(embeddings) % 192 == 0 or len(embeddings) == total_texts:
                logger.info(f"Embedded {len(embeddings)}/{total_texts} chunks.")
                
    return embeddings

def get_embedding_dimension() -> int:
    model = _get_model()
    # Check embedding dimension (usually 384 for bge-small-en-v1.5)
    return model.get_sentence_embedding_dimension()
