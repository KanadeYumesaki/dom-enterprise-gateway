from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.repositories.tenant import TenantRepository
from app.repositories.user import UserRepository
from app.repositories.chat import ChatSessionRepository, ChatMessageRepository
from app.repositories.knowledge import KnowledgeDocumentRepository
from app.repositories.memory import StructuredMemoryRepository, EpisodicMemoryRepository # New import
from app.repositories.feedback import FeedbackRepository # New import
# from app.dependencies import get_current_user # Removed circular import
from app.schemas.auth import AuthenticatedUser
from app.schemas.auth import AuthenticatedUser
from app.services.auth import AuthService # Import AuthService for dependency function
from app.services.dom_orchestrator import DomOrchestratorService # New import
from app.services.answer_composer import AnswerComposerService # New import
from app.services.rag_service import RagService # New import
from app.services.file_service import FileService # New import
from app.services.memory_service import MemoryService # New import
from app.services.chat_service import ChatService # New import
from app.services.feedback_service import FeedbackService # New import
from app.llm.mock_llm import MockLLMClient # New import

# テナントIDでフィルタリングされないシステムレベルのリポジトリ
def get_system_tenant_repository(session: Annotated[AsyncSession, Depends(get_db_session)]) -> TenantRepository:
    """
    システムレベルのTenantRepositoryを提供します（テナントIDによるフィルタリングなし）。
    AuthServiceの初期ユーザー/テナント作成などで使用されます。
    """
    return TenantRepository(session, tenant_id=None)

def get_system_user_repository(session: Annotated[AsyncSession, Depends(get_db_session)]) -> UserRepository:
    """
    システムレベルのUserRepositoryを提供します（テナントIDによるフィルタリングなし）。
    AuthServiceの初期ユーザー/テナント作成などで使用されます。
    """
    return UserRepository(session, tenant_id=None)

# Auth Service Dependency (Moved here to avoid circular dependencies)
def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_system_user_repository)],
    tenant_repo: Annotated[TenantRepository, Depends(get_system_tenant_repository)]
) -> AuthService:
    return AuthService(user_repo, tenant_repo)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthenticatedUser:
    """
    リクエストヘッダーからBearerトークンを抽出し、AuthServiceで検証してAuthenticatedUserを返します。
    """
    try:
        user = await auth_service.verify_id_token(token)
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

async def get_current_admin_user(current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]) -> AuthenticatedUser:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )
    return current_user

# 認証済みユーザーのテナントIDでフィルタリングされるリポジトリ
def get_tenant_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)] # AuthenticatedUserを取得
) -> TenantRepository:
    """
    TenantRepositoryの依存性注入を提供します。
    現在のユーザーのテナントIDをリポジトリに渡します。
    """
    return TenantRepository(session, tenant_id=current_user.tenant_id)

def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)] # AuthenticatedUserを取得
) -> UserRepository:
    """
    UserRepositoryの依存性注入を提供します。
    現在のユーザーのテナントIDをリポジリに渡します。
    """
    return UserRepository(session, tenant_id=current_user.tenant_id)

# チャット関連のリポジリ
def get_chat_session_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]
) -> ChatSessionRepository:
    """
    ChatSessionRepositoryの依存性注入を提供します。
    """
    return ChatSessionRepository(session, tenant_id=current_user.tenant_id)

def get_chat_message_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]
) -> ChatMessageRepository:
    """
    ChatMessageRepositoryの依存性注入を提供します。
    """
    return ChatMessageRepository(session, tenant_id=current_user.tenant_id)

def get_knowledge_document_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]
) -> KnowledgeDocumentRepository:
    """
    KnowledgeDocumentRepositoryの依存性注入を提供します。
    """
    return KnowledgeDocumentRepository(session, tenant_id=current_user.tenant_id)

def get_structured_memory_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]
) -> StructuredMemoryRepository:
    """
    StructuredMemoryRepositoryの依存性注入を提供します。
    """
    return StructuredMemoryRepository(session, tenant_id=current_user.tenant_id)

def get_episodic_memory_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]
) -> EpisodicMemoryRepository:
    """
    EpisodicMemoryRepositoryの依存性注入を提供します。
    """
    return EpisodicMemoryRepository(session, tenant_id=current_user.tenant_id)

def get_feedback_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]
) -> FeedbackRepository:
    """
    FeedbackRepositoryの依存性注入を提供します。
    """
    return FeedbackRepository(session, tenant_id=current_user.tenant_id)

# LLMクライアントの依存性注入
def get_mock_llm_client() -> MockLLMClient:
    """
    MockLLMClientの依存性注入を提供します。
    """
    return MockLLMClient()

def get_answer_composer_service() -> AnswerComposerService:
    """
    AnswerComposerServiceの依存性注入を提供します。
    """
    return AnswerComposerService()

def get_rag_service(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    llm_client: Annotated[MockLLMClient, Depends(get_mock_llm_client)] # For now, use MockLLMClient
) -> RagService:
    """
    RagServiceの依存性注入を提供します。
    """
    return RagService(tenant_id=current_user.tenant_id, llm_client=llm_client)

def get_file_service() -> FileService:
    """
    FileServiceの依存性注入を提供します。
    """
    return FileService()

def get_dom_orchestrator_service(
    llm_client: Annotated[MockLLMClient, Depends(get_mock_llm_client)],
    answer_composer: Annotated[AnswerComposerService, Depends(get_answer_composer_service)],
    rag_service: Annotated[RagService, Depends(get_rag_service)] # Add RagService
) -> DomOrchestratorService:
    """
    DomOrchestratorServiceの依存性注入を提供します。
    """
    return DomOrchestratorService(llm_client, answer_composer, rag_service)

def get_memory_service(
    structured_memory_repo: Annotated[StructuredMemoryRepository, Depends(get_structured_memory_repository)],
    episodic_memory_repo: Annotated[EpisodicMemoryRepository, Depends(get_episodic_memory_repository)]
) -> MemoryService:
    """
    MemoryServiceの依存性注入を提供します。
    """
    return MemoryService(structured_memory_repo, episodic_memory_repo)

def get_chat_service(
    chat_session_repo: Annotated[ChatSessionRepository, Depends(get_chat_session_repository)],
    chat_message_repo: Annotated[ChatMessageRepository, Depends(get_chat_message_repository)],
    memory_service: Annotated[MemoryService, Depends(get_memory_service)],
    dom_orchestrator_service: Annotated[DomOrchestratorService, Depends(get_dom_orchestrator_service)]
) -> ChatService:
    """
    ChatServiceの依存性注入を提供します。
    """
    return ChatService(
        chat_session_repo,
        chat_message_repo,
        memory_service,
        dom_orchestrator_service
    )

def get_feedback_service(
    feedback_repo: Annotated[FeedbackRepository, Depends(get_feedback_repository)]
) -> FeedbackService:
    """
    FeedbackServiceの依存性注入を提供します。
    """
    return FeedbackService(feedback_repo)





