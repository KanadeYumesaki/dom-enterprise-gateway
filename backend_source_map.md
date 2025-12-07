# backend ソースコード完全ガイド（自動生成版）

- 生成日: 2025-12-07  
- 生成ツール: OpenAI Codex (GPT-5 系)  
- 目的: `backend/` 配下の Python ファイルとそのクラス・関数・メソッドの役割/引数/戻り値/使い方を、抜け漏れなく日本語で整理。インポートしている主要ライブラリの初心者向け説明も付与。既存コードは一切変更していません（非破壊）。

---

## 使い方
- 調べたいファイル名で検索し、クラス/関数の概要・引数・戻り値・利用例を確認する。
- ライブラリの簡単な解説は文末「使用ライブラリまとめ」を参照。
- ここにない挙動はテストコードセクションを併読することで把握できます。

---

## アプリケーション本体 (`app/`)

### `app/main.py`
#### 使用ライブラリ（import）
- `fastapi.FastAPI`
- `app.api.endpoints`（auth, chat, files, admin, feedback, user_settings, help）
- `app.core.config.settings`
- **app: FastAPI** – タイトルと OpenAPI パスを設定し、各エンドポイント用ルーターを登録。  
- **read_root() -> dict** – ルート `/` で「Welcome to the DOM Enterprise Gateway」を返す簡易ヘルスチェック。

### `app/dependencies.py`
#### 使用ライブラリ（import）
- 標準: `typing.Annotated`, `typing.Optional`
- サードパーティ: `fastapi.Depends`, `fastapi.HTTPException`, `fastapi.status`, `fastapi.security.OAuth2PasswordBearer`, `sqlalchemy.ext.asyncio.AsyncSession`
- プロジェクト内: `app.core.database.get_db_session`, `app.repositories.*`, `app.schemas.auth.AuthenticatedUser`, `app.services.*`, `app.llm.mock_llm.MockLLMClient`

依存性注入ヘルパー。全て FastAPI `Depends` で利用。
- **get_system_tenant_repository(session: AsyncSession) -> TenantRepository** – テナント制限なしのリポジトリ。
- **get_system_user_repository(session) -> UserRepository** – テナント制限なしのユーザーリポジトリ。
- **get_auth_service(user_repo, tenant_repo) -> AuthService** – 認証サービス生成。
- **get_current_user(token, auth_service) -> AuthenticatedUser** – OAuth2 Bearer トークンを検証しアクティブユーザーを返す。失敗時 401。
- **get_current_admin_user(current_user) -> AuthenticatedUser** – is_admin チェック。失敗時 403。
- **get_tenant_repository(session, current_user) -> TenantRepository** – 現在のテナントでフィルタするリポジトリ。
- **get_user_repository(session, current_user) -> UserRepository** – 同上ユーザー版。
- **get_chat_session_repository(session, current_user) -> ChatSessionRepository**
- **get_chat_message_repository(session, current_user) -> ChatMessageRepository**
- **get_knowledge_document_repository(session, current_user) -> KnowledgeDocumentRepository**
- **get_structured_memory_repository(session, current_user) -> StructuredMemoryRepository**
- **get_episodic_memory_repository(session, current_user) -> EpisodicMemoryRepository**
- **get_feedback_repository(session, current_user) -> FeedbackRepository**
- **get_mock_llm_client() -> MockLLMClient** – モック LLM クライアントを提供。
- **get_answer_composer_service() -> AnswerComposerService**
- **get_rag_service(current_user, llm_client) -> RagService** – テナント別の RAG サービス。
- **get_file_service() -> FileService**
- **get_dom_orchestrator_service(llm_client, answer_composer, rag_service) -> DomOrchestratorService**
- **get_memory_service(structured_repo, episodic_repo) -> MemoryService**
- **get_chat_service(chat_session_repo, chat_message_repo, memory_service, dom_orchestrator) -> ChatService**
- **get_feedback_service(feedback_repo) -> FeedbackService**

### `app/core/config.py`
#### 使用ライブラリ（import）
- 標準: `typing.List`
- サードパーティ: `pydantic_settings.BaseSettings`, `pydantic_settings.SettingsConfigDict`
- **Settings(BaseSettings)** – `.env` や環境変数から読み込む全体設定クラス。プロジェクト名、API ベースパス、DB URL、Redis、OIDC 情報、初期管理者メール、アップロード設定などを保持。  
- **settings = Settings()** – シングルトンインスタンス。

### `app/core/database.py`
#### 使用ライブラリ（import）
- サードパーティ: `sqlalchemy.ext.asyncio.create_async_engine`, `sqlalchemy.ext.asyncio.AsyncSession`, `sqlalchemy.orm.sessionmaker`, `sqlalchemy.ext.declarative.declared_attr`, `sqlalchemy.orm.DeclarativeBase`, `sqlalchemy.String`
- プロジェクト内: `app.core.config.settings`
- **Base(DeclarativeBase)** – SQLAlchemy モデル共通基底。テーブル名を `t_<snake_case>` に自動変換。  
- **engine = create_async_engine(DATABASE_URL, echo=True)** – 非同期エンジン。  
- **AsyncSessionLocal = sessionmaker(...)** – 非同期セッションファクトリ。  
- **get_db_session() -> AsyncGenerator[AsyncSession]** – FastAPI 依存性でセッションを yield。

---

## スキーマ (`app/schemas/`)

- **auth.py**  
  - #### 使用ライブラリ（import）
    - 標準: `uuid.UUID`
    - サードパーティ: `pydantic.BaseModel`, `pydantic.EmailStr`
  - `AuthenticatedUser(BaseModel)` – id, tenant_id, email, is_active, is_admin を持つ認証済みユーザー表現。

- **chat.py**  
  - #### 使用ライブラリ（import）
    - 標準: `uuid.UUID`, `datetime.datetime`
    - サードパーティ: `pydantic.BaseModel`, `pydantic.Field`
  - `ChatMessageCreate(session_id: UUID, content: str, role: str)` – 送信メッセージ用リクエスト。  
  - `ChatMessageResponse` – メッセージのレスポンス表現。  
  - `ChatSessionCreate(title: str|None)` – セッション作成リクエスト。  
  - `ChatSessionResponse` – セッションのレスポンス表現。

- **file.py**  
  - #### 使用ライブラリ（import）
    - 標準: `uuid.UUID`, `datetime.datetime`
    - サードパーティ: `pydantic.BaseModel`, `pydantic.Field`
  - `FileUploadResponse` – アップロード結果のメタ情報（id, path, type, size など）。

- **help.py**  
  - #### 使用ライブラリ（import）
    - 標準: `typing.Literal`
    - サードパーティ: `pydantic.BaseModel`
  - `HelpSection` – ヘルプの 1 セクション。id/title/content/order/category を保持。

- **user_settings.py**  
  - #### 使用ライブラリ（import）
    - 標準: `uuid.UUID`, `datetime.datetime`, `typing.Literal`
    - サードパーティ: `pydantic.BaseModel`
  - `UserSettingsBase` – theme/language/font_size/llm_profile/onboarding 状態の共通部分。  
  - `UserSettingsRead` – id・tenant_id・user_id・タイムスタンプを加えたレスポンス用。  
  - `UserSettingsUpdate` – すべて Optional で部分更新を想定したリクエスト用。

- **feedback.py**  
  - #### 使用ライブラリ（import）
    - 標準: `uuid.UUID`, `typing.Optional`, `datetime.datetime`
    - サードパーティ: `pydantic.BaseModel`, `pydantic.Field`
  - `FeedbackCreate(session_id?, message_id?, rating, comment?)` – 評価投稿リクエスト。  
  - `FeedbackResponse` – 保存済みフィードバックのレスポンス。

---

## モデル (`app/models/`)

- **tenant.py – Tenant**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `sqlalchemy` の Column/型, `sqlalchemy.dialects.postgresql.UUID`, `sqlalchemy.sql.func`
    - 標準: `uuid.uuid4`
    - プロジェクト内: `app.core.database.Base`
  テナント情報。name, is_active, created_at, updated_at。

- **user.py – User**  
  - #### 使用ライブラリ（import）
    - サードパーティ: Column/型, `sqlalchemy.orm.relationship`, `sqlalchemy.dialects.postgresql.UUID`, `sqlalchemy.sql.func`
    - 標準: `uuid.uuid4`
    - プロジェクト内: `app.core.database.Base`, `app.models.tenant.Tenant`
  tenant_id, email, hashed_password, is_active, is_admin、作成更新日時。Tenant とのリレーション。

- **chat.py – ChatSession / ChatMessage**  
  - #### 使用ライブラリ（import）
    - サードパーティ: Column/型, `sqlalchemy.orm.relationship`, `sqlalchemy.dialects.postgresql.UUID`, `sqlalchemy.sql.func`
    - 標準: `uuid.uuid4`
    - プロジェクト内: `app.core.database.Base`, `app.models.user.User`, `app.models.tenant.Tenant`
  - ChatSession: user_id, tenant_id, title, is_active など。messages リレーション。  
  - ChatMessage: session_id, role(user/assistant/system), content, raw_llm_response(JSON)。

- **knowledge.py – KnowledgeDocument**  
  - #### 使用ライブラリ（import）
    - サードパーティ: Column/型, `sqlalchemy.dialects.postgresql.UUID`, `sqlalchemy.sql.func`
    - 標準: `uuid.uuid4`
    - プロジェクト内: `app.core.database.Base`
  アップロードファイルのメタ情報（file_name/path/type/size、アップロードユーザーなど）。

- **memory.py – StructuredMemory / EpisodicMemory**  
  - #### 使用ライブラリ（import）
    - サードパーティ: Column/型, `sqlalchemy.dialects.postgresql.UUID`, `sqlalchemy.sql.func`
    - 標準: `uuid.uuid4`
    - プロジェクト内: `app.core.database.Base`
  - StructuredMemory: key/value(JSON) で構造化設定やプロファイルを保存。  
  - EpisodicMemory: セッションごとの要約・決定・前提を保存。

- **feedback.py – Feedback**  
  - #### 使用ライブラリ（import）
    - サードパーティ: Column/型, `sqlalchemy.dialects.postgresql.UUID`, `sqlalchemy.sql.func`
    - 標準: `uuid.uuid4`
    - プロジェクト内: `app.core.database.Base`
  session_id/message_id と紐づく rating(-1/0/1) とコメント。

- **user_settings.py – UserSettings**  
  - #### 使用ライブラリ（import）
    - サードパーティ: Column/型, `sqlalchemy.dialects.postgresql.UUID`, `sqlalchemy.sql.func`, `sqlalchemy.orm.relationship`, `sqlalchemy.UniqueConstraint`
    - 標準: `uuid.uuid4`
    - プロジェクト内: `app.core.database.Base`
  (tenant_id, user_id) ユニーク制約。UI 設定やオンボーディング状態を保持。

---

## リポジトリ層 (`app/repositories/`)

- **base.py – BaseRepository**  
  - #### 使用ライブラリ（import）
    - 標準: `typing` (Generic/TypeVar/Type/List/Optional), `uuid.UUID`
    - サードパーティ: `sqlalchemy.select`, `sqlalchemy.update`, `sqlalchemy.delete`, `sqlalchemy.ext.asyncio.AsyncSession`
    - プロジェクト内: `app.core.database.Base`
  共通 CRUD（get, get_multi, create, update, delete）を提供。tenant_id があればクエリに自動付与。

- **tenant.py – TenantRepository**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `sqlalchemy.ext.asyncio.AsyncSession`
    - プロジェクト内: `app.models.tenant.Tenant`, `app.repositories.base.BaseRepository`
    - 標準: `uuid.UUID`, `typing.Optional`
  `get_by_name(name)` – テナント名で取得。

- **user.py – UserRepository**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `sqlalchemy.ext.asyncio.AsyncSession`
    - プロジェクト内: `app.models.user.User`, `app.repositories.base.BaseRepository`
    - 標準: `uuid.UUID`, `typing.Optional`（関数内で `sqlalchemy.select`）
  `get_by_email(email)` – メールで検索（tenant フィルタ対応）。

- **chat.py – ChatSessionRepository / ChatMessageRepository**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `sqlalchemy.ext.asyncio.AsyncSession`
    - プロジェクト内: `app.models.chat.ChatSession`, `ChatMessage`, `app.repositories.base.BaseRepository`
    - 標準: `uuid.UUID`, `typing.List`, `typing.Optional`（関数内で `sqlalchemy.select`）
  - `get_by_user_id(user_id)` – ユーザーのセッション一覧。  
  - `get_by_session_id(session_id)` – セッション内メッセージ取得（作成日時順）。

- **knowledge.py – KnowledgeDocumentRepository**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `sqlalchemy.ext.asyncio.AsyncSession`
    - プロジェクト内: `app.models.knowledge.KnowledgeDocument`, `app.repositories.base.BaseRepository`
    - 標準: `uuid.UUID`, `typing.Optional`, `typing.List`（関数内で `sqlalchemy.select`）
  - `get_by_filepath(path)` – パスで一意取得。  
  - `search(query?, skip=0, limit=100)` – ファイル名部分一致検索。

- **memory.py – StructuredMemoryRepository / EpisodicMemoryRepository**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `sqlalchemy.ext.asyncio.AsyncSession`
    - プロジェクト内: `app.models.memory.StructuredMemory`, `EpisodicMemory`, `app.repositories.base.BaseRepository`
    - 標準: `uuid.UUID`, `typing.Optional`, `typing.List`（関数内で `sqlalchemy.select`）
  - `get_by_key(key, user_id?)` – 構造化メモリをキーで検索。  
  - `get_by_session_id(session_id)` / `get_all_by_user_id(user_id)` – エピソード記憶取得。

- **feedback.py – FeedbackRepository**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `sqlalchemy.ext.asyncio.AsyncSession`
    - プロジェクト内: `app.models.feedback.Feedback`, `app.repositories.base.BaseRepository`
    - 標準: `uuid.UUID`, `typing.Optional`, `typing.List`（関数内で `sqlalchemy.select`）
  - `get_by_session_id(session_id)` – セッション単位で一覧。  
  - `get_by_message_id(message_id)` – メッセージ単位で 1 件。

- **user_settings.py – UserSettingsRepository**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `sqlalchemy.ext.asyncio.AsyncSession`, `sqlalchemy.select`, `sqlalchemy.update`
    - プロジェクト内: `app.models.user_settings.UserSettings`, `app.repositories.base.BaseRepository`
    - 標準: `uuid.UUID`, `typing.Optional`
  - `get_by_user(tenant_id, user_id)` – (tenant, user) で取得。  
  - `upsert(tenant_id, user_id, data)` – 存在すれば部分 UPDATE、無ければ INSERT。

---

## サービス層 (`app/services/`)

- **auth.py – AuthService**  
  - #### 使用ライブラリ（import）
    - 標準: `typing.Optional`, `logging`, `uuid.UUID`
    - サードパーティ: `fastapi` (Depends/HTTPException/status), `starlette.requests.Request`, `authlib` (OAuth/JWK/JWT), `jose.jwt`, `httpx`
    - プロジェクト内: `app.core.config.settings`, `app.schemas.auth.AuthenticatedUser`, `app.repositories.user.UserRepository`, `app.repositories.tenant.TenantRepository`
  - `get_jwks_uri()` – OIDC の well-known から JWKS URI を取得。  
  - `get_jwks_client()` – JWKS を取得して公開鍵セットを準備。  
  - `verify_id_token(token) -> AuthenticatedUser` – ID トークンを検証しユーザーを作成/取得、管理者判定も実施。

- **chat_service.py – ChatService**  
  - #### 使用ライブラリ（import）
    - 標準: `uuid.UUID`, `typing.List`, `typing.Optional`
    - プロジェクト内: `app.repositories.chat.*`, `app.services.memory_service.MemoryService`, `app.services.dom_orchestrator.DomOrchestratorService`, `app.models.chat.*`, `app.schemas.chat.ChatSessionResponse`
  - `reset_session(session_id, user_id, tenant_id) -> ChatSessionResponse` – 会話履歴を要約→エピソード記憶に保存→旧セッションを非アクティブ化→新セッションを作成。

- **dom_orchestrator.py – DomOrchestratorService**  
  - #### 使用ライブラリ（import）
    - 標準: `typing.AsyncGenerator`, `typing.List`, `uuid.UUID`, `json`
    - プロジェクト内: `app.llm.mock_llm.MockLLMClient`, `app.services.answer_composer.AnswerComposerService`, `app.services.rag_service.RagService`, `app.models.chat.ChatMessage`
  - `process_chat_message(user_message, session_id, is_research_mode=False) -> AsyncGenerator[str]` – 必要に応じ RAG コンテキストを付与し LLM へ送信、IC-5 ライト形式でトークンストリームを返す。  
  - `summarize_chat_history(messages: List[ChatMessage]) -> str` – 会話履歴を LLM に要約させ文字列返却。

- **rag_service.py – RagService**  
  - #### 使用ライブラリ（import）
    - 標準: `typing.List`, `typing.AsyncGenerator`, `typing.Optional`, `uuid.UUID`
    - サードパーティ: `langchain_core.documents.Document`, `langchain_core.output_parsers.StrOutputParser`, `langchain_core.prompts.ChatPromptTemplate`, `langchain_core.runnables.RunnablePassthrough`, `RunnableLambda`, `langchain_core.retrievers.BaseRetriever`, `langchain_postgres.vectorstores.PGVector`, `langchain_google_genai.ChatGoogleGenerativeAI`, `GoogleGenerativeAIEmbeddings`
    - プロジェクト内: `app.core.config.settings`, `app.llm.mock_llm.MockLLMClient`
  - 初期化でテナント別 PGVector を準備し Embedding/LLM を構築。  
  - `add_documents_to_global_rag(documents)` / `add_documents_to_ephemeral_rag(session_id, documents)` – ベクトルストアへ追加。  
  - `query_rag(question, session_id?) -> str` – LCEL で RAG チェーンを実行し回答文字列を返す。  
  - `stream_rag_response(question, session_id?) -> AsyncGenerator[str]` – RAG 応答をストリーミング。

- **answer_composer.py – AnswerComposerService**  
  - #### 使用ライブラリ（import）
    - 標準: `typing.Dict`, `typing.AsyncGenerator`, `re`
  - `compose_ic5_light_response(raw_llm_output) -> dict` – “Decision/Why/Next 3 Actions” の各セクションを正規表現で抽出。  
  - `stream_composed_ic5_light_response(raw_llm_token_stream)` – ストリームを受け取り逐次流す（PoC）。

- **file_service.py – FileService**  
  - #### 使用ライブラリ（import）
    - 標準: `os`, `pathlib.Path`, `typing.BinaryIO`, `typing.Optional`, `uuid.UUID`, `mimetypes`
    - サードパーティ: `fastapi.UploadFile`, `fastapi.HTTPException`, `fastapi.status`, `langchain_core.documents.Document`
    - プロジェクト内: `app.core.config.settings`, `app.models.knowledge.KnowledgeDocument`
  - `validate_file(file)` – サイズと拡張子をチェック。  
  - `save_file(file, tenant_id, user_id) -> KnowledgeDocument` – ストレージへ保存しメタ情報を返す。  
  - `extract_text_from_knowledge_document(doc) -> str` – 拡張子に応じてテキスト抽出（現状プレースホルダ）。  
  - `delete_file_from_storage(path)` – ファイル削除。

- **memory_service.py – MemoryService**  
  - #### 使用ライブラリ（import）
    - 標準: `uuid.UUID`, `typing.Optional`, `typing.List`, `typing.Dict`, `typing.Any`
    - プロジェクト内: `app.repositories.memory.StructuredMemoryRepository`, `EpisodicMemoryRepository`, `app.models.memory.StructuredMemory`, `EpisodicMemory`, `app.schemas.auth.AuthenticatedUser`
  - 構造化/エピソード記憶それぞれの create/get/update/delete をラップし、リポジトリを呼び出す。

- **feedback_service.py – FeedbackService**  
  - #### 使用ライブラリ（import）
    - 標準: `uuid.UUID`, `typing.Optional`, `typing.List`
    - プロジェクト内: `app.repositories.feedback.FeedbackRepository`, `app.models.feedback.Feedback`, `app.schemas.feedback.FeedbackCreate`
  - `create_feedback(user_id, tenant_id, feedback_in)` – フィードバック保存。  
  - `get_feedback_by_session_id(session_id)` / `get_feedback_by_message_id(message_id)`。

- **help.py – HelpService**  
  - #### 使用ライブラリ（import）
    - 標準: `typing.Literal`
    - プロジェクト内: `app.schemas.help.HelpSection`
  - 静的な HELP_SECTIONS_DATA を Pydantic 化。  
  - `list_sections(category)` – user/admin/all でフィルタし order ソート。  
  - `get_section(section_id)` – ID で 1 件取得。  
  - `get_help_service()` – DI 用ファクトリ。

- **user_settings.py – UserSettingsService**  
  - #### 使用ライブラリ（import）
    - 標準: `typing.Annotated`, `uuid.UUID`
    - サードパーティ: `fastapi.Depends`, `sqlalchemy.ext.asyncio.AsyncSession`
    - プロジェクト内: `app.core.database.get_db`, `app.schemas.auth.AuthenticatedUser`, `app.schemas.user_settings.UserSettingsRead`, `UserSettingsUpdate`, `UserSettingsBase`, `app.repositories.user_settings.UserSettingsRepository`
  - `get_or_default(user) -> UserSettingsRead` – DB に無ければデフォルト値を返す（保存はしない）。  
  - `update(user, payload) -> UserSettingsRead` – `exclude_unset=True` で部分更新し upsert。  
  - `get_user_settings_service(...)` – DI 用ファクトリ。

- **llm/mock_llm.py – MockLLMClient**  
  - #### 使用ライブラリ（import）
    - 標準: `typing.AsyncGenerator`, `asyncio`
  - `stream_chat_response(prompt) -> AsyncGenerator[str]` – IC-5 形式のダミー応答を単語ごとに送る。

---

## API エンドポイント (`app/api/endpoints/`)

- **auth.py**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `fastapi.APIRouter`, `fastapi.Depends`, `fastapi.HTTPException`, `fastapi.status`
    - 標準: `typing.Annotated`
    - プロジェクト内: `app.schemas.auth.AuthenticatedUser`, `app.services.auth.AuthService`, `app.dependencies.get_auth_service`, `get_current_user`
  - `read_current_user()` – `/api/v1/auth/me` で現在の認証ユーザーを返す。

- **chat.py**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `fastapi.APIRouter`, `fastapi.Depends`, `fastapi.HTTPException`, `fastapi.status`, `fastapi.responses.StreamingResponse`
    - 標準: `typing.Annotated`, `typing.List`, `typing.AsyncGenerator`, `uuid.UUID`
    - プロジェクト内: `app.schemas.chat.*`, `app.schemas.auth.AuthenticatedUser`, `app.dependencies` (get_current_user / get_chat_session_repository / get_chat_message_repository / get_dom_orchestrator_service / get_chat_service), `app.repositories.chat.*`, `app.services.dom_orchestrator.DomOrchestratorService`, `app.services.chat_service.ChatService`
  - `create_chat_session(session_in, current_user, chat_session_repo)` – セッション作成。  
  - `get_chat_sessions(current_user, chat_session_repo)` – ログインユーザーのセッション一覧。  
  - `send_chat_message(message_in, current_user, chat_session_repo, chat_message_repo)` – ユーザーメッセージ保存。  
  - `stream_chat_response(session_id, current_user, ..., research_mode=False)` – LLM 応答を SSE で配信。  
  - `reset_chat_session(session_id, current_user, chat_service)` – セッションをリセットし新規セッションを返す。

- **files.py**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `fastapi.APIRouter`, `fastapi.Depends`, `fastapi.UploadFile`, `fastapi.File`, `fastapi.HTTPException`, `fastapi.status`
    - 標準: `typing.Annotated`, `typing.List`, `typing.Optional`, `uuid.UUID`
    - プロジェクト内: `app.schemas.file.FileUploadResponse`, `app.schemas.auth.AuthenticatedUser`, `app.dependencies` (get_current_user / get_knowledge_document_repository / get_file_service / get_rag_service), `app.repositories.knowledge.KnowledgeDocumentRepository`, `app.services.file_service.FileService`, `app.services.rag_service.RagService`
  - `upload_file(file, current_user, file_service, knowledge_repo, rag_service, session_id?)` – 保存・テキスト抽出・RAG への登録・DB 保存を実施しメタ情報を返す。

- **admin.py**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `fastapi.APIRouter`, `fastapi.Depends`, `fastapi.HTTPException`, `fastapi.status`
    - 標準: `typing.Annotated`, `typing.List`, `typing.Optional`, `uuid.UUID`
    - プロジェクト内: `app.schemas.auth.AuthenticatedUser`, `app.schemas.file.FileUploadResponse`, `app.dependencies.get_current_user`, `get_current_admin_user`, `app.dependencies.get_knowledge_document_repository`, `app.repositories.knowledge.KnowledgeDocumentRepository`
  - `list_knowledge_documents(current_admin_user, knowledge_repo, skip=0, limit=100, search_query?)` – 管理者専用、ナレッジ文書の一覧/検索。

- **feedback.py**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `fastapi.APIRouter`, `fastapi.Depends`, `fastapi.HTTPException`, `fastapi.status`
    - 標準: `typing.Annotated`, `typing.List`, `typing.Optional`, `uuid.UUID`
    - プロジェクト内: `app.schemas.auth.AuthenticatedUser`, `app.schemas.feedback.FeedbackCreate`, `FeedbackResponse`, `app.dependencies.get_current_user`, `get_feedback_service`, `app.services.feedback_service.FeedbackService`
  - `submit_feedback(feedback_in, current_user, feedback_service)` – フィードバック投稿。  
  - `get_feedback_for_session(session_id, current_user, feedback_service)` – セッション別フィードバック取得（本人・同テナントのみ返却）。  
  - `get_feedback_for_message(message_id, current_user, feedback_service)` – メッセージ別フィードバック取得。

- **help.py**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `fastapi.APIRouter`, `fastapi.Depends`, `fastapi.HTTPException`, `fastapi.status`, `fastapi.Query`
    - 標準: `typing.Annotated`, `typing.Literal`
    - プロジェクト内: `app.dependencies.get_current_user`, `app.schemas.auth.AuthenticatedUser`, `app.schemas.help.HelpSection`, `app.services.help.HelpService`, `get_help_service`
  - `get_help_content(current_user, help_service, section_id?, category="user")` – section_id があれば 1 件、無ければカテゴリ別リスト。

- **user_settings.py**  
  - #### 使用ライブラリ（import）
    - サードパーティ: `fastapi.APIRouter`, `fastapi.Depends`, `fastapi.HTTPException`, `fastapi.status`, `sqlalchemy.ext.asyncio.AsyncSession`
    - 標準: `typing.Annotated`
    - プロジェクト内: `app.core.database.get_db_session`, `app.dependencies.get_current_user`, `app.schemas.auth.AuthenticatedUser`, `app.schemas.user_settings.UserSettingsRead`, `UserSettingsUpdate`, `app.services.user_settings.UserSettingsService`
  - `get_user_settings(current_user, db)` – 現在ユーザーの設定取得（無ければデフォルト）。  
  - `update_user_settings(payload, current_user, db)` – 設定の部分更新。

---

## マイグレーション (`alembic/versions/001_add_user_settings.py`)
#### 使用ライブラリ（import）
- 標準: `typing.Sequence`, `typing.Union`
- サードパーティ: `alembic.op`, `sqlalchemy as sa`, `sqlalchemy.dialects.postgresql`
- **upgrade()** – `t_user_settings` テーブル作成・インデックス付与。  
- **downgrade()** – 上記テーブルとインデックスを削除。

---

## ユーティリティ
- **check_import.py** – `app.services.auth` などのインポート可否を確認する簡易スクリプト（実行で Import 成否を表示）。
  - #### 使用ライブラリ（import）
    - 標準: `sys`
    - プロジェクト内: `app.services.auth`, `app.repositories.user`, `app.repositories.tenant`

---

## テストコード概要 (`app/tests/`)
フィクスチャは依存モックを準備し、各サービス/エンドポイント/リポジトリ/LLM 連携の振る舞いを検証。

- **conftest.py** – テスト用環境変数を設定し、FastAPI の multipart チェックをモック。  
  - #### 使用ライブラリ（import）
    - 標準: `os`
    - サードパーティ: `pytest`
    - プロジェクト内: `fastapi.dependencies.utils` (MagicMock 差し替え)
- **test_main.py** – ルート `/` が 200 と固定レスポンスを返すか検証。  
  - #### 使用ライブラリ（import）
    - サードパーティ: `fastapi.testclient.TestClient`
    - プロジェクト内: `app.main.app`
- **test_endpoints_auth.py** – `/api/v1/auth/me` の成功/未認証/非アクティブ、`get_current_admin_user` の権限チェック。  
  フィクスチャ: `mock_auth_service`, `override_get_auth_service`, `mock_authenticated_user`, `override_get_current_user`。  
  - #### 使用ライブラリ（import）
    - サードパーティ: `pytest`, `fastapi.testclient.TestClient`, `fastapi.HTTPException`
    - 標準: `unittest.mock`, `uuid`
    - プロジェクト内: `app.main`, `app.schemas.auth`, `app.services.auth`, `app.dependencies`
- **test_endpoints_chat.py** – セッション作成・一覧・送信・ストリーム配信（research_mode on/off）・権限エラーを検証。  
  フィクスチャ: `mock_current_user` ほかチャット/LLM関連モック。  
  - #### 使用ライブラリ（import）
    - サードパーティ: `pytest`, `fastapi.testclient.TestClient`
    - 標準: `unittest.mock`, `uuid`, `datetime`, `json`
    - プロジェクト内: `app.main`, `app.schemas.chat`, `app.schemas.auth`, `app.repositories.chat`, `app.services.dom_orchestrator`, `app.dependencies`
- **test_endpoints_files.py** – ファイルアップロード（グローバル/Ephemeral RAG）、ファイル名なし、バリデーションエラーを検証。  
  - #### 使用ライブラリ（import）
    - サードパーティ: `pytest`, `fastapi.testclient.TestClient`, `fastapi.HTTPException`
    - 標準: `unittest.mock`, `uuid`, `io.BytesIO`, `datetime`
    - プロジェクト内: `app.main`, `app.schemas`, `app.repositories.knowledge`, `app.services.file_service`, `app.services.rag_service`, `app.dependencies`, `app.core.config.settings`
- **test_endpoints_admin.py** – 管理者向けナレッジ一覧の成功/検索/非管理者エラー。  
  - #### 使用ライブラリ（import）
    - サードパーティ: `pytest`, `fastapi.testclient.TestClient`
    - 標準: `unittest.mock`, `uuid`, `datetime`
    - プロジェクト内: `app.main`, `app.schemas.auth`, `app.schemas.file`, `app.dependencies`, `app.repositories.knowledge`
- **test_endpoints_feedback.py** – フィードバック投稿・セッション別取得・メッセージ別取得・権限なしケース。  
  - #### 使用ライブラリ（import）
    - サードパーティ: `pytest`, `fastapi.testclient.TestClient`, `fastapi.encoders.jsonable_encoder`
    - 標準: `unittest.mock`, `uuid`, `datetime`
    - プロジェクト内: `app.main`, `app.schemas.auth`, `app.schemas.feedback`, `app.dependencies`, `app.services.feedback_service`
- **test_user_settings.py** – デフォルト返却、初回 upsert、部分更新保持、既存取得。  
  - #### 使用ライブラリ（import）
    - サードパーティ: `pytest`
    - 標準: `uuid`
    - プロジェクト内: `app.schemas.user_settings`, `app.services.user_settings`, `app.schemas.auth`
- **test_memory_service.py** – MemoryService の create/get/update/delete をモックリポジトリで検証。  
  - #### 使用ライブラリ（import）
    - サードパーティ: `pytest`
    - 標準: `unittest.mock`, `uuid`, `datetime`
    - プロジェクト内: `app.services.memory_service`, `app.repositories.memory`, `app.models.memory`, `app.schemas.auth`
- **test_chat_service.py** – セッションリセット成功/未検出/要約保存失敗時の挙動を確認。  
  - #### 使用ライブラリ（import）
    - サードパーティ: `pytest`
    - 標準: `unittest.mock`, `uuid`, `datetime`
    - プロジェクト内: `app.services.chat_service`, `app.repositories.chat`, `app.services.memory_service`, `app.services.dom_orchestrator`, `app.models.chat`, `app.schemas.auth`, `app.schemas.chat`
- **test_dom_orchestrator_service.py** – IC-5 形式ストリーミング、RAG あり/なしの研究モード、警告メッセージを検証。  
  - #### 使用ライブラリ（import）
    - サードパーティ: `pytest`
    - 標準: `unittest.mock`, `typing.AsyncGenerator`, `uuid`
    - プロジェクト内: `app.services.dom_orchestrator`, `app.llm.mock_llm`, `app.services.answer_composer`, `app.services.rag_service`
- **test_rag_service.py** – RagService 初期化、query/add_documents、（一部ストリームは skip マーク）。  
  - #### 使用ライブラリ（import）
    - サードパーティ: `pytest`, `unittest.mock`, `langchain_core.documents.Document`, `langchain_core.messages.AIMessageChunk`, `langchain_core.prompts.ChatPromptTemplate`, `langchain_core.runnables.RunnablePassthrough`, `langchain_postgres.vectorstores.PGVector`, `langchain_google_genai.*`
    - 標準: `uuid`
    - プロジェクト内: `app.services.rag_service`, `app.llm.mock_llm`, `app.core.config.settings`
- **test_auth_service.py** – JWKS 取得成功/失敗、OIDC 設定なしエラー、トークン検証で新規/既存ユーザー、管理者判定。  
  - #### 使用ライブラリ（import）
    - サードパーティ: `pytest`, `unittest.mock`, `jose.jwt`
    - 標準: `uuid`
    - プロジェクト内: `app.services.auth`, `app.schemas.auth`, `app.repositories.user`, `app.repositories.tenant`, `app.models.tenant`, `app.models.user`, `app.core.config.settings`
- **test_repositories.py** – BaseRepository テナントフィルタ、create の自動 tenant_id 付与、Tenant/User 専用メソッドを検証。  
  - #### 使用ライブラリ（import）
    - サードパーティ: `pytest`, `unittest.mock`, `sqlalchemy.ext.asyncio.AsyncSession`, `sqlalchemy.select`
    - 標準: `uuid`
    - プロジェクト内: `app.repositories.base`, `app.repositories.tenant`, `app.repositories.user`, `app.models.tenant`, `app.models.user`, `app.core.database.Base`
- **test_help.py** – HelpService のカテゴリ別一覧、単一取得、必須フィールド確認。
  - #### 使用ライブラリ（import）
    - サードパーティ: `pytest`
    - プロジェクト内: `app.services.help.HelpService`, `app.schemas.help.HelpSection`

---

## 使用ライブラリまとめ（初心者向け）
- **FastAPI / Starlette** – Python 製の高速 Web API フレームワーク。`APIRouter` でルート定義、`Depends` で依存注入、`StreamingResponse` でストリーミング応答を実装。  
- **SQLAlchemy (async)** – 非同期データベース ORM。`DeclarativeBase` でモデル定義し、`AsyncSession` で CRUD を行う。  
- **Pydantic / pydantic_settings** – 入力・設定値の型検証。`BaseModel` でスキーマ、`BaseSettings` で環境変数読み込み。  
- **Authlib / python-jose** – OIDC/JWT の署名検証。`JsonWebToken.decode` で ID トークンを検証し、`jwk.import_key_set` で公開鍵セットを扱う。  
- **httpx** – 非同期 HTTP クライアント。外部の OIDC well-known / JWKS 取得に使用。  
- **langchain_core / langchain_postgres / langchain_google_genai** – RAG パイプライン用。`PGVector` でベクトルストア、`ChatGoogleGenerativeAI` で LLM、`GoogleGenerativeAIEmbeddings` でベクトル化。  
- **fastapi.security.OAuth2PasswordBearer** – Authorization ヘッダーの Bearer トークン抽出に使用。  
- **uuid / datetime / typing / pathlib / mimetypes / os** – 標準ライブラリ。ID 生成、日時、型ヒント、ファイル操作、MIME 推定など。  
- **pytest / unittest.mock / fastapi.testclient** – テスト実行と依存モック化、API クライアントシミュレーション。

---

## 安全利用上の注意
- .env や実際の秘密情報はこのリポジトリに含めないでください。  
- RAG/LLM 部分はダミー実装が多く、本番利用時は鍵管理・タイムアウト・リトライ・バリデーションを強化してください。  
- ファイルアップロードはサイズ/拡張子のみ簡易チェックなので、ウイルススキャンや MIME 厳格判定を追加することを推奨します。

---

## 生成メタ情報
- 生成日: 2025-12-07 (米国時間想定)  
- モデル: OpenAI GPT-5 (Codex CLI)  
- 依頼内容: 既存コード非破壊での完全日本語リファレンス作成
