from __future__ import annotations

import httpx
import json
import math
from dataclasses import dataclass, asdict
from typing import Callable, Dict, List, Optional, Tuple
# add at top with other imports
import asyncio
from functools import lru_cache


# -------- Data classes --------
@dataclass(frozen=True)
class SoilLayer:
    depth_cm_from: int
    depth_cm_to: int
    ph_h2o: float
    soc_g_per_kg: float
    nitrogen_g_per_kg: float
    # texture
    clay_g_per_kg: float   # g/kg
    sand_g_per_kg: float   # g/kg
    silt_g_per_kg: float   # g/kg

@dataclass(frozen=True)
class SoilBundle:
    latitude: float
    longitude: float
    layers: List[SoilLayer]

    @property
    def topsoil(self) -> Optional[SoilLayer]:
        return self.layers[0] if self.layers else None

# --- utility: snap to a regular grid (~250m) so we hit cell centers quickly
def _snap_to_grid(lat: float, lon: float, step_deg: float = 0.0025) -> tuple[float, float]:
    return (round(lat / step_deg) * step_deg, round(lon / step_deg) * step_deg)

# tighten request timeout a bit (SoilGrids is usually quick)
_PER_REQ_TIMEOUT = 30.0  # seconds

# -------- Normalization --------
def _as_float(x, default=float("nan")) -> float:
    try:
        return float(x)
    except Exception:
        return default

def _parse_depth_label(label: str) -> tuple[int, int]:
    s = label.lower().replace("cm", "").strip()
    parts = s.split("-")
    if len(parts) == 2:
        try:
            return int(parts[0]), int(parts[1])
        except Exception:
            return 0, 0
    return 0, 0

def normalize_soilgrids(payload: Dict) -> SoilBundle:
    geometry = payload.get("geometry", {})
    coordinates = geometry.get("coordinates", [float("nan"), float("nan")])
    lon = _as_float(coordinates[0])
    lat = _as_float(coordinates[1])

    props = (payload.get("properties") or {}).get("layers") or []

    by_prop: Dict[str, Dict[str, float]] = {
        "phh2o": {}, "soc": {}, "nitrogen": {},
        "clay": {}, "sand": {}, "silt": {}
    }

    for layer in props:
        name = (layer.get("name") or "").lower()
        if name not in by_prop:
            continue

        unit_measure = layer.get("unit_measure", {})
        d_factor = unit_measure.get("d_factor", 1.0) or 1.0

        for d in layer.get("depths") or []:
            label = str(d.get("label") or "").strip()
            values = d.get("values") or {}
            mean = values.get("mean")

            if mean is not None:
                by_prop[name][label] = _as_float(mean) / d_factor
            else:
                by_prop[name][label] = float("nan")

    labels = set()
    for m in by_prop.values():
        labels.update(m.keys())

    def _sort_key(lbl: str):
        a, b = _parse_depth_label(lbl)
        return (a, b, lbl)

    ordered = sorted(labels, key=_sort_key)

    layers: List[SoilLayer] = []
    for lbl in ordered:
        d_from, d_to = _parse_depth_label(lbl)
        layers.append(
            SoilLayer(
                depth_cm_from=d_from,
                depth_cm_to=d_to,
                ph_h2o=_as_float(by_prop["phh2o"].get(lbl)),
                soc_g_per_kg=_as_float(by_prop["soc"].get(lbl)),
                nitrogen_g_per_kg=_as_float(by_prop["nitrogen"].get(lbl)),
                clay_g_per_kg=_as_float(by_prop["clay"].get(lbl)),
                sand_g_per_kg=_as_float(by_prop["sand"].get(lbl)),
                silt_g_per_kg=_as_float(by_prop["silt"].get(lbl)),
            )
        )

    return SoilBundle(latitude=lat, longitude=lon, layers=layers)


# -------- HTTP fetch --------
SOILGRIDS_QUERY_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

def soilgrids_http_fetcher(lat: float, lon: float) -> dict:
    params = {
        "lon": lon,
        "lat": lat,
        "property": ["phh2o", "soc", "nitrogen", "clay", "sand", "silt"],
        "depth": "0-5cm",
        "value": "mean",
    }
    headers = {"Accept": "application/json"}
    # lower timeout than before
    with httpx.Client(timeout=_PER_REQ_TIMEOUT, headers=headers) as client:
        r = client.get(SOILGRIDS_QUERY_URL, params=params)
        r.raise_for_status()
        try:
            return r.json()
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Expected JSON from SoilGrids, got non-JSON at {SOILGRIDS_QUERY_URL}") from e


# -------- Neighbor search to avoid nulls --------
def _has_useful_layers(data: dict) -> bool:
    try:
        layers = ((data.get("properties") or {}).get("layers")) or []
        for layer in layers:
            for d in (layer.get("depths") or []):
                values = d.get("values") or {}
                mean = values.get("mean", None)
                if isinstance(mean, (int, float)) and not (isinstance(mean, float) and math.isnan(mean)):
                    return True
        return False
    except Exception:
        return False

def _haversine_m(lat1, lon1, lat2, lon2) -> float:
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))


# small cache to save repeat calls when user pans around same area
@lru_cache(maxsize=256)
def _cached_fetch(lat: float, lon: float) -> dict:
    return soilgrids_http_fetcher(lat, lon)

async def _fetch_async(client: httpx.AsyncClient, lat: float, lon: float) -> tuple[dict | None, float, float]:
    try:
        params = {
            "lon": lon,
            "lat": lat,
            "property": ["phh2o", "soc", "nitrogen", "clay", "sand", "silt"],
            "depth": "0-5cm",
            "value": "mean",
        }
        r = await client.get(SOILGRIDS_QUERY_URL, params=params)
        r.raise_for_status()
        data = r.json()
        return (data if _has_useful_layers(data) else None, lat, lon)
    except Exception:
        return (None, lat, lon)

async def _probe_neighbors_parallel(lat: float, lon: float, *, step_deg: float, rings: int, max_concurrency: int = 8):
    # build the perimeter coords for rings 1..N, snapped to avoid redundant points
    coords: list[tuple[float, float]] = []
    seen = set()
    for k in range(1, rings + 1):
        for dy in range(-k, k + 1):
            for dx in range(-k, k + 1):
                if max(abs(dx), abs(dy)) != k:
                    continue
                lat2 = lat + dy * step_deg
                lon2 = lon + dx * step_deg
                lat2, lon2 = _snap_to_grid(lat2, lon2, step_deg=step_deg)  # snap each probe
                key = (round(lat2, 6), round(lon2, 6))
                if key not in seen:
                    seen.add(key)
                    coords.append((lat2, lon2))

    # async client with concurrency cap
    sem = asyncio.Semaphore(max_concurrency)
    async with httpx.AsyncClient(timeout=_PER_REQ_TIMEOUT, headers={"Accept": "application/json"}) as client:
        async def task(latx: float, lonx: float):
            async with sem:
                return await _fetch_async(client, latx, lonx)

        tasks = [asyncio.create_task(task(a, b)) for (a, b) in coords]
        # as soon as one returns useful, cancel the rest
        try:
            for coro in asyncio.as_completed(tasks):
                data, la, lo = await coro
                if data is not None:
                    # cancel outstanding tasks
                    for t in tasks:
                        if not t.done():
                            t.cancel()
                    return data, la, lo
        finally:
            # ensure all tasks complete/cancel to avoid warnings
            await asyncio.gather(*tasks, return_exceptions=True)

    return None, None, None

def soilgrids_try_neighbors(
    lat: float,
    lon: float,
    *,
    snap_step_deg: float = 0.0025,  # ~250 m grid
    ring_step_deg: float = 0.0015,  # ~165 m radial step
    rings: int = 4,                 # up to ~660 m radius
) -> Tuple[dict, float, float, float]:
    """
    Fast strategy:
      1) exact point
      2) snapped-to-grid point (single call)
      3) parallel ring probe (limited concurrency) until first useful cell
    """
    # 1) exact
    try:
        j = _cached_fetch(lat, lon)
        if _has_useful_layers(j):
            return j, lat, lon, 0.0
    except Exception:
        pass

    # 2) single snapped probe (often lands on a populated cell)
    s_lat, s_lon = _snap_to_grid(lat, lon, step_deg=snap_step_deg)
    if (s_lat, s_lon) != (lat, lon):
        try:
            j = _cached_fetch(s_lat, s_lon)
            if _has_useful_layers(j):
                dist = _haversine_m(lat, lon, s_lat, s_lon)
                return j, s_lat, s_lon, dist
        except Exception:
            pass

    # 3) parallel neighbor ring (fast exit on first success)
    data, la, lo = asyncio.run(_probe_neighbors_parallel(lat, lon, step_deg=ring_step_deg, rings=rings))
    if data is not None and la is not None and lo is not None:
        dist = _haversine_m(lat, lon, la, lo)
        return data, la, lo, dist

    raise RuntimeError("no soil data found in neighborhood")



# -------- Public API used by router --------
FetchFunc = Callable[[float, float], Dict]

def get_soil(lat: float, lon: float, fetcher: FetchFunc) -> SoilBundle:
    payload = fetcher(lat, lon)
    return normalize_soilgrids(payload)

def resilient_soil_fetcher(lat: float, lon: float) -> Dict:
    data, used_lat, used_lon, dist_m = soilgrids_try_neighbors(lat, lon)
    data["_resolved_lat"] = used_lat
    data["_resolved_lon"] = used_lon
    data["_resolved_distance_m"] = dist_m
    return data


# -------- Response helper (now includes resolved metadata if available) --------
def to_response_dict(
    bundle: SoilBundle,
    *,
    resolved_lat: float | None = None,
    resolved_lon: float | None = None,
    resolved_distance_m: float | None = None,
) -> Dict:
    out = {
        "latitude": bundle.latitude,
        "longitude": bundle.longitude,
        "layers": [asdict(l) for l in bundle.layers],
        "topsoil": asdict(bundle.topsoil) if bundle.topsoil else None,
    }
    if resolved_lat is not None and resolved_lon is not None:
        out["resolved_latitude"] = resolved_lat
        out["resolved_longitude"] = resolved_lon
    if resolved_distance_m is not None:
        out["resolved_distance_m"] = round(resolved_distance_m, 1)
    return out
