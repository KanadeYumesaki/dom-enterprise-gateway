from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from app.schemas.auth import AuthenticatedUser
from app.services.auth import AuthService
from app.dependencies import get_auth_service, get_current_user

router = APIRouter()


@router.get("/me", response_model=AuthenticatedUser, summary="現在の認証済みユーザー情報を取得")
async def read_current_user(current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]):
    """
    現在の認証済みユーザーの情報を取得します。
    """
    return current_user

