from __future__ import annotations

from typing import Callable, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.services.soil import (
    get_soil,
    resilient_soil_fetcher,
    to_response_dict,
)

router = APIRouter(prefix="/api", tags=["soil"])

# Dependency type for stubbing
FetchFunc = Callable[[float, float], Dict]

def get_fetcher() -> FetchFunc:
    return resilient_soil_fetcher

@router.get("/soil")
def get_soil_endpoint(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    fetcher: FetchFunc = Depends(get_fetcher),
) -> Dict:
    """
    Returns SoilGrids topsoil data. If the exact point fails, we automatically
    nudge to the nearest working grid cell and include:
      resolved_latitude, resolved_longitude, resolved_distance_m  (when applicable)
    """
    try:
        # 1) Fetch once (neighbor-aware) and pull any resolution metadata
        raw = fetcher(lat, lon)
        used_lat = raw.pop("_resolved_lat", None)
        used_lon = raw.pop("_resolved_lon", None)
        used_dist = raw.pop("_resolved_distance_m", None)

        # 2) Normalize the already-fetched payload
        bundle = get_soil(lat, lon, lambda _lat, _lon: raw)

        

        # 3) Respond (adds resolved_* if present)
        return to_response_dict(
            bundle,
            resolved_lat=used_lat,
            resolved_lon=used_lon,
            resolved_distance_m=used_dist,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"soil fetch failed: {e}")
