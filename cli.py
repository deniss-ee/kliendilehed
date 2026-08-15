import asyncio
import click
from rich.console import Console
from rich.table import Table
from app.schemas.common import StoreCode
from app.scrapers.adapters import get_store_adapter
from app.db.session import engine, Base, AsyncSessionLocal
import structlog

console = Console()

@click.group()
def cli():
    """Estonian Grocery Comparison & Price Tracker CLI."""
    pass

@cli.command()
def init_db():
    """Create all database tables and seed store chains locally."""
    async def _init():
        from sqlalchemy import select
        from app.db.models import Store
        from app.schemas.common import StoreCode

        console.print("[bold blue]Connecting to database & creating schema...[/bold blue]")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Seed stores
        async with AsyncSessionLocal() as session:
            stores_data = [
                ("SELVER", "Selver", "https://www.selver.ee", True, "Partnerkaart"),
                ("RIMI", "Rimi", "https://www.rimi.ee/epood", True, "Rimi kaart"),
                ("PRISMA", "Prisma", "https://www.prismamarket.ee", True, "S-Etukortti / Prisma Konto"),
                ("MAXIMA", "Maxima (Barbora)", "https://barbora.ee", True, "Aitäh kaart"),
                ("COOP", "Coop", "https://ecoop.ee", True, "Säästukaart / Säästukaart Pluss"),
                ("GROSSI", "Grossi Toidukaubad", "https://www.grossitoidukaubad.ee", False, None),
                ("LIDL", "Lidl", "https://www.lidl.ee", False, "Lidl Plus"),
            ]
            for code, name, base_url, has_ecom, loyalty in stores_data:
                res = await session.execute(select(Store).where(Store.code == code))
                if not res.scalar_one_or_none():
                    session.add(Store(code=code, name=name, base_url=base_url, has_ecom=has_ecom, loyalty_program_name=loyalty))
            await session.commit()

        console.print("[bold green][OK] Database schema initialized and stores seeded successfully![/bold green]")

    asyncio.run(_init())

@cli.command()
@click.option(
    "--store",
    type=click.Choice([s.value for s in StoreCode], case_sensitive=False),
    required=True,
    help="Store to scrape (e.g. SELVER, PRISMA, COOP, RIMI)",
)
@click.option("--limit", default=10, help="Maximum number of offers to fetch for preview")
@click.option("--promotions-only", is_flag=True, default=False, help="Fetch discount/campaign items only")
def test_scrape(store: str, limit: int, promotions_only: bool):
    """Test scraping a store adapter and preview raw items."""
    async def _test():
        store_code = StoreCode(store.upper())
        adapter = get_store_adapter(store_code)

        console.print(f"[bold cyan]Fetching up to {limit} items from {store_code.value}...[/bold cyan]")
        
        table = Table(title=f"Sample Offers from {store_code.value}")
        table.add_column("External ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Price (Reg / Disc / Loyal)", style="green")
        table.add_column("EAN", style="magenta")
        table.add_column("Unit Price", style="yellow")

        count = 0
        try:
            stream = adapter.fetch_promotions(limit=limit) if promotions_only else adapter.fetch_catalog(limit=limit)
            async for offer in stream:
                disc_str = f" / -{offer.raw_price_discount}€" if offer.raw_price_discount else ""
                loyal_str = f" / {offer.raw_price_loyalty}€ ({offer.loyalty_card_required})" if offer.raw_price_loyalty else ""
                price_summary = f"{offer.raw_price_regular}€{disc_str}{loyal_str}"

                table.add_row(
                    offer.external_id,
                    offer.raw_title[:40],
                    price_summary,
                    offer.raw_ean or "-",
                    offer.raw_unit_price or "-",
                )
                count += 1
                if count >= limit:
                    break
        finally:
            await adapter.close()

        console.print(table)
        console.print(f"[bold green][OK] Fetched and validated {count} items successfully![/bold green]")

    asyncio.run(_test())

@cli.command()
@click.argument("text", default="Farmi hapukoor 20% 500g")
@click.option("--price", default=1.49, type=float, help="Sample price in EUR")
def test_normalize(text: str, price: float):
    """Test unit extraction, brand recognition, and unit price calculation on a title."""
    from decimal import Decimal
    from app.normalization.unit_extractor import UnitExtractor
    from app.normalization.brand_extractor import BrandExtractor
    from app.normalization.loyalty_parser import LoyaltyParser

    unit_info = UnitExtractor.extract(text)
    brand = BrandExtractor.extract_brand(text)
    loyalty = LoyaltyParser.parse(text)

    console.print(f"[bold cyan]Input Title:[/bold cyan] {text}")
    console.print(f"[bold cyan]Input Price:[/bold cyan] {price:.2f} €")
    console.print("-" * 50)
    
    if unit_info:
        u_price = unit_info.calculate_unit_price(Decimal(str(price)))
        console.print(f"[bold green]Standard Unit:[/bold green] {unit_info.unit_amount} {unit_info.unit_type.value} (qty: {unit_info.package_quantity})")
        console.print(f"[bold green]Calculated Unit Price:[/bold green] [bold yellow]{u_price} €/{unit_info.unit_type.value}[/bold yellow]")
        console.print(f"[bold green]Clean Title (without units):[/bold green] '{unit_info.clean_title}'")
    
    console.print(f"[bold magenta]Detected Brand:[/bold magenta] {brand or 'None'}")
    if loyalty.loyalty_program:
        console.print(f"[bold blue]Loyalty Program:[/bold blue] {loyalty.loyalty_program}")

@cli.command()
@click.option("--limit", default=50, help="Maximum number of offers to resolve")
def resolve_offers(limit: int):
    """Run 3-tier entity resolution pipeline on unprocessed scraped offers."""
    async def _resolve():
        from sqlalchemy import select
        from app.db.session import AsyncSessionLocal
        from app.db.models import RawScrapedOffer
        from app.resolution.resolver import EntityResolver

        console.print(f"[bold cyan]Running 3-tier entity resolution on up to {limit} offers...[/bold cyan]")
        async with AsyncSessionLocal() as session:
            stmt = select(RawScrapedOffer).limit(limit)
            result = await session.execute(stmt)
            offers = list(result.scalars().all())

            if not offers:
                console.print("[yellow]No raw offers found in database. Run scrapers first![/yellow]")
                return

            new_can_count = 0
            mapped_count = 0
            for offer in offers:
                res = await EntityResolver.resolve_offer(session, offer)
                if res.is_new_canonical:
                    new_can_count += 1
                mapped_count += 1

            await session.commit()

        console.print(f"[bold green][OK] Resolved {mapped_count} offers ({new_can_count} new canonical products created)![/bold green]")

    asyncio.run(_resolve())

@cli.command()
@click.option("--host", default="127.0.0.1", help="Host interface")
@click.option("--port", default=8000, help="Port to listen on")
@click.option("--reload", is_flag=True, default=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    """Start the FastAPI backend server."""
    import uvicorn
    console.print(f"[bold green]Starting API Server at http://{host}:{port}... (Swagger docs at http://{host}:{port}/docs)[/bold green]")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)

@cli.command()
@click.option("--limit", default=20, help="Items to scrape per store")
def run_pipeline(limit: int):
    """Run full scraping and entity resolution pipeline across all Estonian stores."""
    from app.orchestration.scheduler import LocalOrchestrator
    orchestrator = LocalOrchestrator()
    console.print(f"[bold cyan]Triggering pipeline for all stores (limit {limit} items/store)...[/bold cyan]")
    asyncio.run(orchestrator.run_pipeline_once(per_store_limit=limit))
    console.print("[bold green][OK] Pipeline cycle completed![/bold green]")

@cli.command()
@click.option("--interval", default=6, help="Interval in hours between runs")
def start_scheduler(interval: int):
    """Start background recurring scraping daemon."""
    from app.orchestration.scheduler import LocalOrchestrator
    orchestrator = LocalOrchestrator(interval_hours=interval)
    console.print(f"[bold green]Starting background scraper daemon (every {interval} hours)... Press Ctrl+C to stop.[/bold green]")
    try:
        asyncio.run(orchestrator.start_loop())
    except KeyboardInterrupt:
        orchestrator.stop()
        console.print("[yellow]Scheduler stopped.[/yellow]")

@cli.command()
def demo_e2e():
    """Run full End-to-End simulation: Ingest -> 3-Tier Resolution -> Basket Optimization."""
    async def _demo():
        from decimal import Decimal
        from app.db.session import AsyncSessionLocal
        from app.db.models import Store, RawScrapedOffer, CanonicalProduct
        from app.schemas.common import StoreCode, UnitType
        from app.schemas.ingest import ScrapedRawOfferPayload
        from app.scrapers.adapters import get_store_adapter
        from app.resolution.resolver import EntityResolver
        from app.consumer_api.basket_optimizer import BasketOptimizer, BasketRequest, BasketItemRequest
        from sqlalchemy import select

        console.print("[bold cyan]================================================================[/bold cyan]")
        console.print("[bold cyan]       ESTONIAN GROCERY PLATFORM: END-TO-END DEMO SIMULATION    [/bold cyan]")
        console.print("[bold cyan]================================================================[/bold cyan]\n")

        # 1. Prepare realistic multi-store grocery offers
        sample_offers = [
            # Item 1: Tere Piim 2.5% 1L (Same EAN across stores)
            ScrapedRawOfferPayload(
                store_code=StoreCode.SELVER, external_id="selver-milk-1", raw_title="Tere piim 2,5% 1L kile",
                product_url="https://selver.ee/tere-piim", raw_price_regular=Decimal("0.89"), raw_price_discount=Decimal("0.75"),
                raw_ean="4740098110033", raw_brand="Tere"
            ),
            ScrapedRawOfferPayload(
                store_code=StoreCode.PRISMA, external_id="prisma-milk-1", raw_title="Piim 2,5% Tere 1 l",
                product_url="https://prismamarket.ee/tere-piim", raw_price_regular=Decimal("0.85"),
                raw_ean="4740098110033", raw_brand="Tere"
            ),
            ScrapedRawOfferPayload(
                store_code=StoreCode.COOP, external_id="coop-milk-1", raw_title="Kilepiim Tere 2.5% 1L",
                product_url="https://ecoop.ee/tere-piim", raw_price_regular=Decimal("0.89"), raw_price_loyalty=Decimal("0.69"),
                loyalty_card_required="Säästukaart", raw_ean="4740098110033", raw_brand="Tere"
            ),

            # Item 2: Alma Või 82% 200g
            ScrapedRawOfferPayload(
                store_code=StoreCode.SELVER, external_id="selver-butter-1", raw_title="Alma Eesti või 82% 200g",
                product_url="https://selver.ee/alma-voi", raw_price_regular=Decimal("2.19"), raw_brand="Alma"
            ),
            ScrapedRawOfferPayload(
                store_code=StoreCode.PRISMA, external_id="prisma-butter-1", raw_title="Või 82% Alma 200 g",
                product_url="https://prismamarket.ee/alma-voi", raw_price_regular=Decimal("1.89"), raw_brand="Alma"
            ),
            ScrapedRawOfferPayload(
                store_code=StoreCode.COOP, external_id="coop-butter-1", raw_title="Eesti või Alma 82% 200g",
                product_url="https://ecoop.ee/alma-voi", raw_price_regular=Decimal("2.25"), raw_price_loyalty=Decimal("1.79"),
                loyalty_card_required="Säästukaart", raw_brand="Alma"
            ),

            # Item 3: Paulig Classic Kohvioad 1kg
            ScrapedRawOfferPayload(
                store_code=StoreCode.SELVER, external_id="selver-coffee-1", raw_title="Paulig Classic kohvioad 1kg",
                product_url="https://selver.ee/paulig", raw_price_regular=Decimal("14.99"), raw_price_discount=Decimal("10.99"),
                raw_brand="Paulig"
            ),
            ScrapedRawOfferPayload(
                store_code=StoreCode.PRISMA, external_id="prisma-coffee-1", raw_title="Kohvioad Classic Paulig 1 kg",
                product_url="https://prismamarket.ee/paulig", raw_price_regular=Decimal("12.49"), raw_brand="Paulig"
            ),
            ScrapedRawOfferPayload(
                store_code=StoreCode.COOP, external_id="coop-coffee-1", raw_title="Paulig Classic kohviuba 1000g",
                product_url="https://ecoop.ee/paulig", raw_price_regular=Decimal("13.99"), raw_brand="Paulig"
            ),

            # Item 4: Farmi Hapukoor 20% 500g
            ScrapedRawOfferPayload(
                store_code=StoreCode.SELVER, external_id="selver-sourcream-1", raw_title="Farmi hapukoor 20% 500g",
                product_url="https://selver.ee/farmi", raw_price_regular=Decimal("1.59"), raw_brand="Farmi"
            ),
            ScrapedRawOfferPayload(
                store_code=StoreCode.PRISMA, external_id="prisma-sourcream-1", raw_title="Hapukoor 20% Farmi 500 g",
                product_url="https://prismamarket.ee/farmi", raw_price_regular=Decimal("1.45"), raw_brand="Farmi"
            ),
        ]

        console.print(f"[bold yellow]Step 1: Ingesting {len(sample_offers)} store offers across Selver, Prisma, and Coop...[/bold yellow]")
        by_store = {}
        for off in sample_offers:
            by_store.setdefault(off.store_code, []).append(off)
        for store_code, offers in by_store.items():
            adapter = get_store_adapter(store_code)
            await adapter.ingest_batch(offers)
            await adapter.close()
        console.print("[green][OK] Raw store offers saved successfully.[/green]\n")

        # 2. Run Resolution
        console.print("[bold yellow]Step 2: Running 3-Tier Entity Resolution Engine...[/bold yellow]")
        async with AsyncSessionLocal() as session:
            stmt = select(RawScrapedOffer)
            raw_offers = list((await session.execute(stmt)).scalars().all())
            resolved_canonicals = []

            for r_off in raw_offers:
                res = await EntityResolver.resolve_offer(session, r_off)
                if res.canonical_product_id not in resolved_canonicals:
                    resolved_canonicals.append(res.canonical_product_id)

            await session.commit()
            console.print(f"[green][OK] Merged {len(raw_offers)} store offers into {len(resolved_canonicals)} Master Canonical Products![/green]\n")

            # 3. Basket Optimizer
            console.print("[bold yellow]Step 3: Calculating Smart Grocery Basket for 4 items...[/bold yellow]")
            basket_req = BasketRequest(
                items=[
                    BasketItemRequest(canonical_product_id=cid, quantity=1)
                    for cid in resolved_canonicals
                ],
                user_loyalty_cards=["Partnerkaart", "Säästukaart", "Rimi kaart"],
            )

            opt_result = await BasketOptimizer.optimize(session, basket_req)

            # Print Single Store Rankings
            console.print("\n[bold]Single-Store Basket Totals:[/bold]")
            for rank, store_summary in enumerate(opt_result.single_store_rankings, 1):
                missing = f" (Missing {store_summary.missing_items_count} items)" if store_summary.missing_items_count > 0 else " (All items available)"
                console.print(f"  [{rank}] [bold]{store_summary.store_name}[/bold]: [bold green]{store_summary.total_cost} EUR[/bold green]{missing} | Savings: {store_summary.total_savings} EUR")

            # Print Split Route
            console.print(f"\n[bold]Smart Split-Store Route (Cheapest Combined Total):[/bold]")
            console.print(f"  Total Spend: [bold green]{opt_result.optimized_split_route.total_cost} EUR[/bold green]")
            console.print(f"  Extra Savings vs Best Single Store: [bold yellow]{opt_result.optimized_split_route.savings_vs_best_single} EUR[/bold yellow]")
            console.print(f"  Total Loyalty Card Savings: [bold cyan]{opt_result.total_loyalty_savings} EUR[/bold cyan]")
            
            console.print("\n[bold]Where to buy each item:[/bold]")
            for store_name, items in opt_result.optimized_split_route.store_breakdown.items():
                console.print(f"  * [bold magenta]{store_name}:[/bold magenta]")
                for it in items:
                    console.print(f"     - {it['name']}: {it['unit_price']:.2f} EUR")

        console.print("\n[bold green]================================================================[/bold green]")
        console.print("[bold green]          DEMO COMPLETE: ALL SYSTEMS RUNNING PERFECTLY!          [/bold green]")
        console.print("[bold green]================================================================[/bold green]")

    asyncio.run(_demo())

if __name__ == "__main__":
    cli()
