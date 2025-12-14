from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    アプリケーション全体の設定値を管理するクラスです。

    - 基本はここに「安全なデフォルト値」を定義しておき、
      環境変数（や .env）の値があればそちらで上書きします。
    - 本番環境では Docker やデプロイ設定で必ず本物の値を
      環境変数として渡す前提です。
    """

    # pydantic-settings の設定
    model_config = SettingsConfigDict(
        env_file=".env",              # backend/.env があれば読み込む
        env_file_encoding="utf-8",
        extra="ignore",               # 想定外の環境変数があっても無視
    )

    # --- アプリケーション基本情報 ---
    PROJECT_NAME: str = "DOM Enterprise Gateway"
    API_V1_STR: str = "/api/v1"

    # --- データベース設定 ---
    # ※ 本番では環境変数 DATABASE_URL を必ず設定する前提
    #    未設定の場合はローカル開発用の PostgreSQL ダミーURL
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/dom_gateway"

    # PGVector のコレクション名
    PG_COLLECTION_NAME: str = "llm_documents"

    # --- Redis 設定 ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # --- Dev Auth (P0.1) ---
    DEV_AUTH_ENABLED: bool = False
    SESSION_SECRET: str = "change-me-session-secret"

    # --- Dev DB bootstrap (P0.1 only) ---
    AUTO_CREATE_DB: bool = False

    # --- 認証 / OIDC 設定 ---
    # ここも、本番では環境変数で上書きされる前提。
    # テストやローカル開発ではこのダミー値が使われます。
    OIDC_ISSUER: str = "https://accounts.google.com"  # 例: Google
    OIDC_CLIENT_ID: str = "dummy-client-id"
    OIDC_CLIENT_SECRET: str = "dummy-client-secret"
    OIDC_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/callback"

    # 初期管理者メールアドレス
    INITIAL_ADMIN_EMAIL: str = "admin@example.com"

    # --- ファイルアップロード設定 ---
    # アップロード先ディレクトリ
    UPLOAD_DIRECTORY: str = "uploads"

    # 1ファイルの最大サイズ（MB単位）
    MAX_FILE_SIZE_MB: int = 30

    # 許可するファイル拡張子のリスト
    ALLOWED_FILE_EXTENSIONS: List[str] = [
        "pdf",
        "txt",
        "md",
        "docx",
        "xlsx",
        "pptx",
    ]


# グローバルに 1 インスタンスだけ生成して、アプリ全体で共有します。
settings = Settings()
