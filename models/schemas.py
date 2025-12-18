from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class FileType(str, Enum):
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"
    RTF = "rtf"
    ODT = "odt"
    XLS = "xls"
    XLSX = "xlsx"
    CSV = "csv"
    PPT = "ppt"
    PPTX = "pptx"
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    BMP = "bmp"
    TIFF = "tiff"
    HTML = "html"
    JSON = "json"
    XML = "xml"
    MD = "md"
    IMAGE = "image"

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: str = "default_user"
    use_context: bool = True

class ChatResponse(BaseModel):
    response: str
    session_id: str
    context_used: List[str] = []
    user_mood: str = "unknown"
    confidence: float = 0.0
    processing_time: float

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    chunk_count: int
    upload_date: datetime

class StatsResponse(BaseModel):
    total_documents: int
    total_sessions: int
    file_statistics: List[Dict[str, Any]]