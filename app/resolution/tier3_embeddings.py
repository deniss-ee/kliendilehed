from decimal import Decimal
from typing import Optional, Tuple, List
import numpy as np
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import CanonicalProduct
from app.normalization.unit_extractor import ExtractedUnitInfo
import structlog

logger = structlog.get_logger()

# FastEmbed local multilingual embedding model
_EMBEDDING_MODEL = None

def get_embedding_model():
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        try:
            from fastembed import TextEmbedding
            _EMBEDDING_MODEL = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        except Exception as e:
            logger.warning("fastembed_init_fallback", error=str(e))
            _EMBEDDING_MODEL = None
    return _EMBEDDING_MODEL

class EmbeddingMatcher:
    """Tier 3: Local Semantic Vector Search (Supports both pgvector and local numpy fallback)."""

    COSINE_SIMILARITY_THRESHOLD = 0.82

    @classmethod
    def generate_embedding(cls, text: str) -> Optional[List[float]]:
        model = get_embedding_model()
        if model is None or not text.strip():
            return None
        try:
            embeddings = list(model.embed([text]))
            if embeddings:
                return embeddings[0].tolist()
        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e))
        return None

    @classmethod
    async def match(
        cls,
        session: AsyncSession,
        query_text: str,
        unit_info: ExtractedUnitInfo,
    ) -> Optional[Tuple[CanonicalProduct, Decimal]]:
        vector = cls.generate_embedding(query_text)
        if not vector:
            return None

        min_amount = unit_info.unit_amount * Decimal("0.90")
        max_amount = unit_info.unit_amount * Decimal("1.10")

        # Fetch unit-filtered candidates
        stmt = select(CanonicalProduct).where(
            and_(
                CanonicalProduct.unit_type == unit_info.unit_type.value,
                CanonicalProduct.unit_amount >= min_amount,
                CanonicalProduct.unit_amount <= max_amount,
                CanonicalProduct.title_embedding.isnot(None),
            )
        ).limit(30)

        result = await session.execute(stmt)
        candidates = list(result.scalars().all())

        if not candidates:
            return None

        q_vec = np.array(vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return None

        best_cand: Optional[CanonicalProduct] = None
        best_sim = 0.0

        for cand in candidates:
            if not cand.title_embedding:
                continue
            try:
                c_vec = np.array(cand.title_embedding, dtype=np.float32)
                c_norm = np.linalg.norm(c_vec)
                if c_norm > 0:
                    sim = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
                    if sim > best_sim:
                        best_sim = sim
                        best_cand = cand
            except Exception:
                continue

        if best_cand and best_sim >= cls.COSINE_SIMILARITY_THRESHOLD:
            return best_cand, Decimal(str(round(best_sim, 4)))

        return None
