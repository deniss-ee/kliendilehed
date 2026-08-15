from enum import Enum

class StoreCode(str, Enum):
    SELVER = "SELVER"
    RIMI = "RIMI"
    PRISMA = "PRISMA"
    MAXIMA = "MAXIMA"
    COOP = "COOP"
    GROSSI = "GROSSI"
    LIDL = "LIDL"

class UnitType(str, Enum):
    KG = "kg"
    G = "g"
    L = "l"
    ML = "ml"
    PIECE = "piece"

class MatchTier(str, Enum):
    EXACT_EAN = "EXACT_EAN"
    RULE_BASED = "RULE_BASED"
    SEMANTIC_VECTOR = "SEMANTIC_VECTOR"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
