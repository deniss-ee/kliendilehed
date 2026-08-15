from app.schemas.common import StoreCode
from app.scrapers.base import BaseStoreScraper
from app.scrapers.adapters.selver import SelverAdapter
from app.scrapers.adapters.prisma import PrismaAdapter
from app.scrapers.adapters.coop import CoopAdapter
from app.scrapers.adapters.rimi import RimiAdapter
from typing import Dict, Type

ADAPTER_REGISTRY: Dict[StoreCode, Type[BaseStoreScraper]] = {
    StoreCode.SELVER: SelverAdapter,
    StoreCode.PRISMA: PrismaAdapter,
    StoreCode.COOP: CoopAdapter,
    StoreCode.RIMI: RimiAdapter,
}

def get_store_adapter(store_code: StoreCode) -> BaseStoreScraper:
    adapter_cls = ADAPTER_REGISTRY.get(store_code)
    if not adapter_cls:
        raise ValueError(f"No scraper adapter registered for store code: {store_code}")
    return adapter_cls()

__all__ = [
    "ADAPTER_REGISTRY",
    "get_store_adapter",
    "SelverAdapter",
    "PrismaAdapter",
    "CoopAdapter",
    "RimiAdapter",
]
