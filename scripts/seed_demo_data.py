import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random

from sqlalchemy import select, delete
from app.db.session import AsyncSessionLocal
from app.db.models import (
    Store,
    RawScrapedOffer,
    CanonicalProduct,
    OfferCanonicalMapping,
    PriceHistory,
)
from app.schemas.common import StoreCode
from app.schemas.ingest import ScrapedRawOfferPayload
from app.scrapers.adapters import get_store_adapter
from app.resolution.resolver import EntityResolver

PRODUCTS_DATA = [
    # --- DAIRY & EGGS ---
    {
        "ean": "4740098110033",
        "brand": "Tere",
        "title": "Tere piim 2,5% 1L kile",
        "img": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "0.89", "disc": "0.75", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "0.85", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "0.89", "disc": None, "loyalty": "0.69", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "0.88", "disc": "0.79", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110040",
        "brand": "Alma",
        "title": "Alma piim 2,5% 1L kile",
        "img": "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "0.89", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "0.82", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "0.89", "disc": "0.79", "loyalty": None, "card": None},
            {"store": StoreCode.RIMI, "reg": "0.89", "disc": None, "loyalty": "0.72", "card": "Rimi kaart"},
        ],
    },
    {
        "ean": "4740098110057",
        "brand": "Farmi",
        "title": "Farmi hapukoor 20% 500g",
        "img": "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "1.59", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "1.45", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "1.55", "disc": "1.29", "loyalty": None, "card": None},
            {"store": StoreCode.RIMI, "reg": "1.49", "disc": None, "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110064",
        "brand": "Alma",
        "title": "Alma Eesti või 82% 200g",
        "img": "https://images.unsplash.com/photo-1589985270748-0c6efb47164b?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "2.19", "disc": "1.89", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "1.89", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "2.25", "disc": None, "loyalty": "1.79", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "2.19", "disc": None, "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110071",
        "brand": "Saaremaa",
        "title": "Saaremaa või 82% 200g",
        "img": "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "2.29", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "1.99", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "2.35", "disc": "1.95", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110088",
        "brand": "Valio",
        "title": "Valio Atleet originaal juust viilutatud 500g",
        "img": "https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "4.89", "disc": "3.89", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "4.19", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "4.99", "disc": None, "loyalty": "3.79", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "4.79", "disc": "3.99", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110095",
        "brand": "Tere",
        "title": "Tere kohuke vanilli kakaoglasuuris 43g",
        "img": "https://images.unsplash.com/photo-1579954115545-a95591f28bfc?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "0.55", "disc": "0.39", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "0.45", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "0.55", "disc": None, "loyalty": "0.38", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "0.52", "disc": "0.42", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110101",
        "brand": "Tallegg",
        "title": "Tallegg vabalt peetavate kanade munad M 10tk",
        "img": "https://images.unsplash.com/photo-1506976785307-8732e854ad03?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "2.49", "disc": "1.99", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "2.19", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "2.55", "disc": None, "loyalty": "1.95", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "2.39", "disc": None, "loyalty": None, "card": None},
        ],
    },

    # --- COFFEE & TEA ---
    {
        "ean": "4740098110118",
        "brand": "Paulig",
        "title": "Paulig Classic kohvioad 1kg",
        "img": "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "14.99", "disc": "10.99", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "12.49", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "13.99", "disc": None, "loyalty": "10.50", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "14.49", "disc": "11.49", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110125",
        "brand": "Paulig",
        "title": "Paulig Presidentti jahvatatud kohv 500g",
        "img": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "6.99", "disc": "5.29", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "5.99", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "6.79", "disc": "5.49", "loyalty": None, "card": None},
            {"store": StoreCode.RIMI, "reg": "6.89", "disc": None, "loyalty": "5.19", "card": "Rimi kaart"},
        ],
    },
    {
        "ean": "4740098110132",
        "brand": "Lavazza",
        "title": "Lavazza Qualita Oro kohvioad 1kg",
        "img": "https://images.unsplash.com/photo-1611854779393-1b2da9d400fe?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "21.99", "disc": "16.99", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "18.49", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.RIMI, "reg": "20.99", "disc": "17.49", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110149",
        "brand": "Löfbergs",
        "title": "Löfbergs Medium Roast jahvatatud kohv 500g",
        "img": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "5.49", "disc": "3.99", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "4.69", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "5.29", "disc": None, "loyalty": "3.89", "card": "Säästukaart"},
        ],
    },
    {
        "ean": "4740098110156",
        "brand": "Dilmah",
        "title": "Dilmah Ceylon Premium must tee 20pk",
        "img": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "2.19", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "1.79", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "2.15", "disc": "1.69", "loyalty": None, "card": None},
            {"store": StoreCode.RIMI, "reg": "1.99", "disc": None, "loyalty": None, "card": None},
        ],
    },

    # --- BAKERY ---
    {
        "ean": "4740098110163",
        "brand": "Leibur",
        "title": "Leibur Rukkipala leib 330g",
        "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "1.29", "disc": "0.99", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "1.15", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "1.29", "disc": None, "loyalty": "0.95", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "1.25", "disc": "1.05", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110170",
        "brand": "Fazer",
        "title": "Fazer Must leib päevalilleseemnetega 280g",
        "img": "https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "1.39", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "1.19", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "1.35", "disc": "1.09", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110187",
        "brand": "Eesti Pagar",
        "title": "Eesti Pagar Kodusai viilutatud 320g",
        "img": "https://images.unsplash.com/photo-1586444248902-2f64eddc13df?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "0.95", "disc": "0.79", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "0.85", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "0.99", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.RIMI, "reg": "0.89", "disc": "0.75", "loyalty": None, "card": None},
        ],
    },

    # --- MEAT & FISH ---
    {
        "ean": "4740098110194",
        "brand": "Rakvere",
        "title": "Rakvere kodune hakkliha 500g",
        "img": "https://images.unsplash.com/photo-1603048588665-791ca8aea617?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "3.49", "disc": "2.69", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "2.99", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "3.59", "disc": None, "loyalty": "2.59", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "3.39", "disc": "2.79", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110200",
        "brand": "Tallegg",
        "title": "Tallegg jahutatud broilerifilee 500g",
        "img": "https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "4.99", "disc": "3.99", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "4.29", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "4.89", "disc": "3.89", "loyalty": None, "card": None},
            {"store": StoreCode.RIMI, "reg": "4.79", "disc": None, "loyalty": "3.75", "card": "Rimi kaart"},
        ],
    },
    {
        "ean": "4740098110217",
        "brand": "Nõo",
        "title": "Nõo Lihavürst E-vaba lastevorst 300g",
        "img": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "2.19", "disc": "1.69", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "1.89", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "2.25", "disc": None, "loyalty": "1.65", "card": "Säästukaart"},
        ],
    },
    {
        "ean": "4740098110224",
        "brand": "M.V.Wool",
        "title": "M.V.Wool jahutatud lõhefilee 1kg",
        "img": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "18.99", "disc": "13.99", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "14.99", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.RIMI, "reg": "17.99", "disc": "14.49", "loyalty": None, "card": None},
        ],
    },

    # --- PRODUCE ---
    {
        "ean": "4740098110231",
        "brand": "Chiquita",
        "title": "Banaan Chiquita 1kg",
        "img": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "1.69", "disc": "1.19", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "1.29", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "1.59", "disc": None, "loyalty": "1.15", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "1.49", "disc": "1.25", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110248",
        "brand": "Eesti Õun",
        "title": "Kodumaine õun Kuldrenett 1kg",
        "img": "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "1.99", "disc": "1.49", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "1.69", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "1.89", "disc": "1.39", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110255",
        "brand": "Luunja",
        "title": "Luunja pikk kurk 1kg",
        "img": "https://images.unsplash.com/photo-1449300079323-02e209d9d3a6?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "2.89", "disc": "2.19", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "2.39", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "2.79", "disc": None, "loyalty": "2.09", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "2.69", "disc": "2.29", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110262",
        "brand": "Eesti Kartul",
        "title": "Pestud kartul Laura 2.5kg",
        "img": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "2.49", "disc": "1.89", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "1.99", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "2.39", "disc": "1.79", "loyalty": None, "card": None},
        ],
    },

    # --- DRINKS ---
    {
        "ean": "4740098110279",
        "brand": "Aura",
        "title": "Aura apelsinimahl 100% 1L",
        "img": "https://images.unsplash.com/photo-1613478223719-2ab802602423?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "1.89", "disc": "1.39", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "1.59", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "1.79", "disc": None, "loyalty": "1.29", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "1.75", "disc": "1.45", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110286",
        "brand": "Coca-Cola",
        "title": "Coca-Cola karastusjook 1.5L",
        "img": "https://images.unsplash.com/photo-1554866585-cd94860890b7?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "2.19", "disc": "1.59", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "1.79", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "2.09", "disc": None, "loyalty": "1.49", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "1.99", "disc": "1.65", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110293",
        "brand": "Värska",
        "title": "Värska Originaal looduslik mineraalvesi 1.5L",
        "img": "https://images.unsplash.com/photo-1548839140-29a749e1bc4e?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "1.19", "disc": "0.89", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "0.99", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "1.15", "disc": "0.85", "loyalty": None, "card": None},
            {"store": StoreCode.RIMI, "reg": "1.09", "disc": None, "loyalty": None, "card": None},
        ],
    },

    # --- SWEETS & SNACKS ---
    {
        "ean": "4740098110309",
        "brand": "Kalev",
        "title": "Kalev Maiuspala pralineekompvekid 175g",
        "img": "https://images.unsplash.com/photo-1548741487-18d16a1a096c?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "4.19", "disc": "2.99", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "3.49", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "3.99", "disc": None, "loyalty": "2.89", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "3.89", "disc": "3.19", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110316",
        "brand": "Kalev",
        "title": "Kalev Anneke piimašokolaad 100g",
        "img": "https://images.unsplash.com/photo-1587132137056-bfbf0166836e?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "1.69", "disc": "1.19", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "1.39", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "1.65", "disc": "1.15", "loyalty": None, "card": None},
            {"store": StoreCode.RIMI, "reg": "1.59", "disc": "1.25", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110323",
        "brand": "Pringles",
        "title": "Pringles Original kartulikrõpsud 165g",
        "img": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "2.99", "disc": "1.99", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "2.49", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "2.89", "disc": None, "loyalty": "1.89", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "2.79", "disc": "2.09", "loyalty": None, "card": None},
        ],
    },

    # --- HOUSEHOLD & CLEANING ---
    {
        "ean": "4740098110330",
        "brand": "Fairy",
        "title": "Fairy Lemon nõudepesuvahend 900ml",
        "img": "https://images.unsplash.com/photo-1585670270677-4560d2b33633?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "3.49", "disc": "2.49", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "2.89", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "3.39", "disc": "2.39", "loyalty": None, "card": None},
            {"store": StoreCode.RIMI, "reg": "3.29", "disc": None, "loyalty": "2.29", "card": "Rimi kaart"},
        ],
    },
    {
        "ean": "4740098110347",
        "brand": "Ariel",
        "title": "Ariel Color pesugeel 1.5L (30 pesukorda)",
        "img": "https://images.unsplash.com/photo-1610557892470-55d9e80c0bce?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "11.99", "disc": "7.99", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "9.49", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "11.49", "disc": None, "loyalty": "7.49", "card": "Säästukaart"},
            {"store": StoreCode.RIMI, "reg": "10.99", "disc": "8.29", "loyalty": None, "card": None},
        ],
    },
    {
        "ean": "4740098110354",
        "brand": "Zewa",
        "title": "Zewa Deluxe 3-kihiline tualettpaber 8 rulli",
        "img": "https://images.unsplash.com/photo-1584556812952-905ffd0c611a?w=500&auto=format&fit=crop&q=80",
        "offers": [
            {"store": StoreCode.SELVER, "reg": "5.49", "disc": "3.69", "loyalty": None, "card": None},
            {"store": StoreCode.PRISMA, "reg": "4.49", "disc": None, "loyalty": None, "card": None},
            {"store": StoreCode.COOP, "reg": "5.29", "disc": "3.49", "loyalty": None, "card": None},
            {"store": StoreCode.RIMI, "reg": "4.99", "disc": "3.79", "loyalty": None, "card": None},
        ],
    },
]

async def seed():
    print("=" * 70)
    print("      SEEDING 30+ CANONICAL GROCERY PRODUCTS & 60-DAY HISTORIES       ")
    print("=" * 70)

    # 1. Ingest raw store offers across adapters
    print(f"\n[1/3] Ingesting {len(PRODUCTS_DATA)} multi-store product bundles...")
    raw_payloads = []
    for p_idx, prod in enumerate(PRODUCTS_DATA):
        for o in prod["offers"]:
            st_code = o["store"]
            payload = ScrapedRawOfferPayload(
                store_code=st_code,
                external_id=f"{st_code.value.lower()}-prod-{p_idx}",
                raw_title=prod["title"],
                product_url=f"https://www.{st_code.value.lower()}.ee/product/{p_idx}",
                raw_image_url=prod["img"],
                raw_price_regular=Decimal(o["reg"]),
                raw_price_discount=Decimal(o["disc"]) if o["disc"] else None,
                raw_price_loyalty=Decimal(o["loyalty"]) if o["loyalty"] else None,
                loyalty_card_required=o["card"],
                raw_ean=prod["ean"],
                raw_brand=prod["brand"],
            )
            raw_payloads.append((st_code, payload))

    # Ingest per store
    by_store = {}
    for st_code, pay in raw_payloads:
        by_store.setdefault(st_code, []).append(pay)

    for st_code, items in by_store.items():
        adapter = get_store_adapter(st_code)
        await adapter.ingest_batch(items)
        await adapter.close()

    print(f"[OK] Saved {len(raw_payloads)} store offers across Selver, Prisma, Coop, Rimi.")

    # 2. Run 3-Tier Resolution
    print("\n[2/3] Resolving and linking canonical master catalog...")
    async with AsyncSessionLocal() as session:
        stmt = select(RawScrapedOffer)
        raw_offers = list((await session.execute(stmt)).scalars().all())

        resolved_count = 0
        canonical_map = {}
        for r_off in raw_offers:
            res = await EntityResolver.resolve_offer(session, r_off)
            resolved_count += 1
            canonical_map[r_off.id] = res.canonical_product_id

        await session.commit()
        print(f"[OK] Successfully linked into Master Canonical Catalog.")

        # 3. Generate 60 Days of realistic Time-Series Price History
        print("\n[3/3] Generating 60-day historical price points for charts...")
        now = datetime.now(timezone.utc)
        history_records = []

        for r_off in raw_offers:
            cid = canonical_map.get(r_off.id)
            if not cid:
                continue

            base_reg = float(r_off.raw_price_regular)
            has_disc = bool(r_off.raw_price_discount or r_off.raw_price_loyalty)

            # Generate snapshots every 5 days for the past 60 days
            for days_ago in range(60, 0, -5):
                snap_time = now - timedelta(days=days_ago)

                # Simulate promotional campaign windows (every ~20 days)
                is_promo_window = (days_ago % 25) < 8
                if is_promo_window:
                    disc_price = round(base_reg * random.uniform(0.72, 0.85), 2)
                    reg_price = base_reg
                else:
                    disc_price = None
                    reg_price = round(base_reg * random.uniform(0.98, 1.02), 2)

                entry = PriceHistory(
                    id=str(uuid.uuid4()),
                    raw_offer_id=str(r_off.id),
                    canonical_product_id=str(cid),
                    store_id=str(r_off.store_id),
                    price_regular=Decimal(str(reg_price)),
                    price_discount=Decimal(str(disc_price)) if disc_price else None,
                    price_loyalty=None,
                    effective_unit_price=Decimal(str(disc_price or reg_price)),
                    unit_type="unit",
                    recorded_at=snap_time,
                )
                history_records.append(entry)

        session.add_all(history_records)
        await session.commit()
        print(f"[OK] Created {len(history_records)} historical price logs across all stores.")

    print("\n" + "=" * 70)
    print("               DATABASE SEEDING COMPLETE!               ")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(seed())
