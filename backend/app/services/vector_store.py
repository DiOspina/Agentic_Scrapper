"""
Vector Store Service for managing Qdrant and PGVector.
"""
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
    CollectionStatus,
)
from langchain_core.documents import Document as LangChainDocument
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import Qdrant as QdrantVectorStore
from langchain_community.vectorstores import PGVector

from app.core.config import settings
from app.services.llm import get_embeddings


_vector_store_instance = None
_qdrant_client_instance = None


class VectorStoreService:
    """Service for vector store operations."""

    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        collection_name: Optional[str] = None,
    ):
        self.embeddings = embeddings or get_embeddings()
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self._client = self._get_client()
        self._ensure_collection()

    def _get_client(self) -> QdrantClient:
        """Get or create Qdrant client."""
        global _qdrant_client_instance
        if _qdrant_client_instance is None:
            _qdrant_client_instance = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
        return _qdrant_client_instance

    def _ensure_collection(self) -> None:
        """Ensure collection exists."""
        try:
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.OPENAI_EMBEDDING_DIMENSION,
                        distance=Distance.COSINE,
                    ),
                )
        except Exception as e:
            # Collection might already exist
            pass

    def get_langchain_store(self) -> QdrantVectorStore:
        """Get LangChain Qdrant vector store."""
        return QdrantVectorStore(
            client=self._client,
            collection_name=self.collection_name,
            embeddings=self.embeddings,
        )

    async def add_documents(
        self,
        documents: List[LangChainDocument],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Add documents to vector store."""
        store = self.get_langchain_store()
        return await store.aadd_documents(documents, ids=ids)

    async def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Add texts to vector store."""
        store = self.get_langchain_store()
        return await store.aadd_texts(texts, metadatas=metadatas, ids=ids)

    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[LangChainDocument]:
        """Search for similar documents."""
        store = self.get_langchain_store()

        if filter:
            # Convert filter to Qdrant format
            qdrant_filter = self._build_filter(filter)
            return await store.asimilarity_search(query, k=k, filter=qdrant_filter)

        return await store.asimilarity_search(query, k=k)

    async def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.0,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[tuple]:
        """Search with similarity scores."""
        store = self.get_langchain_store()

        if filter:
            qdrant_filter = self._build_filter(filter)
            return await store.asimilarity_search_with_relevance_scores(
                query, k=k, score_threshold=score_threshold, filter=qdrant_filter
            )

        return await store.asimilarity_search_with_relevance_scores(
            query, k=k, score_threshold=score_threshold
        )

    async def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents by IDs."""
        self._client.delete(
            collection_name=self.collection_name,
            points_selector=ids,
        )
        return True

    async def delete_by_metadata(self, filter: Dict[str, Any]) -> bool:
        """Delete documents by metadata filter."""
        qdrant_filter = self._build_filter(filter)
        self._client.delete(
            collection_name=self.collection_name,
            points_selector=qdrant_filter,
        )
        return True

    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics."""
        info = self._client.get_collection(self.collection_name)
        return {
            "name": info.config.params.vectors.size if info.config.params.vectors else "unknown",
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": info.status.value,
        }

    def _build_filter(self, filter_dict: Dict[str, Any]) -> Filter:
        """Build Qdrant filter from dictionary."""
        conditions = []
        for key, value in filter_dict.items():
            if isinstance(value, dict):
                # Handle operators like {"$in": [...], "$gt": 10}
                for op, op_value in value.items():
                    if op == "$in":
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=op_value))
                        )
            else:
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

        return Filter(must=conditions) if conditions else None

    async def scroll(
        self,
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Scroll through collection."""
        qdrant_filter = self._build_filter(filter) if filter else None

        results = self._client.scroll(
            collection_name=self.collection_name,
            scroll_filter=qdrant_filter,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        return [
            {
                "id": point.id,
                "payload": point.payload,
            }
            for point in results[0]
        ]

    async def upsert_points(self, points: List[PointStruct]) -> bool:
        """Upsert points directly."""
        self._client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        return True


def get_vector_store(
    embeddings: Optional[Embeddings] = None,
    collection_name: Optional[str] = None,
) -> VectorStoreService:
    """Get or create vector store service."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreService(embeddings, collection_name)
    return _vector_store_instance


async def get_pgvector_store(
    embeddings: Optional[Embeddings] = None,
    collection_name: Optional[str] = None,
) -> PGVector:
    """Get PGVector store (alternative)."""
    from app.db.database import engine

    return PGVector(
        connection_string=settings.DATABASE_URL.replace("+asyncpg", ""),
        embedding_function=embeddings or get_embeddings(),
        collection_name=collection_name or settings.QDRANT_COLLECTION,
        engine=engine.sync_engine,
    )