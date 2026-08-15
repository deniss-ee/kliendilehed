from decimal import Decimal
from typing import AsyncIterator, Optional, List, Dict, Any
from app.scrapers.base import BaseStoreScraper
from app.schemas.common import StoreCode
from app.schemas.ingest import ScrapedRawOfferPayload
import structlog

logger = structlog.get_logger()

class SelverAdapter(BaseStoreScraper):
    """Adapter for Selver (e-selver.ee)."""

    store_code = StoreCode.SELVER
    BASE_URL = "https://www.selver.ee"
    API_URL = "https://www.selver.ee/api/rest/products"

    async def fetch_catalog(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[ScrapedRawOfferPayload]:
        page = 1
        page_size = 50
        yielded = 0

        while True:
            params = {
                "page": page,
                "pageSize": page_size,
            }
            if category:
                params["category"] = category

            try:
                data = await self.fast_engine.get_json(self.API_URL, params=params)
            except Exception as e:
                logger.warning("selver_fetch_failed", page=page, error=str(e))
                break

            items: List[Dict[str, Any]] = data.get("items") or data.get("products") or []
            if not items:
                break

            for item in items:
                payload = self._parse_item(item)
                if payload:
                    yield payload
                    yielded += 1
                    if limit and yielded >= limit:
                        return

            total_pages = data.get("pageCount") or data.get("total_pages") or 1
            if page >= total_pages:
                break
            page += 1

    async def fetch_promotions(
        self,
        limit: Optional[int] = None,
    ) -> AsyncIterator[ScrapedRawOfferPayload]:
        """Fetches active Partnerkaart & general promotional items."""
        page = 1
        yielded = 0
        while True:
            params = {
                "page": page,
                "pageSize": 50,
                "discount": "1",
            }
            try:
                data = await self.fast_engine.get_json(self.API_URL, params=params)
            except Exception as e:
                logger.warning("selver_promotions_failed", page=page, error=str(e))
                break

            items = data.get("items") or []
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
            sku = str(item.get("sku") or item.get("id"))
            name = item.get("name") or item.get("title") or ""
            if not name:
                return None

            # Prices
            price_regular = Decimal(str(item.get("original_price") or item.get("price") or 0))
            price_discount = None
            price_loyalty = None

            if "special_price" in item and item["special_price"]:
                price_discount = Decimal(str(item["special_price"]))

            if "partner_price" in item and item["partner_price"]:
                price_loyalty = Decimal(str(item["partner_price"]))

            # EAN
            ean = item.get("ean") or item.get("gtin") or item.get("barcode")
            if ean:
                ean = str(ean).strip()

            url_key = item.get("url_key") or sku
            product_url = f"{self.BASE_URL}/{url_key}" if not str(url_key).startswith("http") else str(url_key)

            # Image
            image_url = item.get("image") or item.get("thumbnail")
            if image_url and not str(image_url).startswith("http"):
                image_url = f"https://www.selver.ee/img/800/800/resize/{image_url.lstrip('/')}"

            return ScrapedRawOfferPayload(
                store_code=self.store_code,
                external_id=sku,
                raw_title=name,
                product_url=product_url,
                raw_price_regular=price_regular,
                raw_price_discount=price_discount,
                raw_price_loyalty=price_loyalty,
                raw_unit_price=item.get("unit_price_str") or item.get("unit_price"),
                raw_brand=item.get("brand") or item.get("manufacturer"),
                raw_category=item.get("category_name") or item.get("category"),
                raw_description=item.get("description"),
                raw_image_url=image_url,
                raw_ean=ean,
                loyalty_card_required="Partnerkaart" if price_loyalty else None,
                is_available=bool(item.get("is_in_stock", True)),
                raw_payload=item,
            )
        except Exception as ex:
            logger.debug("selver_parse_error", error=str(ex), item_id=item.get("id"))
            return None
