# backend/app/schemas/crop_disease.py
from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field


class CropDiseaseDetectionResponse(BaseModel):
    success: bool = Field(..., description="Whether disease detection was successful")
    diseases: Optional[List[str]] = Field(None, description="Diagnosis and recommendations for crop disease")
    disease_probabilities: Optional[List[float]] = Field(None, description="Probabilities for each detected disease")
    symptoms: Optional[List[str]] = Field(None, description="Symptoms observed in the crop")
    Treatments: Optional[List[str]] = Field(None, description="Recommendations for treatment and prevention")
    prevention_tips: Optional[List[str]] = Field(None, description="Advice for prevention")
    image_path: Optional[str] = Field(None, description="Path to the uploaded image")
    error: Optional[str] = Field(None, description="Error message if detection failed")
