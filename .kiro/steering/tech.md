# DOM Enterprise Gateway – Tech Steering

## 1. 全体方針

- 言語: **Python 3.12**（バックエンド）、**TypeScript**（Angular フロントエンド）
- アーキテクチャ:
  - FastAPI ベースの BFF / API サーバー
  - LangChain v1 ベースの RAG / エージェントオーケストレーション
  - PostgreSQL + pgvector / Redis
  - Docker / docker-compose による PoC 環境の一発起動
- 実装スタイル:
  - 型ヒント・docstring を徹底し、初学者にも読みやすいコードを目指す。
  - 例外握りつぶし（`except Exception: pass` 等）は禁止。
  - ネットワーク / LLM / DB / ファイル I/O / 認証エラーなど、カテゴリごとに例外クラスを定義し、丁寧にハンドリングする。

---

## 2. Backend 技術スタック（Python 3.12）

### 2.1 Web フレームワーク
- **FastAPI**
  - 非同期処理対応・型ヒント前提の実装。
  - OpenAPI スキーマ自動生成を活用し、フロント/バックの契約を明確にする。

### 2.2 LLM / RAG / Agentic

- **LangChain v1**
  - `Runnable` / LCEL を活用して RAG チェーン・エージェントフローを実装。
  - 主な利用コンポーネント:
    - `ChatPromptTemplate` / `RunnableSequence`
    - `VectorStore`（pgvector or 対応ドライバ）
    - `RetrievalQA` もしくは `RetrievalChain` ベースの RAG
  - P0 では「短いステップの Agentic RAG」に留める：
    - DOM → Helper → Research → Answer の 1〜数ステップ。
    - 最大ステップ数／トークン数に上限を設定し、暴走を防ぐ。

- **LlmClient 抽象**
  - インターフェース例:
    - `LlmClient.respond(messages, options) -> { text, usage, raw_response }`
  - 実装:
    - `MainLlmClient`: Gemini 2.x 系（Pro / Flash 等）
    - `HelperLlmClient`: PoC では Gemini で代用。将来 DeepSeek 小モデル（7B〜8B）に切り替え。

### 2.3 認証・認可

- **OAuth2.0 + OIDC**
  - Auth Code + PKCE フローを前提。
  - ライブラリ候補：
    - `authlib` / `python-jose` 等で ID トークン/アクセストークン検証。
  - アクセストークンから `sub` / `email` / `groups` 等を抽出し、  
    RBAC（user / admin）を決定する。

- **初期管理者ブートストラップ**
  - 環境変数 `INITIAL_ADMIN_EMAIL` を定義。
  - 初回ログイン時に、このメールアドレスのユーザーを `admin` ロールで作成。

### 2.4 DB / ストレージ

- **PostgreSQL 15+**
  - アプリケーションデータ（users / chat_sessions / messages / memories / knowledge / audit_logs 等）。
  - pgvector 拡張（RAG 用ベクトルストアを DB 内に持つか、外部ベクトル DB とするかは P0 の実装判断）。

- **Redis**
  - Ephemeral Session Store（セッション一時保存・ロック・レートリミット）。
  - 簡易キャッシュ（RAG 結果・プロンプトテンプレなど）。

- **ファイルストレージ**
  - P0 ではローカルディスク or S3 互換ストレージのいずれかに対応できるよう抽象化。
  - ファイルメタデータは PostgreSQL、実体はストレージに格納。

### 2.5 ORM / マイグレーション

- **SQLAlchemy + Alembic**
  - モデル定義は SQLAlchemy Declarative。
  - すべてのスキーマ変更は Alembic でマイグレーションを生成・適用。
  - 破壊的変更（カラム削除・リネーム）は、
    - 新カラム追加 → データ移行 → 旧カラム削除 の 3 ステップで行う。

---

## 3. Frontend 技術スタック（Angular）

- **Angular (LTS)** + TypeScript
  - UI レイヤー（チャット画面、ナレッジ管理画面、設定画面、ヘルプセンター）。
- 状態管理:
  - Angular Signals or NGXS / Akita 等、軽量な状態管理ライブラリのいずれか（P0 では最小限）。
- UI コンポーネント:
  - Material Design 系コンポーネントライブラリ（Angular Material 等）。
- i18n:
  - Angular i18n or ngx-translate を利用し、
    - デフォルト日本語、
    - 英語 UI への切り替えが可能な設計。

- 認証フロー:
  - ブラウザ側で OAuth2.0/OIDC フローを開始し、  
    トークンは可能な限りメモリ or httpOnly Cookie で管理（localStorage 直接保管は避ける）。

---

## 4. ログ / メトリクス / トレーシング

- ログ:
  - Python 標準 `logging` もしくは `structlog` を利用し、
    - request_id / session_id / user_id / tenant_id をコンテキストに含める。
  - 重要イベント（reset / policy change / ナレッジ削除 等）は `audit_logs` テーブルにも保存。

- メトリクス / トレーシング（PoC 時点では必須ではないが方針を持つ）:
  - 将来の OpenTelemetry 統合を前提に、
    - 各 API の処理時間
    - LLM 呼び出し時間・トークン使用量
  を計測できるようにコード側で計測ポイントを想定しておく。

---

## 5. テスト戦略

- バックエンド:
  - **pytest** + `pytest-asyncio` + `httpx` (FastAPI のテストクライアント)。
  - ユニットテスト:
    - LlmClient のモックを利用し、ビジネスロジックをテスト。
  - 統合テスト:
    - Docker 内で DB / Redis を立ち上げた状態での API テスト。

- フロントエンド:
  - Angular 既定のテストフレームワーク（Jasmine/Karma）もしくは Jest。
  - E2E テストは将来 `Playwright` を検討。

---

## 6. Docker / デプロイ

- PoC 環境:
  - `docker-compose.yml` で
    - backend（FastAPI）
    - frontend（Angular）
    - postgres
    - redis
  を起動。

- ベースイメージ方針:
  - backend: `python:3.12-slim` 系をベースに、依存ライブラリを最小限に。
  - frontend: `node:lts` でビルドし、成果物は Nginx 等の軽量イメージで配信。

---

## 7. コーディング規約（要点）

- すべてのクラス・関数・メソッドに docstring を付与し、
  - 引数
  - 戻り値
  - 処理内容
  を日本語で記述する（学習用を兼ねる）。
- 例外処理は具体的な例外型を捕捉し、適切な HTTP ステータス・エラーメッセージを返す。
- LLM 呼び出し部分は LlmClient に閉じ込め、ビジネスロジック側から直接 SDK を呼ばない。
- LangChain v1 を前提とし、非推奨 API は使用しない。

---

## 8. ブランチ戦略（推奨）

- **main**: 最新の安定版。直接コミットは禁止。  
- **develop**: 次期リリースの開発統合ブランチ。
- **feature/**: 機能開発用ブランチ。命名例：`feature/fr-chat-streaming`。
- **fix/**: バグ修正用ブランチ。
- **release/**: リリース準備用ブランチ。

Pull Request 単位でコードレビューを行い、  
少なくとも **requirements/design/tasks に対する実装差分が説明できる状態** を維持する。
