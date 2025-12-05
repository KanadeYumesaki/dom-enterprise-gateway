from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FeedbackCreate(BaseModel):
    """
    フィードバック作成のためのPydanticスキーマ。
    """
    session_id: Optional[UUID] = Field(None, description="フィードバックが関連するチャットセッションのID")
    message_id: Optional[UUID] = Field(None, description="フィードバックが関連する特定のメッセージのID")
    rating: int = Field(..., ge=-1, le=1, description="評価 (-1: 👎, 0: 未評価, 1: 👍)")
    comment: Optional[str] = Field(None, max_length=1000, description="自由記述コメント")

class FeedbackResponse(BaseModel):
    """
    フィードバックのレスポンスに使用するPydanticスキーマ。
    """
    id: UUID
    tenant_id: UUID
    user_id: UUID
    session_id: Optional[UUID] = None
    message_id: Optional[UUID] = None
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
