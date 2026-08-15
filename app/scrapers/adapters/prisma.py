from decimal import Decimal
from typing import AsyncIterator, Optional, List, Dict, Any
from app.scrapers.base import BaseStoreScraper
from app.schemas.common import StoreCode
from app.schemas.ingest import ScrapedRawOfferPayload
import structlog

logger = structlog.get_logger()

class PrismaAdapter(BaseStoreScraper):
    """Adapter for Prisma Peremarket (prismamarket.ee)."""

    store_code = StoreCode.PRISMA
    BASE_URL = "https://www.prismamarket.ee"
    API_URL = "https://www.prismamarket.ee/api/products"

    async def fetch_catalog(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[ScrapedRawOfferPayload]:
        page = 1
        page_size = 60
        yielded = 0

        while True:
            params = {
                "page": page,
                "limit": page_size,
            }
            if category:
                params["category_id"] = category

            try:
                data = await self.fast_engine.get_json(self.API_URL, params=params)
            except Exception as e:
                logger.warning("prisma_fetch_failed", page=page, error=str(e))
                break

            items: List[Dict[str, Any]] = data.get("entries") or data.get("products") or []
            if not items:
                break

            for item in items:
                payload = self._parse_item(item)
                if payload:
                    yield payload
                    yielded += 1
                    if limit and yielded >= limit:
                        return

            page_info = data.get("pagination") or {}
            total_pages = page_info.get("total_pages") or 1
            if page >= total_pages:
                break
            page += 1

    async def fetch_promotions(
        self,
        limit: Optional[int] = None,
    ) -> AsyncIterator[ScrapedRawOfferPayload]:
        page = 1
        yielded = 0
        while True:
            params = {
                "page": page,
                "limit": 60,
                "on_sale": "true",
            }
            try:
                data = await self.fast_engine.get_json(self.API_URL, params=params)
            except Exception as e:
                logger.warning("prisma_promotions_failed", page=page, error=str(e))
                break

            items = data.get("entries") or []
            if not items:
                break

            for item in items:
                payload = self._parse_item(item)
                if payload:
                    yield payload
                    yielded += 1
                    if limit and yielded >= limit:
                        return

            page += 1

    def _parse_item(self, item: Dict[str, Any]) -> Optional[ScrapedRawOfferPayload]:
        try:
            item_id = str(item.get("id") or item.get("ean") or item.get("code"))
            name = item.get("name") or item.get("title") or ""
            if not name:
                return None

            price_regular = Decimal(str(item.get("price") or item.get("regular_price") or 0))
            price_discount = None
            if item.get("original_price") and Decimal(str(item["original_price"])) > price_regular:
                # If original price is higher, regular is discounted
                price_discount = price_regular
                price_regular = Decimal(str(item["original_price"]))
            elif item.get("discount_price"):
                price_discount = Decimal(str(item["discount_price"]))

            ean = str(item.get("ean")).strip() if item.get("ean") else None
            slug = item.get("slug") or item_id
            product_url = f"{self.BASE_URL}/entry/{slug}" if not str(slug).startswith("http") else str(slug)

            image_url = item.get("image_url") or item.get("image")

            return ScrapedRawOfferPayload(
                store_code=self.store_code,
                external_id=item_id,
                raw_title=name,
                product_url=product_url,
                raw_price_regular=price_regular,
                raw_price_discount=price_discount,
                raw_price_loyalty=None,
                raw_unit_price=item.get("unit_price"),
                raw_brand=item.get("brand") or item.get("subname"),
                raw_category=item.get("category_name") or item.get("department"),
                raw_description=item.get("description"),
                raw_image_url=image_url,
                raw_ean=ean,
                loyalty_card_required=None,
                is_available=bool(item.get("available", True)),
                raw_payload=item,
            )
        except Exception as ex:
            logger.debug("prisma_parse_error", error=str(ex), item_id=item.get("id"))
            return None
