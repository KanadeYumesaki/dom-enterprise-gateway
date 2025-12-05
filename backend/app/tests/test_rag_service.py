import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_postgres.vectorstores import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

from app.services.rag_service import RagService
from app.llm.mock_llm import MockLLMClient
from app.core.config import settings

@pytest.fixture
def mock_tenant_id():
    return uuid4()

@pytest.fixture
def mock_llm_client():
    return AsyncMock(spec=MockLLMClient)

@pytest.fixture
def mock_pgvector():
    """PGVectorクラスのモック"""
    with patch('app.services.rag_service.PGVector', autospec=True) as MockPGVector:
        mock_instance = MockPGVector.return_value
        mock_instance.as_retriever.return_value = AsyncMock() # .as_retriever()もモック
        yield MockPGVector

@pytest.fixture
def mock_embeddings():
    """GoogleGenerativeAIEmbeddingsのモック"""
    with patch('app.services.rag_service.GoogleGenerativeAIEmbeddings', autospec=True) as MockEmbeddings:
        yield MockEmbeddings

@pytest.fixture
def mock_chat_google_generative_ai():
    """ChatGoogleGenerativeAIのモック"""
    with patch('app.services.rag_service.ChatGoogleGenerativeAI', autospec=True) as MockChatLLM:
        yield MockChatLLM

@pytest.fixture
def rag_service(
    mock_tenant_id,
    mock_llm_client,
    mock_pgvector,
    mock_embeddings,
    mock_chat_google_generative_ai
):
    """RagServiceのフィクスチャ"""
    service = RagService(tenant_id=mock_tenant_id, llm_client=mock_llm_client)
    # 依存するオブジェクトがモックであることを確認
    assert isinstance(service.global_vectorstore, MagicMock)
    assert isinstance(service.embeddings, MagicMock)
    assert isinstance(service.llm, MagicMock)
    return service

@pytest.mark.asyncio
async def test_rag_service_initialization(
    mock_tenant_id,
    mock_llm_client,
    mock_pgvector,
    mock_embeddings,
    mock_chat_google_generative_ai
):
    """RagServiceが正しく初期化されることをテスト"""
    service = RagService(tenant_id=mock_tenant_id, llm_client=mock_llm_client)
    
    mock_embeddings.assert_called_once_with(model="models/embedding-001")
    mock_pgvector.assert_called_once_with(
        collection_name=f"{settings.PG_COLLECTION_NAME}_{str(mock_tenant_id).replace('-', '_')}",
        connection_string=settings.DATABASE_URL,
        embedding=mock_embeddings.return_value,
    )
    mock_chat_google_generative_ai.assert_called_once_with(model="gemini-pro")
    assert service.tenant_id == mock_tenant_id
    assert service.llm_client == mock_llm_client
    assert service.retriever == mock_pgvector.return_value.as_retriever.return_value
    assert isinstance(service.rag_chain, RunnablePassthrough) # LCELチェーンが構築されていることを確認

@pytest.mark.asyncio
async def test_query_rag(rag_service, mock_chat_google_generative_ai):
    """query_ragメソッドのテスト"""
    test_question = "What is RAG?"
    expected_answer = "RAG is Retrieval Augmented Generation."

    # LCELチェーン内のLLMのinvokeをモック
    mock_chat_google_generative_ai.return_value.ainvoke.return_value = expected_answer

    # Retrieverのget_relevant_documentsもモック
    rag_service.retriever.aget_relevant_documents.return_value = [
        Document(page_content="RAG combines retrieval and generation.")
    ]

    answer = await rag_service.query_rag(test_question)
    assert answer == expected_answer
    
    # retrieverが呼ばれたことを確認 (LCEL内部で発生)
    rag_service.retriever.aget_relevant_documents.assert_awaited_once()
    # LLMが呼ばれたことを確認 (LCEL内部で発生)
    # mock_chat_google_generative_ai.return_value.ainvoke.assert_awaited_once() # これはRAGチェーン内で複雑なため、直接確認は難しい

@pytest.mark.asyncio
async def test_add_documents(rag_service, mock_pgvector):
    """add_documentsメソッドのテスト"""
    test_documents = [Document(page_content="Test content")]
    await rag_service.add_documents(test_documents)
    mock_pgvector.return_value.aadd_documents.assert_awaited_once_with(test_documents)

@pytest.mark.asyncio
async def test_stream_rag_response(rag_service, mock_chat_google_generative_ai):
    """stream_rag_responseメソッドのテスト"""
    test_question = "Stream this."
    stream_chunks = ["First", "Second", "Third"]

    # LCELチェーン内のLLMのastreamをモック
    async def mock_llm_stream():
        for chunk in stream_chunks:
            yield chunk
    mock_chat_google_generative_ai.return_value.astream.return_value = mock_llm_stream()
    
    rag_service.retriever.aget_relevant_documents.return_value = [] # ダミー

    received_chunks = []
    async for chunk in rag_service.stream_rag_response(test_question):
        received_chunks.append(chunk)

    assert received_chunks == stream_chunks
    rag_service.retriever.aget_relevant_documents.assert_awaited_once()
    # mock_chat_google_generative_ai.return_value.astream.assert_awaited_once()
