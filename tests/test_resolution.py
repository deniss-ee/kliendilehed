import pytest
from app.resolution.tier1_barcode import BarcodeMatcher

class TestBarcodeMatcher:
    def test_valid_ean13_checksum(self):
        # Valid standard EAN-13 barcodes
        # 474009811003 -> (10 - 7) % 10 = 3 => 4740098110033
        assert BarcodeMatcher.is_valid_ean("4740098110033") is True
        # 400840040412 -> 4008400404127
        assert BarcodeMatcher.is_valid_ean("4008400404127") is True
        # Coca Cola 5449000000996
        assert BarcodeMatcher.is_valid_ean("5449000000996") is True

    def test_invalid_ean13_checksum(self):
        # Corrupted check digit
        assert BarcodeMatcher.is_valid_ean("4740098110039") is False
        assert BarcodeMatcher.is_valid_ean("123456") is False
        assert BarcodeMatcher.is_valid_ean("notanumber123") is False

    def test_normalize_ean(self):
        assert BarcodeMatcher.normalize_ean(" 4740098110033 ") == "4740098110033"
        assert BarcodeMatcher.normalize_ean("EAN: 4740098110033") == "4740098110033"
        assert BarcodeMatcher.normalize_ean("invalid") is None
