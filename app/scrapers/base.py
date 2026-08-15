import abc
import time
from datetime import datetime
from typing import AsyncIterator, List, Optional
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.db.session import AsyncSessionLocal
from app.db.models import Store, RawScrapedOffer
from app.schemas.common import StoreCode
from app.schemas.ingest import ScrapedRawOfferPayload, ScrapeResult
from app.scrapers.engine_fast import FastEngine
import structlog

logger = structlog.get_logger()

class BaseStoreScraper(abc.ABC):
    """Abstract base class for all Estonian store adapters."""

    store_code: StoreCode
    fast_engine: FastEngine

    def __init__(self, requests_per_second: float = 2.0):
        self.fast_engine = FastEngine(rate_limit_rps=requests_per_second)

    @abc.abstractmethod
    async def fetch_catalog(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[ScrapedRawOfferPayload]:
        """Stream raw product offers from the store."""
        pass

    @abc.abstractmethod
    async def fetch_promotions(
        self,
        limit: Optional[int] = None,
    ) -> AsyncIterator[ScrapedRawOfferPayload]:
        """Stream current discount campaigns & promotional deals."""
        pass

    async def ingest_batch(self, offers: List[ScrapedRawOfferPayload]) -> ScrapeResult:
        """Persists raw offers into database with idempotent hash change-detection."""
        started_at = datetime.utcnow()
        t0 = time.monotonic()
        total = len(offers)
        new_count = 0
        updated_count = 0
        error_count = 0

        async with AsyncSessionLocal() as session:
            # 1. Resolve store ID
            res = await session.execute(
                select(Store.id).where(Store.code == self.store_code)
            )
            store_id = res.scalar_one_or_none()
            if not store_id:
                raise ValueError(f"Store with code {self.store_code} not found in database. Run init-db seed.")

            for offer in offers:
                try:
                    stmt = insert(RawScrapedOffer).values(
                        store_id=store_id,
                        external_id=offer.external_id,
                        raw_title=offer.raw_title,
                        raw_brand=offer.raw_brand,
                        raw_category=offer.raw_category,
                        raw_description=offer.raw_description,
                        raw_image_url=offer.raw_image_url,
                        product_url=offer.product_url,
                        raw_ean=offer.raw_ean,
                        raw_price_regular=offer.raw_price_regular,
                        raw_price_discount=offer.raw_price_discount,
                        raw_price_loyalty=offer.raw_price_loyalty,
                        raw_unit_price=offer.raw_unit_price,
                        loyalty_card_required=offer.loyalty_card_required,
                        raw_payload=offer.raw_payload,
                        payload_hash=offer.payload_hash,
                        is_available=offer.is_available,
                        scraped_at=offer.scraped_at,
                    )

                    # On conflict, only update if payload hash changed
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["store_id", "external_id"],
                        set_={
                            "raw_title": stmt.excluded.raw_title,
                            "raw_brand": stmt.excluded.raw_brand,
                            "raw_category": stmt.excluded.raw_category,
                            "raw_image_url": stmt.excluded.raw_image_url,
                            "product_url": stmt.excluded.product_url,
                            "raw_ean": stmt.excluded.raw_ean,
                            "raw_price_regular": stmt.excluded.raw_price_regular,
                            "raw_price_discount": stmt.excluded.raw_price_discount,
                            "raw_price_loyalty": stmt.excluded.raw_price_loyalty,
                            "raw_unit_price": stmt.excluded.raw_unit_price,
                            "loyalty_card_required": stmt.excluded.loyalty_card_required,
                            "raw_payload": stmt.excluded.raw_payload,
                            "payload_hash": stmt.excluded.payload_hash,
                            "is_available": stmt.excluded.is_available,
                            "scraped_at": stmt.excluded.scraped_at,
                        },
                        where=(RawScrapedOffer.payload_hash != stmt.excluded.payload_hash),
                    )

                    result = await session.execute(stmt)
                    if result.rowcount > 0:
                        updated_count += 1
                except Exception as e:
                    logger.error("error_ingesting_offer", error=str(e), external_id=offer.external_id)
                    error_count += 1

            await session.commit()

        finished_at = datetime.utcnow()
        duration = time.monotonic() - t0

        return ScrapeResult(
            store_code=self.store_code,
            total_scraped=total,
            new_offers=new_count,
            updated_offers=updated_count,
            errors=error_count,
            duration_seconds=round(duration, 3),
            started_at=started_at,
            finished_at=finished_at,
        )

    async def close(self):
        await self.fast_engine.close()
