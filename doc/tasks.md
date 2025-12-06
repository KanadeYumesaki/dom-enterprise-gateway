# 実装タスクリスト: DOM Enterprise Gateway P0 Core Chat

## 1. バックエンド基盤構築
- [x] 1.1 プロジェクトとDockerの初期設定
  - `pyproject.toml` にて FastAPI, LangChain, SQLAlchemy, Alembic 等の依存関係を定義する。
  - `backend` ディレクトリ構造（`app/api`, `app/services`など）を作成する。
  - `docker-compose.yml` にて `backend`, `postgres`, `redis` サービスの基本定義を行う。
  - `.env.example` にて、データベース接続情報や`INITIAL_ADMIN_EMAIL`などの環境変数を定義する。
  - _Requirements: 8.3_
- [x] 1.2 データベースモデルとマイグレーションの設定
  - SQLAlchemyの `Base` と非同期エンジンを設定する。
  - `User`, `Tenant`, `ChatSession`, `ChatMessage` のコアとなるSQLAlchemyモデルを定義する。
  - Alembicを初期化し、最初のマイグレーションスクリプトを生成する。
  - _Requirements: 2.2, 3.1, 8.2_
- [x] 1.3 データアクセス層 (Repository) の実装 (P)
  - 各SQLAlchemyモデルに対応する非同期Repositoryクラス（例: `UserRepository`）を実装する。
  - CRUD（作成、読み取り、更新、削除）の基本メソッドをRepositoryに実装する。
  - FastAPIの `Depends` を利用して、DBセッションをRepositoryに注入する仕組みを構築する。
  - _Requirements: 2.2, 5.2_

## 2. 認証と認可機能の実装
- [x] 2.1 OIDC認証サービスの実装
  - `authlib` を利用して、OIDCプロバイダからのトークンを検証する `AuthService` を実装する。
  - `/.well-known/openid-configuration` からJWKSを取得し、JWTをデコード・検証するロジックを構築する。
  - 認証されたユーザー情報を保持するPydanticスキーマ `AuthenticatedUser` を定義する。
  - _Requirements: 2.1, 8.1_
- [x] 2.2 APIエンドポイントの保護
  - 認証されたユーザー情報（`AuthenticatedUser`）を返す `/api/auth/me` エンドポイントを作成する。
  - FastAPIの `Depends` を利用して、APIルーターに認証必須の依存関係を組み込む。
  - `admin` ロールが必要なエンドポイントのための認可デコレータまたは依存関係を実装する。
  - _Requirements: 2.2_
- [x] 2.3 初期管理者とテナント分離ロジックの実装
  - `INITIAL_ADMIN_EMAIL` 環境変数を参照し、初回ログインユーザーを管理者に設定するロジックを実装する。
  - Repositoryのクエリが、リクエストコンテキストから取得した `tenant_id` で常にフィルタリングされることを保証する仕組みを構築する。
  - _Requirements: 2.3_

## 3. コアチャット機能の実装
- [x] 3.1 チャットメッセージングAPIの実装
  - チャットメッセージを受け取る `/api/chat/send` エンドポイントを実装する。
  - `DomOrchestratorService` の基本骨格を実装し、APIから呼び出す。
  - _Requirements: 3.1_
- [x] 3.2 LLM応答のストリーミング (SSE)
  - `DomOrchestratorService` 内でLLMからの応答をトークンごとに受け取る。
  - FastAPIの `StreamingResponse` と `text/event-stream` を利用して、トークンをクライアントにストリーミング配信する `/api/chat/stream/{session_id}` エンドポイントを実装する。
  - _Requirements: 3.1_
- [x] 3.3 IC-5ライト形式の回答生成
  - `AnswerAgent` (または `AnswerComposerService`) にて、LLMの最終出力を「Decision」「Why」「Next 3 Actions」のMarkdownセクションに整形する処理を実装する。
  - _Requirements: 3.2_

## 4. RAGとファイル管理機能の実装
- [x] 4.1 基本的なRAGサービスの実装 (P)
  - `langchain-postgres` を利用して `PGVector` ストアを初期化する `RagService` を実装する。
  - LCELを利用して、コンテキスト検索と質問応答を組み合わせた基本的なRAGチェーンを構築する。
  - _Requirements: 4.1_
- [x] 4.2 ファイルアップロードとEphemeral RAGの実装 (P)
  - ファイルをアップロードし、メタデータをDBに保存する `/api/files/upload` エンドポイントを実装する。
  - アップロードされたファイルからテキストを抽出し、セッションIDに紐づく一時的なベクトルインデックスに登録するロジックを `RagService` に実装する。
  - ファイルサイズや種類のバリデーションを実装する。
  - _Requirements: 4.3, 5.1_
- [x] 4.3 Agentic Researchモードの実装
  - `DomOrchestratorService` に、`is_research_mode` フラグに応じてRAGチェーンの呼び出し回数やプロンプトを変更するロジックを追加する。
  - _Requirements: 4.4_
- [x] 4.4 ナレッジ管理APIの実装 (P)
  - 管理者がナレッジドキュメントの一覧表示と検索を行える `/api/admin/knowledge` エンドポイントを実装する。
  - _Requirements: 5.2_

## 5. メモリとセッション管理機能の実装
- [x] 5.1 メモリ管理サービスの実装 (P)
  - `StructuredMemory` と `EpisodicMemory` のCRUD操作を行う `MemoryService` と `*Repository` を実装する。
  - _Requirements: 6.1_
- [x] 5.2 セッションリセット機能の実装
  - `/reset` コマンドを受け取り、`ChatService` を呼び出す `/api/chat/reset` エンドポイントを実装する。
  - `ChatService` に、セッション要約とEpisodicMemoryへの保存が成功した場合のみ短期記憶をクリアする「Resetインバリアント」ロジックを実装する。
  - _Requirements: 6.3_
- [x] 5.3 フィードバックAPIの実装 (P)
  - ユーザーからの👍/👎評価とコメントを受け取り、DBに保存する `/api/feedback` エンドポイントを実装する。
  - _Requirements: 7.1_

## 6. フロントエンド基盤構築 (P)
- [x] 6.1 Angularプロジェクトの初期設定
  - Angular CLIで新規プロジェクトを作成し、`@angular/material` を追加する。
  - `backend` ディレクトリ構成（`app/components`, `app/services`など）を作成する。
  - Husky と Prettier を使用して、コードのフォーマットが自動的に行われるようにする。
  - _Requirements: 8.3_
- [x] 6.2 コアサービスと状態管理の実装
  - バックエンドAPIと通信するための `ApiService` を実装する。
  - ユーザーの認証状態やプロファイルを管理する `AuthService` を実装する。
  - Angular Signalsを使用して、シンプルなグローバル状態（例：ユーザー情報、ローディング状態）を管理する `StateService` を作成する。
  - _Requirements: 2.1, 2.2_

## 7. フロントエンドUIコンポーネント実装
- [ ] 7.1 (P) 認証とメインレイアウトの実装
  - ログイン・ログアウト処理を実装し、OIDCプロバイダへリダイレクトさせる。
  - ヘッダー、サイドバー、コンテンツエリアを含む基本的なアプリケーションレイアウトを構築する。
  - _Requirements: 2.1_
- [ ] 7.2 (P) チャット画面の実装
  - メッセージの表示、入力フォーム、ストリーミングメッセージのリアルタイム更新を行う `ChatComponent` を実装する。
  - Markdownで返されるIC-5形式の回答をパースして適切に表示する。
  - ファイル添付UIとアップロード処理を実装する。
  - _Requirements: 3.1, 3.2, 5.1_
- [ ] 7.3 (P) ナレッジ管理画面の実装
  - 管理者向けに、ナレッジ一覧を表示・検索する `KnowledgeComponent` を実装する。
  - _Requirements: 5.2_
- [ ] 7.4 (P) 設定・ヘルプ画面の実装
  - ユーザーが表示設定（テーマ、言語）を変更できる `SettingsComponent` を実装する。
  - `help_content_outline.md` に基づく静的なヘルプコンテンツを表示する `HelpComponent` を実装する。
  - 初回ログイン時に表示されるオンボーディングツアーのコンポーネントを実装する。
  - _Requirements: 7.2, 7.3_

## 8. 統合とテスト
- [ ] 8.1 E2Eテストシナリオの作成と実行 (Cancelled for P0)
- [ ] 8.2 Docker Composeによる統合環境の最終調整 (Cancelled for P0)
- [ ] 8.3 最終リグレッションテスト (Cancelled for P0)