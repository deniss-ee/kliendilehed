import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import select, func, or_, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models import (
    CanonicalProduct,
    RawScrapedOffer,
    OfferCanonicalMapping,
    CatalogAuditLog,
    PriceHistory,
)
from app.schemas.canonical import (
    CanonicalProductDTO,
    AdminCanonicalOverrideRequest,
    OfferLinkRequest,
)
from app.schemas.common import MatchTier, UnitType
from app.storage.minio_client import storage_client

admin_router = APIRouter(prefix="/api/admin", tags=["Back-Office Admin"])

# ============================================================================
# 1. CATALOG BROWSING & PRODUCT MANAGEMENT
# ============================================================================

@admin_router.get("/products", response_model=Dict[str, Any])
async def list_canonical_products(
    query: Optional[str] = Query(None, description="Search by name, brand, or EAN"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    is_curated: Optional[bool] = Query(None, description="Filter by manual curation status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """List canonical master products with pagination and filters."""
    stmt = select(CanonicalProduct)

    if query:
        search_filter = or_(
            CanonicalProduct.name_et.ilike(f"%{query}%"),
            CanonicalProduct.brand.ilike(f"%{query}%"),
            CanonicalProduct.ean.ilike(f"%{query}%"),
        )
        stmt = stmt.where(search_filter)

    if brand:
        stmt = stmt.where(CanonicalProduct.brand.ilike(f"%{brand}%"))

    if is_curated is not None:
        stmt = stmt.where(CanonicalProduct.is_manually_curated == is_curated)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = (await session.execute(count_stmt)).scalar_one()

    # Pagination
    stmt = stmt.order_by(CanonicalProduct.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(stmt)
    products = result.scalars().all()

    items = [
        {
            "id": str(p.id),
            "ean": p.ean,
            "name_et": p.name_et,
            "brand": p.brand,
            "category_path": p.category_path,
            "unit_amount": float(p.unit_amount),
            "unit_type": p.unit_type,
            "package_quantity": p.package_quantity,
            "display_image_url": p.custom_image_url or p.primary_image_url,
            "custom_image_url": p.custom_image_url,
            "is_manually_curated": p.is_manually_curated,
            "locked_fields": p.locked_fields,
            "updated_at": p.updated_at,
        }
        for p in products
    ]

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size,
    }

@admin_router.get("/products/{product_id}")
async def get_canonical_product_details(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
):
    """Detailed canonical product profile with mapped store offers and price logs."""
    stmt = (
        select(CanonicalProduct)
        .where(CanonicalProduct.id == product_id)
        .options(
            selectinload(CanonicalProduct.mappings).joinedload(OfferCanonicalMapping.raw_offer),
            selectinload(CanonicalProduct.price_records),
        )
    )
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Canonical product not found")

    mapped_offers = []
    for mapping in product.mappings:
        offer = mapping.raw_offer
        mapped_offers.append(
            {
                "mapping_id": str(mapping.id),
                "raw_offer_id": str(offer.id),
                "store_code": offer.store_id,
                "external_id": offer.external_id,
                "raw_title": offer.raw_title,
                "raw_price_regular": float(offer.raw_price_regular),
                "raw_price_discount": float(offer.raw_price_discount) if offer.raw_price_discount else None,
                "raw_price_loyalty": float(offer.raw_price_loyalty) if offer.raw_price_loyalty else None,
                "product_url": offer.product_url,
                "raw_image_url": offer.raw_image_url,
                "raw_ean": offer.raw_ean,
                "match_tier": mapping.match_tier.value,
                "confidence_score": float(mapping.confidence_score),
                "is_manual_lock": mapping.is_manual_lock,
            }
        )

    return {
        "id": str(product.id),
        "ean": product.ean,
        "name_et": product.name_et,
        "name_ru": product.name_ru,
        "name_en": product.name_en,
        "brand": product.brand,
        "category_path": product.category_path,
        "unit_amount": float(product.unit_amount),
        "unit_type": product.unit_type,
        "package_quantity": product.package_quantity,
        "primary_image_url": product.primary_image_url,
        "custom_image_url": product.custom_image_url,
        "display_image_url": product.custom_image_url or product.primary_image_url,
        "rich_description": product.rich_description,
        "is_manually_curated": product.is_manually_curated,
        "locked_fields": product.locked_fields,
        "mapped_offers": mapped_offers,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }

# ============================================================================
# 2. MANUAL OVERRIDE & PRODUCT ENRICHMENT
# ============================================================================

@admin_router.put("/products/{product_id}/override")
async def override_canonical_product(
    product_id: uuid.UUID,
    override: AdminCanonicalOverrideRequest,
    reviewer: str = Query("admin", description="Curator name/ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """Curator overrides canonical product fields and locks them from automated changes."""
    stmt = select(CanonicalProduct).where(CanonicalProduct.id == product_id)
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Canonical product not found")

    old_state = {
        "name_et": product.name_et,
        "brand": product.brand,
        "unit_amount": str(product.unit_amount),
        "unit_type": product.unit_type,
        "custom_image_url": product.custom_image_url,
        "rich_description": product.rich_description,
        "locked_fields": product.locked_fields,
    }

    # Apply manual updates
    if override.name_et is not None:
        product.name_et = override.name_et
    if override.name_ru is not None:
        product.name_ru = override.name_ru
    if override.name_en is not None:
        product.name_en = override.name_en
    if override.brand is not None:
        product.brand = override.brand
    if override.category_path is not None:
        product.category_path = override.category_path
    if override.unit_amount is not None:
        product.unit_amount = override.unit_amount
    if override.unit_type is not None:
        product.unit_type = override.unit_type.value
    if override.package_quantity is not None:
        product.package_quantity = override.package_quantity
    if override.custom_image_url is not None:
        product.custom_image_url = override.custom_image_url
    if override.rich_description is not None:
        product.rich_description = override.rich_description

    # Merge locked fields
    current_locks = set(product.locked_fields or [])
    new_locks = current_locks.union(set(override.lock_fields))
    product.locked_fields = list(new_locks)
    product.is_manually_curated = True
    product.updated_at = datetime.utcnow()

    # Write audit log
    audit = CatalogAuditLog(
        entity_type="CANONICAL_PRODUCT",
        entity_id=product.id,
        action="UPDATE_METADATA",
        changed_by=reviewer,
        old_state=old_state,
        new_state={
            "name_et": product.name_et,
            "brand": product.brand,
            "unit_amount": str(product.unit_amount),
            "unit_type": product.unit_type,
            "custom_image_url": product.custom_image_url,
            "rich_description": product.rich_description,
            "locked_fields": product.locked_fields,
        },
    )
    session.add(audit)
    await session.commit()

    return {"status": "success", "message": "Product metadata updated and locked successfully."}

@admin_router.post("/products/{product_id}/image")
async def upload_custom_product_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    reviewer: str = Query("admin"),
    session: AsyncSession = Depends(get_db_session),
):
    """Uploads a high-resolution product photo to local MinIO and sets custom_image_url."""
    stmt = select(CanonicalProduct).where(CanonicalProduct.id == product_id)
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Canonical product not found")

    content = await file.read()
    image_url = storage_client.upload_image(
        file_bytes=content,
        content_type=file.content_type or "image/jpeg",
        filename_prefix=f"prod-{product_id}",
    )

    old_url = product.custom_image_url
    product.custom_image_url = image_url
    
    # Auto-lock custom image
    current_locks = set(product.locked_fields or [])
    current_locks.add("custom_image_url")
    product.locked_fields = list(current_locks)
    product.is_manually_curated = True
    product.updated_at = datetime.utcnow()

    audit = CatalogAuditLog(
        entity_type="CANONICAL_PRODUCT",
        entity_id=product.id,
        action="UPLOAD_IMAGE",
        changed_by=reviewer,
        old_state={"custom_image_url": old_url},
        new_state={"custom_image_url": image_url},
    )
    session.add(audit)
    await session.commit()

    return {"status": "success", "image_url": image_url}

# ============================================================================
# 3. MANUAL MATCHING, SPLIT & MERGE TOOLS
# ============================================================================

@admin_router.get("/mappings/review")
async def get_mappings_for_review(
    max_confidence: float = Query(0.85, description="Filter matches below confidence threshold"),
    session: AsyncSession = Depends(get_db_session),
):
    """Review queue for low-confidence or uncurated offer matches."""
    stmt = (
        select(OfferCanonicalMapping)
        .where(
            OfferCanonicalMapping.is_manual_lock == False,
            OfferCanonicalMapping.confidence_score <= Decimal(str(max_confidence)),
        )
        .options(
            selectinload(OfferCanonicalMapping.raw_offer),
            selectinload(OfferCanonicalMapping.canonical_product),
        )
        .limit(50)
    )
    result = await session.execute(stmt)
    mappings = result.scalars().all()

    return [
        {
            "mapping_id": str(m.id),
            "match_tier": m.match_tier.value,
            "confidence_score": float(m.confidence_score),
            "offer": {
                "id": str(m.raw_offer.id),
                "store_id": str(m.raw_offer.store_id),
                "title": m.raw_offer.raw_title,
                "price": float(m.raw_offer.raw_price_regular),
                "image_url": m.raw_offer.raw_image_url,
                "ean": m.raw_offer.raw_ean,
            },
            "canonical_product": {
                "id": str(m.canonical_product.id),
                "name_et": m.canonical_product.name_et,
                "brand": m.canonical_product.brand,
                "unit": f"{m.canonical_product.unit_amount} {m.canonical_product.unit_type}",
                "image_url": m.canonical_product.custom_image_url or m.canonical_product.primary_image_url,
            },
        }
        for m in mappings
    ]

@admin_router.post("/mappings/link")
async def link_offer_manually(
    request: OfferLinkRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Manually link a raw store offer to a canonical product with permanent manual lock."""
    raw_offer_id = uuid.UUID(request.raw_offer_id)
    canonical_id = uuid.UUID(request.canonical_product_id)

    stmt = select(OfferCanonicalMapping).where(OfferCanonicalMapping.raw_offer_id == raw_offer_id)
    mapping = (await session.execute(stmt)).scalar_one_or_none()

    if mapping:
        mapping.canonical_product_id = canonical_id
        mapping.match_tier = MatchTier.MANUAL_OVERRIDE
        mapping.confidence_score = Decimal("1.0000")
        mapping.is_manual_lock = request.lock_mapping
        mapping.reviewed_by = request.reviewer
        mapping.reviewed_at = datetime.utcnow()
    else:
        new_mapping = OfferCanonicalMapping(
            raw_offer_id=raw_offer_id,
            canonical_product_id=canonical_id,
            match_tier=MatchTier.MANUAL_OVERRIDE,
            confidence_score=Decimal("1.0000"),
            is_manual_lock=request.lock_mapping,
            reviewed_by=request.reviewer,
            reviewed_at=datetime.utcnow(),
        )
        session.add(new_mapping)

    audit = CatalogAuditLog(
        entity_type="MAPPING",
        entity_id=raw_offer_id,
        action="LINK_OFFER",
        changed_by=request.reviewer,
        new_state={"canonical_product_id": str(canonical_id), "is_manual_lock": request.lock_mapping},
    )
    session.add(audit)
    await session.commit()

    return {"status": "success", "message": "Offer linked and locked successfully."}

@admin_router.post("/mappings/split")
async def split_offer_into_new_product(
    raw_offer_id: uuid.UUID,
    reviewer: str = Query("admin"),
    session: AsyncSession = Depends(get_db_session),
):
    """Splits an incorrectly mapped offer into its own dedicated new CanonicalProduct."""
    stmt = select(RawScrapedOffer).where(RawScrapedOffer.id == raw_offer_id)
    raw_offer = (await session.execute(stmt)).scalar_one_or_none()

    if not raw_offer:
        raise HTTPException(status_code=404, detail="Raw offer not found")

    from app.normalization.unit_extractor import UnitExtractor
    from app.normalization.brand_extractor import BrandExtractor

    unit_info = UnitExtractor.extract(raw_offer.raw_title)
    brand = BrandExtractor.extract_brand(raw_offer.raw_title, raw_offer.raw_brand)

    # Create fresh canonical entity
    new_product = CanonicalProduct(
        id=uuid.uuid4(),
        ean=raw_offer.raw_ean,
        name_et=unit_info.clean_title if unit_info else raw_offer.raw_title,
        brand=brand,
        unit_amount=unit_info.unit_amount if unit_info else Decimal("1.000"),
        unit_type=unit_info.unit_type.value if unit_info else "piece",
        package_quantity=unit_info.package_quantity if unit_info else 1,
        primary_image_url=raw_offer.raw_image_url,
        is_manually_curated=True,
    )
    session.add(new_product)
    await session.flush()

    # Re-link mapping
    map_stmt = select(OfferCanonicalMapping).where(OfferCanonicalMapping.raw_offer_id == raw_offer_id)
    mapping = (await session.execute(map_stmt)).scalar_one_or_none()

    if mapping:
        mapping.canonical_product_id = new_product.id
        mapping.match_tier = MatchTier.MANUAL_OVERRIDE
        mapping.confidence_score = Decimal("1.0000")
        mapping.is_manual_lock = True
        mapping.reviewed_by = reviewer
        mapping.reviewed_at = datetime.utcnow()

    await session.commit()
    return {"status": "success", "new_canonical_product_id": str(new_product.id)}

@admin_router.post("/products/merge")
async def merge_canonical_products(
    target_product_id: uuid.UUID,
    source_product_ids: List[uuid.UUID],
    reviewer: str = Query("admin"),
    session: AsyncSession = Depends(get_db_session),
):
    """Merges multiple duplicate canonical products into a single target product."""
    # 1. Re-point all mappings from source products to target product
    await session.execute(
        update(OfferCanonicalMapping)
        .where(OfferCanonicalMapping.canonical_product_id.in_(source_product_ids))
        .values(
            canonical_product_id=target_product_id,
            match_tier=MatchTier.MANUAL_OVERRIDE,
            is_manual_lock=True,
            reviewed_by=reviewer,
            reviewed_at=datetime.utcnow(),
        )
    )

    # 2. Re-point price history records
    await session.execute(
        update(PriceHistory)
        .where(PriceHistory.canonical_product_id.in_(source_product_ids))
        .values(canonical_product_id=target_product_id)
    )

    # 3. Delete obsolete source canonical products
    await session.execute(
        delete(CanonicalProduct).where(CanonicalProduct.id.in_(source_product_ids))
    )

    audit = CatalogAuditLog(
        entity_type="CANONICAL_PRODUCT",
        entity_id=target_product_id,
        action="MERGE_PRODUCTS",
        changed_by=reviewer,
        old_state={"merged_ids": [str(sid) for sid in source_product_ids]},
    )
    session.add(audit)
    await session.commit()

    return {"status": "success", "message": f"Merged {len(source_product_ids)} products into {target_product_id}"}

@admin_router.get("/audit-logs")
async def get_catalog_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
):
    """View recent curation audit logs."""
    stmt = select(CatalogAuditLog).order_by(CatalogAuditLog.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    logs = result.scalars().all()
    return logs
