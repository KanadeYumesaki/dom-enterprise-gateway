# DOM Enterprise Gateway – Architecture / Structure Steering

## 1. C4 コンテナレベル概要

- **ユーザー（ブラウザ）**
  - Angular SPA を利用してチャット・ナレッジ管理・設定・ヘルプにアクセス。

- **Frontend コンテナ（Angular App）**
  - チャット UI、ナレッジ管理 UI、設定画面、ヘルプセンターを提供。
  - OAuth2.0/OIDC によるログインフローを開始し、FastAPI Backend と通信。

- **Backend コンテナ（FastAPI）**
  - 認証済 API の窓口。
  - LLM / RAG / メモリ / ファイルアップロード / ナレッジ管理のビジネスロジック。
  - LlmGateway 経由で Gemini を呼び出し、LangChain v1 のチェーンを実行。

- **データコンテナ**
  - PostgreSQL:
    - users, tenants, chat_sessions, chat_messages,
      structured_memory, episodic_memory, knowledge_documents,
      explanation_objects, audit_logs, feedback など。
    - 必要に応じて pgvector 拡張でベクトルを保持。
  - Redis:
    - Ephemeral Session Store（セッション一時保存・ロック・レートリミット）。
    - 簡易キャッシュ。
  - ファイルストレージ（ローカル or S3 互換）:
    - アップロードされたファイルの実体。

---

## 2. Backend 論理アーキテクチャ

### 2.1 レイヤ構造

1. **API Layer (FastAPI Routers)**
   - `/auth/*` : ログイン状態確認、ユーザー情報取得。
   - `/chat/*` : チャット開始・メッセージ送信・reset・セッション一覧。
   - `/files/*` : ファイルアップロード・削除・一覧。
   - `/knowledge/*` : ナレッジ登録・検索・削除・再インデックス。
   - `/memory/*` : Structured/EpisodicMemory の閲覧（管理者）。
   - `/admin/*` : テナント設定、監査ログ、フィードバック一覧。
   - `/help/*` : ヘルプセンターコンテンツ取得。

2. **Service Layer**
   - **AuthService**
     - OAuth2.0/OIDC トークン検証。
     - user/tenant の解決、ロール判定（user/admin）。
   - **ChatService**
     - チャットセッションの開始・更新・終了・reset のビジネスロジック。
     - Reset インバリアント（保存成功時のみ短期メモリ削除）を実装。
   - **DomOrchestratorService**
     - Domain Orchestrator Meister として、
       - モード判定（通常・リサーチ・コードなど）
       - Helper/Research/Answer へのタスク分解・指示
       を行う。
   - **HelperService**
     - ユーザー入力の要約・タグ付け・RAG クエリ生成・メモリ検索キー生成など。
   - **ResearchService**
     - LangChain v1 のチェーンを利用して Evidence 検索・集約。
     - Ephemeral RAG（添付ファイル）の検索もここで行う。
     - Agentic RAG として「足りない情報がある場合、一定ステップまで追加検索する」ロジックを持つ。
   - **AnswerComposerService**
     - Research 結果＋DOM の意図を受け取り、IC-5 ライトに整形。
   - **MemoryService**
     - StructuredMemory / EpisodicMemory / Ephemeral Session Store の CRUD。
   - **RagService**
     - グローバルナレッジ用ベクトルインデックスと、
       セッション限定の Ephemeral インデックスを管理。
   - **FileService**
     - ファイルアップロード／ストレージ保存／メタデータ登録／削除。
     - ファイルサイズ／拡張子／総容量のバリデーション。
   - **PiiService**
     - 入力テキスト・ナレッジ・メモリ保存前に PII マスキング／トークン化を行う。
   - **AuditService / FeedbackService**
     - reset / policy change / ナレッジ操作等の監査ログ。
     - チャット回答に対する 👍/👎・コメントを保存し、AgentOps 評価データとして利用。

3. **Data Access Layer (Repository)**
   - 各テーブルごとに Repository クラスを定義し、  
     Service レイヤからは Repository 経由でしか DB に触れない。

4. **LlmGateway / Provider Layer**
   - `LlmClient` 抽象インターフェース。
   - Provider 実装：
     - `GeminiClient`（PoC 本命）
   - すべてのエージェントは LlmGateway を通じて LLM を呼び出し、  
     トークン使用量・レスポンス時間を記録する。

---

## 3. Frontend 構造（Angular）

- **主要モジュール**
  - `AppModule`
  - `ChatModule`
    - チャット画面、メッセージ表示、IC-5 セクション表示、ファイル添付 UI。
  - `KnowledgeModule`
    - ナレッジ一覧・詳細・アップロード・削除・検索 UI（管理者向け）。
  - `SettingsModule`
    - ユーザー設定（フォントサイズ・テーマ・LLM 選択）、
      テナント設定（管理者のみ）。
  - `HelpModule`
    - ヘルプセンター・オンボーディングフロー。

- **共通コンポーネント**
  - Header / Sidebar / Notification (Toast) / Confirm Dialog。
  - ローディング表示、エラーバナー。

- **i18n**
  - 文言は i18n リソースファイル（例: `assets/i18n/ja.json` / `en.json`）で管理。

---

## 4. ディレクトリ構成（トップレベル案）

```plaintext
dom-enterprise-gateway/
  backend/
    app/
      api/            # FastAPI ルーター
      services/       # Auth/Chat/Memory/Rag/File/...
      repositories/   # DB アクセス
      models/         # SQLAlchemy モデル
      schemas/        # Pydantic スキーマ
      llm/            # LlmClient / プロンプト定義 / エージェント
      core/           # 設定・依存性注入・ログ
      tests/          # pytest テスト
  frontend/
    src/
      app/
        chat/
        knowledge/
        settings/
        help/
        shared/
  migrations/         # Alembic
  docker/
    backend/
    frontend/
    db/
    redis/
  .kiro/
  .gemini/
  docs/
    requirements_p0_core_chat.md
    help_content_outline.md
    DOM Enterprise Gateway.txt
````

---

## 5. 代表的なデータフロー

### 5.1 通常チャット + RAG

1. ユーザーがブラウザからメッセージ送信（＋必要ならファイル添付済み）。
2. Frontend → Backend `/chat/message`（アクセストークン付き）。
3. AuthService がユーザー・テナントを解決。
4. ChatService → DomOrchestratorService:

   * モード判定（通常／リサーチ／コードなど）。
   * Helper に要約・タグ付け・RAG クエリ生成を依頼。
5. HelperService → RagService:

   * グローバルナレッジ＋Ephemeral RAG から Evidence を取得。
6. ResearchService が Evidence を整理し、ミニレビュー＋IC-5 素案を生成。
7. AnswerComposerService がユーザー向け IC-5 ライトに整形。
8. 結果をストリーミングで Frontend に返却。
9. FeedbackService がユーザーの 👍/👎 を受け取り、評価データを保存。

### 5.2 ファイルアップロードと Ephemeral RAG

1. ユーザーがチャット画面からファイルを選択 → Frontend が `/files/upload` に送信。
2. Backend の FileService が：

   * サイズ / 拡張子 / ファイル数制限をチェック。
   * ストレージに保存し、メタデータ（session_id, user_id, tenant_id 等）を DB に記録。
   * テキスト抽出 → PiiService でマスキング → RagService で Ephemeral インデックスに登録。
3. 後続のチャットメッセージでは、ResearchService が Ephemeral インデックスを含めた検索を実行。
4. セッション終了時（保存して終了 or reset）に、Ephemeral インデックスから削除。

### 5.3 /reset と Reset インバリアント

1. ユーザーが `/reset` を実行。
2. ChatService が現在のセッションをロックし、HelperService に要約生成を依頼。
3. 要約を PiiService でマスキング → MemoryService が EpisodicMemory に保存。
4. 保存が成功した場合のみ：

   * 短期メモリ（チャット履歴）をクリアし、新しいセッション ID を発行。
5. 要約生成／保存が連続して失敗した場合：

   * ユーザーに「保存せずに強制リセットするか？」を確認し、同意があれば短期メモリを破棄。

---

## 6. 拡張ポイント（P1+ を見据えた構造）

* LlmClient の Provider 追加（GPT / Claude / DeepSeek 等）。
* マルチテナント管理画面（使用量・ポリシー・課金など）。
* AgentOps ダッシュボード：

  * セッションの成功率・フィードバック傾向・回答パターンなどの可視化。
* より高度な Agentic RAG：

  * 自己改善ループ（prompt チューニングやツール選択の自動最適化）。
* ワークフロー連携（チケットシステム・Slack/Teams 等）。

この structure.md を **「設計の土台」** とし、
具体的な requirements / design / tasks は `.kiro/specs/...` 側で詳細化していく。
