from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.dependencies import get_current_user
from app.schemas.auth import AuthenticatedUser
from app.schemas.help import HelpSection
from app.services.help import HelpService, get_help_service

router = APIRouter(prefix="/api/help", tags=["help"])

@router.get("/content", response_model=list[HelpSection] | HelpSection, summary="ヘルプコンテンツ取得")
async def get_help_content(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    help_service: Annotated[HelpService, Depends(get_help_service)],
    section_id: str | None = Query(None, description="セクションID（指定すれば1件、無ければ一覧）"),
    category: Literal["user", "admin", "all"] = Query("user", description="カテゴリフィルタ")
):
    """
    ヘルプコンテンツを取得します。
    
    使い方:
    - section_id 無し: 指定カテゴリの全セクション一覧を返す
    - section_id 有り: 該当セクション1件を返す
    
    Query Parameters:
    - section_id: セクションID（例: "intro", "chat", "files"）
    - category: "user" (一般ユーザー向け) / "admin" (管理者向け) / "all" (全て)
    
    認証:
    - Bearer トークンが必要です（ログイン済みユーザーのみ）。
    
    エラー:
    - 401: 認証エラー
    - 404: 指定された section_id が見つからない
    """
    if section_id:
        # 1件取得
        section = help_service.get_section(section_id)
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Help section '{section_id}' not found"
            )
        return section
    else:
        # 一覧取得
        return help_service.list_sections(category)
