from datetime import date
from pydantic import BaseModel, Field
from typing import Optional
from models.care_task import TaskType, RecurrenceType
from fastapi import Form

class PlantCareTaskBase(BaseModel):
    """Base model for plant care task data."""
    plant_id: int = Field(..., description="ID that belongs to the plant")
    task_type: TaskType = Field(..., description="Type of care task")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    recurrence_type: RecurrenceType = Field(..., description="Recurrence type")
    due_date: Optional[date] = Field(None, description="Due date")
    frequency_days: Optional[int] = Field(None, description="How often to perform task (in days)")
    user_id: Optional[int] = Field(None, description="ID of the user who owns this task")

    @classmethod
    def as_form(
            cls,
            title: str = Form(...),
            plant_id: int = Form(...),
            task_type: TaskType = Form(...),
            description: Optional[str] = Form(None),
            recurrence_type: RecurrenceType = Form(...),
            frequency_days: Optional[int] = Form(None),
            due_date: Optional[date] = Form(None),
            user_id: Optional[int] = Form(None)
    ):
        return cls(
            title=title,
            plant_id=plant_id,
            task_type=task_type,
            description=description if description else None,
            recurrence_type=recurrence_type,
            frequency_days=frequency_days,
            due_date=due_date,
            user_id=user_id
        )


class PlantCareTaskCreate(PlantCareTaskBase):
    """Model for creating a new plant care task."""
    pass


class PlantCareTaskUpdate(BaseModel):
    """Model for updating a plant care task."""
    id: Optional[int] = Field(..., description="Task ID")
    plant_id: int = Field(None, description="ID that belongs to the plant")
    task_type: Optional[TaskType] = Field(None, description="Type of care task")
    title: Optional[str] = Field(None, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    recurrence_type: Optional[RecurrenceType] = Field(None, description="Recurrence type")
    frequency_days: Optional[int] = Field(None, description="How often to perform task (in days)")
    due_date: Optional[date] = Field(None, description="Due date")
    user_id: Optional[int] = Field(None, description="ID of the user who owns this task")
    updated_at: Optional[date] = Field(None, description="updated date")

    @classmethod
    def as_form(
            cls,
            id: Optional[int] = Form(None),
            title: Optional[str] = Form(None),
            plant_id: Optional[int] = Form(None),
            task_type: Optional[TaskType] = Form(None),
            description: Optional[str] = Form(None),
            recurrence_type: Optional[RecurrenceType] = Form(None),
            frequency_days: Optional[int] = Form(None),
            due_date: Optional[date] = Form(None),
            user_id: Optional[int] = Form(None),
            updated_at: Optional[date] = Form(None)
    ):
        return cls(
            id=id,
            title=title,
            plant_id=plant_id,
            task_type=task_type,
            description=description,
            recurrence_type=recurrence_type,
            frequency_days=frequency_days,
            due_date=due_date,
            user_id=user_id,
            updated_at=updated_at
        )



class TaskInfoResponse(BaseModel):
    """Model for task info response."""
    task_type: TaskType = Field(None, description="Type of care task")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    due_date: date = Field(None, description="Due date")
    frequency_days: Optional[int] = Field(None, description="How often to perform task (in days)")
    plant_name: Optional[str] = Field(None, description="Name of the plant this task belongs to")
