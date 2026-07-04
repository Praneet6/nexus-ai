"""
F05 — Collective Memory
Anonymises resolved queries, embeds them into Pinecone, and retrieves similar
past solutions to accelerate current resolutions.
"""
import re
import hashlib
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# PII regex patterns
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(\+?\d[\d\s\-]{9,12}\d)\b")
_ORDER_RE = re.compile(r"\b[A-Z]{2,4}[-]?\d{4,12}\b")
_CC_RE    = re.compile(r"\b(?:\d[ -]?){13,16}\b")
_NAME_RE  = re.compile(r"\b[A-Z][a-z]{2,}\s[A-Z][a-z]{2,}\b")

_model = None
_pinecone_index = None


def get_embedding_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("[F05] Embedding model loaded: all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"[F05] Could not load embedding model: {e}")
            _model = None
    return _model


def get_pinecone_index(api_key: str, index_name: str):
    global _pinecone_index
    if _pinecone_index is not None:
        return _pinecone_index
    if not api_key:
        return None
    try:
        from pinecone import Pinecone, ServerlessSpec
        pc = Pinecone(api_key=api_key)
        existing = [i.name for i in pc.list_indexes()]
        if index_name not in existing:
            pc.create_index(
                name=index_name,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            logger.info(f"[F05] Created Pinecone index: {index_name}")
        _pinecone_index = pc.Index(index_name)
        logger.info(f"[F05] Connected to Pinecone index: {index_name}")
        return _pinecone_index
    except Exception as e:
        logger.warning(f"[F05] Pinecone unavailable: {e}")
        return None


def strip_pii(text: str) -> str:
    """Remove personal information before embedding or storing."""
    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _PHONE_RE.sub("[PHONE]", text)
    text = _ORDER_RE.sub("[ORDER_ID]", text)
    text = _CC_RE.sub("[CARD]", text)
    text = _NAME_RE.sub("[NAME]", text)
    return text.strip()


def embed_text(text: str) -> Optional[list[float]]:
    model = get_embedding_model()
    if model is None:
        return None
    try:
        return model.encode(text, normalize_embeddings=True).tolist()
    except Exception as e:
        logger.warning(f"[F05] Embedding failed: {e}")
        return None


def make_vector_id(text: str) -> str:
    return hashlib.sha256(text[:100].encode()).hexdigest()[:32]


@dataclass
class CollectiveMatch:
    query_summary: str
    resolution_summary: str
    next_likely_issue: str
    occurrence_count: int
    similarity_score: float


async def store_resolved_query(
    query_text: str,
    resolution_text: str,
    next_issue: str = "",
    pinecone_index=None,
) -> bool:
    """Anonymise and store a resolved query in Pinecone."""
    if pinecone_index is None:
        return False
    try:
        clean_query = strip_pii(query_text)
        clean_resolution = strip_pii(resolution_text)
        embedding = embed_text(clean_query)
        if embedding is None:
            return False

        vector_id = make_vector_id(clean_query)

        # Check if pattern already exists to increment counter
        existing = pinecone_index.fetch(ids=[vector_id])
        existing_count = 0
        if existing and existing.get("vectors") and vector_id in existing["vectors"]:
            existing_count = existing["vectors"][vector_id].get("metadata", {}).get("occurrence_count", 0)

        pinecone_index.upsert(vectors=[{
            "id": vector_id,
            "values": embedding,
            "metadata": {
                "query_summary": clean_query[:500],
                "resolution_summary": clean_resolution[:500],
                "next_likely_issue": strip_pii(next_issue)[:200],
                "occurrence_count": existing_count + 1,
            },
        }])
        logger.info(f"[F05] Stored resolved query (occurrence #{existing_count + 1})")
        return True
    except Exception as e:
        logger.warning(f"[F05] store_resolved_query failed: {e}")
        return False


async def find_similar_queries(
    query_text: str,
    pinecone_index=None,
    top_k: int = 3,
    min_score: float = 0.75,
) -> list[CollectiveMatch]:
    """Semantic search for similar past resolutions."""
    if pinecone_index is None:
        return []
    try:
        clean = strip_pii(query_text)
        embedding = embed_text(clean)
        if embedding is None:
            return []

        results = pinecone_index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
        )

        matches = []
        for match in results.get("matches", []):
            if match["score"] >= min_score:
                meta = match.get("metadata", {})
                matches.append(CollectiveMatch(
                    query_summary=meta.get("query_summary", ""),
                    resolution_summary=meta.get("resolution_summary", ""),
                    next_likely_issue=meta.get("next_likely_issue", ""),
                    occurrence_count=int(meta.get("occurrence_count", 1)),
                    similarity_score=round(match["score"], 3),
                ))
        return matches
    except Exception as e:
        logger.warning(f"[F05] find_similar_queries failed: {e}")
        return []


def build_collective_context_prompt(matches: list[CollectiveMatch]) -> str:
    """Inject collective intelligence silently into Claude's context."""
    if not matches:
        return ""

    best = matches[0]
    total = sum(m.occurrence_count for m in matches)
    lines = [
        f"\n[COLLECTIVE INTELLIGENCE — {total} similar cases found across all customers]",
        f"Most similar past issue: {best.query_summary[:200]}",
        f"How it was resolved: {best.resolution_summary[:300]}",
    ]
    if best.next_likely_issue:
        lines.append(
            f"⚠ Users with this issue often encounter next: {best.next_likely_issue}. "
            "Proactively warn the user about this AFTER resolving their current issue."
        )
    if len(matches) > 1:
        lines.append(f"Confidence: {best.similarity_score:.0%} match based on {best.occurrence_count} occurrences.")

    return "\n".join(lines)
