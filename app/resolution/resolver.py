import uuid
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import (
    RawScrapedOffer,
    CanonicalProduct,
    OfferCanonicalMapping,
    PriceHistory,
)
from app.schemas.common import MatchTier, UnitType
from app.normalization.unit_extractor import UnitExtractor, ExtractedUnitInfo
from app.normalization.brand_extractor import BrandExtractor
from app.normalization.loyalty_parser import LoyaltyParser
from app.resolution.tier1_barcode import BarcodeMatcher
from app.resolution.tier2_rules import RuleBasedMatcher
from app.resolution.tier3_embeddings import EmbeddingMatcher
import structlog

logger = structlog.get_logger()

class ResolutionResult(BaseModel):
    raw_offer_id: str
    canonical_product_id: str
    match_tier: MatchTier
    confidence: Decimal
    is_new_canonical: bool
    is_manual_locked: bool = False

class EntityResolver:
    """Multi-Tier Local Entity Resolution & Catalog Orchestrator."""

    @classmethod
    async def resolve_offer(
        cls,
        session: AsyncSession,
        raw_offer: RawScrapedOffer,
    ) -> ResolutionResult:
        # 1. Check for manual lock
        existing_mapping_res = await session.execute(
            select(OfferCanonicalMapping).where(
                OfferCanonicalMapping.raw_offer_id == raw_offer.id
            )
        )
        existing_mapping = existing_mapping_res.scalar_one_or_none()

        if existing_mapping and existing_mapping.is_manual_lock:
            # Manual lock active: skip re-matching, preserve manual link
            await cls._record_price_history(session, raw_offer, existing_mapping.canonical_product_id)
            return ResolutionResult(
                raw_offer_id=str(raw_offer.id),
                canonical_product_id=str(existing_mapping.canonical_product_id),
                match_tier=existing_mapping.match_tier,
                confidence=existing_mapping.confidence_score,
                is_new_canonical=False,
                is_manual_locked=True,
            )

        # 2. Extract normalized metadata & units
        unit_info = UnitExtractor.extract(raw_offer.raw_title) or ExtractedUnitInfo(
            raw_match="",
            clean_title=raw_offer.raw_title.strip(),
            unit_amount=Decimal("1.000"),
            unit_type=UnitType.PIECE,
            package_quantity=1,
            original_amount=Decimal("1.000"),
            original_unit="tk",
        )
        detected_brand = BrandExtractor.extract_brand(raw_offer.raw_title, raw_offer.raw_brand)

        # 3. Tier 1: Deterministic EAN Match
        canonical_product: Optional[CanonicalProduct] = None
        match_tier: MatchTier = MatchTier.RULE_BASED
        confidence = Decimal("1.0000")

        if raw_offer.raw_ean:
            canonical_product = await BarcodeMatcher.match(session, raw_offer.raw_ean)
            if canonical_product:
                match_tier = MatchTier.EXACT_EAN
                confidence = Decimal("1.0000")

        # 4. Tier 2: Rule-Based Fuzzy Match
        if not canonical_product:
            tier2_res = await RuleBasedMatcher.match(
                session=session,
                clean_title=unit_info.clean_title,
                brand=detected_brand,
                unit_info=unit_info,
            )
            if tier2_res:
                canonical_product, confidence = tier2_res
                match_tier = MatchTier.RULE_BASED

        # 5. Tier 3: Local Semantic Vector Search
        if not canonical_product:
            tier3_res = await EmbeddingMatcher.match(
                session=session,
                query_text=f"{detected_brand or ''} {unit_info.clean_title}".strip(),
                unit_info=unit_info,
            )
            if tier3_res:
                canonical_product, confidence = tier3_res
                match_tier = MatchTier.SEMANTIC_VECTOR

        is_new = False
        # 6. If no match across all 3 tiers, provision a new CanonicalProduct
        if not canonical_product:
            embedding = EmbeddingMatcher.generate_embedding(
                f"{detected_brand or ''} {unit_info.clean_title}".strip()
            )
            canonical_product = CanonicalProduct(
                id=str(uuid.uuid4()),
                ean=BarcodeMatcher.normalize_ean(raw_offer.raw_ean),
                name_et=unit_info.clean_title,
                brand=detected_brand,
                unit_amount=unit_info.unit_amount,
                unit_type=unit_info.unit_type.value,
                package_quantity=unit_info.package_quantity,
                primary_image_url=raw_offer.raw_image_url,
                title_embedding=embedding,
                is_manually_curated=False,
                locked_fields=[],
            )
            session.add(canonical_product)
            await session.flush()
            is_new = True
            confidence = Decimal("1.0000")

        # 7. Upsert Mapping
        if existing_mapping:
            existing_mapping.canonical_product_id = str(canonical_product.id)
            existing_mapping.match_tier = match_tier.value
            existing_mapping.confidence_score = confidence
        else:
            new_mapping = OfferCanonicalMapping(
                id=str(uuid.uuid4()),
                raw_offer_id=str(raw_offer.id),
                canonical_product_id=str(canonical_product.id),
                match_tier=match_tier.value,
                confidence_score=confidence,
                is_manual_lock=False,
            )
            session.add(new_mapping)

        # 8. Record Price History Snapshot
        await cls._record_price_history(session, raw_offer, str(canonical_product.id))

        return ResolutionResult(
            raw_offer_id=str(raw_offer.id),
            canonical_product_id=str(canonical_product.id),
            match_tier=match_tier,
            confidence=confidence,
            is_new_canonical=is_new,
            is_manual_locked=False,
        )

    @classmethod
    async def _record_price_history(
        cls,
        session: AsyncSession,
        raw_offer: RawScrapedOffer,
        canonical_product_id: str,
    ):
        unit_info = UnitExtractor.extract(raw_offer.raw_title)
        effective_price = raw_offer.raw_price_discount or raw_offer.raw_price_regular
        unit_price = unit_info.calculate_unit_price(effective_price) if unit_info else effective_price

        price_entry = PriceHistory(
            id=str(uuid.uuid4()),
            raw_offer_id=str(raw_offer.id),
            canonical_product_id=str(canonical_product_id),
            store_id=str(raw_offer.store_id),
            price_regular=raw_offer.raw_price_regular,
            price_discount=raw_offer.raw_price_discount,
            price_loyalty=raw_offer.raw_price_loyalty,
            effective_unit_price=unit_price,
            unit_type=unit_info.unit_type.value if unit_info else "piece",
        )
        session.add(price_entry)
