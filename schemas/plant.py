from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from fastapi import Form

class PlantBase(BaseModel):
    """Base model for plant data."""
    name: str = Field(
        description="The common or user-assigned name of the plant, used for identification (e.g., 'Basil Plant' or 'Rose')."
    )
    species: Optional[str] = Field(
        default=None,
        description="The scientific or specific species name of the plant, if known (e.g., 'Ocimum basilicum' for basil)."
    )
    plant_location: Optional[str] = Field(
        default=None,
        description="The physical location of the plant, such as 'backyard', 'indoor windowsill', or 'greenhouse'."
    )
    home_location: Optional[str] = Field(
        default=None,
        description="The location of the user."
    )
    notes: Optional[str] = Field(default=None, description="Any information about the plant")

    @classmethod
    def as_form(cls,
                name: str = Form(...),
                species: Optional[str] = Form(...),
                plant_location: str = Form(...),
                home_location: str = Form(...),
                notes: Optional[str] = Form(...)
                ):
        return cls(
            name=name, species=species, plant_location=plant_location, home_location=home_location, notes=notes
        )


class PlantCreate(PlantBase):
    """Model for creating a new plant."""
    pass


class PlantUpdate(BaseModel):
    """Model for updating plant details - all fields are optional."""
    id: Optional[str] = None
    name: Optional[str] = None
    species: Optional[str] = None
    home_location: Optional[str] = None
    plant_location: Optional[str] = None
    notes: Optional[str] = None

class PlantResponse(PlantBase):
    """Response model for plant data."""
    id: int
    user_id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
