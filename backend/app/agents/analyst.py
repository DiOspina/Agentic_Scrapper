"""
Analyst Agent (RAG) for processing documents and extracting insights.
"""
import asyncio
import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from langchain_core.documents import Document as LangChainDocument
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant as QdrantVectorStore
from langchain_community.vectorstores import PGVector
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from app.agents.base import BaseAgent, AgentContext, AgentResult, AgentState
from app.models.agent_log import AgentType, LogLevel
from app.core.config import settings
from app.services.embeddings import get_embeddings
from app.services.vector_store import get_vector_store


class AnalysisType(str, Enum):
    SUMMARIZATION = "summarization"
    KEY_METRICS = "key_metrics"
    PATTERN_DETECTION = "pattern_detection"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    ENTITY_EXTRACTION = "entity_extraction"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    TREND_ANALYSIS = "trend_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    CUSTOM_QUERY = "custom_query"


@dataclass
class AnalysisConfig:
    analysis_types: List[AnalysisType] = field(default_factory=lambda: [
        AnalysisType.SUMMARIZATION,
        AnalysisType.KEY_METRICS,
        AnalysisType.PATTERN_DETECTION,
    ])
    chunk_size: int = settings.RAG_CHUNK_SIZE
    chunk_overlap: int = settings.RAG_CHUNK_OVERLAP
    top_k: int = settings.RAG_TOP_K
    similarity_threshold: float = settings.RAG_SIMILARITY_THRESHOLD
    embedding_model: str = settings.OPENAI_EMBEDDING_MODEL
    use_reranking: bool = True
    max_tokens_per_chunk: int = 8000
    temperature: float = 0.1


@dataclass
class DocumentChunk:
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class AnalysisResult:
    analysis_type: AnalysisType
    result: Dict[str, Any]
    confidence: float
    sources: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)


class AnalystAgent(BaseAgent):
    """Agent for RAG-based document analysis and insight extraction."""

    def __init__(
        self,
        llm=None,
        config: Optional[Dict[str, Any]] = None,
        analysis_config: Optional[AnalysisConfig] = None,
    ):
        super().__init__(
            agent_type=AgentType.ANALYST,
            name="analyst",
            llm=llm,
            config=config,
        )
        self.analysis_config = analysis_config or AnalysisConfig()
        self._embeddings: Optional[Embeddings] = None
        self._vector_store: Optional[VectorStore] = None
        self._text_splitter: Optional[RecursiveCharacterTextSplitter] = None

    async def _on_initialize(self) -> None:
        """Initialize embeddings and vector store."""
        self._embeddings = get_embeddings()
        self._vector_store = await get_vector_store()
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.analysis_config.chunk_size,
            chunk_overlap=self.analysis_config.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.logger.info("Analyst agent initialized with RAG capabilities")

    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute analysis based on input documents and queries."""
        documents = context.input_data.get("documents", [])
        queries = context.input_data.get("queries", [])
        analysis_types = context.input_data.get("analysis_types", [t.value for t in self.analysis_config.analysis_types])
        document_ids = context.input_data.get("document_ids", [])

        # Convert analysis types
        types_to_run = [AnalysisType(t) for t in analysis_types if t in AnalysisType.__members__.values()]

        all_results: List[AnalysisResult] = []
        all_metrics: Dict[str, float] = {}
        total_tokens = 0

        # If document IDs provided, load from vector store
        if document_ids:
            documents = await self._load_documents_from_store(document_ids)

        # If documents provided directly, process and index them
        if documents and not document_ids:
            await self._index_documents(documents)

        # Run analyses
        for analysis_type in types_to_run:
            try:
                result = await self._run_analysis(analysis_type, documents, queries, context)
                all_results.append(result)

                # Aggregate metrics
                for key, value in result.metrics.items():
                    all_metrics[f"{analysis_type.value}.{key}"] = value

                self.log(
                    LogLevel.INFO,
                    f"Completed {analysis_type.value} analysis",
                    step_name=f"analysis_{analysis_type.value}",
                    details={"confidence": result.confidence, "sources_count": len(result.sources)},
                )

            except Exception as e:
                self.logger.error(f"Analysis {analysis_type.value} failed", error=str(e))
                self.log(
                    LogLevel.ERROR,
                    f"Analysis failed: {str(e)}",
                    step_name=f"analysis_{analysis_type.value}_error",
                    details={"error": str(e)},
                )
                context.errors.append(f"{analysis_type.value}: {str(e)}")

        # Answer custom queries
        query_results = []
        if queries:
            for query in queries:
                result = await self._answer_query(query, context)
                query_results.append(result)

        output_data = {
            "analyses": [self._analysis_result_to_dict(r) for r in all_results],
            "query_results": query_results,
            "metrics": all_metrics,
            "document_count": len(documents),
            "errors": context.errors,
        }

        return AgentResult(
            success=len(all_results) > 0 or len(query_results) > 0,
            output_data=output_data,
            error="; ".join(context.errors) if context.errors else None,
            metrics=all_metrics,
            tokens_used=total_tokens,
        )

    async def _index_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Index documents into vector store."""
        all_chunks = []
        doc_ids = []

        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            doc_id = doc.get("document_id", str(uuid.uuid4()))

            # Split into chunks
            chunks = self._text_splitter.split_text(content)

            for i, chunk_text in enumerate(chunks):
                chunk = DocumentChunk(
                    content=chunk_text,
                    metadata={
                        **metadata,
                        "document_id": doc_id,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                )
                all_chunks.append(chunk)

            doc_ids.append(doc_id)

        # Generate embeddings
        if all_chunks:
            texts = [c.content for c in all_chunks]
            embeddings = await self._embeddings.aembed_documents(texts)

            for chunk, embedding in zip(all_chunks, embeddings):
                chunk.embedding = embedding

            # Store in vector store
            await self._store_chunks(all_chunks)

        return doc_ids

    async def _store_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Store chunks in vector store."""
        if hasattr(self._vector_store, "aadd_documents"):
            # LangChain vector store
            lc_docs = [
                LangChainDocument(page_content=c.content, metadata=c.metadata)
                for c in chunks
            ]
            await self._vector_store.aadd_documents(lc_docs)
        else:
            # Direct Qdrant client
            client = self._get_qdrant_client()
            points = [
                PointStruct(
                    id=c.chunk_id,
                    vector=c.embedding,
                    payload={**c.metadata, "content": c.content},
                )
                for c in chunks
            ]
            client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)

    def _get_qdrant_client(self) -> QdrantClient:
        """Get Qdrant client."""
        return QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

    async def _load_documents_from_store(self, document_ids: List[str]) -> List[Dict[str, Any]]:
        """Load documents from vector store by document IDs."""
        client = self._get_qdrant_client()
        documents = []

        for doc_id in document_ids:
            # Search for chunks belonging to this document
            results = client.scroll(
                collection_name=settings.QDRANT_COLLECTION,
                scroll_filter=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=doc_id))]
                ),
                limit=1000,
            )

            chunks = []
            for point in results[0]:
                chunks.append({
                    "content": point.payload.get("content", ""),
                    "metadata": {k: v for k, v in point.payload.items() if k != "content"},
                })

            if chunks:
                # Combine chunks back into document
                full_content = "\n\n".join([c["content"] for c in chunks])
                documents.append({
                    "document_id": doc_id,
                    "content": full_content,
                    "metadata": chunks[0]["metadata"] if chunks else {},
                    "chunks": chunks,
                })

        return documents

    async def _run_analysis(
        self,
        analysis_type: AnalysisType,
        documents: List[Dict[str, Any]],
        queries: List[str],
        context: AgentContext,
    ) -> AnalysisResult:
        """Run a specific type of analysis."""
        if analysis_type == AnalysisType.SUMMARIZATION:
            return await self._summarize_documents(documents)
        elif analysis_type == AnalysisType.KEY_METRICS:
            return await self._extract_key_metrics(documents)
        elif analysis_type == AnalysisType.PATTERN_DETECTION:
            return await self._detect_patterns(documents)
        elif analysis_type == AnalysisType.SENTIMENT_ANALYSIS:
            return await self._analyze_sentiment(documents)
        elif analysis_type == AnalysisType.ENTITY_EXTRACTION:
            return await self._extract_entities(documents)
        elif analysis_type == AnalysisType.COMPARATIVE_ANALYSIS:
            return await self._comparative_analysis(documents)
        elif analysis_type == AnalysisType.TREND_ANALYSIS:
            return await self._analyze_trends(documents)
        elif analysis_type == AnalysisType.ANOMALY_DETECTION:
            return await self._detect_anomalies(documents)
        elif analysis_type == AnalysisType.CUSTOM_QUERY:
            return await self._custom_query_analysis(documents, queries)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")

    async def _summarize_documents(self, documents: List[Dict[str, Any]]) -> AnalysisResult:
        """Generate executive summaries of documents."""
        summaries = []

        for doc in documents:
            content = doc.get("content", "")[:self.analysis_config.max_tokens_per_chunk]

            prompt = f"""Provide a concise executive summary of the following document.
Focus on key findings, important data points, and actionable insights.

Document:
{content}

Summary:"""

            response = await self.call_llm([HumanMessage(content=prompt)])
            summaries.append({
                "document_id": doc.get("document_id"),
                "summary": response.content,
                "word_count": len(content.split()),
            })

        return AnalysisResult(
            analysis_type=AnalysisType.SUMMARIZATION,
            result={"summaries": summaries},
            confidence=0.9,
            sources=[{"document_id": d.get("document_id")} for d in documents],
        )

    async def _extract_key_metrics(self, documents: List[Dict[str, Any]]) -> AnalysisResult:
        """Extract numerical metrics and KPIs from documents."""
        all_metrics = []

        for doc in documents:
            content = doc.get("content", "")[:self.analysis_config.max_tokens_per_chunk]

            prompt = f"""Extract all numerical metrics, KPIs, statistics, and quantitative data from the following document.
Return as JSON array with objects containing: metric_name, value, unit, context, confidence.

Document:
{content}

Metrics JSON:"""

            response = await self.call_llm([HumanMessage(content=prompt)])

            try:
                metrics = json.loads(response.content)
                for m in metrics:
                    m["document_id"] = doc.get("document_id")
                all_metrics.extend(metrics)
            except json.JSONDecodeError:
                # Try to extract from text
                all_metrics.append({
                    "document_id": doc.get("document_id"),
                    "raw_response": response.content,
                    "parse_error": True,
                })

        return AnalysisResult(
            analysis_type=AnalysisType.KEY_METRICS,
            result={"metrics": all_metrics},
            confidence=0.85,
            sources=[{"document_id": d.get("document_id")} for d in documents],
            metrics={"total_metrics_found": len(all_metrics)},
        )

    async def _detect_patterns(self, documents: List[Dict[str, Any]]) -> AnalysisResult:
        """Detect patterns and recurring themes in documents."""
        combined_content = "\n\n---\n\n".join([d.get("content", "")[:5000] for d in documents])

        prompt = f"""Analyze the following documents and identify:
1. Recurring themes and topics
2. Common patterns in data or narratives
3. Frequently mentioned entities, concepts, or terms
4. Structural patterns (formatting, organization)
5. Any anomalies or outliers

Return as JSON with categories: themes, patterns, entities, structures, anomalies.

Documents:
{combined_content}

Analysis JSON:"""

        response = await self.call_llm([HumanMessage(content=prompt)])

        try:
            patterns = json.loads(response.content)
        except json.JSONDecodeError:
            patterns = {"raw_response": response.content, "parse_error": True}

        return AnalysisResult(
            analysis_type=AnalysisType.PATTERN_DETECTION,
            result=patterns,
            confidence=0.8,
            sources=[{"document_id": d.get("document_id")} for d in documents],
        )

    async def _analyze_sentiment(self, documents: List[Dict[str, Any]]) -> AnalysisResult:
        """Analyze sentiment of documents."""
        sentiments = []

        for doc in documents:
            content = doc.get("content", "")[:self.analysis_config.max_tokens_per_chunk]

            prompt = f"""Analyze the sentiment and tone of the following document.
Return JSON with: overall_sentiment (positive/negative/neutral), sentiment_score (-1 to 1),
key_emotional_tones, confidence.

Document:
{content}

Sentiment JSON:"""

            response = await self.call_llm([HumanMessage(content=prompt)])

            try:
                sentiment = json.loads(response.content)
                sentiment["document_id"] = doc.get("document_id")
                sentiments.append(sentiment)
            except json.JSONDecodeError:
                sentiments.append({
                    "document_id": doc.get("document_id"),
                    "raw_response": response.content,
                    "parse_error": True,
                })

        return AnalysisResult(
            analysis_type=AnalysisType.SENTIMENT_ANALYSIS,
            result={"sentiments": sentiments},
            confidence=0.85,
            sources=[{"document_id": d.get("document_id")} for d in documents],
        )

    async def _extract_entities(self, documents: List[Dict[str, Any]]) -> AnalysisResult:
        """Extract named entities from documents."""
        all_entities = []

        for doc in documents:
            content = doc.get("content", "")[:self.analysis_config.max_tokens_per_chunk]

            prompt = f"""Extract all named entities from the following document.
Categories: PERSON, ORGANIZATION, LOCATION, DATE, MONEY, PERCENT, PRODUCT, EVENT, LAW, GPE.
Return as JSON array with: entity, type, context, confidence.

Document:
{content}

Entities JSON:"""

            response = await self.call_llm([HumanMessage(content=prompt)])

            try:
                entities = json.loads(response.content)
                for e in entities:
                    e["document_id"] = doc.get("document_id")
                all_entities.extend(entities)
            except json.JSONDecodeError:
                all_entities.append({
                    "document_id": doc.get("document_id"),
                    "raw_response": response.content,
                    "parse_error": True,
                })

        return AnalysisResult(
            analysis_type=AnalysisType.ENTITY_EXTRACTION,
            result={"entities": all_entities},
            confidence=0.85,
            sources=[{"document_id": d.get("document_id")} for d in documents],
            metrics={"total_entities": len(all_entities)},
        )

    async def _comparative_analysis(self, documents: List[Dict[str, Any]]) -> AnalysisResult:
        """Compare multiple documents."""
        if len(documents) < 2:
            return AnalysisResult(
                analysis_type=AnalysisType.COMPARATIVE_ANALYSIS,
                result={"error": "Need at least 2 documents for comparison"},
                confidence=0.0,
            )

        combined = "\n\n=== DOCUMENT {} ===\n{}".format(
            i, d.get("content", "")[:3000]
        ) for i, d in enumerate(documents))

        prompt = f"""Compare the following documents and identify:
1. Similarities and differences in content, themes, and conclusions
2. Contradictory information
3. Complementary information
4. Unique insights from each document
5. Overall consensus or divergence

Return as JSON with: similarities, differences, contradictions, complementary, unique_insights, consensus_level.

Documents:
{combined}

Comparison JSON:"""

        response = await self.call_llm([HumanMessage(content=prompt)])

        try:
            comparison = json.loads(response.content)
        except json.JSONDecodeError:
            comparison = {"raw_response": response.content, "parse_error": True}

        return AnalysisResult(
            analysis_type=AnalysisType.COMPARATIVE_ANALYSIS,
            result=comparison,
            confidence=0.8,
            sources=[{"document_id": d.get("document_id")} for d in documents],
        )

    async def _analyze_trends(self, documents: List[Dict[str, Any]]) -> AnalysisResult:
        """Analyze trends over time in documents."""
        # This requires documents with temporal metadata
        trends = []

        for doc in documents:
            content = doc.get("content", "")[:self.analysis_config.max_tokens_per_chunk]
            metadata = doc.get("metadata", {})
            date = metadata.get("date") or metadata.get("created_at") or metadata.get("timestamp")

            prompt = f"""Identify trends, changes over time, and temporal patterns in the following document.
Document date: {date}
Return JSON with: trends (array of trend objects with direction, magnitude, timeframe, confidence), overall_trend.

Document:
{content}

Trends JSON:"""

            response = await self.call_llm([HumanMessage(content=prompt)])

            try:
                trend = json.loads(response.content)
                trend["document_id"] = doc.get("document_id")
                trends.append(trend)
            except json.JSONDecodeError:
                trends.append({
                    "document_id": doc.get("document_id"),
                    "raw_response": response.content,
                    "parse_error": True,
                })

        return AnalysisResult(
            analysis_type=AnalysisType.TREND_ANALYSIS,
            result={"trends": trends},
            confidence=0.75,
            sources=[{"document_id": d.get("document_id")} for d in documents],
        )

    async def _detect_anomalies(self, documents: List[Dict[str, Any]]) -> AnalysisResult:
        """Detect anomalies and outliers in documents."""
        anomalies = []

        for doc in documents:
            content = doc.get("content", "")[:self.analysis_config.max_tokens_per_chunk]

            prompt = f"""Identify anomalies, outliers, unusual patterns, or suspicious data in the following document.
Return JSON with: anomalies (array of anomaly objects with description, severity, evidence, confidence), anomaly_count.

Document:
{content}

Anomalies JSON:"""

            response = await self.call_llm([HumanMessage(content=prompt)])

            try:
                anomaly = json.loads(response.content)
                anomaly["document_id"] = doc.get("document_id")
                anomalies.append(anomaly)
            except json.JSONDecodeError:
                anomalies.append({
                    "document_id": doc.get("document_id"),
                    "raw_response": response.content,
                    "parse_error": True,
                })

        return AnalysisResult(
            analysis_type=AnalysisType.ANOMALY_DETECTION,
            result={"anomalies": anomalies},
            confidence=0.75,
            sources=[{"document_id": d.get("document_id")} for d in documents],
        )

    async def _custom_query_analysis(self, documents: List[Dict[str, Any]], queries: List[str]) -> AnalysisResult:
        """Answer custom queries about documents."""
        results = []

        for query in queries:
            result = await self._answer_query(query, documents=documents)
            results.append(result)

        return AnalysisResult(
            analysis_type=AnalysisType.CUSTOM_QUERY,
            result={"query_results": results},
            confidence=0.8,
            sources=[{"document_id": d.get("document_id")} for d in documents],
        )

    async def _answer_query(
        self,
        query: str,
        context: Optional[AgentContext] = None,
        documents: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Answer a query using RAG."""
        # Retrieve relevant chunks
        if self._vector_store:
            retriever = self._vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k": self.analysis_config.top_k,
                    "score_threshold": self.analysis_config.similarity_threshold,
                },
            )
            relevant_docs = await retriever.ainvoke(query)
            context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
            sources = [
                {"content": doc.page_content[:200], "metadata": doc.metadata}
                for doc in relevant_docs
            ]
        elif documents:
            # Use provided documents
            context_text = "\n\n".join([d.get("content", "")[:2000] for d in documents])
            sources = [{"document_id": d.get("document_id")} for d in documents]
        else:
            context_text = ""
            sources = []

        prompt = f"""Answer the following question based on the provided context.
If the answer cannot be determined from the context, say so.

Context:
{context_text}

Question: {query}

Answer:"""

        response = await self.call_llm([HumanMessage(content=prompt)])

        return {
            "query": query,
            "answer": response.content,
            "sources": sources,
            "confidence": 0.8 if sources else 0.3,
        }

    def _analysis_result_to_dict(self, result: AnalysisResult) -> Dict[str, Any]:
        """Convert AnalysisResult to dictionary."""
        return {
            "analysis_type": result.analysis_type.value,
            "result": result.result,
            "confidence": result.confidence,
            "sources": result.sources,
            "metrics": result.metrics,
        }