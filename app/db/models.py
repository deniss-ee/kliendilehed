import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Any, Dict
from sqlalchemy import (
    String,
    Text,
    Numeric,
    Boolean,
    ForeignKey,
    DateTime,
    Integer,
    Enum as SQLEnum,
    UniqueConstraint,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.schemas.common import StoreCode, MatchTier

class Store(Base):
    __tablename__ = "stores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    has_ecom: Mapped[bool] = mapped_column(Boolean, default=True)
    loyalty_program_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    branches: Mapped[List["StoreBranch"]] = relationship("StoreBranch", back_populates="store", cascade="all, delete-orphan")
    raw_offers: Mapped[List["RawScrapedOffer"]] = relationship("RawScrapedOffer", back_populates="store", cascade="all, delete-orphan")
    price_records: Mapped[List["PriceHistory"]] = relationship("PriceHistory", back_populates="store", cascade="all, delete-orphan")

class StoreBranch(Base):
    __tablename__ = "store_branches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    store_id: Mapped[str] = mapped_column(String(36), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    external_branch_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    city: Mapped[str] = mapped_column(String(100), default="Tallinn")
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    store: Mapped["Store"] = relationship("Store", back_populates="branches")

    __table_args__ = (
        UniqueConstraint("store_id", "external_branch_id", name="uq_store_branch_ext_id"),
    )

class CanonicalProduct(Base):
    __tablename__ = "canonical_products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ean: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True, nullable=True)
    name_et: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name_ru: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name_en: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    category_path: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    unit_amount: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(20), nullable=False)
    package_quantity: Mapped[int] = mapped_column(Integer, default=1)

    primary_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rich_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Stored as JSON or Vector depending on backend
    title_embedding: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)

    is_manually_curated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    locked_fields: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    mappings: Mapped[List["OfferCanonicalMapping"]] = relationship(
        "OfferCanonicalMapping", back_populates="canonical_product", cascade="all, delete-orphan"
    )
    price_records: Mapped[List["PriceHistory"]] = relationship("PriceHistory", back_populates="canonical_product")

class RawScrapedOffer(Base):
    __tablename__ = "raw_scraped_offers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    store_id: Mapped[str] = mapped_column(String(36), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(150), nullable=False)

    raw_title: Mapped[str] = mapped_column(Text, nullable=False)
    raw_brand: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    raw_category: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_url: Mapped[str] = mapped_column(Text, nullable=False)
    raw_ean: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)

    raw_price_regular: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    raw_price_discount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    raw_price_loyalty: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    raw_unit_price: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    loyalty_card_required: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    raw_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    store: Mapped["Store"] = relationship("Store", back_populates="raw_offers")
    mapping: Mapped[Optional["OfferCanonicalMapping"]] = relationship(
        "OfferCanonicalMapping", back_populates="raw_offer", uselist=False, cascade="all, delete-orphan"
    )
    price_records: Mapped[List["PriceHistory"]] = relationship(
        "PriceHistory", back_populates="raw_offer", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("store_id", "external_id", name="uq_raw_offers_store_external"),
    )

class OfferCanonicalMapping(Base):
    __tablename__ = "offer_canonical_mapping"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    raw_offer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("raw_scraped_offers.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    canonical_product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("canonical_products.id", ondelete="CASCADE"), nullable=False, index=True
    )

    match_tier: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)

    is_manual_lock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    raw_offer: Mapped["RawScrapedOffer"] = relationship("RawScrapedOffer", back_populates="mapping")
    canonical_product: Mapped["CanonicalProduct"] = relationship("CanonicalProduct", back_populates="mappings")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    raw_offer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("raw_scraped_offers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    canonical_product_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("canonical_products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    store_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("store_branches.id", ondelete="SET NULL"), nullable=True
    )

    price_regular: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_discount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    price_loyalty: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    effective_unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(20), nullable=False)

    discount_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    campaign_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    store: Mapped["Store"] = relationship("Store", back_populates="price_records")
    raw_offer: Mapped["RawScrapedOffer"] = relationship("RawScrapedOffer", back_populates="price_records")
    canonical_product: Mapped[Optional["CanonicalProduct"]] = relationship("CanonicalProduct", back_populates="price_records")

class CatalogAuditLog(Base):
    __tablename__ = "catalog_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(100), default="admin", nullable=False)
    old_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    new_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
