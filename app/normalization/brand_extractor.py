import re
from typing import Optional, List

class BrandExtractor:
    """Extracts and canonicalizes Estonian and international FMCG brands."""

    KNOWN_BRANDS = [
        # Dairy & Eggs
        "Tere", "Farmi", "Alma", "Valio", "Saaremaa", "Nopri", "Pajumäe", "Epiim", "Džiugas", "Philadelphia", "Zott",
        # Meat & Fish
        "Rakvere", "Maks & Moorits", "Nõo", "Rannarootsi", "Vastse-Kuuste", "Karni", "Linnamäe", "M.V.Wool", "Briis",
        # Bakery & Grains
        "Leibur", "Eesti Pagar", "Fazer", "Tartu Mill", "Veski Mati", "Vilma", "Hagar",
        # Preserves & Sauces
        "Salvest", "Põltsamaa", "Felix", "Heinz", "Hellmann's", "Santa Maria", "Maggi", "Knorr",
        # Sweets & Snacks
        "Kalev", "Laima", "Pergale", "Milka", "Taffel", "Lay's", "Estrella", "Pringles", "Paulig", "Lavazza", "Jacobs",
        # Drinks & Beer
        "A. Le Coq", "Saku", "Värska Originaal", "Värska", "Aura", "Põltsamaa", "Limonaad", "Coca-Cola", "Pepsi", "Red Bull",
        # Household & Hygiene
        "Mayeri", "Fairy", "Persil", "Ariel", "Domestos", "Gillette", "Colgate", "Head & Shoulders",
    ]

    @classmethod
    def extract_brand(cls, title: str, fallback_brand: Optional[str] = None) -> Optional[str]:
        if fallback_brand and fallback_brand.strip():
            # Check if fallback brand matches a canonical brand casing
            for brand in cls.KNOWN_BRANDS:
                if fallback_brand.lower().strip() == brand.lower():
                    return brand
            return fallback_brand.strip().title()

        if not title:
            return None

        # Search for known brand in title
        for brand in cls.KNOWN_BRANDS:
            # Word boundary regex
            pattern = rf"(?i)\b{re.escape(brand)}\b"
            if re.search(pattern, title):
                return brand

        return None
