import re
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import CanonicalProduct
from app.schemas.common import MatchTier

class BarcodeMatcher:
    """Tier 1: Deterministic EAN-8 / EAN-13 / GTIN Barcode Matcher."""

    @staticmethod
    def is_valid_ean(ean: str) -> bool:
        """Validates EAN-8, EAN-13, and GTIN-14 check digit."""
        if not ean or not ean.isdigit():
            return False

        if len(ean) not in [8, 12, 13, 14]:
            return False

        # Compute checksum
        digits = [int(d) for d in ean]
        check_digit = digits[-1]
        sum_digits = 0
        reversed_digits = digits[:-1][::-1]

        for i, digit in enumerate(reversed_digits):
            weight = 3 if (i % 2 == 0) else 1
            sum_digits += digit * weight

        calc_check_digit = (10 - (sum_digits % 10)) % 10
        return check_digit == calc_check_digit

    @classmethod
    def normalize_ean(cls, raw_ean: Optional[str]) -> Optional[str]:
        if not raw_ean:
            return None
        # Remove non-digits
        clean = re.sub(r"\D", "", raw_ean)
        if cls.is_valid_ean(clean):
            return clean
        return None

    @classmethod
    async def match(
        cls,
        session: AsyncSession,
        raw_ean: Optional[str],
    ) -> Optional[CanonicalProduct]:
        valid_ean = cls.normalize_ean(raw_ean)
        if not valid_ean:
            return None

        stmt = select(CanonicalProduct).where(CanonicalProduct.ean == valid_ean)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
