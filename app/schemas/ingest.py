from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, HttpUrl, computed_field
import hashlib
import json
from app.schemas.common import StoreCode, UnitType, MatchTier

class ScrapedRawOfferPayload(BaseModel):
    store_code: StoreCode
    external_id: str = Field(..., description="Store internal SKU / product ID")
    raw_title: str
    product_url: str
    raw_price_regular: Decimal = Field(..., ge=0)
    raw_price_discount: Optional[Decimal] = Field(None, ge=0)
    raw_price_loyalty: Optional[Decimal] = Field(None, ge=0)
    raw_unit_price: Optional[str] = None
    raw_brand: Optional[str] = None
    raw_category: Optional[str] = None
    raw_description: Optional[str] = None
    raw_image_url: Optional[str] = None
    raw_ean: Optional[str] = None
    loyalty_card_required: Optional[str] = None
    is_available: bool = True
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    raw_payload: Dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def payload_hash(self) -> str:
        """Deterministic hash to skip redundant updates."""
        canonical_dict = {
            "store": self.store_code.value,
            "id": self.external_id,
            "price_reg": str(self.raw_price_regular),
            "price_disc": str(self.raw_price_discount) if self.raw_price_discount is not None else None,
            "price_loyal": str(self.raw_price_loyalty) if self.raw_price_loyalty is not None else None,
            "avail": self.is_available,
            "ean": self.raw_ean,
            "title": self.raw_title.strip(),
        }
        canonical_str = json.dumps(canonical_dict, sort_keys=True)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

class ScrapeResult(BaseModel):
    store_code: StoreCode
    total_scraped: int
    new_offers: int
    updated_offers: int
    errors: int = 0
    duration_seconds: float
    started_at: datetime
    finished_at: datetime
