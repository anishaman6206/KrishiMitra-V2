# backend/app/routers/ai.py
from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, Body, HTTPException

from backend.app.services.ai_chat import translate_text

router = APIRouter(prefix="/api/ai", tags=["ai"])

@router.post("/translate")
def ai_translate(
    payload: Dict[str, Any] = Body(
        ...,
        example={"text": "Apply 20 kg urea per acre.", "target_language": "hi"}
    )
):
    """
    Translate arbitrary text using Gemini.
    Body fields:
      - text (str)             REQUIRED
      - target_language (str)  REQUIRED (e.g., "hi", "en", "bn", "mr")
    """
    try:
        text = str(payload.get("text") or "").strip()
        target_language = str(payload.get("target_language") or "").strip()
        if not text or not target_language:
            raise HTTPException(status_code=400, detail="text and target_language are required")

        out = translate_text(text=text, target_language=target_language)
        return out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"translate failed: {e}")
