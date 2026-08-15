from decimal import Decimal
from typing import Optional, Tuple, List
from rapidfuzz import fuzz
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import CanonicalProduct
from app.schemas.common import UnitType
from app.normalization.unit_extractor import ExtractedUnitInfo

class RuleBasedMatcher:
    """Tier 2: Rule-Based Fuzzy Matcher (Brand + Unit + Token Set Ratio)."""

    CONFIDENCE_THRESHOLD = 0.82

    @classmethod
    async def match(
        cls,
        session: AsyncSession,
        clean_title: str,
        brand: Optional[str],
        unit_info: ExtractedUnitInfo,
    ) -> Optional[Tuple[CanonicalProduct, Decimal]]:
        # Candidate filter query: matching unit_type and unit_amount within 5% tolerance
        min_amount = unit_info.unit_amount * Decimal("0.95")
        max_amount = unit_info.unit_amount * Decimal("1.05")

        conditions = [
            CanonicalProduct.unit_type == unit_info.unit_type.value,
            CanonicalProduct.unit_amount >= min_amount,
            CanonicalProduct.unit_amount <= max_amount,
            CanonicalProduct.package_quantity == unit_info.package_quantity,
        ]

        if brand:
            conditions.append(CanonicalProduct.brand.ilike(f"%{brand}%"))

        stmt = select(CanonicalProduct).where(and_(*conditions)).limit(30)
        result = await session.execute(stmt)
        candidates: List[CanonicalProduct] = list(result.scalars().all())

        if not candidates and brand:
            # Fallback search without brand filter if brand wasn't found in master catalog
            stmt = select(CanonicalProduct).where(
                and_(
                    CanonicalProduct.unit_type == unit_info.unit_type.value,
                    CanonicalProduct.unit_amount >= min_amount,
                    CanonicalProduct.unit_amount <= max_amount,
                    CanonicalProduct.package_quantity == unit_info.package_quantity,
                )
            ).limit(30)
            result = await session.execute(stmt)
            candidates = list(result.scalars().all())

        if not candidates:
            return None

        best_candidate: Optional[CanonicalProduct] = None
        best_score = 0.0

        for cand in candidates:
            # Compute token set ratio and partial ratio
            score_token = fuzz.token_set_ratio(clean_title.lower(), cand.name_et.lower())
            score_sort = fuzz.token_sort_ratio(clean_title.lower(), cand.name_et.lower())
            weighted_score = (score_token * 0.6) + (score_sort * 0.4)

            # Bonus if brand matches exactly
            if brand and cand.brand and brand.lower() == cand.brand.lower():
                weighted_score += 5.0

            normalized_score = min(weighted_score / 100.0, 1.0)

            if normalized_score > best_score:
                best_score = normalized_score
                best_candidate = cand

        if best_candidate and best_score >= cls.CONFIDENCE_THRESHOLD:
            return best_candidate, Decimal(str(round(best_score, 4)))

        return None
