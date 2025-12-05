from uuid import UUID
from pydantic import BaseModel, EmailStr

class AuthenticatedUser(BaseModel):
    """
    認証されたユーザー情報を表すPydanticスキーマ。
    OIDCトークンから抽出される情報を保持します。
    """
    id: UUID
    tenant_id: UUID
    email: EmailStr
    is_active: bool = True
    is_admin: bool = False # サービス管理者かどうか

    class Config:
        from_attributes = True
