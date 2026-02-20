# backend/app/routers/crop_disease.py
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.app.schemas.crop_disease import CropDiseaseDetectionResponse
from backend.app.services.vision.vit_disease import detect_crop_disease as vit_detect
from backend.app.services.vision.crop_disease_llm import (
    _prompt_for_diagnosis,
    call_gemini_json,
    build_response_dict,
)

router = APIRouter(prefix="/api/v1/cropdisease", tags=["crop-disease"])

UPLOAD_DIR = Path("backend/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/detect", response_model=CropDiseaseDetectionResponse)
async def detect_crop_disease(
    file: UploadFile = File(..., description="Leaf/plant image"),
    query: Optional[str] = Form(None, description="Optional notes/symptoms"),
):
    """
    1) Run ViT on the image to get top-k class probs
    2) Send those candidates + user notes to Gemini (REST) to produce final JSON
    """
    try:
        # ---- save the file (so you can inspect it later / return path) ----
        suffix = Path(file.filename or "image").suffix or ".jpg"
        fname = f"{uuid.uuid4().hex}{suffix}"
        fpath = UPLOAD_DIR / fname
        raw = await file.read()
        fpath.write_bytes(raw)

        # ---- ViT predictions (your helper) ----
        vit_out = vit_detect(str(fpath))  # list[{"disease":..., "probability":...}] or [{"error": "..."}]
        if vit_out and "error" in vit_out[0]:
            raise HTTPException(status_code=400, detail=vit_out[0]["error"])

        # Convert to list[(label, prob)] for LLM prompt
        topk = [(d["disease"], float(d["probability"])) for d in vit_out][:3]

        # ---- LLM step ----
        prompt = _prompt_for_diagnosis(topk, query)
        llm_json = call_gemini_json(prompt)

        # ---- Final response dict (normalized) ----
        resp = build_response_dict(llm_json, str(fpath))
        return CropDiseaseDetectionResponse(**resp)

    except HTTPException:
        raise
    except Exception as e:
        # Return a graceful failure payload (never a 500 raw trace)
        return CropDiseaseDetectionResponse(
            success=False,
            diseases=None,
            disease_probabilities=None,
            symptoms=None,
            Treatments=None,
            prevention_tips=None,
            image_path=None,
            error=str(e),
        )
