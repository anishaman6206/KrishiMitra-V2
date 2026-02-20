from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List
import math
import httpx

# This would typically be in a different file, but including it here
# so the file is runnable for testing if needed.
# from backend.app.config import get_settings
class MockSettings:
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    http_timeout_seconds: float = 10.0

def get_settings():
    return MockSettings()

# ----- Data classes -----
@dataclass(frozen=True)
class CurrentWeather:
    temperature_c: float
    wind_speed_ms: float
    precipitation_mm: float           # total precip (rain + others)
    humidity_pct: float = float("nan")
    rain_mm: float = float("nan")     # rainfall-only (current)

@dataclass(frozen=True)
class DailyForecast:
    date: str                         # ISO date e.g. "2025-10-09"
    tmax_c: float
    tmin_c: float
    precip_mm: float                  # total precip (rain + others)
    humidity_mean_pct: float = float("nan")
    rain_mm: float = float("nan")     # rainfall-only (daily)
    rain_chance_pct: float = float("nan") # NEW optional (daily precip prob %)

@dataclass(frozen=True)
class WeatherBundle:
    latitude: float
    longitude: float
    current: CurrentWeather
    daily: List[DailyForecast]
    next24h_total_rain_mm: float = float("nan") # NEW: hourly -> total for next 24h

# ----- Helpers -----
def _as_float(x, default=float("nan")) -> float:
    try:
        v = float(x)
        return v
    except Exception:
        return default

# ----- Single public API: one request, full normalization -----
def get_weather(lat: float, lon: float) -> WeatherBundle:
    """
    One-call Open-Meteo fetch:
      - current: temperature, precipitation, rain, showers, humidity, wind
      - hourly: rain, showers (to build next24h total)
      - daily: tmax/tmin, precipitation_sum, rain_sum, showers_sum, humidity_mean, precip_probability_max
    """
    s = get_settings()
    url = s.open_meteo_base_url # e.g. https://api.open-meteo.com/v1/forecast
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "auto",
        "temperature_unit": "celsius",
        "windspeed_unit": "ms", # keep ms to match your CurrentWeather.wind_speed_ms
        "current": "temperature_2m,precipitation,wind_speed_10m,relative_humidity_2m,rain,showers", # Added 'showers'
        "hourly": "rain,showers", # Get both rain types for accumulation
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,showers_sum,relative_humidity_2m_mean,precipitation_probability_max", # Added 'showers_sum'
        "forecast_days": 7,
    }

    with httpx.Client(timeout=s.http_timeout_seconds) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        payload: Dict = r.json()

    # --- normalize current ---
    cur = payload.get("current") or {}
    
    # FIX: Calculate total rain by adding rain and showers
    current_rain = _as_float(cur.get("rain"), 0.0)
    current_showers = _as_float(cur.get("showers"), 0.0)
    total_current_rain = current_rain + current_showers
    
    current = CurrentWeather(
        temperature_c=_as_float(cur.get("temperature_2m")),
        wind_speed_ms=_as_float(cur.get("wind_speed_10m")),
        precipitation_mm=_as_float(cur.get("precipitation")),
        humidity_pct=_as_float(cur.get("relative_humidity_2m")),
        rain_mm=round(total_current_rain, 2), # FIX: Use summed/rounded value
    )

    # --- build next24h total from hourly.rain + hourly.showers ---
    hourly = payload.get("hourly") or {}
    hourly_rain = list(hourly.get("rain") or [])[:24] # Slice to max 24h
    hourly_showers = list(hourly.get("showers") or [])[:24] # Slice to max 24h

    # Pad the shorter list with 0s to match the longer one
    len_rain = len(hourly_rain)
    len_showers = len(hourly_showers)
    max_len = max(len_rain, len_showers)
    
    if len_rain < max_len:
        hourly_rain.extend([0.0] * (max_len - len_rain))
    if len_showers < max_len:
        hourly_showers.extend([0.0] * (max_len - len_showers))

    next24h_total_rain_mm = float("nan")
    if max_len > 0:
        total_24h_rain = 0.0
        for i in range(max_len):
            total_24h_rain += _as_float(hourly_rain[i], 0.0) + _as_float(hourly_showers[i], 0.0)
        # FIX: Round the final sum to 2 decimal places
        next24h_total_rain_mm = round(total_24h_rain, 2)

    # --- normalize daily ---
    daily = payload.get("daily") or {}
    times   = list(daily.get("time") or [])
    tmaxs   = list(daily.get("temperature_2m_max") or [])
    tmins   = list(daily.get("temperature_2m_min") or [])
    precs   = list(daily.get("precipitation_sum") or [])
    rains   = list(daily.get("rain_sum") or [])
    showers = list(daily.get("showers_sum") or []) # Get showers_sum
    hums    = list(daily.get("relative_humidity_2m_mean") or [])
    chances = list(daily.get("precipitation_probability_max") or [])

    # Ensure all main arrays match the length of 'times' for safe access
    n_times = len(times)
    n = min(len(tmaxs), len(tmins), len(precs))
    if n < n_times:
        print(f"Warning: Mismatch in daily data lengths. Truncating to {n} days.")
        n_times = n # Truncate all processing to the shortest critical array

    days: List[DailyForecast] = []
    for i in range(n_times):
        # FIX: Calculate total daily rain
        daily_rain = _as_float(rains[i], 0.0) if i < len(rains) else 0.0
        daily_showers = _as_float(showers[i], 0.0) if i < len(showers) else 0.0
        total_daily_rain = daily_rain + daily_showers

        days.append(
            DailyForecast(
                date=str(times[i]),
                tmax_c=_as_float(tmaxs[i]),
                tmin_c=_as_float(tmins[i]),
                precip_mm=_as_float(precs[i]),
                humidity_mean_pct=_as_float(hums[i]) if i < len(hums) else float("nan"),
                rain_mm=round(total_daily_rain, 2), # FIX: Use summed/rounded value
                rain_chance_pct=_as_float(chances[i]) if i < len(chances) else float("nan"),
            )
        )

    return WeatherBundle(
        latitude=_as_float(payload.get("latitude")),
        longitude=_as_float(payload.get("longitude")),
        current=current,
        daily=days,
        next24h_total_rain_mm=next24h_total_rain_mm, # This is now correctly rounded
    )

# ----- Router helper -----
def to_response_dict(bundle: WeatherBundle) -> Dict:
    out = {
        "latitude": bundle.latitude,
        "longitude": bundle.longitude,
        "current": asdict(bundle.current),
        "daily": [asdict(d) for d in bundle.daily],
    }
    # expose 24h total if available
    if not math.isnan(bundle.next24h_total_rain_mm):
        out["next24h_total_rain_mm"] = bundle.next24h_total_rain_mm
    return out

# --- Example of how to run this file ---
if __name__ == "__main__":
    # Example coordinates from your output
    lat_example = 22.5
    lon_example = 87.625
    
    print(f"Fetching weather for: ({lat_example}, {lon_example})")
    
    try:
        weather_bundle = get_weather(lat=lat_example, lon=lon_example)
        response_dict = to_response_dict(weather_bundle)
        
        # Pretty-print the JSON-like dictionary
        import json
        print(json.dumps(response_dict, indent=2))

    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

