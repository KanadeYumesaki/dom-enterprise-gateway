from fastapi import FastAPI

from app.api.endpoints import admin, auth, chat, feedback, files, help, user_settings
from app.core.config import settings  # 設定をインポート

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# APIルーターをインクルード（APIバージョンプレフィックスを付与）
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(files.router, prefix=f"{settings.API_V1_STR}/files", tags=["files"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(feedback.router, prefix=f"{settings.API_V1_STR}/feedback", tags=["feedback"])

# 新規追加分もバージョンに合わせて登録
app.include_router(user_settings.router, prefix=settings.API_V1_STR, tags=["user_settings"])
app.include_router(help.router, prefix=settings.API_V1_STR, tags=["help"])


@app.get("/")
async def read_root():
    return {"message": "Welcome to the DOM Enterprise Gateway"}
