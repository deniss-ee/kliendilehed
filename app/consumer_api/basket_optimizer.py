import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import CanonicalProduct, OfferCanonicalMapping, RawScrapedOffer, Store
from app.schemas.common import StoreCode

class BasketItemRequest(BaseModel):
    canonical_product_id: str
    quantity: int = Field(default=1, ge=1)

class BasketRequest(BaseModel):
    items: List[BasketItemRequest]
    user_loyalty_cards: List[str] = Field(
        default_factory=lambda: ["Partnerkaart", "Rimi kaart", "Säästukaart", "Aitäh kaart", "Lidl Plus"],
        description="List of loyalty cards the user owns",
    )

class StoreOfferQuote(BaseModel):
    store_code: StoreCode
    store_name: str
    product_title: str
    regular_price: Decimal
    effective_price: Decimal
    is_discount: bool
    loyalty_card_used: Optional[str] = None
    product_url: str

class OptimizedBasketItem(BaseModel):
    canonical_product_id: str
    canonical_name: str
    quantity: int
    quotes_by_store: Dict[str, StoreOfferQuote]
    cheapest_store: StoreCode
    cheapest_price: Decimal

class SingleStoreSummary(BaseModel):
    store_code: StoreCode
    store_name: str
    available_items_count: int
    missing_items_count: int
    total_cost: Decimal
    regular_total_cost: Decimal
    total_savings: Decimal
    missing_item_names: List[str] = []

class SplitStoreRoute(BaseModel):
    total_cost: Decimal
    savings_vs_best_single: Decimal
    store_breakdown: Dict[str, List[Dict[str, Any]]] # store_code -> items to buy there

class BasketOptimizationResult(BaseModel):
    total_requested_items: int
    items_analyzed: List[OptimizedBasketItem]
    single_store_rankings: List[SingleStoreSummary]
    cheapest_single_store: Optional[SingleStoreSummary]
    optimized_split_route: SplitStoreRoute
    total_loyalty_savings: Decimal

class BasketOptimizer:
    """Calculates single-store vs multi-store optimal shopping baskets with loyalty discounts."""

    @classmethod
    async def optimize(
        cls,
        session: AsyncSession,
        request: BasketRequest,
    ) -> BasketOptimizationResult:
        product_ids = [str(item.canonical_product_id) for item in request.items]
        qty_map = {str(item.canonical_product_id): item.quantity for item in request.items}

        # 1. Fetch canonical products with mapped store offers
        stmt = (
            select(CanonicalProduct)
            .where(CanonicalProduct.id.in_(product_ids))
            .options(
                selectinload(CanonicalProduct.mappings)
                .joinedload(OfferCanonicalMapping.raw_offer)
                .joinedload(RawScrapedOffer.store)
            )
        )
        result = await session.execute(stmt)
        products = list(result.scalars().all())

        # Also fetch all stores
        stores_res = await session.execute(select(Store))
        all_stores = {s.code: s.name for s in stores_res.scalars().all()}

        analyzed_items: List[OptimizedBasketItem] = []
        # store_code -> list of (item, quote, qty)
        store_inventory: Dict[StoreCode, Dict[str, Dict[str, Any]]] = {code: {} for code in all_stores.keys()}

        split_route_items: Dict[str, List[Dict[str, Any]]] = {
            (code.value if hasattr(code, 'value') else str(code)): [] for code in all_stores.keys()
        }
        split_total_cost = Decimal("0.00")
        total_loyalty_savings = Decimal("0.00")

        for prod in products:
            prod_id_str = str(prod.id)
            qty = qty_map.get(prod_id_str, 1)

            quotes_by_store: Dict[str, StoreOfferQuote] = {}
            cheapest_price = Decimal("999999.99")
            cheapest_store_code_str: str = "SELVER"

            for mapping in prod.mappings:
                offer = mapping.raw_offer
                if not offer or not offer.is_available:
                    continue

                raw_code = offer.store.code
                store_code_str = raw_code.value if hasattr(raw_code, 'value') else str(raw_code)
                store_code_enum = StoreCode(store_code_str) if store_code_str in StoreCode._value2member_map_ else StoreCode.SELVER
                store_name = offer.store.name

                # Determine effective price based on discounts and user's loyalty cards
                effective_price = offer.raw_price_regular
                loyalty_used = None
                is_disc = False

                # 1. Regular discount
                if offer.raw_price_discount and offer.raw_price_discount < effective_price:
                    effective_price = offer.raw_price_discount
                    is_disc = True

                # 2. Loyalty discount
                if offer.raw_price_loyalty:
                    card_req = offer.loyalty_card_required or offer.store.loyalty_program_name
                    if not card_req or card_req in request.user_loyalty_cards:
                        if offer.raw_price_loyalty < effective_price:
                            effective_price = offer.raw_price_loyalty
                            loyalty_used = card_req
                            is_disc = True
                            loyalty_diff = (offer.raw_price_discount or offer.raw_price_regular) - offer.raw_price_loyalty
                            if loyalty_diff > 0:
                                total_loyalty_savings += loyalty_diff * Decimal(qty)

                quote = StoreOfferQuote(
                    store_code=store_code_enum,
                    store_name=store_name,
                    product_title=offer.raw_title,
                    regular_price=offer.raw_price_regular,
                    effective_price=effective_price,
                    is_discount=is_disc,
                    loyalty_card_used=loyalty_used,
                    product_url=offer.product_url,
                )

                quotes_by_store[store_code_str] = quote
                store_inventory[raw_code][prod_id_str] = {
                    "product": prod,
                    "quote": quote,
                    "qty": qty,
                }

                if effective_price < cheapest_price:
                    cheapest_price = effective_price
                    cheapest_store_code_str = store_code_str

            if quotes_by_store:
                item_total = cheapest_price * Decimal(qty)
                split_total_cost += item_total
                split_route_items[cheapest_store_code_str].append(
                    {
                        "canonical_id": prod_id_str,
                        "name": prod.name_et,
                        "quantity": qty,
                        "unit_price": float(cheapest_price),
                        "total_price": float(item_total),
                        "product_url": quotes_by_store[cheapest_store_code_str].product_url,
                    }
                )

                cheapest_enum = StoreCode(cheapest_store_code_str) if cheapest_store_code_str in StoreCode._value2member_map_ else StoreCode.SELVER
                analyzed_items.append(
                    OptimizedBasketItem(
                        canonical_product_id=prod_id_str,
                        canonical_name=prod.name_et,
                        quantity=qty,
                        quotes_by_store=quotes_by_store,
                        cheapest_store=cheapest_enum,
                        cheapest_price=cheapest_price,
                    )
                )

        # 2. Build Single Store Rankings
        single_rankings: List[SingleStoreSummary] = []
        total_requested = len(request.items)

        for store_code, items_dict in store_inventory.items():
            avail_count = len(items_dict)
            if avail_count == 0:
                continue

            missing_count = total_requested - avail_count
            store_total = Decimal("0.00")
            store_reg_total = Decimal("0.00")
            missing_names = []

            for item_req in request.items:
                c_id = item_req.canonical_product_id
                if c_id in items_dict:
                    entry = items_dict[c_id]
                    q = entry["quote"]
                    store_total += q.effective_price * Decimal(entry["qty"])
                    store_reg_total += q.regular_price * Decimal(entry["qty"])
                else:
                    # Find product name
                    p_name = next((p.name_et for p in products if str(p.id) == c_id), "Unknown")
                    missing_names.append(p_name)

            savings = store_reg_total - store_total

            store_code_str = store_code.value if hasattr(store_code, 'value') else str(store_code)
            store_code_enum = StoreCode(store_code_str) if store_code_str in StoreCode._value2member_map_ else StoreCode.SELVER
            s_name = all_stores.get(store_code) or all_stores.get(store_code_str) or store_code_str

            single_rankings.append(
                SingleStoreSummary(
                    store_code=store_code_enum,
                    store_name=s_name,
                    available_items_count=avail_count,
                    missing_items_count=missing_count,
                    total_cost=store_total.quantize(Decimal("0.01")),
                    regular_total_cost=store_reg_total.quantize(Decimal("0.01")),
                    total_savings=savings.quantize(Decimal("0.01")),
                    missing_item_names=missing_names,
                )
            )

        # Sort single store rankings: first by completeness (fewest missing), then by lowest total cost
        single_rankings.sort(key=lambda s: (s.missing_items_count, s.total_cost))
        cheapest_single = single_rankings[0] if single_rankings else None

        # Clean empty stores from split route
        active_split_breakdown = {k: v for k, v in split_route_items.items() if len(v) > 0}
        split_savings = Decimal("0.00")
        if cheapest_single and cheapest_single.missing_items_count == 0:
            split_savings = (cheapest_single.total_cost - split_total_cost).quantize(Decimal("0.01"))

        return BasketOptimizationResult(
            total_requested_items=total_requested,
            items_analyzed=analyzed_items,
            single_store_rankings=single_rankings,
            cheapest_single_store=cheapest_single,
            optimized_split_route=SplitStoreRoute(
                total_cost=split_total_cost.quantize(Decimal("0.01")),
                savings_vs_best_single=max(Decimal("0.00"), split_savings),
                store_breakdown=active_split_breakdown,
            ),
            total_loyalty_savings=total_loyalty_savings.quantize(Decimal("0.01")),
        )
