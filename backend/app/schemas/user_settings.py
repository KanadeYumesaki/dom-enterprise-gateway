from uuid import UUID
from datetime import datetime
from typing import Literal
from pydantic import BaseModel

class UserSettingsBase(BaseModel):
    """
    ユーザー設定の基底スキーマ。
    
    共通フィールドを定義します。
    """
    theme: Literal["light", "dark"] = "light"
    language: Literal["ja", "en"] = "ja"
    font_size: Literal["small", "medium", "large"] = "medium"
    llm_profile: str | None = None
    has_seen_onboarding: bool = False
    onboarding_skipped: bool = False

class UserSettingsRead(UserSettingsBase):
    """
    ユーザー設定の読み取り用スキーマ（API Response）。
    
    GET /api/user/settings のレスポンスで使用します。
    """
    id: UUID
    tenant_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime | None
    
    class Config:
        from_attributes = True

class UserSettingsUpdate(BaseModel):
    """
    ユーザー設定の更新用スキーマ（API Request）。
    
    役割:
    - POST /api/user/settings のリクエストボディで使用します。
    - 全フィールドが Optional なので、「部分更新」が可能です。
    
    データフロー:
    - API レイヤ: このスキーマで受け取る
    - Service レイヤ: payload.model_dump(exclude_unset=True) で「実際にセットされたフィールドのみ」の dict を作成
    - Repository レイヤ: その dict だけを UPDATE に使用
    
    これにより、ユーザーが theme だけ変更したい場合に、他のフィールド（language, font_size等）が
    None に上書きされる事故を防ぎます。
    """
    theme: Literal["light", "dark"] | None = None
    language: Literal["ja", "en"] | None = None
    font_size: Literal["small", "medium", "large"] | None = None
    llm_profile: str | None = None
    has_seen_onboarding: bool | None = None
    onboarding_skipped: bool | None = None
