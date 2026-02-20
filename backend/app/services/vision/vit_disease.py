# backend/app/services/vision/vit_disease.py
from __future__ import annotations

import io
from typing import List, Tuple

import torch
from PIL import Image, UnidentifiedImageError
from transformers import ViTImageProcessor, ViTForImageClassification
from backend.app.config import get_settings

s = get_settings()
HUGGING_FACE_HUB_TOKEN=s.HUGGING_FACE_HUB_TOKEN 
# You can override the model at runtime:
#   PowerShell:  $env:KM_VIT_MODEL_ID = "some/model"
# Default below works with many PlantVillage ViT fine-tunes on HF Hub.
_PROCESSOR = None
_MODEL = None


def _lazy_load():
    global _PROCESSOR, _MODEL
    if _PROCESSOR is None:
        _PROCESSOR = ViTImageProcessor.from_pretrained("wambugu71/crop_leaf_diseases_vit")
    if _MODEL is None:
        _MODEL = ViTForImageClassification.from_pretrained(
            "wambugu1738/crop_leaf_diseases_vit",
            ignore_mismatched_sizes=True,
        )
        _MODEL.eval()


def _softmax_to_topk(probs: torch.Tensor, top_k: int = 3) -> List[Tuple[str, float]]:
    # probs: (num_classes,)
    topk = torch.topk(probs, k=min(top_k, probs.shape[0]))
    idxs = topk.indices.tolist()
    vals = topk.values.tolist()
    id2label = _MODEL.config.id2label  # type: ignore[attr-defined]
    return [(id2label.get(i, str(i)), float(vals[j])) for j, i in enumerate(idxs)]


@torch.no_grad()
def detect_crop_disease(image_path: str) -> List[dict]:
    """
    Your original helper: returns a list of dicts:
    [{"disease": <label>, "probability": <float>}, ...]  (top-3)
    """
    try:
        _lazy_load()
        image = Image.open(image_path).convert("RGB")
        inputs = _PROCESSOR(images=image, return_tensors="pt")
        outputs = _MODEL(**inputs)
        probs = outputs.logits.softmax(dim=-1).squeeze(0)  # (num_classes,)
        top3 = _softmax_to_topk(probs, top_k=3)
        return [{"disease": lbl, "probability": prob} for (lbl, prob) in top3]
    except UnidentifiedImageError:
        return [{"error": "Invalid image file."}]
    except Exception as e:
        return [{"error": f"Error: {str(e)}"}]


@torch.no_grad()
def predict_topk_from_path(image_path: str, top_k: int = 3) -> List[Tuple[str, float]]:
    """
    Compatible with our LLM prompt: returns [(label, probability), ...]
    """
    _lazy_load()
    image = Image.open(image_path).convert("RGB")
    inputs = _PROCESSOR(images=image, return_tensors="pt")
    outputs = _MODEL(**inputs)
    probs = outputs.logits.softmax(dim=-1).squeeze(0)
    return _softmax_to_topk(probs, top_k=top_k)


@torch.no_grad()
def predict_topk(image_bytes: bytes, top_k: int = 3) -> List[Tuple[str, float]]:
    """
    Bytes version (used by earlier code). Kept for convenience.
    """
    _lazy_load()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = _PROCESSOR(images=image, return_tensors="pt")
    outputs = _MODEL(**inputs)
    probs = outputs.logits.softmax(dim=-1).squeeze(0)
    return _softmax_to_topk(probs, top_k=top_k)