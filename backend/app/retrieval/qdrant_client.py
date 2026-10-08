import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.config.settings import settings

logger = logging.getLogger("app.retrieval.qdrant_client")

# Reusable client instance
_client = None

def get_client() -> QdrantClient:
    global _client
    if _client is None:
        logger.info(f"Initializing Qdrant client with URL: {settings.QDRANT_URL}")
        _client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
            timeout=60
        )
    return _client

def create_collection(collection_name: str, vector_size: int):
    client = get_client()
    try:
        collections_response = client.get_collections()
        existing_collections = [c.name for c in collections_response.collections]
        
        if collection_name not in existing_collections:
            logger.info(f"Creating Qdrant collection: {collection_name} with dimension {vector_size}")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )
        else:
            logger.info(f"Qdrant collection: {collection_name} already exists.")
    except Exception as e:
        logger.error(f"Failed to create collection {collection_name}: {e}")
        raise e
