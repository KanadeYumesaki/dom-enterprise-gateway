import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import String, text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase  # Import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger(__name__)

# 環境変数からデータベースURLを取得
DATABASE_URL = settings.DATABASE_URL

# Baseクラスの定義 (DeclarativeBaseを継承)
class Base(DeclarativeBase): # Renamed CustomBase to Base
    __abstract__ = True
    @declared_attr
    def __tablename__(cls):
        # テーブル命名規約: 't_' + クラス名をスネークケースに変換
        return "t_" + ''.join(['_'+i.lower() if 'A'<=i<='Z' else i for i in cls.__name__]).lstrip('_')

# 非同期エンジンの作成
# DATABASE_URLがNoneでないことを保証するか、Validationを行うべきだが、Settingsでデフォルト値がある前提。
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured")

engine = create_async_engine(DATABASE_URL, echo=True)

# 非同期セッションの作成
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 非同期DBセッションを返す依存性注入用の関数
async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session


async def auto_create_tables(retries: int = 5, backoff_sec: float = 1.0) -> None:
    """
    DEV用途: AUTO_CREATE_DB=true のときだけ起動時にテーブルを自動作成する。
    本番では絶対に有効化しないこと。
    """
    if not settings.AUTO_CREATE_DB:
        logger.info("AUTO_CREATE_DB is disabled. Skipping automatic table creation.")
        return

    logger.info("AUTO_CREATE_DB enabled. Starting table creation.")
    # すべてのモデルをmetadataに登録するため副作用import
    import app.models  # noqa: F401

    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info(
                "AUTO_CREATE_DB completed. tables=%s",
                list(Base.metadata.tables.keys()),
            )
            return
        except Exception as exc:
            if attempt == retries:
                logger.exception("AUTO_CREATE_DB failed after %s attempts", attempt)
                raise
            wait = backoff_sec * attempt
            logger.warning(
                "AUTO_CREATE_DB attempt %s failed (%s). Retrying in %.1fs",
                attempt,
                exc,
                wait,
            )
            await asyncio.sleep(wait)


async def backfill_dev_timestamps() -> None:
    """
    DEV用途: AUTO_CREATE_DB=true のときだけ、null の updated_at を created_at で補完する。
    既存データが原因の ResponseValidationError を防ぐ。
    """
    if not settings.AUTO_CREATE_DB:
        logger.info("AUTO_CREATE_DB is disabled. Skipping timestamp backfill.")
        return

    statements = {
        "t_chat_session": "UPDATE t_chat_session SET updated_at = created_at WHERE updated_at IS NULL",
        "t_user_settings": "UPDATE t_user_settings SET updated_at = created_at WHERE updated_at IS NULL",
    }

    try:
        async with engine.begin() as conn:
            for table, stmt in statements.items():
                result = await conn.execute(text(stmt))
                logger.info(
                    "Timestamp backfill for %s executed. rows=%s",
                    table,
                    result.rowcount,
                )
    except Exception:
        logger.exception("Timestamp backfill failed")
        raise
