# backend/app/services/vision/crop_disease_llm.py
from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Tuple, Optional

import httpx

from backend.app.config import get_settings


DEFAULT_GEMINI_MODEL = (
    os.getenv("KM_GEMINI_MODEL")
    or os.getenv("GEMINI_MODEL")
    or "gemini-2.5-flash"
)

def _strip_code_fences(text: str) -> str:
    text = text.strip()
    m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else text

def _prompt_for_diagnosis(
    topk: List[Tuple[str, float]],
    extra_query: Optional[str],
) -> str:
    """
    Ask for strict JSON only. We DO NOT ask the model to explain
    how it decided—only to fill fields the client expects.
    """
    topk_str = ", ".join([f"{label} ({prob:.2f})" for label, prob in topk])
    extra = f"\nFarmer notes: {extra_query.strip()}\n" if (extra_query and extra_query.strip()) else ""

    return f"""You are an expert plant pathologist.

Return ONLY a strict JSON object with the following keys:
  "success": true|false,
  "diseases": string array,
  "disease_probabilities": number array (each 0..1, same order as diseases),
  "symptoms": string array,
  "Treatments": string array,
  "prevention_tips": string array

NO extra text, NO markdown, NO code fences. JSON object ONLY.

Vision model candidate classes (with probabilities): {topk_str}.{extra}

If confidence is low, include your best 1–3 differentials with conservative probabilities.
Probability array must have the same length as diseases.
Keep items concise and farmer-friendly.
"""

def call_gemini_json(prompt: str, model: Optional[str] = None) -> Dict:
    s = get_settings()
    api_key = s.gemini_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY / KM_GEMINI_API_KEY")

    model_name = model or DEFAULT_GEMINI_MODEL
    endpoint = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}]
    }

    with httpx.Client(timeout=s.http_timeout_seconds) as client:
        r = client.post(endpoint, params={"key": api_key}, headers={"Content-Type": "application/json"}, json=body)
        if r.status_code == 404:
            raise RuntimeError(f"404 unknown/unsupported Gemini model '{model_name}' at v1 endpoint")
        r.raise_for_status()
        data = r.json()

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        raise RuntimeError("Unexpected Gemini response shape; no text found")

    cleaned = _strip_code_fences(text)
    return json.loads(cleaned)

def build_response_dict(raw: Dict, image_path: Optional[str]) -> Dict:
    """
    Make sure required keys exist and are sane.
    """
    out = {
        "success": bool(raw.get("success", True)),
        "diseases": list(raw.get("diseases") or []),
        "disease_probabilities": [float(x) for x in (raw.get("disease_probabilities") or [])],
        "symptoms": list(raw.get("symptoms") or []),
        "Treatments": list(raw.get("Treatments") or raw.get("treatments") or []),
        "prevention_tips": list(raw.get("prevention_tips") or []),
        "image_path": image_path,
        "error": None,
    }
    # Clamp probs to [0,1] and length-match if needed
    if out["disease_probabilities"] and len(out["disease_probabilities"]) != len(out["diseases"]):
        n = min(len(out["disease_probabilities"]), len(out["diseases"]))
        out["diseases"] = out["diseases"][:n]
        out["disease_probabilities"] = out["disease_probabilities"][:n]
    out["disease_probabilities"] = [max(0.0, min(1.0, p)) for p in out["disease_probabilities"]]
    return out
