from decimal import Decimal
from typing import AsyncIterator, Optional, List, Dict, Any
from bs4 import BeautifulSoup
from app.scrapers.base import BaseStoreScraper
from app.schemas.common import StoreCode
from app.schemas.ingest import ScrapedRawOfferPayload
import structlog
import re

logger = structlog.get_logger()

class RimiAdapter(BaseStoreScraper):
    """Adapter for Rimi (rimi.ee/epood)."""

    store_code = StoreCode.RIMI
    BASE_URL = "https://www.rimi.ee/epood/ee"

    async def fetch_catalog(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[ScrapedRawOfferPayload]:
        page = 1
        page_size = 40
        yielded = 0
        cat_path = category or "tooted"

        while True:
            url = f"{self.BASE_URL}/{cat_path}?currentPage={page}&pageSize={page_size}"
            try:
                html = await self.fast_engine.get_html(url)
            except Exception as e:
                logger.warning("rimi_fetch_failed", page=page, error=str(e))
                break

            items = self._parse_html_products(html)
            if not items:
                break

            for offer in items:
                yield offer
                yielded += 1
                if limit and yielded >= limit:
                    return

            page += 1

    async def fetch_promotions(
        self,
        limit: Optional[int] = None,
    ) -> AsyncIterator[ScrapedRawOfferPayload]:
        """Fetches active Rimi Kaart & campaign discounts."""
        return self.fetch_catalog(category="pakkumised", limit=limit)

    def _parse_html_products(self, html: str) -> List[ScrapedRawOfferPayload]:
        soup = BeautifulSoup(html, "html.parser")
        product_cards = soup.select(".product-grid__item, .card")
        offers: List[ScrapedRawOfferPayload] = []

        for card in product_cards:
            try:
                title_elem = card.select_one(".card__name, .product-card__title")
                if not title_elem:
                    continue
                raw_title = title_elem.get_text(strip=True)

                link_elem = card.select_one("a.card__url, a.product-card__link")
                href = link_elem.get("href") if link_elem else ""
                product_url = f"https://www.rimi.ee{href}" if href.startswith("/") else href

                # Extract SKU / product id from card data attribute or link
                external_id = card.get("data-product-code") or card.get("data-gtm-eec-product-id")
                if not external_id and href:
                    match = re.search(r"/p/([a-zA-Z0-9_-]+)", href)
                    if match:
                        external_id = match.group(1)
                    else:
                        external_id = href.rstrip("/").split("/")[-1]

                if not external_id:
                    continue

                # Pricing
                major_elem = card.select_one(".price-tag .major, .price > span")
                minor_elem = card.select_one(".price-tag .minor, .price sup")
                price_regular = Decimal(0)
                if major_elem:
                    major = major_elem.get_text(strip=True).replace("€", "").strip()
                    minor = minor_elem.get_text(strip=True).replace("€", "").strip() if minor_elem else "00"
                    price_regular = Decimal(f"{major}.{minor}")

                old_price_elem = card.select_one(".old-price, .price--old")
                price_discount = None
                if old_price_elem:
                    old_text = re.sub(r"[^\d,\.]", "", old_price_elem.get_text(strip=True)).replace(",", ".")
                    if old_text:
                        old_price = Decimal(old_text)
                        if old_price > price_regular:
                            price_discount = price_regular
                            price_regular = old_price

                # Unit price
                unit_price_elem = card.select_one(".card__price-per-unit, .price-per")
                raw_unit_price = unit_price_elem.get_text(strip=True) if unit_price_elem else None

                # Image
                img_elem = card.select_one("img")
                raw_image_url = img_elem.get("src") or img_elem.get("data-src") if img_elem else None

                # Loyalty
                loyalty_elem = card.select_one(".card__badge--loyalty, .badge-loyalty")
                loyalty_required = "Rimi kaart" if loyalty_elem else None

                offers.append(
                    ScrapedRawOfferPayload(
                        store_code=self.store_code,
                        external_id=str(external_id),
                        raw_title=raw_title,
                        product_url=product_url or "https://www.rimi.ee/epood",
                        raw_price_regular=price_regular,
                        raw_price_discount=price_discount,
                        raw_price_loyalty=price_discount if loyalty_required else None,
                        raw_unit_price=raw_unit_price,
                        raw_image_url=raw_image_url,
                        loyalty_card_required=loyalty_required,
                        is_available=True,
                        raw_payload={"scraped_html": str(card)[:500]},
                    )
                )
            except Exception as e:
                logger.debug("rimi_card_parse_error", error=str(e))
                continue

        return offers
