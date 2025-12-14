from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.dependencies import get_current_user
from app.schemas.auth import AuthenticatedUser
from app.schemas.user_settings import UserSettingsRead, UserSettingsUpdate
from app.services.user_settings import UserSettingsService

router = APIRouter(prefix="/user", tags=["user_settings"])

@router.get("/settings", response_model=UserSettingsRead, summary="ユーザー設定取得")
async def get_user_settings(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    現在のユーザーの設定を取得します。
    
    動作:
    - DB にレコードがある場合: そのレコードを返す
    - DB にレコードが無い場合: デフォルト設定を返す（自動INSERT はしない）
    
    認証:
    - Bearer トークンが必要です。
    
    エラー:
    - 401: 認証エラー（トークン不正・期限切れ）
    - 500: サーバーエラー
    """
    service = UserSettingsService(db, current_user.tenant_id)
    return await service.get_or_default(current_user)

@router.post("/settings", response_model=UserSettingsRead, summary="ユーザー設定更新")
async def update_user_settings(
    payload: UserSettingsUpdate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    現在のユーザーの設定を更新します（部分更新対応）。
    
    動作:
    - payload に含まれるフィールドのみを更新します。
    - 例: theme だけを変更したい場合、他のフィールドは維持されます。
    - レコードが無い場合は新規作成します。
    
    認証:
    - Bearer トークンが必要です。
    
    エラー:
    - 401: 認証エラー
    - 422: バリデーションエラー（不正な値）
    - 500: サーバーエラー
    """
    service = UserSettingsService(db, current_user.tenant_id)
    return await service.update(current_user, payload)
