from typing import Optional
import logging
from uuid import UUID

from fastapi import Depends, HTTPException, status
from starlette.requests import Request

from authlib.integrations.starlette_client import OAuth
from authlib.jose import JsonWebKey, JsonWebToken, jwk, jwt
from authlib.jose.errors import MissingClaimError, InvalidClaimError
from jose import jwt as python_jose_jwt  # python-jose の jwt

from app.core.config import settings
from app.schemas.auth import AuthenticatedUser
from app.repositories.user import UserRepository
from app.repositories.tenant import TenantRepository

logger = logging.getLogger(__name__)

class AuthService:
    """
    OIDC認証サービス。
    IDトークンの検証、ユーザー情報の抽出、JWKSの管理を行います。
    """
    def __init__(self, user_repository: UserRepository, tenant_repository: TenantRepository):
        self.user_repository = user_repository
        self.tenant_repository = tenant_repository
        self._jwks_client = None
        self._jwks_uri: Optional[str] = None
        self._jwt_decoder = JsonWebToken(["RS256"]) # RS256アルゴリズムを使用

    async def get_jwks_uri(self) -> str:
        """
        OIDCプロバイダのメタデータからJWKS URIを取得します。
        """
        if self._jwks_uri:
            return self._jwks_uri

        # well-known endpointから設定を取得
        discovery_url = f"{settings.OIDC_ISSUER}/.well-known/openid-configuration"
        try:
            # authlibのAsyncOAuthClientを使用
            # from authlib.integrations.base_client import AsyncOAuthClient # if needed
            # client = AsyncOAuthClient() # if needed

            # 通常は直接フェッチ
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(discovery_url)
                response.raise_for_status()
                config = response.json()
                self._jwks_uri = config.get("jwks_uri")
                if not self._jwks_uri:
                    raise ValueError("jwks_uri not found in OIDC discovery configuration.")
            return self._jwks_uri
        except Exception as e:
            logger.error(f"Failed to fetch OIDC discovery configuration from {discovery_url}: {e}")
            raise

    async def get_jwks_client(self):
        """
        JWKSクライアントを取得します。JWKS URIから公開鍵をフェッチします。
        """
        if self._jwks_client:
            return self._jwks_client

        jwks_uri = await self.get_jwks_uri()
        
        try:
             import httpx
             async with httpx.AsyncClient() as client:
                 response = await client.get(jwks_uri)
                 response.raise_for_status()
                 jwks_data = response.json()
                 
             self._jwks_client = jwk.JsonWebKey.import_key_set(jwks_data) # JWKSデータから鍵セットをインポート
             return self._jwks_client
        except Exception as e:
             logger.error(f"Failed to fetch JWKS from {jwks_uri}: {e}")
             raise
             
    async def verify_id_token(self, token: str) -> AuthenticatedUser:
        """
        IDトークンを検証し、認証済みユーザー情報を返します。
        """
        if not settings.OIDC_CLIENT_ID:
            raise ValueError("OIDC_CLIENT_ID is not configured.")

        # JWKSクライアントをフェッチ
        jwks_client = await self.get_jwks_client()

        # JWTヘッダーをデコードしてkidを取得
        header = python_jose_jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise ValueError("ID Token is missing 'kid' in header.")

        # kidに基づいて公開鍵を取得
        public_key = jwks_client.find_by_kid(kid)
        if not public_key:
            raise ValueError(f"No matching public key found for kid: {kid}")

        # IDトークンを検証
        try:
            claims = self._jwt_decoder.decode(
                token,
                public_key,
                claims_options={
                    "iss": {"essential": True, "value": settings.OIDC_ISSUER},
                    "aud": {"essential": True, "value": settings.OIDC_CLIENT_ID},
                    "exp": {"essential": True},
                    "iat": {"essential": True},
                    "sub": {"essential": True},
                    "email": {"essential": True},
                }
            )
            claims.validate() # claimsの検証を実行
        except (MissingClaimError, InvalidClaimError, Exception) as e:
            logger.error(f"ID Token verification failed: {e}")
            raise

        # ユーザー情報の抽出と取得/作成
        user_email = claims["email"]
        user_sub = claims["sub"] # OIDCプロバイダでの一意なユーザー識別子

        # ユーザーとテナントをデータベースから取得または作成
        tenant = await self.tenant_repository.get_by_name(settings.PROJECT_NAME)
        if not tenant:
            tenant = await self.tenant_repository.create({"name": settings.PROJECT_NAME})
            logger.info(f"Created new tenant: {tenant.name}")

        user = await self.user_repository.get_by_email(user_email)
        if not user:
            # パスワードはOIDC認証では使用しないためダミーを設定
            user = await self.user_repository.create({
                "tenant_id": tenant.id,
                "email": user_email,
                "hashed_password": "OIDC_USER_DUMMY_PASSWORD",
                "is_admin": (user_email == settings.INITIAL_ADMIN_EMAIL)
            })
            logger.info(f"Created new user: {user.email} for tenant: {tenant.name}")
        
        # AuthenticatedUserスキーマに変換
        return AuthenticatedUser(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin
        )
