import json
import logging
import time
import uuid
from pathlib import Path
from qdrant_client.http import models
from app.retrieval.qdrant_client import get_client, create_collection
from app.ingestion.embedder import generate_embeddings, get_embedding_dimension
from app.ingestion.payload_builder import build_payload

logger = logging.getLogger("app.ingestion.vector_store_loader")

COLLECTION_NAME = "stratos_documents"

def load_chunks_to_qdrant() -> dict:
    start_time = time.time()
    
    # Resolve processed_chunks.json path
    chunks_file_path = Path(__file__).parent / "output" / "processed_chunks.json"
    if not chunks_file_path.exists():
        # Try fallbacks
        chunks_file_path = Path(__file__).parent.parent / "ingestion" / "output" / "processed_chunks.json"
        if not chunks_file_path.exists():
            raise FileNotFoundError(f"Could not locate processed_chunks.json at {chunks_file_path}")
            
    logger.info(f"Reading chunks from {chunks_file_path}...")
    with open(chunks_file_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    total_chunks = len(chunks)
    logger.info(f"Loaded {total_chunks} chunks from disk.")
    
    # 1. Initialize Embedder & Get Dimension
    vector_size = get_embedding_dimension()
    
    # 2. Re-create Collection in Qdrant to ensure no stale chunk points persist
    client = get_client()
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
    )
    
    # Create required payload indexes for RBAC filtering
    rbac_indexes = [
        ("sensitivity_level", models.PayloadSchemaType.KEYWORD),
        ("department", models.PayloadSchemaType.KEYWORD),
        ("min_clearance_level", models.PayloadSchemaType.INTEGER),
        ("restricted_to_owner", models.PayloadSchemaType.BOOL),
        ("owner_employee_id", models.PayloadSchemaType.KEYWORD),
        ("manager_id", models.PayloadSchemaType.KEYWORD),
        ("access_roles", models.PayloadSchemaType.KEYWORD)
    ]
    for field_name, schema_type in rbac_indexes:
        client.create_payload_index(collection_name=COLLECTION_NAME, field_name=field_name, field_schema=schema_type)
    
    # 3. Generate Embeddings for all chunk contents
    texts = [c["content"] for c in chunks]
    embeddings = generate_embeddings(texts)
    
    # 4. Construct Qdrant Points
    client = get_client()
    points = []
    
    sensitivity_counts = {}
    department_counts = {}
    
    logger.info("Constructing payloads and points for Qdrant...")
    for idx, chunk in enumerate(chunks):
        payload = build_payload(chunk)
        
        # Track statistics
        sens = payload["sensitivity_level"]
        sensitivity_counts[sens] = sensitivity_counts.get(sens, 0) + 1
        
        dept = payload["department"]
        if dept:
            department_counts[dept] = department_counts.get(dept, 0) + 1
            
        # Generate deterministic UUID for qdrant point ID
        chunk_id = payload["chunk_id"]
        point_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))
        
        point = models.PointStruct(
            id=point_uuid,
            vector=embeddings[idx],
            payload=payload
        )
        points.append(point)
        
    # 5. Upsert points in batches of 50
    upsert_batch_size = 50
    total_points = len(points)
    logger.info(f"Upserting {total_points} points to Qdrant in batches of {upsert_batch_size}...")
    
    failures = 0
    for idx in range(0, total_points, upsert_batch_size):
        batch = points[idx:idx + upsert_batch_size]
        try:
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch,
                wait=True
            )
            # Log progress
            logger.info(f"Upserted {min(idx + upsert_batch_size, total_points)}/{total_points} points.")
        except Exception as e:
            logger.error(f"Failed to upsert batch at index {idx}: {e}")
            failures += len(batch)
            
    time_taken = time.time() - start_time
    logger.info(f"Ingestion completed in {time_taken:.2f} seconds. Failures: {failures}")
    
    return {
        "status": "success" if failures == 0 else "partial_success",
        "total_points_stored": total_points - failures,
        "failures": failures,
        "time_taken_seconds": round(time_taken, 2),
        "collection": COLLECTION_NAME,
        "sensitivity_breakdown": sensitivity_counts,
        "department_breakdown": department_counts
    }
