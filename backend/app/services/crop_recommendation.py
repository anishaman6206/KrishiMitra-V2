#crop_recommendation.py
from __future__ import annotations
from typing import Dict, List, Optional
import os, json, re
import httpx
from datetime import datetime

from backend.app.config import get_settings
from backend.app.services.weather import get_weather, to_response_dict as weather_to_resp
from backend.app.services.soil import resilient_soil_fetcher, get_soil, to_response_dict as soil_to_resp

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent"

def _gemini_call(prompt: str, *, timeout: float = 45.0) -> str:
    """
    Call Gemini v1 and return text. We bias towards JSON-only output.
    """
    s = get_settings()
    api_key = s.gemini_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY")

    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        # Hint the model to be concise & deterministic
        "generationConfig": {
            "temperature": 0.2,
        },
    }

    headers = {"Content-Type": "application/json"}
    with httpx.Client(timeout=timeout, headers=headers) as client:
        r = client.post(GEMINI_ENDPOINT, params={"key": api_key}, json=body)
        r.raise_for_status()
        data = r.json()

    # extract text
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        raise RuntimeError("Unexpected Gemini response shape; no text found")

# ---------------- JSON parsing helpers ----------------

_JSON_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)

def _extract_json_array(text: str) -> list:
    """
    Try strict json.loads first. If it fails, try to extract the first JSON array
    substring and parse that. Raise on failure.
    """
    text = (text or "").strip()
    # happy path
    try:
        val = json.loads(text)
        if isinstance(val, list):
            return val
    except Exception:
        pass

    # attempt to extract the first [...] block
    m = _JSON_ARRAY_RE.search(text)
    if m:
        frag = m.group(0)
        try:
            val = json.loads(frag)
            if isinstance(val, list):
                return val
        except Exception:
            pass

    raise ValueError("no JSON array found")

def _normalize_top3(arr: list) -> List[Dict]:
    """
    Take any list of dict-like items, build up to 3 {crop, probability} rows.
    """
    out: List[Dict] = []
    for item in arr:
        if not isinstance(item, dict):
            continue
        crop = str(item.get("crop", "")).strip().lower()
        if not crop:
            continue
        try:
            prob = float(item.get("probability", 0))
        except Exception:
            prob = 0.0
        # clamp
        prob = 0.0 if prob < 0 else 1.0 if prob > 1 else prob
        out.append({"crop": crop, "probability": prob})
        if len(out) == 3:
            break
    # pad if needed
    while len(out) < 3:
        out.append({"crop": "other", "probability": 0.5})
    return out

# --------------- Prompting ----------------

def _build_prompt(*, lat: float, lon: float, soil: Optional[Dict], weather: Optional[Dict], rotation_history: Optional[List[str]]) -> str:
    # Static knowledge about Indian cropping seasons to guide the model
    agronomic_context = """
General Agronomic Context for India:
The agricultural calendar has three main seasons. Use the current date to determine the most relevant season for sowing recommendations.
- **Kharif (Monsoon Crops, Sown June-July):** Rice, Maize, Cotton, Soybean, Millets (Jowar, Bajra), Groundnut, Sugarcane, Pulses (Arhar, Moong, Urad).
- **Rabi (Winter Crops, Sown October-December):** Wheat, Barley, Mustard, Peas, Chickpeas (Gram), Lentils (Masur), Oats.
- **Zaid (Summer Crops, Sown March-June):** Watermelon, Muskmelon, Cucumber, Gourds, Summer Moong.
"""

    lines = []
    # Get the current date and format it as YYYY-MM-DD
    current_date = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"Current Date: {current_date} (This is the start of the Rabi season).")

    if soil and soil.get("topsoil"):
        ts = soil["topsoil"]
        lines.append(
            f"Soil (0–5cm): pH={ts.get('ph_h2o')}, SOC_g_per_kg={ts.get('soc_g_per_kg')}, "
            f"N_g_per_kg={ts.get('nitrogen_g_per_kg')}, clay={ts.get('clay_g_per_kg')}, "
            f"sand={ts.get('sand_g_per_kg')}, silt={ts.get('silt_g_per_kg')}"
        )
    else:
        lines.append("Soil: unavailable at this location; infer using climate + general agronomy.")

    if weather:
        cur = weather.get("current") or {}
        lines.append(f"Weather now: T={cur.get('temperature_c')}°C, RH={cur.get('humidity_pct')}%, wind={cur.get('wind_speed_ms')} m/s, rain={cur.get('rain_mm')}")
        if weather.get("daily"):
            d0 = weather["daily"][0]
            # prefer rain_mm; fall back to precip_mm
            rain0 = d0.get("rain_mm", d0.get("precip_mm"))
            lines.append(
                f"Forecast day1: tmax={d0.get('tmax_c')}°C, tmin={d0.get('tmin_c')}°C, rain={rain0}mm, RH={d0.get('humidity_mean_pct','')}"
            )
    rot = ", ".join(rotation_history or [])
    lines.append(f"Crop rotation history (recent first): {rot or 'unknown'}")

    # The final prompt combines the static knowledge with the dynamic data.
    return f"""You are KrishiMitra, a helpful agronomy assistant for Indian farmers.

Task: Suggest the top 3 crops suited to the current conditions at lat={lat}, lon={lon}. Prioritize crops suitable for the current sowing season.
Return ONLY a MINIFIED JSON array of exactly 3 objects, no code fences, no extra text.
Each object must have:
- "crop": lowercase crop name (string)
- "probability": number between 0 and 1

{agronomic_context}
Specifics for this location:
{chr(10).join(lines)}
"""

def recommend_top3_crops(*, lat: float, lon: float, rotation_history: Optional[List[str]] = None) -> List[Dict]:
    # Weather: best-effort
    weather_pack = None
    try:
        w = get_weather(lat, lon)
        weather_pack = weather_to_resp(w)
    except Exception:
        weather_pack = None

    # Soil: best-effort (resilient fetcher)
    soil_pack = None
    try:
        raw = resilient_soil_fetcher(lat, lon)
        bundle = get_soil(lat, lon, lambda _lat, _lon: raw)
        soil_pack = soil_to_resp(bundle)
    except Exception:
        soil_pack = None

    # Build prompt & call model
    prompt = _build_prompt(lat=lat, lon=lon, soil=soil_pack, weather=weather_pack, rotation_history=rotation_history)
    text = _gemini_call(prompt, timeout=60.0)

    # Try to parse
    try:
        arr = _extract_json_array(text)
        return _normalize_top3(arr)
    except Exception:
        # One-shot repair: ask the model to convert its own output to valid JSON
        repair_prompt = (
            'Reformat the following into ONLY a MINIFIED JSON array of exactly 3 '
            'objects with fields "crop" (lowercase string) and "probability" (0..1). '
            'No prose, no code fences.\n\nTEXT:\n' + text
        )
        repaired = _gemini_call(repair_prompt, timeout=45.0)
        try:
            arr2 = _extract_json_array(repaired)
            return _normalize_top3(arr2)
        except Exception as e2:
            raise RuntimeError(f"LLM parse failed: {e2}")