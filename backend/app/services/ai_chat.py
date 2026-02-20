# backend/app/services/ai_chat.py
from __future__ import annotations

import os
from typing import Dict, Optional

import httpx

from backend.app.config import get_settings

DEFAULT_GEMINI_MODEL = (
    os.getenv("KM_GEMINI_MODEL")
    or os.getenv("GEMINI_MODEL")
    or "gemini-2.5-flash"
)

def _gemini_call(prompt: str, *, model: Optional[str] = None) -> str:
    s = get_settings()
    api_key = s.gemini_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY / KM_GEMINI_API_KEY")
    endpoint = f"https://generativelanguage.googleapis.com/v1/models/{model or DEFAULT_GEMINI_MODEL}:generateContent"
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    with httpx.Client(timeout=s.http_timeout_seconds) as client:
        r = client.post(endpoint, params={"key": api_key}, headers={"Content-Type": "application/json"}, json=body)
        if r.status_code == 404:
            raise RuntimeError(f"404 unknown/unsupported Gemini model '{model or DEFAULT_GEMINI_MODEL}' at v1 endpoint")
        r.raise_for_status()
        data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        raise RuntimeError("Unexpected Gemini response shape; no text found")

def build_context_blob(
    *,
    soil: Optional[Dict] = None,
    weather: Optional[Dict] = None,
    price: Optional[Dict] = None,
) -> str:
    lines = []
    if soil:
        top = soil.get("topsoil") or {}
        lines.append(f"Soil (0–5cm): pH={top.get('ph_h2o')}, SOC_g_per_kg={top.get('soc_g_per_kg')}, N_g_per_kg={top.get('nitrogen_g_per_kg')}")
    if weather:
        cur = weather.get("current") or {}
        lines.append(f"Weather now: T={cur.get('temperature_c')}°C, RH={cur.get('humidity_pct')}%, wind={cur.get('wind_speed_ms')} m/s")
        if weather.get("daily"):
            d0 = weather["daily"][0]
            lines.append(f"Forecast day1: tmax={d0.get('tmax_c')}°C, tmin={d0.get('tmin_c')}°C, precip={d0.get('precip_mm')}mm, RH={d0.get('humidity_mean_pct','')}")
    if price:
        lines.append(f"Latest price: {price.get('commodity')} @ {price.get('mandi') or 'N/A'} = ₹{price.get('price')} per {price.get('unit','')}")
    return "\n".join(lines)

def ask_ai(
    *,
    question: str,
    target_language: Optional[str] = None,  # e.g., "hi" or "Hindi"
    user_context_text: Optional[str] = None,
    context_structured: Optional[Dict] = None,
    model: Optional[str] = None,
) -> Dict:
    """
    Returns: { "answer": <string>, "language": <string> }
    """
    context_blob = ""
    if context_structured:
        context_blob = build_context_blob(
            soil=context_structured.get("soil"),
            weather=context_structured.get("weather"),
            price=context_structured.get("price"),
        )
    tl = (target_language or "").strip()
    lang_line = f"Answer in {tl}." if tl else "Answer in the same language as the user's question."
    user_ctx_line = f"\nFarmer notes: {user_context_text.strip()}" if user_context_text else ""
    prompt = f"""You are KrishiMitra, a helpful agricultural assistant for Indian farmers.

{lang_line}
Be concise and actionable. Use bullet points where helpful. Avoid hallucinating; if unknown, say what data is needed.

Context (optional):
{context_blob or '—'}

Farmer question:
{question}
{user_ctx_line}
"""
    text = _gemini_call(prompt, model=model)
    return {"answer": text.strip(), "language": tl or "auto"}

def translate_text(*, text: str, target_language: str, model: Optional[str] = None) -> Dict:
    """
    Returns: { "translated": <string>, "language": <target_language> }
    """
    prompt = f"""Translate the following text to {target_language}. 
Return ONLY the translated text, no explanations, no code fences.

Text:
{text}"""
    translated = _gemini_call(prompt, model=model)
    return {"translated": translated.strip(), "language": target_language}
