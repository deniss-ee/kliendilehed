import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple
from pydantic import BaseModel, Field
from app.schemas.common import UnitType

class ExtractedUnitInfo(BaseModel):
    raw_match: str
    clean_title: str
    unit_amount: Decimal = Field(..., description="Canonical unit amount (in kg, l, or count)")
    unit_type: UnitType
    package_quantity: int = Field(default=1, description="Number of items in multi-pack")
    original_amount: Decimal
    original_unit: str

    def calculate_unit_price(self, price: Decimal) -> Decimal:
        """Calculates normalized price per kg, per l, or per piece."""
        total_amount = self.unit_amount * Decimal(self.package_quantity)
        if total_amount <= 0:
            return price
        unit_price = price / total_amount
        return unit_price.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

class UnitExtractor:
    """Multilingual unit, volume, weight, and multi-pack extractor."""

    # Percentage ignore pattern (fat %, alcohol %): "2,5%", "82%", "5.2% vol"
    PERCENTAGE_PATTERN = re.compile(r"(?i)\d+(?:[.,]\d+)?\s*%(?:\s*vol)?")

    # Multi-pack pattern: e.g. "6x0.33l", "4 x 100g", "24x0.33L", "3 x 1,5 L", "10x20g"
    MULTIPACK_PATTERN = re.compile(
        r"(?i)(?:^|\s|\()(\d+)\s*(?:x|\*)\s*(\d+(?:[.,]\d+)?)\s*(kg|kilogrammi|кг|g|grammi|г|l|liitrit|lt|л|ml|milliliitrit|мл|cl|dl|tk|tükki|tükk|шт|pcs|pk|pakk)(?=\s|$|[,\.\)\]/])"
    )

    # Single unit pattern: e.g. "500g", "1,5 l", "0.75L", "400 g neto", "10 tk", "1 kg"
    SINGLE_UNIT_PATTERN = re.compile(
        r"(?i)(?:^|\s|\()(\d+(?:[.,]\d+)?)\s*(kg|kilogrammi|кг|g|grammi|г|l|liitrit|lt|л|ml|milliliitrit|мл|cl|dl|tk|tükki|tükk|шт|pcs|pk|pakk|rulli)(?=\s|$|[,\.\)\]/])"
    )

    @classmethod
    def extract(cls, raw_title: str) -> Optional[ExtractedUnitInfo]:
        if not raw_title:
            return None

        # Mask percentages temporarily to avoid false positive unit captures
        masked_title = cls.PERCENTAGE_PATTERN.sub("___PCT___", raw_title)

        # 1. Try multi-pack extraction first
        multi_match = cls.MULTIPACK_PATTERN.search(masked_title)
        if multi_match:
            pkg_qty = int(multi_match.group(1))
            val_str = multi_match.group(2).replace(",", ".")
            unit_str = multi_match.group(3).lower()
            orig_amount = Decimal(val_str)
            raw_match_str = multi_match.group(0).strip(" (")

            canonical_amount, canonical_unit = cls._normalize_unit(orig_amount, unit_str)
            clean_title = cls.clean_title(raw_title, raw_match_str)

            return ExtractedUnitInfo(
                raw_match=raw_match_str,
                clean_title=clean_title,
                unit_amount=canonical_amount,
                unit_type=canonical_unit,
                package_quantity=pkg_qty,
                original_amount=orig_amount,
                original_unit=unit_str,
            )

        # 2. Try single unit extraction (search all matches and pick the most appropriate)
        matches = list(cls.SINGLE_UNIT_PATTERN.finditer(masked_title))
        if matches:
            match = matches[-1]
            val_str = match.group(1).replace(",", ".")
            unit_str = match.group(2).lower()
            orig_amount = Decimal(val_str)
            raw_match_str = match.group(0).strip(" (")

            canonical_amount, canonical_unit = cls._normalize_unit(orig_amount, unit_str)
            clean_title = cls.clean_title(raw_title, raw_match_str)

            return ExtractedUnitInfo(
                raw_match=raw_match_str,
                clean_title=clean_title,
                unit_amount=canonical_amount,
                unit_type=canonical_unit,
                package_quantity=1,
                original_amount=orig_amount,
                original_unit=unit_str,
            )

        # Fallback default: 1 piece
        return ExtractedUnitInfo(
            raw_match="",
            clean_title=raw_title.strip(),
            unit_amount=Decimal("1.000"),
            unit_type=UnitType.PIECE,
            package_quantity=1,
            original_amount=Decimal("1.000"),
            original_unit="tk",
        )

    @staticmethod
    def _normalize_unit(amount: Decimal, unit: str) -> Tuple[Decimal, UnitType]:
        """Converts localized weight/volume unit into canonical SI units (kg, l, piece)."""
        unit = unit.lower()

        # Weights -> Canonical: kg
        if unit in ["kg", "kilogrammi", "кг"]:
            return amount.quantize(Decimal("0.001")), UnitType.KG
        elif unit in ["g", "grammi", "г"]:
            return (amount / Decimal("1000")).quantize(Decimal("0.001")), UnitType.KG

        # Volumes -> Canonical: l
        elif unit in ["l", "liitrit", "lt", "л"]:
            return amount.quantize(Decimal("0.001")), UnitType.L
        elif unit in ["ml", "milliliitrit", "мл"]:
            return (amount / Decimal("1000")).quantize(Decimal("0.001")), UnitType.L
        elif unit == "cl":
            return (amount / Decimal("100")).quantize(Decimal("0.001")), UnitType.L
        elif unit == "dl":
            return (amount / Decimal("10")).quantize(Decimal("0.001")), UnitType.L

        # Counts -> Canonical: piece
        elif unit in ["tk", "tükki", "tükk", "шт", "pcs", "pk", "pakk", "rulli"]:
            return amount.quantize(Decimal("0.001")), UnitType.PIECE

        return amount.quantize(Decimal("0.001")), UnitType.PIECE

    @classmethod
    def clean_title(cls, full_title: str, unit_match_str: str) -> str:
        """Removes the unit token, extra punctuation, and trims whitespace."""
        if not unit_match_str:
            return full_title.strip()

        cleaned = full_title.replace(unit_match_str, " ")
        cleaned = re.sub(r"[,/]\s*$", "", cleaned.strip())
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()
