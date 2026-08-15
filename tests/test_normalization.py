import pytest
from decimal import Decimal
from app.schemas.common import UnitType
from app.normalization.unit_extractor import UnitExtractor
from app.normalization.loyalty_parser import LoyaltyParser
from app.normalization.brand_extractor import BrandExtractor

class TestUnitExtractor:
    @pytest.mark.parametrize(
        "title, expected_amount, expected_unit, expected_qty",
        [
            # Estonian standard formats
            ("Tere piim 2,5% 1L", Decimal("1.000"), UnitType.L, 1),
            ("Alma täispiim 3.8-4.2% 1,5 l", Decimal("1.500"), UnitType.L, 1),
            ("Farmi hapukoor 20% 500g", Decimal("0.500"), UnitType.KG, 1),
            ("Alma või 82% 200 g", Decimal("0.200"), UnitType.KG, 1),
            ("Rakvere Lastevorst 300g", Decimal("0.300"), UnitType.KG, 1),
            ("Kollane banaan 1kg", Decimal("1.000"), UnitType.KG, 1),
            ("Värska Originaal mineraalvesi 1.5L", Decimal("1.500"), UnitType.L, 1),
            ("Hellmann's Original majonees 405ml", Decimal("0.405"), UnitType.L, 1),
            ("Santa Maria jahvatatud must pipar 40g", Decimal("0.040"), UnitType.KG, 1),
            ("Eesti Pagar Rukkipala 6 tk", Decimal("6.000"), UnitType.PIECE, 1),
            
            # Multi-pack formats
            ("Coca-Cola karastusjook 6x0.33l", Decimal("0.330"), UnitType.L, 6),
            ("A. Le Coq Premium õlu 24x0.33L", Decimal("0.330"), UnitType.L, 24),
            ("Paulig Presidentti kohvioad 4 x 500g", Decimal("0.500"), UnitType.KG, 4),
            ("Aura apelsinimahl 3x1.5L", Decimal("1.500"), UnitType.L, 3),
            ("Maggi puljongikuubikud 10x10g", Decimal("0.010"), UnitType.KG, 10),
            
            # Russian formats
            ("Молоко Tere 2.5% 1л", Decimal("1.000"), UnitType.L, 1),
            ("Сметана Farmi 20% 500г", Decimal("0.500"), UnitType.KG, 1),
            ("Сливочное масло Alma 200 г", Decimal("0.200"), UnitType.KG, 1),
            ("Яйца куриные M 10 шт", Decimal("10.000"), UnitType.PIECE, 1),
            
            # Complex title with percentage & units
            ("Saaremaa juust 26% viilutatud 500g", Decimal("0.500"), UnitType.KG, 1),
            ("Saku Originaal hele õlu 4.6% 0.5L purk", Decimal("0.500"), UnitType.L, 1),
        ],
    )
    def test_unit_extraction_cases(self, title, expected_amount, expected_unit, expected_qty):
        info = UnitExtractor.extract(title)
        assert info is not None
        assert info.unit_amount == expected_amount
        assert info.unit_type == expected_unit
        assert info.package_quantity == expected_qty

    def test_unit_price_calculation(self):
        # 500g for 1.49 EUR -> 2.98 EUR/kg
        info = UnitExtractor.extract("Farmi hapukoor 20% 500g")
        unit_price = info.calculate_unit_price(Decimal("1.49"))
        assert unit_price == Decimal("2.980")

        # 6x0.33L (total 1.98L) for 4.99 EUR -> 2.520 EUR/L
        info = UnitExtractor.extract("Coca-Cola 6x0.33l")
        unit_price = info.calculate_unit_price(Decimal("4.99"))
        assert unit_price == Decimal("2.520")

class TestLoyaltyParser:
    def test_bundle_discount_parsing(self):
        condition = LoyaltyParser.parse("Osta 2 tk = 2.50 €")
        assert condition.is_multi_buy is True
        assert condition.required_quantity == 2
        assert condition.bundle_price == Decimal("2.50")
        assert condition.unit_discount_price == Decimal("1.25")

    def test_saastukaart_detection(self):
        condition = LoyaltyParser.parse("Soodushind Säästukaardiga", discount_price=Decimal("1.19"))
        assert condition.loyalty_program == "Säästukaart"
        assert condition.unit_discount_price == Decimal("1.19")

    def test_partnerkaart_detection(self):
        condition = LoyaltyParser.parse("Partnerkaardiga -25%", discount_price=Decimal("2.99"))
        assert condition.loyalty_program == "Partnerkaart"
        assert condition.unit_discount_price == Decimal("2.99")

class TestBrandExtractor:
    def test_known_brand_extraction(self):
        assert BrandExtractor.extract_brand("Tere piim 2.5% 1L") == "Tere"
        assert BrandExtractor.extract_brand("Farmi kodujuust hapukoorega 330g") == "Farmi"
        assert BrandExtractor.extract_brand("Alma või 82% 200g") == "Alma"
        assert BrandExtractor.extract_brand("Rakvere Lastevorst 300g") == "Rakvere"
        assert BrandExtractor.extract_brand("Fazer Geisha šokolaad 150g") == "Fazer"
        assert BrandExtractor.extract_brand("Värska Originaal mineraalvesi 1.5L") == "Värska Originaal"
