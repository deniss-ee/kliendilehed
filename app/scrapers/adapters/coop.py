from decimal import Decimal
from typing import AsyncIterator, Optional, List, Dict, Any
from app.scrapers.base import BaseStoreScraper
from app.schemas.common import StoreCode
from app.schemas.ingest import ScrapedRawOfferPayload
import structlog

logger = structlog.get_logger()

class CoopAdapter(BaseStoreScraper):
    """Adapter for Coop Eesti (ecoop.ee)."""

    store_code = StoreCode.COOP
    BASE_URL = "https://ecoop.ee"
    API_URL = "https://ecoop.ee/api/v1/products"

    async def fetch_catalog(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[ScrapedRawOfferPayload]:
        page = 1
        page_size = 48
        yielded = 0

        while True:
            params = {
                "page": page,
                "page_size": page_size,
            }
            if category:
                params["category"] = category

            try:
                data = await self.fast_engine.get_json(self.API_URL, params=params)
            except Exception as e:
                logger.warning("coop_fetch_failed", page=page, error=str(e))
                break

            results: List[Dict[str, Any]] = data.get("results") or data.get("data") or []
            if not results:
                break

            for item in results:
                payload = self._parse_item(item)
                if payload:
                    yield payload
                    yielded += 1
                    if limit and yielded >= limit:
                        return

            if not data.get("next"):
                break
            page += 1

    async def fetch_promotions(
        self,
        limit: Optional[int] = None,
    ) -> AsyncIterator[ScrapedRawOfferPayload]:
        """Fetches active Säästukaart & campaign discount products."""
        page = 1
        yielded = 0
        while True:
            params = {
                "page": page,
                "page_size": 48,
                "is_discount": "true",
            }
            try:
                data = await self.fast_engine.get_json(self.API_URL, params=params)
            except Exception as e:
                logger.warning("coop_promotions_failed", page=page, error=str(e))
                break

            results = data.get("results") or []
            if not results:
                break

            for item in results:
                payload = self._parse_item(item)
                if payload:
                    yield payload
                    yielded += 1
                    if limit and yielded >= limit:
                        return

            if not data.get("next"):
                break
            page += 1

    def _parse_item(self, item: Dict[str, Any]) -> Optional[ScrapedRawOfferPayload]:
        try:
            item_id = str(item.get("id") or item.get("code") or item.get("ean"))
            name = item.get("name") or item.get("title") or ""
            if not name:
                return None

            price_regular = Decimal(str(item.get("price") or item.get("regular_price") or 0))
            price_discount = None
            price_loyalty = None

            # Säästukaart loyalty discount
            if item.get("saastukaart_price"):
                price_loyalty = Decimal(str(item["saastukaart_price"]))
            elif item.get("campaign_price"):
                price_discount = Decimal(str(item["campaign_price"]))

            ean = str(item.get("ean") or item.get("barcode")).strip() if (item.get("ean") or item.get("barcode")) else None
            slug = item.get("slug") or item_id
            product_url = f"{self.BASE_URL}/toode/{slug}" if not str(slug).startswith("http") else str(slug)

            images = item.get("images") or []
            image_url = images[0].get("url") if images and isinstance(images[0], dict) else item.get("image")

            return ScrapedRawOfferPayload(
                store_code=self.store_code,
                external_id=item_id,
                raw_title=name,
                product_url=product_url,
                raw_price_regular=price_regular,
                raw_price_discount=price_discount,
                raw_price_loyalty=price_loyalty,
                raw_unit_price=item.get("unit_price_text") or item.get("unit_price"),
                raw_brand=item.get("brand") or item.get("producer"),
                raw_category=item.get("category_path") or item.get("category"),
                raw_description=item.get("description"),
                raw_image_url=image_url,
                raw_ean=ean,
                loyalty_card_required="Säästukaart" if price_loyalty else None,
                is_available=bool(item.get("in_stock", True)),
                raw_payload=item,
            )
        except Exception as ex:
            logger.debug("coop_parse_error", error=str(ex), item_id=item.get("id"))
            return None
