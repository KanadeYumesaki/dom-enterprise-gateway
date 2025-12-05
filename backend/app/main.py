from fastapi import FastAPI
from app.api.endpoints import auth, chat, files, admin, feedback # auth, chat, files, admin, feedbackルーターをインポート
from app.core.config import settings # 設定をインポート

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# APIルーターをインクルード
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(files.router, prefix=f"{settings.API_V1_STR}/files", tags=["files"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(feedback.router, prefix=f"{settings.API_V1_STR}/feedback", tags=["feedback"]) # feedbackルーターを追加

@app.get("/")
async def read_root():
    return {"message": "Welcome to the DOM Enterprise Gateway"}