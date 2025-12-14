import json
import secrets
from typing import Annotated
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse

from app.schemas.auth import AuthenticatedUser
from app.services.auth import AuthService
from app.dependencies import (
    get_auth_service,
    get_current_user,
    _sign_payload,
    STATE_COOKIE_NAME,
    SESSION_COOKIE_NAME,
)
from app.core.config import settings

router = APIRouter()


def _validate_redirect_uri(request: Request, redirect_uri: str) -> str:
    """
    P0.1: relative path only。絶対URLは拒否してXSS/オープンリダイレクトを防ぐ。
    """
    if not redirect_uri or not redirect_uri.startswith("/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid redirect_uri")
    if redirect_uri.startswith("//"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid redirect_uri")
    # 正規化して返却
    return redirect_uri


@router.get("/login", summary="(DEV) 認証開始", status_code=status.HTTP_302_FOUND)
async def dev_login(request: Request, redirect_uri: str = Query(..., description="相対パスのみ許可")):
    if not settings.DEV_AUTH_ENABLED:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="OIDC login not implemented yet")

    safe_redirect = _validate_redirect_uri(request, redirect_uri)
    state = secrets.token_urlsafe(16)

    # redirect_uri に state, code を付与
    parsed = urlparse(safe_redirect)
    query = parse_qs(parsed.query)
    query["state"] = [state]
    query["code"] = ["dev"]
    new_query = urlencode(query, doseq=True)
    redirected = urlunparse(parsed._replace(query=new_query))

    response = RedirectResponse(url=redirected, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        STATE_COOKIE_NAME,
        state,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        path="/",
    )
    return response


@router.get("/callback", response_model=AuthenticatedUser, summary="(DEV) 認証コールバック")
async def dev_callback(request: Request, state: str = Query(...), code: str = Query(...)):
    if not settings.DEV_AUTH_ENABLED:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="OIDC callback not implemented yet")

    state_cookie = request.cookies.get(STATE_COOKIE_NAME)
    if not state_cookie or state_cookie != state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")
    if code != "dev":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    dev_user = AuthenticatedUser(
        id=uuid4(),
        tenant_id=uuid4(),
        email="dev@example.com",
        is_active=True,
        is_admin=True,
    )

    session_token = _sign_payload(dev_user.model_dump())
    response = JSONResponse(content=json.loads(dev_user.model_dump_json()))
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_token,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        path="/",
    )
    # state cookieは不要になるため削除
    response.delete_cookie(STATE_COOKIE_NAME, path="/")
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="(DEV) ログアウト")
async def dev_logout(request: Request, response: Response):
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(STATE_COOKIE_NAME, path="/")
    return response


@router.get("/me", response_model=AuthenticatedUser, summary="現在の認証済みユーザー情報を取得")
async def read_current_user(current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]):
    """
    現在の認証済みユーザーの情報を取得します。
    """
    return current_user
