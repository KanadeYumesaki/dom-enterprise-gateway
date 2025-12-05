from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase # Import DeclarativeBase

from app.core.config import settings

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
