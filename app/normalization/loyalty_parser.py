import re
from decimal import Decimal
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class ParsedLoyaltyCondition(BaseModel):
    loyalty_program: Optional[str] = None
    is_multi_buy: bool = False
    required_quantity: int = 1
    bundle_price: Optional[Decimal] = None
    unit_discount_price: Optional[Decimal] = None
    campaign_name: Optional[str] = None
    valid_until_raw: Optional[str] = None

class LoyaltyParser:
    """Parses loyalty card mechanics and multi-buy conditions from promotional text."""

    LOYALTY_CARD_KEYWORDS = [
        (r"(?i)\bs[aä][aä]stu(?:kaart|kaardi)?", "Säästukaart"),
        (r"(?i)\bpartner(?:kaart|kaardi)?", "Partnerkaart"),
        (r"(?i)\brimi\s*(?:kaart|kaardi)?", "Rimi kaart"),
        (r"(?i)\bait[aä]h\s*(?:kaart|kaardi)?", "Aitäh kaart"),
        (r"(?i)\blidl\s*plus", "Lidl Plus"),
    ]

    # "2 tk = 2.50 €" or "3 tk 4.00"
    BUNDLE_PATTERN = re.compile(
        r"(?i)\b(\d+)\s*(?:tk|tükki|pakk|pk)\s*(?:=|on|\:)?\s*(\d+(?:[.,]\d+)?)\s*(?:€|eur)?\b"
    )

    # "osta 2 või enam", "alates 2 tk", "min. 3 tk"
    MIN_QTY_PATTERN = re.compile(
        r"(?i)(?:osta|alates|min\.?)\s*(\d+)\s*(?:tk|tükki|või enam|ja rohkem)"
    )

    # "3=2", "2=1", "1+1"
    X_FOR_Y_PATTERN = re.compile(r"\b(\d+)\s*(?:=|\+)\s*(\d+)\b")

    @classmethod
    def parse(
        cls,
        text: str,
        known_loyalty: Optional[str] = None,
        discount_price: Optional[Decimal] = None,
    ) -> ParsedLoyaltyCondition:
        if not text:
            return ParsedLoyaltyCondition(
                loyalty_program=known_loyalty,
                unit_discount_price=discount_price,
            )

        loyalty_prog = known_loyalty

        # 1. Detect loyalty card name (handles Estonian inflections like Säästukaardiga, Partnerkaardile)
        if not loyalty_prog:
            for pattern, card_name in cls.LOYALTY_CARD_KEYWORDS:
                if re.search(pattern, text):
                    loyalty_prog = card_name
                    break

        # 2. Check for bundle price ("2 tk = 3.00 €")
        bundle_match = cls.BUNDLE_PATTERN.search(text)
        if bundle_match:
            qty = int(bundle_match.group(1))
            total_price = Decimal(bundle_match.group(2).replace(",", "."))
            unit_price = (total_price / Decimal(qty)).quantize(Decimal("0.01"))
            return ParsedLoyaltyCondition(
                loyalty_program=loyalty_prog,
                is_multi_buy=True,
                required_quantity=qty,
                bundle_price=total_price,
                unit_discount_price=unit_price,
                campaign_name=text.strip(),
            )

        # 3. Check for minimum quantity threshold ("Alates 2 tk")
        min_qty_match = cls.MIN_QTY_PATTERN.search(text)
        if min_qty_match:
            qty = int(min_qty_match.group(1))
            return ParsedLoyaltyCondition(
                loyalty_program=loyalty_prog,
                is_multi_buy=True,
                required_quantity=qty,
                unit_discount_price=discount_price,
                campaign_name=text.strip(),
            )

        # 4. Check for X for Y ("1+1" or "3=2")
        x_y_match = cls.X_FOR_Y_PATTERN.search(text)
        if x_y_match:
            buy_qty = int(x_y_match.group(1))
            pay_qty = int(x_y_match.group(2))
            return ParsedLoyaltyCondition(
                loyalty_program=loyalty_prog,
                is_multi_buy=True,
                required_quantity=buy_qty + (1 if "+" in text else 0),
                unit_discount_price=discount_price,
                campaign_name=f"{buy_qty}={pay_qty}" if "=" in text else f"{buy_qty}+{pay_qty}",
            )

        return ParsedLoyaltyCondition(
            loyalty_program=loyalty_prog,
            is_multi_buy=False,
            required_quantity=1,
            unit_discount_price=discount_price,
            campaign_name=text.strip() if len(text) < 50 else None,
        )
