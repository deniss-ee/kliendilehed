import uuid
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, and_, desc
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models import (
    CanonicalProduct,
    RawScrapedOffer,
    OfferCanonicalMapping,
    PriceHistory,
    Store,
)
from app.schemas.common import StoreCode
from app.consumer_api.basket_optimizer import (
    BasketOptimizer,
    BasketRequest,
    BasketOptimizationResult,
)

consumer_router = APIRouter(prefix="/api", tags=["Consumer Portal & Deal Tracker"])

# ============================================================================
# 1. PRODUCT SEARCH & COMPARISON
# ============================================================================

@consumer_router.get("/products/search")
async def search_products(
    query: Optional[str] = Query(None, description="Search keyword, brand, or EAN"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    store: Optional[str] = Query(None, description="Filter by store code (e.g. SELVER, RIMI)"),
    on_sale_only: bool = Query(False, description="Filter only items currently on discount"),
    sort_by: str = Query("relevance", enum=["relevance", "price_asc", "price_desc", "name"]),
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """Public search for grocery items with side-by-side price comparison."""
    stmt = (
        select(CanonicalProduct)
        .options(
            selectinload(CanonicalProduct.mappings)
            .joinedload(OfferCanonicalMapping.raw_offer)
            .joinedload(RawScrapedOffer.store)
        )
    )

    if query:
        search_filter = or_(
            CanonicalProduct.name_et.ilike(f"%{query}%"),
            CanonicalProduct.brand.ilike(f"%{query}%"),
            CanonicalProduct.ean.ilike(f"%{query}%"),
        )
        stmt = stmt.where(search_filter)

    if brand:
        stmt = stmt.where(CanonicalProduct.brand.ilike(f"%{brand}%"))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = (await session.execute(count_stmt)).scalar_one()

    # Apply sorting & pagination
    if sort_by == "name":
        stmt = stmt.order_by(CanonicalProduct.name_et.asc())
    else:
        stmt = stmt.order_by(CanonicalProduct.updated_at.desc())

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(stmt)
    products = result.scalars().all()

    items = []
    for p in products:
        offers_by_store = []
        min_price = Decimal("999999.00")
        has_discount = False

        for m in p.mappings:
            offer = m.raw_offer
            if not offer or not offer.is_available:
                continue

            eff_price = offer.raw_price_loyalty or offer.raw_price_discount or offer.raw_price_regular
            if eff_price < min_price:
                min_price = eff_price

            is_disc = bool(offer.raw_price_discount or offer.raw_price_loyalty)
            if is_disc:
                has_discount = True

            offers_by_store.append(
                {
                    "store_code": offer.store.code.value,
                    "store_name": offer.store.name,
                    "price_regular": float(offer.raw_price_regular),
                    "price_discount": float(offer.raw_price_discount) if offer.raw_price_discount else None,
                    "price_loyalty": float(offer.raw_price_loyalty) if offer.raw_price_loyalty else None,
                    "effective_price": float(eff_price),
                    "is_discount": is_disc,
                    "loyalty_card": offer.loyalty_card_required,
                    "product_url": offer.product_url,
                }
            )

        if on_sale_only and not has_discount:
            continue

        items.append(
            {
                "id": str(p.id),
                "ean": p.ean,
                "name": p.name_et,
                "brand": p.brand,
                "unit": f"{p.unit_amount} {p.unit_type}",
                "package_quantity": p.package_quantity,
                "image_url": p.custom_image_url or p.primary_image_url,
                "min_price": float(min_price) if min_price < 999999 else None,
                "has_discount": has_discount,
                "store_count": len(offers_by_store),
                "offers": offers_by_store,
            }
        )

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "page_size": page_size,
    }

@consumer_router.get("/products/{product_id}")
async def get_product_comparison_profile(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
):
    """Detailed multi-store price comparison and unit pricing for a single product."""
    stmt = (
        select(CanonicalProduct)
        .where(CanonicalProduct.id == product_id)
        .options(
            selectinload(CanonicalProduct.mappings)
            .joinedload(OfferCanonicalMapping.raw_offer)
            .joinedload(RawScrapedOffer.store),
            selectinload(CanonicalProduct.price_records),
        )
    )
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    offers = []
    for m in product.mappings:
        o = m.raw_offer
        eff_price = o.raw_price_loyalty or o.raw_price_discount or o.raw_price_regular
        unit_price = (eff_price / product.unit_amount).quantize(Decimal("0.001")) if product.unit_amount > 0 else eff_price

        offers.append(
            {
                "store_code": o.store.code.value,
                "store_name": o.store.name,
                "store_base_url": o.store.base_url,
                "title_in_store": o.raw_title,
                "price_regular": float(o.raw_price_regular),
                "price_discount": float(o.raw_price_discount) if o.raw_price_discount else None,
                "price_loyalty": float(o.raw_price_loyalty) if o.raw_price_loyalty else None,
                "effective_price": float(eff_price),
                "effective_unit_price": float(unit_price),
                "unit_metric": f"EUR/{product.unit_type}",
                "loyalty_card": o.loyalty_card_required,
                "product_url": o.product_url,
                "raw_image_url": o.raw_image_url,
                "is_available": o.is_available,
            }
        )

    # Sort offers by lowest effective price
    offers.sort(key=lambda x: x["effective_price"])

    return {
        "id": str(product.id),
        "ean": product.ean,
        "name": product.name_et,
        "brand": product.brand,
        "unit_amount": float(product.unit_amount),
        "unit_type": product.unit_type,
        "package_quantity": product.package_quantity,
        "image_url": product.custom_image_url or product.primary_image_url,
        "rich_description": product.rich_description,
        "store_comparison": offers,
    }

# ============================================================================
# 2. PRICE TRENDS & DEALS FEED
# ============================================================================

@consumer_router.get("/products/{product_id}/history")
async def get_product_price_history(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
):
    """Time-series price history across stores for charts."""
    stmt = (
        select(PriceHistory)
        .where(PriceHistory.canonical_product_id == product_id)
        .options(joinedload(PriceHistory.store))
        .order_by(PriceHistory.recorded_at.asc())
    )
    result = await session.execute(stmt)
    records = result.scalars().all()

    return [
        {
            "store_code": r.store.code.value,
            "store_name": r.store.name,
            "price_regular": float(r.price_regular),
            "price_discount": float(r.price_discount) if r.price_discount else None,
            "price_loyalty": float(r.price_loyalty) if r.price_loyalty else None,
            "recorded_at": r.recorded_at,
        }
        for r in records
    ]

@consumer_router.get("/deals")
async def get_top_deals(
    limit: int = Query(30, ge=1, le=100),
    store: Optional[str] = Query(None, description="Filter deals by store code"),
    session: AsyncSession = Depends(get_db_session),
):
    """Real-time deals feed highlighting top supermarket discounts."""
    stmt = (
        select(RawScrapedOffer)
        .where(
            and_(
                RawScrapedOffer.is_available == True,
                or_(
                    RawScrapedOffer.raw_price_discount.isnot(None),
                    RawScrapedOffer.raw_price_loyalty.isnot(None),
                ),
            )
        )
        .options(
            joinedload(RawScrapedOffer.store),
            joinedload(RawScrapedOffer.mapping).joinedload(OfferCanonicalMapping.canonical_product),
        )
        .order_by(RawScrapedOffer.scraped_at.desc())
        .limit(limit)
    )

    result = await session.execute(stmt)
    offers = result.scalars().all()

    deals = []
    for o in offers:
        disc_price = o.raw_price_discount or o.raw_price_loyalty or o.raw_price_regular
        savings = o.raw_price_regular - disc_price
        pct = (savings / o.raw_price_regular * 100).quantize(Decimal("0.1")) if o.raw_price_regular > 0 else Decimal(0)

        canonical = o.mapping.canonical_product if o.mapping else None

        deals.append(
            {
                "raw_offer_id": str(o.id),
                "canonical_product_id": str(canonical.id) if canonical else None,
                "store_code": o.store.code.value,
                "store_name": o.store.name,
                "title": canonical.name_et if canonical else o.raw_title,
                "regular_price": float(o.raw_price_regular),
                "discount_price": float(disc_price),
                "discount_percentage": float(pct),
                "loyalty_card": o.loyalty_card_required,
                "image_url": (canonical.custom_image_url if canonical else None) or o.raw_image_url,
                "product_url": o.product_url,
            }
        )

    # Sort by highest discount percentage
    deals.sort(key=lambda d: d["discount_percentage"], reverse=True)
    return deals

# ============================================================================
# 3. GROCERY BASKET COST OPTIMIZER
# ============================================================================

@consumer_router.post("/basket/optimize", response_model=BasketOptimizationResult)
async def optimize_grocery_basket(
    request: BasketRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Calculates the cheapest single-store vs multi-store shopping basket."""
    if not request.items:
        raise HTTPException(status_code=400, detail="Basket items list cannot be empty")

    return await BasketOptimizer.optimize(session, request)
