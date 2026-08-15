-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Enum Types
DO $$ BEGIN
    CREATE TYPE store_chain_enum AS ENUM (
        'SELVER', 'RIMI', 'PRISMA', 'MAXIMA', 'COOP', 'GROSSI', 'LIDL'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE match_tier_enum AS ENUM (
        'EXACT_EAN',
        'RULE_BASED',
        'SEMANTIC_VECTOR',
        'MANUAL_OVERRIDE'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 1. Stores & Store Branches
CREATE TABLE IF NOT EXISTS stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code store_chain_enum NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    base_url VARCHAR(255) NOT NULL,
    has_ecom BOOLEAN DEFAULT TRUE,
    loyalty_program_name VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS store_branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    external_branch_id VARCHAR(100),
    name VARCHAR(150) NOT NULL,
    city VARCHAR(100) NOT NULL DEFAULT 'Tallinn',
    address VARCHAR(255),
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(store_id, external_branch_id)
);

-- 2. Canonical Master Products (Source of Truth)
CREATE TABLE IF NOT EXISTS canonical_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ean VARCHAR(20) UNIQUE,
    name_et VARCHAR(255) NOT NULL,
    name_ru VARCHAR(255),
    name_en VARCHAR(255),
    brand VARCHAR(100),
    category_path VARCHAR(255)[],
    
    unit_amount NUMERIC(10, 3) NOT NULL,
    unit_type VARCHAR(20) NOT NULL,
    package_quantity INT DEFAULT 1,
    
    primary_image_url TEXT,
    custom_image_url TEXT,
    rich_description TEXT,
    
    title_embedding vector(384),
    
    is_manually_curated BOOLEAN NOT NULL DEFAULT FALSE,
    locked_fields JSONB DEFAULT '[]'::jsonb,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_canonical_products_ean ON canonical_products(ean);
CREATE INDEX IF NOT EXISTS idx_canonical_products_brand ON canonical_products(brand);
CREATE INDEX IF NOT EXISTS idx_canonical_products_trgm_name_et ON canonical_products USING gin (name_et gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_canonical_products_embedding_hnsw ON canonical_products USING hnsw (title_embedding vector_cosine_ops);

-- 3. Raw Scraped Offers (Immutable Scraper Output)
CREATE TABLE IF NOT EXISTS raw_scraped_offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    external_id VARCHAR(150) NOT NULL,
    
    raw_title TEXT NOT NULL,
    raw_brand VARCHAR(150),
    raw_category TEXT,
    raw_description TEXT,
    raw_image_url TEXT,
    product_url TEXT NOT NULL,
    raw_ean VARCHAR(50),
    
    raw_price_regular NUMERIC(10, 2) NOT NULL,
    raw_price_discount NUMERIC(10, 2),
    raw_price_loyalty NUMERIC(10, 2),
    raw_unit_price TEXT,
    
    loyalty_card_required VARCHAR(100),
    raw_payload JSONB NOT NULL,
    payload_hash VARCHAR(64) NOT NULL,
    
    is_available BOOLEAN DEFAULT TRUE,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(store_id, external_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_offers_store_external ON raw_scraped_offers(store_id, external_id);
CREATE INDEX IF NOT EXISTS idx_raw_offers_raw_ean ON raw_scraped_offers(raw_ean);
CREATE INDEX IF NOT EXISTS idx_raw_offers_payload_hash ON raw_scraped_offers(payload_hash);

-- 4. Offer to Canonical Mapping
CREATE TABLE IF NOT EXISTS offer_canonical_mapping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_offer_id UUID NOT NULL UNIQUE REFERENCES raw_scraped_offers(id) ON DELETE CASCADE,
    canonical_product_id UUID NOT NULL REFERENCES canonical_products(id) ON DELETE CASCADE,
    
    match_tier match_tier_enum NOT NULL,
    confidence_score NUMERIC(5, 4) NOT NULL,
    
    is_manual_lock BOOLEAN NOT NULL DEFAULT FALSE,
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mapping_canonical_id ON offer_canonical_mapping(canonical_product_id);
CREATE INDEX IF NOT EXISTS idx_mapping_raw_offer_id ON offer_canonical_mapping(raw_offer_id);
CREATE INDEX IF NOT EXISTS idx_mapping_manual_lock ON offer_canonical_mapping(is_manual_lock);

-- 5. Time-Series Price History
CREATE TABLE IF NOT EXISTS price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_offer_id UUID NOT NULL REFERENCES raw_scraped_offers(id) ON DELETE CASCADE,
    canonical_product_id UUID REFERENCES canonical_products(id) ON DELETE SET NULL,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES store_branches(id) ON DELETE SET NULL,
    
    price_regular NUMERIC(10, 2) NOT NULL,
    price_discount NUMERIC(10, 2),
    price_loyalty NUMERIC(10, 2),
    
    effective_unit_price NUMERIC(10, 3) NOT NULL,
    unit_type VARCHAR(20) NOT NULL,
    
    is_on_promotion BOOLEAN GENERATED ALWAYS AS (
        price_discount IS NOT NULL OR price_loyalty IS NOT NULL
    ) STORED,
    discount_percentage NUMERIC(5, 2),
    campaign_name VARCHAR(150),
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_price_history_canonical ON price_history(canonical_product_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_offer ON price_history(raw_offer_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_store ON price_history(store_id, recorded_at DESC);

-- 6. Catalog Audit Logs
CREATE TABLE IF NOT EXISTS catalog_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    changed_by VARCHAR(100) NOT NULL DEFAULT 'admin',
    old_state JSONB,
    new_state JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed Initial Estonian Grocery Stores
INSERT INTO stores (code, name, base_url, has_ecom, loyalty_program_name)
VALUES 
    ('SELVER', 'Selver', 'https://www.selver.ee', TRUE, 'Partnerkaart'),
    ('RIMI', 'Rimi', 'https://www.rimi.ee/epood', TRUE, 'Rimi kaart'),
    ('PRISMA', 'Prisma', 'https://www.prismamarket.ee', TRUE, 'S-Etukortti / Prisma Konto'),
    ('MAXIMA', 'Maxima (Barbora)', 'https://barbora.ee', TRUE, 'Aitäh kaart'),
    ('COOP', 'Coop', 'https://ecoop.ee', TRUE, 'Säästukaart / Säästukaart Pluss'),
    ('GROSSI', 'Grossi Toidukaubad', 'https://www.grossitoidukaubad.ee', FALSE, NULL),
    ('LIDL', 'Lidl', 'https://www.lidl.ee', FALSE, 'Lidl Plus')
ON CONFLICT (code) DO UPDATE 
SET name = EXCLUDED.name,
    base_url = EXCLUDED.base_url,
    loyalty_program_name = EXCLUDED.loyalty_program_name;
