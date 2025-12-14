# DOM Enterprise Gateway – P0 Core Chat

DOM Enterprise Gateway は、エンタープライズ向けの **ガバナンス付き LLM ゲートウェイ** の PoC です。  
P0 では「コアチャット」を中心に、以下を実現します。

- OAuth2 / OIDC による認証・テナント分離・RBAC（`user` / `admin`）
- マルチエージェント（DOM / Helper / Research / Answer）+ LangChain v1
- RAG（pgvector）＋長期メモリ＋フィードバック
- Angular 20 + Zoneless + SSR + Material Design 3 による Web UI

> ⚠️ 現在（2025-12 時点）、OIDC プロバイダを起動していない環境では  
> `/login` から先の画面に遷移できないため、  
> **Settings / Help など MainLayout 配下の UI は「実装済みだがブラウザ上の最終動作は未確認」**です。

---

## 1. 全体アーキテクチャ

### 1.1 コンポーネント構成

```mermaid
flowchart LR
  User["エンドユーザー<br/>(Webブラウザ)"] --> Frontend["Frontend<br/>Angular 20 / SSR / Material"]
  Frontend -->|REST + SSE| Backend["Backend API<br/>FastAPI + LangChain v1"]
  Backend --> DB[(PostgreSQL 15 + pgvector)]
  Backend --> Cache[(Redis)]
  Backend --> LLM["LLM Provider<br/>(Gemini シリーズ想定)"]
  Backend --> IdP["IdP / OIDC Provider"]

  subgraph Infra
    DB
    Cache
  end
````

### 1.2 主要機能（P0）

* 認証・認可 / RBAC / テナント分離
* コアチャット（ストリーミング応答 / IC-5 ライト形式）
* RAG + 長期メモリ（セッション要約・Structured/Episodic Memory）
* ナレッジ管理（管理者用一覧・検索）
* 設定（テーマ / 言語 / フォントサイズ / Onboarding フラグ）
* ヘルプセンター（画面・機能の説明）
* フィードバックとログ（品質改善のためのメトリクス蓄積）

詳細な機能要件は `requirements_p0_core_chat.md` と
「引き継ぎメモ / 要件フルサマリ」 (`DOM Enterprise Gateway.txt`) を参照してください。

---

## 2. リポジトリ構成

```text
dom-enterprise-gateway/
├── backend/                # FastAPI + LangChain v1 バックエンド
│   ├── app/
│   │   ├── api/           # エンドポイント定義
│   │   ├── models/        # SQLAlchemy モデル
│   │   ├── repositories/  # Repository 層
│   │   ├── services/      # ドメインサービス (ChatService 等)
│   │   └── schemas/       # Pydantic スキーマ
│   └── tests/             # バックエンド単体テスト
├── frontend/               # Angular 20 (standalone + SSR + Zoneless)
│   ├── src/app/
│   │   ├── core/          # 共通サービス (Api/Auth/State/Onboarding など)
│   │   ├── layout/        # MainLayout / Header / Sidebar
│   │   ├── features/      # chat / knowledge / settings / help 等の機能別 UI
│   │   └── pages/         # ルートに対応するページコンポーネント
│   └── ...                # Angular 標準構成
├── .kiro/                  # タスクリスト等のステアリング用メモ
├── requirements_p0_core_chat.md
├── DOM Enterprise Gateway.txt
├── design.md
├── help_content_outline.md
├── tasks.md
└── README.md               # このファイル
```

---

## 3. 技術スタック

### 3.1 Backend

* Python 3.12
* FastAPI
* LangChain v1
* SQLAlchemy + Alembic
* PostgreSQL 15 + pgvector
* Redis
* Poetry によるパッケージ管理

### 3.2 Frontend

* Angular 20（standalone / Signals / Zoneless + SSR）
* TypeScript 5.9
* Angular Material (Material Design 3)
* RxJS
* Karma + Jasmine（ユニットテスト）

### 3.3 インフラ / その他

* Windows 11 + WSL2 (Ubuntu)
* Docker / docker-compose（PostgreSQL / Redis 用）
* OAuth2 / OIDC（企業 IdP 連携を想定）

> 重要: `poetry`, `npm`, `ng`, `docker` など **すべての CLI は WSL2 上の Ubuntu で実行**してください。
> Windows 側の PowerShell / CMD からは直接叩かない前提です。

---

## 4. 初期セットアップ

### 4.1 環境変数ファイルの作成

```bash
# WSL (Ubuntu) 上で
cd ~/work/dom-enterprise-gateway
cp .env.example .env   # 必要に応じて中身を編集
```
```bash
# WSL (Ubuntu) 上で
cd ~/work/dom-enterprise-gateway/backend

# Poetry で依存関係をインストール
poetry install

# （任意）仮想環境をプロジェクト直下に作る場合
poetry config virtualenvs.in-project true
```

### 5.2 データベース起動（docker-compose）

```bash
# プロジェクトルートで
cd ~/work/dom-enterprise-gateway
docker compose up -d postgres redis
```

### 5.3 マイグレーション実行

（実際のコマンドは `alembic.ini` / `Makefile` に合わせてください）

```bash
cd ~/work/dom-enterprise-gateway/backend
poetry run alembic upgrade head
```

### 5.4 テスト実行

```bash
cd ~/work/dom-enterprise-gateway/backend

# すべてのテスト
poetry run pytest app/tests
# 例: 特定ファイルのみ
poetry run pytest app/tests/test_auth_service.py -vv
```

> 引き継ぎメモ時点では、**全 53 テスト中 53 passed, 1 skipped（RAG ストリーミングテスト）** となっています。
> 詳細は `backend/TESTING_NOTES.md` を参照してください。

### 5.5 開発サーバー起動

```bash
cd ~/work/dom-enterprise-gateway/backend
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 6. Frontend のセットアップと起動

### 6.1 依存関係のインストール

```bash
# WSL (Ubuntu) 上で
cd ~/work/dom-enterprise-gateway/frontend
npm install
```

### 6.2 開発サーバー起動（SSR or CSR）

```bash
cd ~/work/dom-enterprise-gateway/frontend
npm start       # package.json の設定に従う (ng serve 相当)
# または dev:ssr 等、実際の scripts に合わせてください
```

ブラウザから `http://localhost:4200` にアクセスします。

> ⚠️ Backend / OIDC を起動していない場合、
> `AuthGuard` により `/login` 画面から先のルート（`/chat`, `/sessions`, `/knowledge`, `/settings`, `/help`）には遷移できません。
> これは仕様どおりの挙動です。

### 6.3 Frontend ビルド

```bash
cd ~/work/dom-enterprise-gateway/frontend
npm run build
```

### 6.4 Frontend テスト

```bash
cd ~/work/dom-enterprise-gateway/frontend
ng test
```

> WSL 内には GUI ブラウザ (Chrome) が入っていないため、
> `No binary for Chrome browser on your platform` というエラーが出ることがあります。
> その場合は、テスト環境を Windows 側に用意するか、Headless Chrome をインストールして設定してください。

---

## 7. 画面と機能の概要（P0 時点）

### 7.1 認証 / 共通レイアウト

* `/login`

  * OIDC プロバイダへのリダイレクトボタンのみを持つシンプルな画面。
* `/auth/callback`

  * IdP からの戻りを受け取り、Backend 経由でセッションを確立するためのコールバック画面。
* `/`（`MainLayoutComponent`）

  * Header + Sidebar + コンテンツ領域。
  * `authGuard` によりログイン必須。
  * Sidebar から以下のルートに遷移：

### 7.2 Chat / Sessions / Memory（概要）

* `/chat`

  * チャットメイン画面。
  * メッセージ一覧、入力フォーム、SSE によるストリーミング表示。
  * IC-5 ライト（Decision / Why / Next 3 Actions）ビュー。
  * ファイル添付とアップロード。
* `/sessions`

  * 過去セッション一覧・再開（P0 では最低限の UI）。
* `/memory`

  * Structured / Episodic Memory の閲覧（P0 範囲内）。

### 7.3 Knowledge 管理（管理者のみ）

* `/knowledge`（`adminGuard` + `authGuard`）

  * 管理者専用ナレッジ管理画面。
  * 機能：

    * ナレッジドキュメント一覧（MatTable + ページネーション + ソート）
    * ファイル名による検索
    * 選択したドキュメントのメタデータ詳細表示
  * P1 では、ファイル内容プレビューやアップロード UI を拡張予定。

### 7.4 Settings / Help / Onboarding（P0 実装済み）

**実装状態**

* `/settings`

  * Backend の `/api/user/settings` と連携。
  * 設定可能な項目（P0）：

    * テーマ: `light` / `dark`
    * 言語: `ja` / `en`
    * フォントサイズ: `small` / `medium` / `large`
    * Onboarding 関連フラグ
  * 画面上は Angular Material のフォームで実装されていますが、
    現時点では OIDC 未起動環境のため、ログインして実際に操作する E2E 確認はまだ行えていません。

* `/help`

  * Backend の `/api/help/content` から `HelpSection` を取得して表示。
  * 左ペインにセクション一覧、右ペインに詳細コンテンツを表示。
  * コンテンツ構成は `help_content_outline.md` をもとにしています。
  * こちらも同様に、UI の最終動作確認は OIDC 起動後に実施予定です。

* Onboarding

  * `UserSettings` のフラグに基づいて、初回ログイン時の簡易ダイアログ（オンボーディング）を表示するサービスを実装済み。
  * SSR で落ちないよう `isPlatformBrowser` を用いてブラウザ専用処理をガード。

---

## 8. 開発ルール（AI エージェント含む）

このリポジトリでは、AI エージェントと協調しながら開発することを前提としています。
主なルールは次の通りです。

1. **推測禁止**

   * `NEW` と書かれていても、まず実際にファイルが存在するか確認し、
     既存なら `MODIFY` 扱いにする。
   * API 仕様や型は、必ず既存コード・要件書を確認してから決める。

2. **エラー握りつぶし禁止**

   * ネットワーク / 4xx / 5xx / タイムアウト / JSON パース / SSE 切断 / 認証 / 権限 / 予期しない例外
     など、考えうるエラーを分類し、UI かログで区別できるようにする。

3. **コメントポリシー**

   * クラス / メソッド / 関数単位で

     * 役割
     * いつ呼ばれるか
     * なぜこの実装なのか
       を日本語でコメントとして残す。

4. **WSL 前提のコマンド記載**

   * README やドキュメントに出すコマンドは、
     基本的に WSL (Ubuntu) で実行する形で記述する。

5. **README 更新**

   * 新しいタスクセット（例: 7.4 完了時）で引き継ぐときは、
     必ずこの README を最新状態に更新してからコミットする。

---

## 9. 今後のロードマップ（抜粋）

* P1

  * Knowledge 管理の CRUD 拡張（アップロード / 削除 / 編集）
  * ファイル内容プレビュー（特に PDF / Markdown）
  * Settings/Help UI の UX 向上と Onboarding ツアーの多ステップ化
  * RAG / Agentic Research の高度化

* P2 以降

  * ガバナンスダッシュボード（フィードバック / ポリシー違反検知 / モデルルーティング）
  * Explainability / トレースビュー
  * 本番運用を想定した監査ログ・多テナント管理 UI など

---

## 10. ライセンス / 問い合わせ

ライセンスや対外公開ポリシーは未確定です。
社内利用・PoC 実験用途として使用し、外部公開する場合は別途合意・レビューを行ってください。
