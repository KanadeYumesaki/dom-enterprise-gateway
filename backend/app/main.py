from fastapi import FastAPI
from app.api.endpoints import auth, chat, files, admin, feedback, user_settings, help # user_settings, helpを追加
from app.core.config import settings # 設定をインポート

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# APIルーターをインクルード
app.include_router(auth.router, tags=["auth"])
app.include_router(chat.router, tags=["chat"])
app.include_router(files.router, tags=["files"])
app.include_router(admin.router, tags=["admin"])
app.include_router(feedback.router, tags=["feedback"])
app.include_router(user_settings.router, tags=["user_settings"])  # 追加
app.include_router(help.router, tags=["help"])  # 追加

@app.get("/")
async def read_root():
    return {"message": "Welcome to the DOM Enterprise Gateway"}