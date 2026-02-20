# backend/app/routers/weather.py (or your existing weather router)
from fastapi import APIRouter, HTTPException, Query
from backend.app.services.weather import get_weather, to_response_dict

router = APIRouter(prefix="/api", tags=["weather"])

@router.get("/weather")
def weather_endpoint(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    try:
        wb = get_weather(lat, lon)
        return to_response_dict(wb)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"weather fetch failed: {e}")
