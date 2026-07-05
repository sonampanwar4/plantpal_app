from pydantic import BaseModel, Field
from typing import Optional, Literal
from fastapi import UploadFile

# Request models
class AIChatRequest(BaseModel):
    """Request model for AI analyse_chat_2 interaction."""
    input_text: str
    plant_id: Optional[int] = None
    type: Literal["chat", "diagnosis"] = "chat"

class UserChatRequestModel(BaseModel):
    """Request model for user interaction."""
    user_id: int
    input_text: str
    chat_type: str
    plant_id: Optional[int] = None
    photo_file: Optional[UploadFile | str] = None

    class Config:
        arbitrary_types_allowed = True

# Response models
class AIChatResponse(BaseModel):
    """Response model for AI analyze_chat output."""
    ai_response: str = Field(
        ...,
        description="A detailed string containing the AI's response to a user query or problem about their plant, providing practical advice, explanations, or solutions based on the provided details."
    )
    type: str = Field(
        default="chat",
        description="A string indicating the type of AI response, set to 'chat' for text-based plant care queries or assistance."
    )

