from fastapi import Form, UploadFile, File
from typing import Optional


class ChatForm:
    def __init__(
            self,
            user_message: str = Form(...),  # required form field
            photo_file: Optional[UploadFile] = File(None),  # optional file upload
            plant_id: Optional[int] = Form(None)  # optional form field
    ):
        self.user_message = user_message
        self.photo_file = photo_file
        self.plant_id = plant_id
