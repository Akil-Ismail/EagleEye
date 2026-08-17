import uuid

from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.core.config import get_settings
from app.vector.qdrant_client import get_qdrant_client

EMBEDDING_SIZE = 512


def ensure_collection() -> None:
    settings = get_settings()
    client = get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection):
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=EMBEDDING_SIZE, distance=Distance.COSINE),
        )


def upsert_face_embedding(
    user_id: int,
    embedding: list[float],
    media_upload_id: int | None,
    enrolled_at: str,
) -> str:
    settings = get_settings()
    client = get_qdrant_client()
    point_id = str(uuid.uuid4())
    client.upsert(
        collection_name=settings.qdrant_collection,
        points=[
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "user_id": user_id,
                    "media_upload_id": media_upload_id,
                    "enrolled_at": enrolled_at,
                },
            )
        ],
    )
    return point_id


def search_similar_faces(embedding: list[float], top_k: int = 5, score_threshold: float | None = None):
    settings = get_settings()
    client = get_qdrant_client()
    return client.query_points(
        collection_name=settings.qdrant_collection,
        query=embedding,
        limit=top_k,
        score_threshold=score_threshold,
    ).points


def delete_user_embeddings(user_id: int) -> None:
    settings = get_settings()
    client = get_qdrant_client()
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]),
    )
