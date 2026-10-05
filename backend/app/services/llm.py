"""
LLM Service for managing language model instances.
"""
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings


_llm_instance: Optional[BaseChatModel] = None
_embeddings_instance = None


def get_llm(
    provider: str = "openai",
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> BaseChatModel:
    """Get or create LLM instance."""
    global _llm_instance

    if _llm_instance is None or provider != "openai":
        if provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured")

            _llm_instance = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=model or settings.OPENAI_MODEL,
                temperature=temperature if temperature is not None else settings.AGENT_TEMPERATURE,
                max_tokens=max_tokens or settings.AGENT_MAX_TOKENS,
                streaming=True,
            )
        elif provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not configured")

            _llm_instance = ChatAnthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                model=model or settings.ANTHROPIC_MODEL,
                temperature=temperature if temperature is not None else settings.AGENT_TEMPERATURE,
                max_tokens=max_tokens or settings.AGENT_MAX_TOKENS,
                streaming=True,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    return _llm_instance


def get_embeddings(
    provider: str = "openai",
    model: Optional[str] = None,
):
    """Get or create embeddings instance."""
    global _embeddings_instance

    if _embeddings_instance is None:
        if provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured for embeddings")

            _embeddings_instance = OpenAIEmbeddings(
                api_key=settings.OPENAI_API_KEY,
                model=model or settings.OPENAI_EMBEDDING_MODEL,
                dimensions=settings.OPENAI_EMBEDDING_DIMENSION,
            )
        elif provider == "huggingface":
            _embeddings_instance = HuggingFaceEmbeddings(
                model_name=model or "sentence-transformers/all-mpnet-base-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
        else:
            raise ValueError(f"Unsupported embeddings provider: {provider}")

    return _embeddings_instance


def reset_llm() -> None:
    """Reset LLM instance (for testing or config changes)."""
    global _llm_instance
    _llm_instance = None


def reset_embeddings() -> None:
    """Reset embeddings instance."""
    global _embeddings_instance
    _embeddings_instance = None