# DOM Enterprise Gateway – P0 Core Chat

DOM Enterprise Gateway の P0 コアチャット機能のバックエンド実装です。  
FastAPI + LangChain + PostgreSQL + Redis をベースに、OIDC 認証と RAG を備えた社内向けチャットゲートウェイを構築します。

## ディレクトリ構成

ルート直下:

- `backend/`  
  FastAPI バックエンド本体。Poetry プロジェクト。
- `.kiro/`  
  cc-sdd / kiro によって生成された仕様 (`spec.json`) やタスクリスト (`tasks.md`)。
- `.gemini/`  
  Gemini / Antigravity 用のメタデータ（通常は手動編集しない）。
- `migrations/`  
  Alembic マイグレーションファイル。
- `.env.example`  
  環境変数のサンプル。**編集してもよいが、`.env` とは別に管理すること。**
- `.env`  
  実行環境用の秘密情報。**Git にはコミットしない。**
- `docker-compose.yml`  
  backend + PostgreSQL + Redis をまとめて起動するための定義（現時点では WSL 上での動作を想定）。

バックエンド内部:

- `backend/app/main.py` – FastAPI エントリポイント
- `backend/app/api/` – API ルーター (`auth`, `chat`, `files`, `admin`, `feedback` など)
- `backend/app/services/` – ドメインサービス (`auth_service`, `chat_service`, `dom_orchestrator`, `rag_service`, `memory_service` など)
- `backend/app/repositories/` – DB アクセス層
- `backend/app/models/` – SQLAlchemy モデル
- `backend/app/schemas/` – Pydantic スキーマ
- `backend/app/core/` – 設定 (`config.py`)、DB 接続 (`database.py`) など
- `backend/app/tests/` – pytest によるユニットテスト・API テスト

## 開発環境

- WSL2 + Ubuntu
- Python 3.12
- Poetry 1.8 以降
- (任意) Docker / docker-compose

### 初期セットアップ

```bash
# WSL 上で
cd ~/work/dom-enterprise-gateway/backend

# Poetry で依存関係をインストール
poetry install

# 仮想環境をプロジェクト直下に作る場合（任意、既に設定済みなら不要）
poetry config virtualenvs.in-project true
````

環境変数ファイルを作成します:

```bash
cd ~/work/dom-enterprise-gateway
cp .env.example .env   # 必要に応じて中身を編集
```

最低限、以下の値を設定します（テスト用なのでダミーでも構いません）:

* `OIDC_CLIENT_ID`
* `OIDC_CLIENT_SECRET`
* `INITIAL_ADMIN_EMAIL`

## テストの実行

```bash
cd ~/work/dom-enterprise-gateway/backend

# すべてのテスト
poetry run pytest app/tests

# 特定のテストファイル
poetry run pytest app/tests/test_auth_service.py -vv
```

一部のテストは外部サービス（PostgreSQL / Redis / LLM）をモック・スタブして動作します。

## アプリケーションの起動 (開発用)

### Poetry + Uvicorn で直接起動

```bash
cd ~/work/dom-enterprise-gateway/backend
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Compose（準備中）

`docker-compose.yml` を用いた起動は今後整備予定です。

## Git 運用と「保険」について

* `.gitignore` により `.venv/`, `.gemini/`, `.pytest_cache/`, `.env` などは Git 管理から除外しています。
* 仕様ファイル `.kiro/` とバックエンド `backend/` は Git 管理対象です。
* AI エージェントによる大規模な修正は、`feat/fix-backend-tests-with-agent` など専用ブランチ上で行い、
  必要な変更のみを `main` にマージする運用を推奨します。
* 重大な変更前にはタグ (例: `backup-before-agent-2025-12-05`) を打っておくと安全にロールバックできます。

## AI エージェント（Antigravity / Gemini）利用時のガイドライン

* 作業ディレクトリは `backend/` に限定し、`.kiro/`・`.gemini/`・`.venv/`・`.git/` などには手を入れさせない。
* 既存テスト (`backend/app/tests`) を尊重し、テストを通す最小限の修正を行う。
* Poetry 仮想環境を利用し、`poetry install` / `poetry run pytest` / `poetry run uvicorn` の 3 つを基本コマンドとする。
* 外部サービスが必要な機能については、可能な限りモック・スタブでカバーし、
  実サービス依存にしないようにする。

