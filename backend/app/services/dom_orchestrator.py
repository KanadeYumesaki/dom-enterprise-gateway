from typing import AsyncGenerator, List
from app.llm.mock_llm import MockLLMClient
from app.services.answer_composer import AnswerComposerService
from app.services.rag_service import RagService
from app.models.chat import ChatMessage # ChatMessageモデルをインポート
import json

class DomOrchestratorService:
    """
    DOM Orchestrator Serviceの基本骨格。
    チャットメッセージを受け取り、LLMとの連携やRAG、メモリ管理などを調整します。
    LLM応答をIC-5ライト形式に整形してストリーミングします。
    Agentic Researchモードをサポートします。
    """
    def __init__(self, llm_client: MockLLMClient, answer_composer: AnswerComposerService, rag_service: RagService):
        self.llm_client = llm_client
        self.answer_composer = answer_composer
        self.rag_service = rag_service

    async def process_chat_message(self, user_message: str, session_id: str, is_research_mode: bool = False) -> AsyncGenerator[str, None]:
        """
        ユーザーからのチャットメッセージを処理し、アシスタントの応答をIC-5ライト形式に整形して
        トークンごとにストリーミングします。
        is_research_modeがTrueの場合、RAGサービスを呼び出してコンテキストを強化します。
        """
        augmented_prompt = user_message

        if is_research_mode:
            # RAGサービスを呼び出して関連情報を取得
            retrieved_context = await self.rag_service.query_rag(user_message, session_id=UUID(session_id))
            if retrieved_context and retrieved_context != "分かりません":
                augmented_prompt = f"ユーザーの質問: {user_message}\n\n関連情報: {retrieved_context}\n\nこの情報に基づいて質問に答えてください。"
            else:
                yield "**Warning**: No relevant information found for research mode. Proceeding without RAG context.\n\n"
        
        full_llm_output = ""
        async for token in self.llm_client.stream_chat_response(augmented_prompt):
            if token == "[END]":
                break
            full_llm_output += token
        
        # LLMの生出力をIC-5ライト形式に整形
        composed_response = await self.answer_composer.compose_ic5_light_response(full_llm_output)

        # 整形された応答をMarkdown形式でストリーム
        if composed_response["Decision"]:
            yield f"**Decision**\n{composed_response['Decision']}\n\n"
        if composed_response["Why"]:
            yield f"**Why**\n{composed_response['Why']}\n\n"
        if composed_response["Next 3 Actions"]:
            yield f"**Next 3 Actions**\n{composed_response['Next 3 Actions']}\n\n"

    async def summarize_chat_history(self, messages: List[ChatMessage]) -> str:
        """
        チャット履歴のリストを受け取り、LLMクライアントを使用して要約を生成します。
        """
        if not messages:
            return "No chat history to summarize."

        history_text = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])
        summary_prompt = f"以下のチャット履歴を要約してください。\n\n{history_text}\n\n要約:"
        
        # LLMクライアントから直接要約を取得 (ストリーミングではなく完了を待つ)
        # MockLLMClientにはstream_chat_responseしかないため、ここではその出力を収集する
        full_summary_response = ""
        async for token in self.llm_client.stream_chat_response(summary_prompt):
            if token == "[END]":
                break
            full_summary_response += token
        
        # ここで、LLMの応答がIC-5ライト形式でない可能性もあるため、生の応答を返す
        return full_summary_response.strip()
