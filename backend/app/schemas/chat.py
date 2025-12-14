from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

# リクエストボディ用スキーマ
class ChatMessageCreate(BaseModel):
    """
    新しいチャットメッセージを作成するためのPydanticスキーマ。
    """
    session_id: UUID = Field(..., description="メッセージが属するチャットセッションのID")
    content: str = Field(..., description="チャットメッセージの内容")
    role: str = Field(..., description="メッセージの送信者 ('user' または 'assistant')")

# レスポンス用スキーマ
class ChatMessageResponse(BaseModel):
    """
    チャットメッセージのレスポンスに使用するPydanticスキーマ。
    """
    id: UUID
    session_id: UUID
    role: str
    content: str
    raw_llm_response: dict | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

class ChatSessionCreate(BaseModel):
    """
    新しいチャットセッションを作成するためのPydanticスキーマ。
    """
    title: str | None = None

class ChatSessionResponse(BaseModel):
    """
    チャットセッションのレスポンスに使用するPydanticスキーマ。
    """
    id: UUID
    user_id: UUID
    tenant_id: UUID
    title: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
