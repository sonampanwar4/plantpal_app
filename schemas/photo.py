from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Union
from datetime import datetime
from enum import Enum


class DiagnosisStatus(str, Enum):
    """Enum for diagnosis status."""
    PENDING = "pending"
    ANALYZED = "analyzed"
    FAILED = "failed"

class PhotoCreate(BaseModel):
    """Schema for creating a photo record."""
    plant_id: Optional[int] = None
    user_id: int
    image_path: str
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    user_query: Optional[str] = None

class LocalPhotoDetail(BaseModel):
    file_size: int
    mime_type: str
    original_filename: str
    image_path: str
    thumbnail_path: str

class PhotoResponse(BaseModel):
    """Schema for photo response."""
    id: int
    plant_id: Optional[int]
    user_id: int
    image_path: str
    original_filename: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    diagnosis_status: str
    user_query: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


# Diagnosis Schemas
class PhotoDiagnosisCreate(BaseModel):
    """Schema for creating a diagnosis."""
    photo_id: int
    user_id: int
    diagnosis_text: str
    treatment_outcome: str
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    identified_issues: Optional[Dict[str, List[str]]] = None
    recommended_actions: Optional[Dict[str, Union[str, List[str]]]] = None


class PhotoDiagnosisUpdate(BaseModel):
    """Schema for updating a diagnosis."""
    diagnosis_text: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    identified_issues: Optional[Dict[str, List[str]]] = None
    recommended_actions: Optional[Dict[str, Union[str, List[str]]]] = None
    treatment_outcome: Optional[str] = None


class DiagnosisResponse(BaseModel):
    """Schema for diagnosis response."""
    id: int
    photo_id: int
    user_id: int
    diagnosis_text: str
    confidence_score: Optional[float]
    identified_issues: Optional[Dict[str, List[str]]]
    recommended_actions: Optional[Dict[str, Union[str, List[str]]]]
    treatment_outcome: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

# Combined Schemas for Complex Operations
class PhotoWithDiagnosis(BaseModel):
    """Schema combining photo with its diagnosis."""
    photo: PhotoResponse
    diagnosis: Optional[DiagnosisResponse] = None
    plant_name: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


# =============Photo analysis Request/Response Models =============

class PlantImageClassification(BaseModel):
    is_plant: bool = Field(
        description="Whether the uploaded image is related to plants."
    )
    symptoms: str = Field(
        description="Explanation if plant-related; otherwise an apology/request message."
    )

class PlantPhotoDiagnosisResponse(BaseModel):
    diagnosis_text: str = Field(
        ..., description="Detailed diagnosis explaining what is affecting the plant."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence level (0 to 1)."
    )
    issues: List[str] = Field(
        ..., description="A list of detected plant issues."
    )
    treatment: List[str] = Field(
        ..., description="A list of recommended treatment actions."
    )
    prevention: str = Field(
        ..., description="Advice on how to prevent the issue from recurring."
    )
    treatment_outcome: str = Field(
        ...,
        description="pending/unimproved/failed/improved/cured/success"
    )

class ImageDiagnosisResponse(BaseModel):
    """Unified response schema for image diagnosis"""
    is_plant_image: bool = Field(
        ..., description="Whether the image is plant-related."
    )
    diagnosis: Optional[PlantPhotoDiagnosisResponse] = Field(
        default=None, description="Plant diagnosis data (only if plant-related)."
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message: The image does not appear to contain a plant or plant-related content. Please upload a photo of a plant for diagnosis. (only if not plant-related)."
    )
