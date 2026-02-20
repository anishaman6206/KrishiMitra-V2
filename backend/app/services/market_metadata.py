# backend/app/services/market_metadata.py
from __future__ import annotations
import json
from pathlib import Path
from functools import lru_cache
from typing import Dict, List, Optional

ENCODER_PATH = Path("backend") / "models" / "pricing_global" / "encoder.json"

@lru_cache(maxsize=1)
def _load_encoder() -> Dict[str, Dict[str, int]]:
    data = json.loads(ENCODER_PATH.read_text(encoding="utf-8"))
    # expected keys: commodity, district, market, variety, grade (name->int)
    return {k: dict(v) for k, v in data.items()}

def list_commodities() -> List[str]:
    enc = _load_encoder()
    return sorted(enc.get("commodity", {}).keys())

def list_districts() -> List[str]:
    enc = _load_encoder()
    return sorted(enc.get("district", {}).keys())

def list_markets() -> List[str]:
    enc = _load_encoder()
    return sorted(enc.get("market", {}).keys())

def list_varieties() -> List[str]:
    enc = _load_encoder()
    return sorted(enc.get("variety", {}).keys())

def list_grades() -> List[str]:
    enc = _load_encoder()
    return sorted(enc.get("grade", {}).keys())

def is_supported(
    *, commodity: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
    variety: Optional[str] = None,
    grade: Optional[str] = None,
) -> bool:
    enc = _load_encoder()
    def ok(space, val): return (val is None) or (val in enc.get(space, {}))
    return all([
        ok("commodity", commodity),
        ok("district", district),
        ok("market", market),
        ok("variety", variety),
        ok("grade", grade),
    ])

print(f"🔢 Market metadata loaded: {len(list_commodities())} commodities, {len(list_districts())} districts, {len(list_markets())} markets, {len(list_varieties())} varieties, {len(list_grades())} grades")
