import asyncio
from datetime import datetime
from typing import List
from app.schemas.common import StoreCode
from app.scrapers.adapters import get_store_adapter
from app.resolution.resolver import EntityResolver
from app.db.session import AsyncSessionLocal
from app.db.models import RawScrapedOffer
from sqlalchemy import select
import structlog

logger = structlog.get_logger()

class LocalOrchestrator:
    """Automated local scraping & entity resolution orchestrator."""

    def __init__(self, stores: List[StoreCode] = None, interval_hours: int = 6):
        self.stores = stores or [StoreCode.SELVER, StoreCode.PRISMA, StoreCode.COOP, StoreCode.RIMI]
        self.interval_hours = interval_hours
        self._is_running = False

    async def run_pipeline_once(self, per_store_limit: int = 100):
        """Runs full scraping & entity resolution cycle once."""
        logger.info("orchestrator_pipeline_started", timestamp=datetime.utcnow().isoformat())

        # 1. Scrape each store
        for store_code in self.stores:
            try:
                adapter = get_store_adapter(store_code)
                logger.info("scraping_store", store=store_code.value)
                
                offers = []
                async for offer in adapter.fetch_promotions(limit=per_store_limit):
                    offers.append(offer)

                if offers:
                    result = await adapter.ingest_batch(offers)
                    logger.info("store_ingest_completed", store=store_code.value, total=result.total_scraped)
                
                await adapter.close()
            except Exception as e:
                logger.error("store_pipeline_failed", store=store_code.value, error=str(e))

        # 2. Entity resolution
        logger.info("entity_resolution_started")
        async with AsyncSessionLocal() as session:
            stmt = select(RawScrapedOffer).limit(per_store_limit * len(self.stores))
            result = await session.execute(stmt)
            unresolved = list(result.scalars().all())

            for offer in unresolved:
                try:
                    await EntityResolver.resolve_offer(session, offer)
                except Exception as e:
                    logger.error("resolution_item_failed", offer_id=str(offer.id), error=str(e))

            await session.commit()
            logger.info("entity_resolution_completed", resolved_count=len(unresolved))

    async def start_loop(self):
        """Starts background recurring execution loop."""
        self._is_running = True
        logger.info("orchestrator_daemon_started", interval_hours=self.interval_hours)

        while self._is_running:
            await self.run_pipeline_once()
            await asyncio.sleep(self.interval_hours * 3600)

    def stop(self):
        self._is_running = False
