# Estonian Grocery Price Tracker, Deal Comparison & Basket Optimizer

A complete, 100% local-first grocery price comparison, deal tracker, and basket optimization platform for the Estonian retail market (Selver, Rimi, Prisma, Maxima, Coop, Grossi, Lidl).

---

## Key Architecture & Guarantees

1. **100% Local-First Infrastructure:** Runs locally with `docker-compose.yml` (PostgreSQL 16 with `pgvector`, Redis, and local MinIO S3 object storage). Zero external cloud dependencies.
2. **Two-Tier Data Model:** Decouples raw immutable store scrapes (`raw_scraped_offers`) from canonical master products (`canonical_products`).
3. **Curation Lock Protection:** Back-office edits (titles, custom high-resolution photos, descriptions, brand/category overrides) are never overwritten by automated scraping runs.
4. **Local 3-Tier Entity Resolution:**
   - **Tier 1:** Exact EAN-13 / GTIN barcode match.
   - **Tier 2:** Rule-based brand + unit volume + token similarity (`RapidFuzz`).
   - **Tier 3:** Local semantic vector embeddings (`FastEmbed` / `pgvector` HNSW cosine similarity).
5. **Smart Basket Cost Optimizer:** Calculates single-store rankings vs multi-store split shopping routes and quantifies loyalty program savings (Säästukaart, Partnerkaart, Rimi kaart, Aitäh kaart).

---

## Quickstart Guide

### 1. Start Local Infrastructure
```bash
docker compose up -d
```
Services:
- **PostgreSQL 16 + pgvector:** `localhost:5432`
- **Redis 7:** `localhost:6379`
- **MinIO Storage Console:** `http://localhost:9001` (User: `minioadmin`, Pass: `minioadmin`)

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database Schema
```bash
python cli.py init-db
```

### 4. CLI Commands

```bash
# Test unit extraction & price normalization
python cli.py test-normalize "Tere piim 2,5% 1L" --price 0.89
python cli.py test-normalize "Coca-Cola karastusjook 6x0.33l" --price 4.99

# Test individual store scrapers
python cli.py test-scrape --store SELVER --limit 10
python cli.py test-scrape --store PRISMA --limit 10
python cli.py test-scrape --store COOP --limit 10 --promotions-only
python cli.py test-scrape --store RIMI --limit 10

# Run 3-tier entity resolution on scraped offers
python cli.py resolve-offers --limit 50

# Run a full scraping + resolution cycle across all stores
python cli.py run-pipeline --limit 30

# Start the background recurring scheduler (runs every 6 hours)
python cli.py start-scheduler --interval 6

# Start the FastAPI Backend Server
python cli.py serve --port 8000
```

---

## API Documentation (`http://localhost:8000/docs`)

### Consumer Endpoints
- `GET /api/products/search`: Search products with multi-store comparison and filters.
- `GET /api/products/{id}`: Detailed side-by-side store price comparison and price-per-unit metrics.
- `GET /api/products/{id}/history`: Time-series price trends chart data.
- `GET /api/deals`: Top supermarket discounts sorted by savings percentage.
- `POST /api/basket/optimize`: Grocery basket optimizer (single-store vs multi-store cheapest shopping route with loyalty card calculation).

### Back-Office Admin Endpoints
- `GET /api/admin/products`: Browse and filter canonical catalog.
- `GET /api/admin/products/{id}`: View product details with mapped store offers.
- `PUT /api/admin/products/{id}/override`: Manual override of product title, brand, units, description, and field locks.
- `POST /api/admin/products/{id}/image`: Upload custom high-resolution product photos directly to local MinIO.
- `GET /api/admin/mappings/review`: Queue of low-confidence matches for review.
- `POST /api/admin/mappings/link`: Manually link offer to master product with permanent lock (`is_manual_lock = True`).
- `POST /api/admin/mappings/split`: Split misclassified offer into a fresh canonical entity.
- `POST /api/admin/products/merge`: Merge duplicate canonical products.
- `GET /api/admin/audit-logs`: Audit trail for back-office user curation actions.

---

## Project Structure

```
kliendilehed/
├── docker/
│   ├── docker-compose.yml
│   └── init-db.sql              # Database schema, extensions & store seeds
├── app/
│   ├── config.py                # App configuration
│   ├── main.py                  # FastAPI entry point
│   ├── db/
│   │   ├── session.py           # Async SQLAlchemy session
│   │   └── models.py            # Complete ORM models & pgvector integration
│   ├── schemas/
│   │   ├── common.py            # Enums
│   │   ├── ingest.py            # Scraper payload contracts
│   │   └── canonical.py         # Master catalog & admin DTOs
│   ├── scrapers/
│   │   ├── base.py              # Base Store Scraper
│   │   ├── middleware.py        # Token-bucket rate limiter & headers
│   │   ├── engine_fast.py       # High-throughput async HTTP client
│   │   ├── engine_browser.py    # Playwright headless browser engine
│   │   └── adapters/            # Selver, Prisma, Coop, Rimi adapters
│   ├── normalization/
│   │   ├── unit_extractor.py    # Multilingual unit & multi-pack regexes
│   │   ├── loyalty_parser.py    # Store loyalty & multi-buy condition parser
│   │   └── brand_extractor.py   # Baltic FMCG brand recognizer
│   ├── resolution/
│   │   ├── tier1_barcode.py     # EAN-13 deterministic matcher
│   │   ├── tier2_rules.py       # Rule-based fuzzy matcher (RapidFuzz)
│   │   ├── tier3_embeddings.py  # Local FastEmbed vector search
│   │   └── resolver.py          # Orchestrator with curation immunity
│   ├── storage/
│   │   └── minio_client.py      # Local MinIO S3 object storage client
│   ├── admin_api/
│   │   └── router.py            # Back-office admin endpoints
│   ├── consumer_api/
│   │   ├── router.py            # Public search & comparison endpoints
│   │   └── basket_optimizer.py  # Smart grocery basket optimizer
│   └── orchestration/
│       └── scheduler.py         # Background automated pipeline runner
├── tests/
│   ├── test_normalization.py    # Normalization & regex unit tests
│   ├── test_resolution.py       # Barcode & entity resolution unit tests
│   └── test_basket_optimizer.py # Basket optimizer unit tests
├── cli.py                       # Unified CLI tool
├── requirements.txt
└── README.md
```