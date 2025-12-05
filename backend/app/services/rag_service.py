from typing import List, AsyncGenerator, Optional
from uuid import UUID
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_postgres.vectorstores import PGVector
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.retrievers import BaseRetriever

from app.core.config import settings
from app.llm.mock_llm import MockLLMClient # Embeddingsは別途モックする必要があるかもしれない

class RagService:
    """
    RAG (Retrieval Augmented Generation) サービス。
    PGVectorを利用したベクトルストアの管理と、LCELによるRAGチェーンの構築を行います。
    グローバルRAGとEphemeral RAGの両方をサポートします。
    """
    def __init__(self, tenant_id: UUID, llm_client: MockLLMClient):
        self.tenant_id = tenant_id
        self.llm_client = llm_client
        self.global_collection_name = f"{settings.PG_COLLECTION_NAME}_{str(tenant_id).replace('-', '_')}"

        # Embeddingモデルの初期化 (ここではダミー/モック)
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        # グローバルPGVectorストアの初期化
        self.global_vectorstore = PGVector(
            collection_name=self.global_collection_name,
            connection_string=settings.DATABASE_URL,
            embedding=self.embeddings,
        )
        self.global_retriever = self.global_vectorstore.as_retriever()

        # Ephemeral Vector Stores (セッションIDごとに管理)
        self._ephemeral_vectorstores = {} # session_id -> PGVectorインスタンス

        # RAGプロンプトの定義
        self.rag_prompt = ChatPromptTemplate.from_messages([
            ("system", """あなたは、提供されたコンテキストに基づいて質問に答えるAIアシスタントです。
             質問に直接関連する情報のみを、簡潔に、日本語で回答してください。
             不明な場合は「分かりません」と答えてください。
             ---
             コンテキスト: {context}
             ---"""),
            ("human", "{question}")
        ])

        # LLM
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro")

    def _get_ephemeral_collection_name(self, session_id: UUID) -> str:
        return f"{self.global_collection_name}_ephemeral_{str(session_id).replace('-', '_')}"

    def get_ephemeral_vectorstore(self, session_id: UUID) -> PGVector:
        """
        指定されたセッションIDに紐づくEphemeral PGVectorストアを取得または作成します。
        """
        if session_id not in self._ephemeral_vectorstores:
            ephemeral_collection_name = self._get_ephemeral_collection_name(session_id)
            self._ephemeral_vectorstores[session_id] = PGVector(
                collection_name=ephemeral_collection_name,
                connection_string=settings.DATABASE_URL,
                embedding=self.embeddings,
            )
        return self._ephemeral_vectorstores[session_id]

    async def add_documents_to_global_rag(self, documents: List[Document]):
        """
        ドキュメントをグローバルPGVectorストアに追加します。
        """
        await self.global_vectorstore.aadd_documents(documents)

    async def add_documents_to_ephemeral_rag(self, session_id: UUID, documents: List[Document]):
        """
        ドキュメントをEphemeral PGVectorストアに追加します。
        """
        ephemeral_vectorstore = self.get_ephemeral_vectorstore(session_id)
        await ephemeral_vectorstore.aadd_documents(documents)

    def _get_retriever_for_session(self, session_id: Optional[UUID] = None) -> BaseRetriever:
        """
        セッションIDに基づいて適切なリトリーバー（グローバルまたはEphemeral）を返します。
        複数のリトリーバーを結合することも可能ですが、ここではEphemeral優先とします。
        """
        if session_id and session_id in self._ephemeral_vectorstores:
            return self._ephemeral_vectorstores[session_id].as_retriever()
        return self.global_retriever

    def _create_rag_chain(self, session_id: Optional[UUID] = None):
        """
        指定されたセッションIDに対応するリトリーバーを使用してRAGチェーンを構築します。
        """
        retriever = self._get_retriever_for_session(session_id)
        
        return (
            RunnablePassthrough.assign(context=(lambda x: x["question"]) | retriever | self._format_docs)
            | self.rag_prompt
            | self.llm
            | StrOutputParser()
        )

    def _format_docs(self, docs: List[Document]) -> str:
        """取得したドキュメントを結合して文字列に整形します。"""
        return "\n\n".join(doc.page_content for doc in docs)

    async def query_rag(self, question: str, session_id: Optional[UUID] = None) -> str:
        """
        RAGチェーンを使用して質問に対する応答を生成します。
        """
        rag_chain = self._create_rag_chain(session_id)
        return await rag_chain.ainvoke({"question": question})

    async def stream_rag_response(self, question: str, session_id: Optional[UUID] = None) -> AsyncGenerator[str, None]:
        """
        RAGチェーンを使用して質問に対する応答をストリーミングで生成します。
        """
        rag_chain = self._create_rag_chain(session_id)
        stream = rag_chain.astream({"question": question})
        async for chunk in stream:
            yield chunk