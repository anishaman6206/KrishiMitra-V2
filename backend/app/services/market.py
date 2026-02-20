# backend/app/services/market.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence, Optional
from datetime import datetime

from backend.app.config import get_settings

# --- Data.gov.in constants ---
API_BASE = "https://api.data.gov.in/resource"
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
USER_AGENT = "KrishiMitra/1.0 (+https://krishimitra.example.com)"


@dataclass(frozen=True)
class MarketPrice:
    commodity: str
    unit: str
    price: float
    mandi: str
    district: str
    state: str
    lastUpdated: str  # as returned by API (often DD/MM/YYYY)


def _parse_price(value: str | float | int) -> float:
    try:
        return float(value)
    except Exception:
        return float("nan")


def _parse_date_maybe(s: str) -> Optional[datetime]:
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def normalize_agmarknet_rows(rows: Sequence[Dict]) -> List[MarketPrice]:
    """
    Normalize Agmarknet-like dicts into MarketPrice objects.
    """
    out: List[MarketPrice] = []
    for r in rows:
        def g(*keys, default=""):
            for k in keys:
                if k in r:
                    return r[k]
                for kk in (k, k.lower(), k.upper(), k.title()):
                    if kk in r:
                        return r[kk]
            return default

        commodity = str(g("commodity")).strip() or "Unknown"
        unit = str(g("unit")).strip() or "Quintal"
        price = _parse_price(g("modal_price", "price", default="nan"))
        mandi = str(g("market", "mandi")).strip() or "Unknown"
        district = str(g("district")).strip() or ""
        state = str(g("state")).strip() or ""
        last_updated = str(g("arrival_date", "date", default="")).strip() or ""

        out.append(MarketPrice(
            commodity=commodity,
            unit=unit,
            price=price,
            mandi=mandi,
            district=district,
            state=state,
            lastUpdated=last_updated,
        ))
    # Stable order: most recent first, then commodity, then mandi
    out.sort(
        key=lambda x: (
            (_parse_date_maybe(x.lastUpdated) or datetime.min),
            x.commodity.lower(),
            x.mandi.lower(),
        ),
        reverse=True,
    )
    return out


# ---- Fetcher pattern (now supports optional filters) ----

FetchFunc = Callable[[Optional[str], Optional[str], Optional[str]], Sequence[Dict]]

def fetch_prices(
    *,
    district: Optional[str],
    commodity: Optional[str] = None,
    mandi: Optional[str] = None,
    fetcher: FetchFunc,
) -> List[MarketPrice]:
    """
    High-level fetch with optional filters. Any of the three can be None.
    """
    d = (district or "").strip()
    c = (commodity or "").strip()
    m = (mandi or "").strip()

    raw_rows = fetcher(d if d else None, c if c else None, m if m else None)
    return normalize_agmarknet_rows(raw_rows)


def get_latest_price(
    *,
    district: Optional[str],
    commodity: Optional[str] = None,
    mandi: Optional[str] = None,
    fetcher: FetchFunc,
) -> Optional[MarketPrice]:
    """
    Returns the single most recent MarketPrice matching the filters, or None.
    """
    prices = fetch_prices(district=district, commodity=commodity, mandi=mandi, fetcher=fetcher)
    return prices[0] if prices else None


# ---- Production HTTP fetcher (uses optional filters) ----
def agmarknet_http_fetcher(
    district: Optional[str],
    commodity: Optional[str] = None,
    mandi: Optional[str] = None,
) -> Sequence[Dict]:
    """
    Data.gov.in Agmarknet fetch using resource ID.
    Accepts optional district, commodity, mandi filters.
    """
    import httpx

    s = get_settings()
    url = f"{API_BASE}/{RESOURCE_ID}"
    params: Dict[str, str | int] = {
        "format": "json",
        "limit": 50,
        "api-key": s.data_gov_in_api_key or "",
    }
    # server-side filters — include only those provided
    if district:
        params["filters[district]"] = district
    if commodity:
        params["filters[commodity]"] = commodity
    if mandi:
        # API field name is 'market' for mandi name
        params["filters[market]"] = mandi

    headers = {"User-Agent": USER_AGENT}

    with httpx.Client(timeout=s.http_timeout_seconds, headers=headers) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "records" in data:
            return list(data["records"])
        if isinstance(data, list):
            return data
        return []
