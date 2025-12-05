from uuid import UUID
from typing import List, Optional

from app.repositories.chat import ChatSessionRepository, ChatMessageRepository
from app.services.memory_service import MemoryService
from app.services.dom_orchestrator import DomOrchestratorService
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import ChatSessionResponse # ChatSessionResponseをインポート

class ChatService:
    """
    チャットセッションとメッセージ管理、およびセッションリセットロジックを提供するサービス。
    """
    def __init__(
        self,
        chat_session_repo: ChatSessionRepository,
        chat_message_repo: ChatMessageRepository,
        memory_service: MemoryService,
        dom_orchestrator_service: DomOrchestratorService
    ):
        self.chat_session_repo = chat_session_repo
        self.chat_message_repo = chat_message_repo
        self.memory_service = memory_service
        self.dom_orchestrator_service = dom_orchestrator_service

    async def reset_session(self, session_id: UUID, user_id: UUID, tenant_id: UUID) -> ChatSessionResponse:
        """
        チャットセッションをリセットします。
        「Resetインバリアント」に従い、セッション要約とEpisodicMemoryへの保存が成功した場合のみ
        短期記憶（チャットメッセージ）をクリアします。
        """
        session = await self.chat_session_repo.get(session_id)
        if not session or session.user_id != user_id or session.tenant_id != tenant_id:
            raise ValueError("Chat session not found or not authorized.")
        
        # 1. セッションのチャット履歴を取得
        messages: List[ChatMessage] = await self.chat_message_repo.get_by_session_id(session_id)
        
        # 2. DomOrchestratorServiceを使ってセッションを要約
        session_summary_content = await self.dom_orchestrator_service.summarize_chat_history(messages)
        
        try:
            # 3. EpisodicMemoryに要約を保存
            episodic_memory = await self.memory_service.create_episodic_memory(
                user_id=user_id,
                session_id=session_id,
                summary=session_summary_content,
                decisions=[], # TODO: 実際の決定事項抽出ロジック
                assumptions=[] # TODO: 実際の前提起因抽出ロジック
            )
            
            # 4. 保存が成功した場合のみ、短期記憶（チャットメッセージ）をクリア
            # （実際にはメッセージを削除するリポジトリメソッドが必要）
            # for message in messages:
            #     await self.chat_message_repo.delete(message.id)
            # 現在のBaseRepositoryにはバルク削除がないため、一旦メッセージを非アクティブにするか、
            # 新しいセッションIDを発行して古いセッションを非アクティブにするロジックを検討。
            # ここでは簡単のため、新しいセッションを作成する形を取る。
            
            # 古いセッションを非アクティブ化
            await self.chat_session_repo.update(session, {"is_active": False})
            
            # 新しいセッションを作成
            new_session = await self.chat_session_repo.create({
                "user_id": user_id,
                "tenant_id": tenant_id,
                "title": f"Reset Session from {session.title or 'Unnamed Session'}"
            })
            return ChatSessionResponse.model_validate(new_session) # レスポンスモデルで返す
            
        except Exception as e:
            # 保存に失敗した場合はリセット処理を中止し、エラーを再raise
            raise ValueError(f"Failed to save session summary to episodic memory. Reset aborted: {e}")
