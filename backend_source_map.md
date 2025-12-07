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
- **app: FastAPI** – タイトルと OpenAPI パスを設定し、各エンドポイント用ルーターを登録。  
- **read_root() -> dict** – ルート `/` で「Welcome to the DOM Enterprise Gateway」を返す簡易ヘルスチェック。

### `app/dependencies.py`
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
- **Settings(BaseSettings)** – `.env` や環境変数から読み込む全体設定クラス。プロジェクト名、API ベースパス、DB URL、Redis、OIDC 情報、初期管理者メール、アップロード設定などを保持。  
- **settings = Settings()** – シングルトンインスタンス。

### `app/core/database.py`
- **Base(DeclarativeBase)** – SQLAlchemy モデル共通基底。テーブル名を `t_<snake_case>` に自動変換。  
- **engine = create_async_engine(DATABASE_URL, echo=True)** – 非同期エンジン。  
- **AsyncSessionLocal = sessionmaker(...)** – 非同期セッションファクトリ。  
- **get_db_session() -> AsyncGenerator[AsyncSession]** – FastAPI 依存性でセッションを yield。

---

## スキーマ (`app/schemas/`)

- **auth.py**  
  - `AuthenticatedUser(BaseModel)` – id, tenant_id, email, is_active, is_admin を持つ認証済みユーザー表現。

- **chat.py**  
  - `ChatMessageCreate(session_id: UUID, content: str, role: str)` – 送信メッセージ用リクエスト。  
  - `ChatMessageResponse` – メッセージのレスポンス表現。  
  - `ChatSessionCreate(title: str|None)` – セッション作成リクエスト。  
  - `ChatSessionResponse` – セッションのレスポンス表現。

- **file.py**  
  - `FileUploadResponse` – アップロード結果のメタ情報（id, path, type, size など）。

- **help.py**  
  - `HelpSection` – ヘルプの 1 セクション。id/title/content/order/category を保持。

- **user_settings.py**  
  - `UserSettingsBase` – theme/language/font_size/llm_profile/onboarding 状態の共通部分。  
  - `UserSettingsRead` – id・tenant_id・user_id・タイムスタンプを加えたレスポンス用。  
  - `UserSettingsUpdate` – すべて Optional で部分更新を想定したリクエスト用。

- **feedback.py**  
  - `FeedbackCreate(session_id?, message_id?, rating, comment?)` – 評価投稿リクエスト。  
  - `FeedbackResponse` – 保存済みフィードバックのレスポンス。

---

## モデル (`app/models/`)

- **tenant.py – Tenant**  
  テナント情報。name, is_active, created_at, updated_at。

- **user.py – User**  
  tenant_id, email, hashed_password, is_active, is_admin、作成更新日時。Tenant とのリレーション。

- **chat.py – ChatSession / ChatMessage**  
  - ChatSession: user_id, tenant_id, title, is_active など。messages リレーション。  
  - ChatMessage: session_id, role(user/assistant/system), content, raw_llm_response(JSON)。

- **knowledge.py – KnowledgeDocument**  
  アップロードファイルのメタ情報（file_name/path/type/size、アップロードユーザーなど）。

- **memory.py – StructuredMemory / EpisodicMemory**  
  - StructuredMemory: key/value(JSON) で構造化設定やプロファイルを保存。  
  - EpisodicMemory: セッションごとの要約・決定・前提を保存。

- **feedback.py – Feedback**  
  session_id/message_id と紐づく rating(-1/0/1) とコメント。

- **user_settings.py – UserSettings**  
  (tenant_id, user_id) ユニーク制約。UI 設定やオンボーディング状態を保持。

---

## リポジトリ層 (`app/repositories/`)

- **base.py – BaseRepository**  
  共通 CRUD（get, get_multi, create, update, delete）を提供。tenant_id があればクエリに自動付与。

- **tenant.py – TenantRepository**  
  `get_by_name(name)` – テナント名で取得。

- **user.py – UserRepository**  
  `get_by_email(email)` – メールで検索（tenant フィルタ対応）。

- **chat.py – ChatSessionRepository / ChatMessageRepository**  
  - `get_by_user_id(user_id)` – ユーザーのセッション一覧。  
  - `get_by_session_id(session_id)` – セッション内メッセージ取得（作成日時順）。

- **knowledge.py – KnowledgeDocumentRepository**  
  - `get_by_filepath(path)` – パスで一意取得。  
  - `search(query?, skip=0, limit=100)` – ファイル名部分一致検索。

- **memory.py – StructuredMemoryRepository / EpisodicMemoryRepository**  
  - `get_by_key(key, user_id?)` – 構造化メモリをキーで検索。  
  - `get_by_session_id(session_id)` / `get_all_by_user_id(user_id)` – エピソード記憶取得。

- **feedback.py – FeedbackRepository**  
  - `get_by_session_id(session_id)` – セッション単位で一覧。  
  - `get_by_message_id(message_id)` – メッセージ単位で 1 件。

- **user_settings.py – UserSettingsRepository**  
  - `get_by_user(tenant_id, user_id)` – (tenant, user) で取得。  
  - `upsert(tenant_id, user_id, data)` – 存在すれば部分 UPDATE、無ければ INSERT。

---

## サービス層 (`app/services/`)

- **auth.py – AuthService**  
  - `get_jwks_uri()` – OIDC の well-known から JWKS URI を取得。  
  - `get_jwks_client()` – JWKS を取得して公開鍵セットを準備。  
  - `verify_id_token(token) -> AuthenticatedUser` – ID トークンを検証しユーザーを作成/取得、管理者判定も実施。

- **chat_service.py – ChatService**  
  - `reset_session(session_id, user_id, tenant_id) -> ChatSessionResponse` – 会話履歴を要約→エピソード記憶に保存→旧セッションを非アクティブ化→新セッションを作成。

- **dom_orchestrator.py – DomOrchestratorService**  
  - `process_chat_message(user_message, session_id, is_research_mode=False) -> AsyncGenerator[str]` – 必要に応じ RAG コンテキストを付与し LLM へ送信、IC-5 ライト形式でトークンストリームを返す。  
  - `summarize_chat_history(messages: List[ChatMessage]) -> str` – 会話履歴を LLM に要約させ文字列返却。

- **rag_service.py – RagService**  
  - 初期化でテナント別 PGVector を準備し Embedding/LLM を構築。  
  - `add_documents_to_global_rag(documents)` / `add_documents_to_ephemeral_rag(session_id, documents)` – ベクトルストアへ追加。  
  - `query_rag(question, session_id?) -> str` – LCEL で RAG チェーンを実行し回答文字列を返す。  
  - `stream_rag_response(question, session_id?) -> AsyncGenerator[str]` – RAG 応答をストリーミング。

- **answer_composer.py – AnswerComposerService**  
  - `compose_ic5_light_response(raw_llm_output) -> dict` – “Decision/Why/Next 3 Actions” の各セクションを正規表現で抽出。  
  - `stream_composed_ic5_light_response(raw_llm_token_stream)` – ストリームを受け取り逐次流す（PoC）。

- **file_service.py – FileService**  
  - `validate_file(file)` – サイズと拡張子をチェック。  
  - `save_file(file, tenant_id, user_id) -> KnowledgeDocument` – ストレージへ保存しメタ情報を返す。  
  - `extract_text_from_knowledge_document(doc) -> str` – 拡張子に応じてテキスト抽出（現状プレースホルダ）。  
  - `delete_file_from_storage(path)` – ファイル削除。

- **memory_service.py – MemoryService**  
  - 構造化/エピソード記憶それぞれの create/get/update/delete をラップし、リポジトリを呼び出す。

- **feedback_service.py – FeedbackService**  
  - `create_feedback(user_id, tenant_id, feedback_in)` – フィードバック保存。  
  - `get_feedback_by_session_id(session_id)` / `get_feedback_by_message_id(message_id)`.

- **help.py – HelpService**  
  - 静的な HELP_SECTIONS_DATA を Pydantic 化。  
  - `list_sections(category)` – user/admin/all でフィルタし order ソート。  
  - `get_section(section_id)` – ID で 1 件取得。  
  - `get_help_service()` – DI 用ファクトリ。

- **user_settings.py – UserSettingsService**  
  - `get_or_default(user) -> UserSettingsRead` – DB に無ければデフォルト値を返す（保存はしない）。  
  - `update(user, payload) -> UserSettingsRead` – `exclude_unset=True` で部分更新し upsert。  
  - `get_user_settings_service(...)` – DI 用ファクトリ。

- **llm/mock_llm.py – MockLLMClient**  
  - `stream_chat_response(prompt) -> AsyncGenerator[str]` – IC-5 形式のダミー応答を単語ごとに送る。

---

## API エンドポイント (`app/api/endpoints/`)

- **auth.py**  
  - `read_current_user()` – `/api/v1/auth/me` で現在の認証ユーザーを返す。

- **chat.py**  
  - `create_chat_session(session_in, current_user, chat_session_repo)` – セッション作成。  
  - `get_chat_sessions(current_user, chat_session_repo)` – ログインユーザーのセッション一覧。  
  - `send_chat_message(message_in, current_user, chat_session_repo, chat_message_repo)` – ユーザーメッセージ保存。  
  - `stream_chat_response(session_id, current_user, ..., research_mode=False)` – LLM 応答を SSE で配信。  
  - `reset_chat_session(session_id, current_user, chat_service)` – セッションをリセットし新規セッションを返す。

- **files.py**  
  - `upload_file(file, current_user, file_service, knowledge_repo, rag_service, session_id?)` – 保存・テキスト抽出・RAG への登録・DB 保存を実施しメタ情報を返す。

- **admin.py**  
  - `list_knowledge_documents(current_admin_user, knowledge_repo, skip=0, limit=100, search_query?)` – 管理者専用、ナレッジ文書の一覧/検索。

- **feedback.py**  
  - `submit_feedback(feedback_in, current_user, feedback_service)` – フィードバック投稿。  
  - `get_feedback_for_session(session_id, current_user, feedback_service)` – セッション別フィードバック取得（本人・同テナントのみ返却）。  
  - `get_feedback_for_message(message_id, current_user, feedback_service)` – メッセージ別フィードバック取得。

- **help.py**  
  - `get_help_content(current_user, help_service, section_id?, category="user")` – section_id があれば 1 件、無ければカテゴリ別リスト。

- **user_settings.py**  
  - `get_user_settings(current_user, db)` – 現在ユーザーの設定取得（無ければデフォルト）。  
  - `update_user_settings(payload, current_user, db)` – 設定の部分更新。

---

## マイグレーション (`alembic/versions/001_add_user_settings.py`)
- **upgrade()** – `t_user_settings` テーブル作成・インデックス付与。  
- **downgrade()** – 上記テーブルとインデックスを削除。

---

## ユーティリティ
- **check_import.py** – `app.services.auth` などのインポート可否を確認する簡易スクリプト（実行で Import 成否を表示）。

---

## テストコード概要 (`app/tests/`)
フィクスチャは依存モックを準備し、各サービス/エンドポイント/リポジトリ/LLM 連携の振る舞いを検証。

- **conftest.py** – テスト用環境変数を設定し、FastAPI の multipart チェックをモック。
- **test_main.py** – ルート `/` が 200 と固定レスポンスを返すか検証。
- **test_endpoints_auth.py** – `/api/v1/auth/me` の成功/未認証/非アクティブ、`get_current_admin_user` の権限チェック。  
  フィクスチャ: `mock_auth_service`, `override_get_auth_service`, `mock_authenticated_user`, `override_get_current_user`。
- **test_endpoints_chat.py** – セッション作成・一覧・送信・ストリーム配信（research_mode on/off）・権限エラーを検証。  
  フィクスチャ: `mock_current_user` ほかチャット/LLM関連モック。
- **test_endpoints_files.py** – ファイルアップロード（グローバル/Ephemeral RAG）、ファイル名なし、バリデーションエラーを検証。
- **test_endpoints_admin.py** – 管理者向けナレッジ一覧の成功/検索/非管理者エラー。  
- **test_endpoints_feedback.py** – フィードバック投稿・セッション別取得・メッセージ別取得・権限なしケース。  
- **test_user_settings.py** – デフォルト返却、初回 upsert、部分更新保持、既存取得。  
- **test_memory_service.py** – MemoryService の create/get/update/delete をモックリポジトリで検証。  
- **test_chat_service.py** – セッションリセット成功/未検出/要約保存失敗時の挙動を確認。  
- **test_dom_orchestrator_service.py** – IC-5 形式ストリーミング、RAG あり/なしの研究モード、警告メッセージを検証。  
- **test_rag_service.py** – RagService 初期化、query/add_documents、（一部ストリームは skip マーク）。  
- **test_auth_service.py** – JWKS 取得成功/失敗、OIDC 設定なしエラー、トークン検証で新規/既存ユーザー、管理者判定。  
- **test_repositories.py** – BaseRepository テナントフィルタ、create の自動 tenant_id 付与、Tenant/User 専用メソッドを検証。  
- **test_help.py** – HelpService のカテゴリ別一覧、単一取得、必須フィールド確認。

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

