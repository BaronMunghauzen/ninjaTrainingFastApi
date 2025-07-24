from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FileResponse(BaseModel):
    uuid: str
    filename: str
    file_size: int
    mime_type: str
    entity_type: str
    entity_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    message: str
    file: FileResponse 