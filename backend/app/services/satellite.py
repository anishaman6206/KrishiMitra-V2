# backend/app/services/satellite.py
from __future__ import annotations
import os, asyncio, datetime as dt
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from sentinelhub import BBox, CRS, SentinelHubRequest, DataCollection, MimeType, SHConfig
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

# .env should hold SH_CLIENT_ID / SH_CLIENT_SECRET
SH_CLIENT_ID = os.getenv("SH_CLIENT_ID")
SH_CLIENT_SECRET = os.getenv("SH_CLIENT_SECRET")

EVALSCRIPT_NDVI = """
//VERSION=3
function setup(){return{input:["B04","B08","SCL"],output:{bands:1,sampleType:"FLOAT32"}}}
function evaluatePixel(s){if([0,3,8,9,10,11].indexOf(s.SCL)!==-1)return[NaN];return[(s.B08-s.B04)/(s.B08+s.B04+1e-6)];}
"""
EVALSCRIPT_NDMI = """
//VERSION=3
function setup(){return{input:["B08","B11","SCL"],output:{bands:1,sampleType:"FLOAT32"}}}
function evaluatePixel(s){if([0,3,8,9,10,11].indexOf(s.SCL)!==-1)return[NaN];return[(s.B08-s.B11)/(s.B08+s.B11+1e-6)];}
"""
EVALSCRIPT_NDWI = """
//VERSION=3
function setup(){return{input:["B03","B08","SCL"],output:{bands:1,sampleType:"FLOAT32"}}}
function evaluatePixel(s){if([0,3,8,9,10,11].indexOf(s.SCL)!==-1)return[NaN];return[(s.B03-s.B08)/(s.B03+s.B08+1e-6)];}
"""
EVALSCRIPT_LAI = """
//VERSION=3
function setup(){return{input:["B04","B08","SCL"],output:{bands:1,sampleType:"FLOAT32"}}}
function evaluatePixel(s){if([0,3,8,9,10,11].indexOf(s.SCL)!==-1)return[NaN];let ndvi=(s.B08-s.B04)/(s.B08+s.B04+1e-6);let lai=0.57*Math.exp(2.33*ndvi);return[lai];}
"""

AVAILABLE = {"ndvi": EVALSCRIPT_NDVI, "ndmi": EVALSCRIPT_NDMI, "ndwi": EVALSCRIPT_NDWI, "lai": EVALSCRIPT_LAI}

def _cfg() -> SHConfig:
    if not SH_CLIENT_ID or not SH_CLIENT_SECRET:
        raise RuntimeError("SH_CLIENT_ID or SH_CLIENT_SECRET not set")
    c = SHConfig()
    c.sh_client_id = SH_CLIENT_ID
    c.sh_client_secret = SH_CLIENT_SECRET
    c.save()
    return c

def _bbox(lat: float, lon: float, size_m: int) -> BBox:
    m_per_deg = 111_320.0
    lat_span = size_m / m_per_deg
    lon_span = size_m / (m_per_deg * np.cos(np.radians(lat)))
    min_lat, max_lat = lat - lat_span/2, lat + lat_span/2
    min_lon, max_lon = lon - lon_span/2, lon + lon_span/2
    return BBox(bbox=[min_lon, min_lat, max_lon, max_lat], crs=CRS.WGS84)

async def _get_products(lat: float, lon: float, products: List[str],
                        daterange: Tuple[str, str], aoi_m: int, res: int) -> Dict[str, Dict[str, Any]]:
    cfg = _cfg()
    bb = _bbox(lat, lon, aoi_m)
    w = max(8, int(aoi_m / res)); h = max(8, int(aoi_m / res))
    reqs = []
    for name in products:
        script = AVAILABLE.get(name)
        if script:
            reqs.append((name, SentinelHubRequest(
                evalscript=script,
                input_data=[SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=daterange,
                    mosaicking_order="leastCC"
                )],
                responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
                bbox=bb, size=(w, h), config=cfg
            )))
    if not reqs:
        return {}
    loop = asyncio.get_running_loop()
    datas = await loop.run_in_executor(None, lambda: [r.get_data() for _, r in reqs])

    out: Dict[str, Dict[str, Any]] = {}
    for (name, _), data in zip(reqs, datas):
        if not data: 
            continue
        arr = np.asarray(data[0], dtype="float32")
        finite = np.isfinite(arr)
        cov = float(finite.mean() * 100.0) if arr.size else 0.0
        vals = arr[finite]
        stats = {
            "mean": float(np.nanmean(vals)) if vals.size else None,
            "std_dev": float(np.nanstd(vals)) if vals.size else None,
            "min": float(np.nanmin(vals)) if vals.size else None,
            "max": float(np.nanmax(vals)) if vals.size else None,
        }
        out[name] = {"stats": stats, "coverage_pct": round(cov, 2)}
    return out

async def sentinel_summary(
    lat: float, lon: float, *, aoi_m: int = 300, days: int = 45, res: int = 10,
    autogrow: bool = True, steps: Tuple[int, ...] = (300, 1000, 2000, 3000),
    min_cov_pct: float = 10.0, low_cov_flag: int = 50
) -> Dict[str, Any]:
    end = dt.date.today(); start = end - dt.timedelta(days=days)
    daterange = (start.isoformat(), end.isoformat())

    tried: List[Dict[str, Any]] = []
    chosen: Optional[Dict[str, Any]] = None
    used: Optional[int] = None
    last: Optional[Dict[str, Any]] = None

    for size in (steps if autogrow else (aoi_m,)):
        data = await _get_products(lat, lon, ["ndvi","ndmi","ndwi","lai"], daterange, size, res)
        last = data
        cov = {k: (v or {}).get("coverage_pct", 0.0) for k, v in (data or {}).items()}
        ok = any(isinstance(cov.get(k), (int,float)) and cov.get(k, 0.0) >= min_cov_pct for k in ("ndvi","ndmi","ndwi","lai"))
        tried.append({"aoi_m": size, "coverage_pct": cov})
        if ok:
            chosen, used = data, size
            break

    chosen = chosen or last or {}
    used = used or (steps[-1])

    def _stat(name: str, key: str):
        d = chosen.get(name) or {}; s = d.get("stats") or {}; return s.get(key)

    cov = {k: (v or {}).get("coverage_pct", 0.0) for k, v in (chosen or {}).items()}
    good = [c for c in cov.values() if isinstance(c, (int,float)) and c > 0]
    avg_cov = float(np.mean(good)) if good else 0.0

    return {
        "ndvi_mean": _stat("ndvi","mean"),
        "ndmi_mean": _stat("ndmi","mean"),
        "ndwi_mean": _stat("ndwi","mean"),
        "lai_mean":  _stat("lai","mean"),
        "coverage_pct": cov,
        "aoi_m": used,
        "window_days": days,
        "attempts": tried,
        "reliability": "low" if avg_cov < low_cov_flag else "high",
    }
