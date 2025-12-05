import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator
from uuid import UUID

from app.services.dom_orchestrator import DomOrchestratorService
from app.llm.mock_llm import MockLLMClient
from app.services.answer_composer import AnswerComposerService
from app.services.rag_service import RagService # New import

@pytest.fixture
def mock_llm_client():
    return AsyncMock(spec=MockLLMClient)

@pytest.fixture
def mock_answer_composer_service():
    return AsyncMock(spec=AnswerComposerService)

@pytest.fixture
def mock_rag_service():
    """RagServiceのモックフィクスチャ"""
    return AsyncMock(spec=RagService)

@pytest.fixture
def dom_orchestrator_service(mock_llm_client, mock_answer_composer_service, mock_rag_service):
    """RagServiceを引数に追加"""
    return DomOrchestratorService(mock_llm_client, mock_answer_composer_service, mock_rag_service)

@pytest.mark.asyncio
async def test_process_chat_message_ic5_light_streaming(
    dom_orchestrator_service,
    mock_llm_client,
    mock_answer_composer_service,
    mock_rag_service # New fixture
):
    """
    DomOrchestratorServiceがLLM応答をIC-5ライト形式に整形してストリーミングするテスト。
    (Research Mode OFF)
    """
    test_prompt = "Test prompt for IC-5"
    test_session_id = str(uuid4()) # strに変換
    raw_llm_output_mock = "Decision: Test Decision. Why: Test Why. Next 3 Actions: Test Action 1, Test Action 2, Test Action 3."
    
    # Mock LLM Client to stream tokens
    async def mock_llm_stream():
        for token in raw_llm_output_mock.split(" "):
            yield token + " "
        yield "[END]"
    mock_llm_client.stream_chat_response.return_value = mock_llm_stream()

    # Mock AnswerComposerService to return formatted dictionary
    mock_answer_composer_service.compose_ic5_light_response.return_value = {
        "Decision": "Test Decision.",
        "Why": "Test Why.",
        "Next 3 Actions": "Test Action 1, Test Action 2, Test Action 3."
    }

    # ストリーミング応答の収集
    streamed_output = ""
    async for chunk in dom_orchestrator_service.process_chat_message(test_prompt, test_session_id, is_research_mode=False):
        streamed_output += chunk

    # 検証
    mock_llm_client.stream_chat_response.assert_awaited_once_with(test_prompt) # RAGなしなので元のプロンプト
    mock_answer_composer_service.compose_ic5_light_response.assert_awaited_once_with(raw_llm_output_mock.strip())
    mock_rag_service.query_rag.assert_not_awaited() # Research Mode OFFなので呼ばれない

    expected_output_parts = [
        "**Decision**\nTest Decision.\n\n",
        "**Why**\nTest Why.\n\n",
        "**Next 3 Actions**\nTest Action 1, Test Action 2, Test Action 3.\n\n"
    ]
    for part in expected_output_parts:
        assert part in streamed_output
    
    assert streamed_output.index(expected_output_parts[0]) < streamed_output.index(expected_output_parts[1])
    assert streamed_output.index(expected_output_parts[1]) < streamed_output.index(expected_output_parts[2])

@pytest.mark.asyncio
async def test_process_chat_message_research_mode_on_with_rag_context(
    dom_orchestrator_service,
    mock_llm_client,
    mock_answer_composer_service,
    mock_rag_service
):
    """
    Research Mode ONでRAGコンテキストが取得できる場合のテスト。
    """
    test_prompt = "RAG Test Question"
    test_session_id = str(uuid4())
    rag_context_mock = "RAG retrieved: Some relevant document content."
    llm_output_with_rag = "Decision: Answer based on RAG. Why: Explained by RAG. Next 3 Actions: Check RAG, Verify RAG, Use RAG."

    mock_rag_service.query_rag.return_value = rag_context_mock
    async def mock_llm_stream():
        for token in llm_output_with_rag.split(" "):
            yield token + " "
        yield "[END]"
    mock_llm_client.stream_chat_response.return_value = mock_llm_stream()
    mock_answer_composer_service.compose_ic5_light_response.return_value = {
        "Decision": "Answer based on RAG.",
        "Why": "Explained by RAG.",
        "Next 3 Actions": "Check RAG, Verify RAG, Use RAG."
    }

    streamed_output = ""
    async for chunk in dom_orchestrator_service.process_chat_message(test_prompt, test_session_id, is_research_mode=True):
        streamed_output += chunk

    mock_rag_service.query_rag.assert_awaited_once_with(test_prompt, session_id=UUID(test_session_id))
    expected_augmented_prompt_prefix = f"ユーザーの質問: {test_prompt}\n\n関連情報: {rag_context_mock}"
    assert expected_augmented_prompt_prefix in mock_llm_client.stream_chat_response.call_args[0][0]
    assert "**Decision**\nAnswer based on RAG.\n\n" in streamed_output

@pytest.mark.asyncio
async def test_process_chat_message_research_mode_on_no_rag_context(
    dom_orchestrator_service,
    mock_llm_client,
    mock_answer_composer_service,
    mock_rag_service
):
    """
    Research Mode ONだがRAGコンテキストが取得できない場合のテスト。
    """
    test_prompt = "No RAG context question"
    test_session_id = str(uuid4())
    llm_output_no_rag = "Decision: Answer without RAG. Why: No RAG data. Next 3 Actions: None."

    mock_rag_service.query_rag.return_value = "分かりません" # またはNone
    async def mock_llm_stream():
        for token in llm_output_no_rag.split(" "):
            yield token + " "
        yield "[END]"
    mock_llm_client.stream_chat_response.return_value = mock_llm_stream()
    mock_answer_composer_service.compose_ic5_light_response.return_value = {
        "Decision": "Answer without RAG.",
        "Why": "No RAG data.",
        "Next 3 Actions": "None."
    }

    streamed_output = ""
    async for chunk in dom_orchestrator_service.process_chat_message(test_prompt, test_session_id, is_research_mode=True):
        streamed_output += chunk

    mock_rag_service.query_rag.assert_awaited_once_with(test_prompt, session_id=UUID(test_session_id))
    assert f"ユーザーの質問: {test_prompt}\n\n関連情報: {mock_rag_service.query_rag.return_value}" not in mock_llm_client.stream_chat_response.call_args[0][0]
    assert "Proceeding without RAG context" in streamed_output # 警告メッセージを確認
    assert "**Decision**\nAnswer without RAG.\n\n" in streamed_output
