from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Annotated, List, AsyncGenerator
from uuid import UUID

from app.schemas.chat import ChatMessageCreate, ChatMessageResponse, ChatSessionResponse, ChatSessionCreate
from app.schemas.auth import AuthenticatedUser
from app.dependencies import get_current_user
from app.repositories.chat import ChatSessionRepository, ChatMessageRepository
from app.services.dom_orchestrator import DomOrchestratorService
from app.services.chat_service import ChatService # New import
from app.dependencies import get_chat_session_repository, get_chat_message_repository, get_dom_orchestrator_service, get_chat_service

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED, summary="新しいチャットセッションを作成")
async def create_chat_session(
    session_in: ChatSessionCreate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    chat_session_repo: Annotated[ChatSessionRepository, Depends(get_chat_session_repository)]
):
    """
    新しいチャットセッションを作成します。
    """
    session_data = session_in.model_dump()
    session_data["user_id"] = current_user.id
    session_data["tenant_id"] = current_user.tenant_id
    new_session = await chat_session_repo.create(session_data)
    return new_session

@router.get("/sessions", response_model=List[ChatSessionResponse], summary="ユーザーのチャットセッション一覧を取得")
async def get_chat_sessions(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    chat_session_repo: Annotated[ChatSessionRepository, Depends(get_chat_session_repository)]
):
    """
    現在のユーザーのチャットセッション一覧を取得します。
    """
    sessions = await chat_session_repo.get_by_user_id(current_user.id)
    return sessions

@router.post("/send", response_model=ChatMessageResponse, summary="チャットメッセージを送信（ユーザーメッセージ保存のみ）")
async def send_chat_message(
    message_in: ChatMessageCreate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    chat_session_repo: Annotated[ChatSessionRepository, Depends(get_chat_session_repository)],
    chat_message_repo: Annotated[ChatMessageRepository, Depends(get_chat_message_repository)],
):
    """
    ユーザーからのチャットメッセージを受け取り、保存します。
    アシスタントの応答は/stream/{session_id}エンドポイントでストリーミングされます。
    """
    # セッションの存在と所有権を確認
    session = await chat_session_repo.get(message_in.session_id)
    if not session or session.user_id != current_user.id or session.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found or not authorized."
        )

    # ユーザーメッセージを保存
    user_message = await chat_message_repo.create({
        "session_id": message_in.session_id,
        "role": "user",
        "content": message_in.content
    })

    # ストリーミング応答は別のエンドポイントで行われるため、ここでは保存したユーザーメッセージを返す
    return user_message

async def generate_llm_response_stream(
    session_id: UUID,
    current_user: AuthenticatedUser,
    chat_session_repo: ChatSessionRepository,
    chat_message_repo: ChatMessageRepository,
    dom_orchestrator: DomOrchestratorService,
    research_mode: bool = False # 新しい引数を追加
) -> AsyncGenerator[str, None]:
    """
    LLMからの応答を生成し、ストリームとして返します。
    """
    # セッションの存在と所有権を確認
    session = await chat_session_repo.get(session_id)
    if not session or session.user_id != current_user.id or session.tenant_id != current_user.tenant_id:
        # クライアントへのエラー送信はStreamingResponseでは複雑なので、ログに記録
        print(f"Unauthorized stream request for session {session_id} by user {current_user.id}")
        yield "ERROR: Unauthorized access or session not found.\n"
        return

    # 最新のユーザーメッセージを取得
    # NOTE: 実際には、セッション履歴全体をLLMに渡す必要があります。ここでは簡易化しています。
    messages = await chat_message_repo.get_by_session_id(session_id)
    if not messages:
        yield "ERROR: No messages in session to respond to.\n"
        return
    
    last_user_message_content = messages[-1].content # 最新メッセージをプロンプトとして利用

    assistant_response_content = ""
    async for token in dom_orchestrator.process_chat_message(last_user_message_content, str(session_id), research_mode): # research_modeを渡す
        if token == "[END]": # DomOrchestratorServiceのモックが終了を示すトークン
            break
        assistant_response_content += token
        yield token # トークンをクライアントに送信

    # アシスタントの最終応答をDBに保存
    if assistant_response_content:
        await chat_message_repo.create({
            "session_id": session_id,
            "role": "assistant",
            "content": assistant_response_content
            # raw_llm_responseは後で実装
        })
    yield "[STREAM_END]" # フロントエンドがストリーム終了を検知するためのカスタムマーカー

@router.get("/stream/{session_id}", summary="指定されたチャットセッションのLLM応答をストリーミング", response_class=StreamingResponse)
async def stream_chat_response(
    session_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    chat_session_repo: Annotated[ChatSessionRepository, Depends(get_chat_session_repository)],
    chat_message_repo: Annotated[ChatMessageRepository, Depends(get_chat_message_repository)],
    dom_orchestrator: Annotated[DomOrchestratorService, Depends(get_dom_orchestrator_service)],
    research_mode: bool = False # 新しいクエリパラメータ
):
    """
    指定されたチャットセッションに対するLLMの応答をSSE (Server-Sent Events) 形式でストリーミングします。
    `research_mode`がTrueの場合、DomOrchestratorServiceがRAGを活用して回答を生成します。
    """
    return StreamingResponse(
        generate_llm_response_stream(
            session_id,
            current_user,
            chat_session_repo,
            chat_message_repo,
            dom_orchestrator,
            research_mode # 新しい引数を渡す
        ),
        media_type="text/event-stream"
    )

@router.post("/reset/{session_id}", response_model=ChatSessionResponse, summary="チャットセッションをリセット")
async def reset_chat_session(
    session_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)]
):
    """
    指定されたチャットセッションをリセットし、新しいセッションを返します。
    """
    try:
        new_session = await chat_service.reset_session(session_id, current_user.id, current_user.tenant_id)
        return new_session
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))