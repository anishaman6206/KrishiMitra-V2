# backend/app/services/price_forecast.py
from __future__ import annotations

import os
import json
import datetime as dt
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from joblib import load

# -----------------------------------------------------------------------------
# Artifacts (same layout as your reference)
# -----------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR = os.getenv("PRICE_GLOBAL_MODEL_DIR", os.path.join(PROJECT_ROOT, "models", "pricing_global"))

_M20 = _M50 = _M80 = _META = _ENC = None

def _artifact_path(name: str) -> str:
    return os.path.join(MODEL_DIR, name)

def _load_artifacts():
    """
    Loads p20/p50/p80 models, meta.json, and encoder.json once.
    Mirrors your reference loader.
    """
    global _M20, _M50, _M80, _META, _ENC
    if _M50 is None:
        _M20 = load(_artifact_path("model_p20.joblib"))
        _M50 = load(_artifact_path("model_p50.joblib"))
        _M80 = load(_artifact_path("model_p80.joblib"))
        with open(_artifact_path("meta.json"), "r", encoding="utf-8") as f:
            _META = json.load(f)
        enc_path = _artifact_path("encoder.json")
        if os.path.exists(enc_path):
            with open(enc_path, "r", encoding="utf-8") as f:
                _ENC = json.load(f)
        else:
            _ENC = {"commodity": {}, "state": {}, "district": {}, "market": {}, "variety": {}, "grade": {}}
    return _M20, _M50, _M80, _META, _ENC

# -----------------------------------------------------------------------------
# Encoders & feature builders (trimmed to what we need)
# -----------------------------------------------------------------------------
def _encode_id(enc_map: Dict[str, int], key: Optional[str]) -> int:
    return int(enc_map.get(str(key), 0)) if key is not None else 0

def _make_feat_row_from_hist(
    hist_df: pd.DataFrame,
    fdate: pd.Timestamp,
    ids: Dict[str, int],
) -> Dict[str, float]:
    tail = hist_df.sort_values("date")["modal_price"].astype(float)
    if len(tail) == 0:
        tail = pd.Series([0.0])
    row = {
        "doy": float(fdate.timetuple().tm_yday),
        "dow": float(fdate.weekday()),
        "month": float(fdate.month),
        "commodity_id": float(ids.get("commodity_id", 0)),
        "state_id": float(ids.get("state_id", 0)),
        "district_id": float(ids.get("district_id", 0)),
        "market_id": float(ids.get("market_id", 0)),
        "variety_id": float(ids.get("variety_id", 0)),
        "grade_id": float(ids.get("grade_id", 0)),
    }
    for L in (1, 7, 14, 28):
        row[f"lag_{L}"] = float(tail.iloc[-1]) if len(tail) < L else float(tail.iloc[-L])
    for W in (7, 14, 28):
        tw = tail.iloc[-W:] if len(tail) >= W else tail
        row[f"rollmean_{W}"] = float(tw.mean())
        row[f"rollstd_{W}"] = float(tw.std() if len(tw) > 1 else 0.0)
    return row

def _adjust_quantiles(p50: float, p20: float, p80: float) -> tuple[float, float, float]:
    """
    Bias-correct and gently widen bands using residual stats from meta.json.
    """
    _, _, _, meta, _ = _load_artifacts()
    shift = float(meta.get("resid_median", 0.0) or 0.0)
    std = float(meta.get("resid_std", 0.0) or 0.0)
    widen_k = 0.2
    p50a = p50 + shift
    p20a = p20 + shift - widen_k * std
    p80a = p80 + shift + widen_k * std
    mid = p50a
    lo = min(p20a, mid)
    hi = max(p80a, mid)
    return mid, lo, hi

def _predict_one(model, Xf: pd.DataFrame) -> float:
    """
    Robust prediction that works whether the artifact is an sklearn wrapper
    (lightgbm.sklearn.LGBMRegressor) or a raw Booster.
    """
    try:
        # happy path: sklearn-style model
        return float(model.predict(Xf)[0])
    except Exception:
        # try underlying booster if present
        booster = getattr(model, "booster_", None)
        if booster is not None:
            return float(booster.predict(Xf.values)[0])
        # or the model itself is a Booster
        try:
            return float(model.predict(Xf.values)[0])
        except Exception as e:
            # surface the original context so you can see which artifact failed
            raise RuntimeError(f"model predict failed ({type(model).__name__}): {e}")
# -----------------------------------------------------------------------------
# Public: price forecast only (no sell/wait)
# -----------------------------------------------------------------------------
def forecast_horizon(
    *,
    now_price: float,
    now_date: Optional[dt.date] = None,
    commodity: str,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
    variety: Optional[str] = None,
    grade: Optional[str] = None,
    horizon_days: int = 7,
) -> Dict[str, Any]:
    """
    Returns { context: {...}, forecast: [{date, p20,p50,p80,p20_adj,p50_adj,p80_adj}, ...] }
    Uses the same global quantile models as your reference, but ONLY produces a forecast.
    """
    m20, m50, m80, meta, enc = _load_artifacts()
    features: List[str] = meta.get("features", [])

    # 1) History seeded with the current price
    today = now_date or dt.date.today()
    hist = pd.DataFrame([{"date": pd.to_datetime(today), "modal_price": float(now_price)}])

    # 2) Encode categorical IDs from exported encoder
    ids = {
        "commodity_id": _encode_id(enc.get("commodity", {}), commodity),
        "state_id": _encode_id(enc.get("state", {}), state),
        "district_id": _encode_id(enc.get("district", {}), district),
        "market_id": _encode_id(enc.get("market", {}), market),
        "variety_id": _encode_id(enc.get("variety", {}), variety),
        "grade_id": _encode_id(enc.get("grade", {}), grade),
    }

    # 3) Roll forward for H days
    out: List[Dict[str, Any]] = []
    base_date = pd.to_datetime(today)
    for d in range(1, horizon_days + 1):
        fdate = base_date + pd.Timedelta(days=d)
        row = _make_feat_row_from_hist(hist, fdate, ids)
        Xf = pd.DataFrame([row])

        # align features
        for col in features:
            if col not in Xf.columns:
                Xf[col] = 0.0
        Xf = Xf[features]

        y20 = _predict_one(m20, Xf)
        y50 = _predict_one(m50, Xf)
        y80 = _predict_one(m80, Xf)

        y50a, y20a, y80a = _adjust_quantiles(y50, y20, y80)

        out.append({
            "date": fdate.date().isoformat(),
            "p20": int(round(y20)),
            "p50": int(round(y50)),
            "p80": int(round(y80)),
            "p20_adj": int(round(y20a)),
            "p50_adj": int(round(y50a)),
            "p80_adj": int(round(y80a)),
        })

        # recursive step: feed adjusted median forward
        hist = pd.concat([hist, pd.DataFrame([{"date": fdate, "modal_price": y50a}])], ignore_index=True)

    return {
        "context": {
            "commodity": commodity,
            "state": state,
            "district": district,
            "market": market,
            "variety": variety,
            "grade": grade,
            "now_price": now_price,
            "now_date": today.isoformat(),
            "model_dir": MODEL_DIR,
        },
        "forecast": out,
    }
