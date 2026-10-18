from pydantic import BaseModel
from typing import List, Optional


class AttachmentMetadata(BaseModel):
    attachment_id: str
    session_id: str
    filename: str
    file_type: str
    file_size: int
    upload_timestamp: str


class AttachmentChunk(BaseModel):
    attachment_id: str
    chunk_id: str
    chunk_text: str
    embedding: List[float]


class AttachmentUploadResponse(BaseModel):
    success: bool
    attachment_id: str
    filename: str
    chunks_created: int
    message: Optional[str] = None


class AttachmentDeleteResponse(BaseModel):
    success: bool
    attachment_id: str
    message: str