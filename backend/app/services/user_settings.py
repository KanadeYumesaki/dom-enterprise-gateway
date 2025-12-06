from typing import Annotated
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import AuthenticatedUser
from app.schemas.user_settings import UserSettingsRead, UserSettingsUpdate, UserSettingsBase
from app.repositories.user_settings import UserSettingsRepository

class UserSettingsService:
    """
    ユーザー設定のビジネスロジック層。
    
    役割:
    - Repository を使って UserSettings の取得・更新を行います。
    - レコードが無い場合のデフォルト設定返却を担当します。
    
    いつ使うか:
    - API エンドポイントから呼び出され、認証済みユーザーの設定を管理します。
    """
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.repo = UserSettingsRepository(db, tenant_id)
    
    async def get_or_default(self, user: AuthenticatedUser) -> UserSettingsRead:
        """
        ユーザー設定を取得します。レコードが無い場合はデフォルト値を返します。
        
        Args:
            user: 認証済みユーザー情報
        
        Returns:
            UserSettingsRead（DB のレコード または デフォルト値）
        
        動作:
        1. DB から (tenant_id, user_id) で検索
        2. 見つかった場合: そのまま返す
        3. 見つからない場合: デフォルト値（UserSettingsBase）を UserSettingsRead に変換して返す
        
        注意:
        - P0 では「見つからない場合は自動 INSERT」せず、デフォルト値を返すだけです。
        - 初回の POST で明示的に保存されます。
        """
        existing = await self.repo.get_by_user(user.tenant_id, user.id)
        
        if existing:
            return UserSettingsRead.model_validate(existing)
        else:
            # デフォルト設定を返す（DB には保存しない）
            default = UserSettingsBase()
            return UserSettingsRead(
                id=UUID(int=0),  # ダミーID（DBに存在しない印）
                tenant_id=user.tenant_id,
                user_id=user.id,
                theme=default.theme,
                language=default.language,
                font_size=default.font_size,
                llm_profile=default.llm_profile,
                has_seen_onboarding=default.has_seen_onboarding,
                onboarding_skipped=default.onboarding_skipped,
                created_at=None,  # type: ignore
                updated_at=None
            )
    
    async def update(self, user: AuthenticatedUser, payload: UserSettingsUpdate) -> UserSettingsRead:
        """
        ユーザー設定を更新します（部分更新対応）。
        
        Args:
            user: 認証済みユーザー情報
            payload: 更新するフィールド（UserSettingsUpdate）
        
        Returns:
            更新後の UserSettingsRead
        
        データフロー（重要）:
        1. API レイヤ: UserSettingsUpdate を受け取る
        2. Service レイヤ（ここ）: payload.model_dump(exclude_unset=True) で「実際にセットされたフィールドのみ」の dict を作成
        3. Repository レイヤ: その dict を upsert に渡す
        4. Repository: dict に含まれるフィールドのみを UPDATE
        
        この仕組みにより、例えば theme だけを変更したい場合に、
        language や font_size が None に上書きされることを防ぎます。
        """
        # exclude_unset=True: ユーザーが実際にセットしたフィールドのみ抽出
        data = payload.model_dump(exclude_unset=True)
        
        # Repository の upsert で作成 or 更新
        updated = await self.repo.upsert(user.tenant_id, user.id, data)
        
        return UserSettingsRead.model_validate(updated)

def get_user_settings_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[AuthenticatedUser, Depends()],  # 実際の依存関係は後で調整
) -> UserSettingsService:
    """
    UserSettingsService の依存性注入用ファクトリ。
    """
    return UserSettingsService(db, current_user.tenant_id)
