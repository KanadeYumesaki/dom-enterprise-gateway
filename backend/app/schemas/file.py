from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class FileUploadResponse(BaseModel):
    """
    ファイルアップロード後のメタデータのレスポンスに使用するPydanticスキーマ。
    """
    id: UUID
    tenant_id: UUID
    file_name: str
    file_path: str
    file_type: str | None = None
    file_size: str | None = None # string representation like "10MB"
    uploaded_by_user_id: UUID | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
