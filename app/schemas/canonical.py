from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import UnitType, MatchTier

class CanonicalProductDTO(BaseModel):
    id: str
    ean: Optional[str] = None
    name_et: str
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    brand: Optional[str] = None
    category_path: List[str] = []
    unit_amount: Decimal
    unit_type: UnitType
    package_quantity: int = 1
    primary_image_url: Optional[str] = None
    custom_image_url: Optional[str] = None
    rich_description: Optional[str] = None
    is_manually_curated: bool = False
    locked_fields: List[str] = []

    @property
    def display_image_url(self) -> Optional[str]:
        return self.custom_image_url or self.primary_image_url

class AdminCanonicalOverrideRequest(BaseModel):
    name_et: Optional[str] = None
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    brand: Optional[str] = None
    category_path: Optional[List[str]] = None
    unit_amount: Optional[Decimal] = None
    unit_type: Optional[UnitType] = None
    package_quantity: Optional[int] = None
    custom_image_url: Optional[str] = None
    rich_description: Optional[str] = None
    lock_fields: List[str] = Field(
        default_factory=list,
        description="Fields protected from automated scraper updates"
    )

class OfferLinkRequest(BaseModel):
    raw_offer_id: str
    canonical_product_id: str
    reviewer: str = "admin"
    lock_mapping: bool = True
