# DOM Enterprise Gateway (PoC) – P0 Core Chat

DOM Enterprise Gateway は、エンタープライズ向けの **ガバナンス付き LLM ゲートウェイ** を検証するための PoC（Proof of Concept）です。

P0/P0.1 では **「ログイン → チャット → 設定/ヘルプ」** までを、WSL2 上の Docker Compose で一気通貫に動かせる状態にします。

---

## 1. 目的（P0 / P0.1）

- Docker Compose で **Backend / Frontend(SSR) / Postgres / Redis / Nginx** を統合起動できる
- Nginx で **`/api` → backend** / **`/` → frontend** をリバースプロキシ（アプリ側の CORS/Proxy 変更は最小）
- **P0.1: Dev 認証** により、IdP（OIDC）なしでも PoC を操作できる
- 既存テストを実行できる（**Backend pytest / Frontend unit test は必須**）

---

## 2. アーキテクチャ（PoC）

- **nginx**: `http://localhost/` を入口にしてルーティング
  - `/api/*` → backend
  - `/*` → frontend (Angular SSR)
- **backend**: FastAPI
- **frontend**: Angular (SSR)
- **postgres**: アプリデータ（チャット/設定など）
- **redis**: キャッシュ/キュー用途

---

## 3. 前提（WSL2）

- Windows + WSL2
- Docker Desktop（WSL2 integration 有効）
- `docker compose` が WSL 内で実行できること

ローカルでテストも回す場合：

- Python 3.12+
- Poetry
- Node.js（フロントのユニットテスト用）

> `poetry install` で `python` が見つからない場合：
> Ubuntu では `python` コマンドが無いことがあるため、`sudo apt-get update && sudo apt-get install -y python-is-python3` を入れると解決します。

---

## 4. 起動方法（Docker Compose / WSL2）

```bash
cd ~/work/dom-enterprise-gateway

# 初回 or 変更後
docker compose up --build -d

# ログ確認
docker compose logs -f nginx backend frontend
````

ブラウザでアクセス：

- `http://localhost/`

---

## 5. P0.1 Dev 認証（最小コストで PoC を操作するための入口）

### 5.1 何をしているか

- `DEV_AUTH_ENABLED=true` のときだけ Dev 認証フローが有効になります。
- `/api/v1/auth/login` → `/api/v1/auth/callback` で **ダミーユーザーの Cookie セッション**を発行します。
- フロントは **Cookie を送るために `withCredentials: true`** で API を呼びます（同一 origin のため基本そのまま動きます）。

> ⚠️ **本番では必ず `DEV_AUTH_ENABLED=false`** にしてください。

### 5.2 必要な環境変数（docker compose 側で設定）

- `DEV_AUTH_ENABLED=true`
- `SESSION_SECRET=...`（十分長いランダム文字列を推奨）

#### DB について（PoC 用）

- マイグレーションを省略して最短で動かすため、PoC では `AUTO_CREATE_DB=true` を使う場合があります。
- `AUTO_CREATE_DB=true` のとき、起動時に **テーブルが無ければ自動作成**します。

> ⚠️ **本番では `AUTO_CREATE_DB=false`**（DDL は Alembic 等で管理）

### 5.3 動作確認（curl）

> ブラウザでログインした後に確認するのが簡単です。

```bash
# ログイン後（ブラウザで Cookie を持っている状態）
# /api/v1/auth/me が 200 で user json を返す
curl -i http://localhost/api/v1/auth/me
```

---

## 6. テスト（P0/P0.1 では必須）

### 6.1 Backend（pytest）

```bash
cd ~/work/dom-enterprise-gateway/backend

# venv が壊れていそうなら一度消す
rm -rf .venv

poetry install
poetry run pytest
```

> `Permission denied: pip` が出る場合は、過去に root で `.venv` を作ってしまっている可能性が高いので、`.venv` を消して作り直してください。

### 6.2 Frontend（Unit Test / Headless）

```bash
cd ~/work/dom-enterprise-gateway/frontend

npm ci
npm test -- --watch=false --browsers=ChromeHeadless
```

> WSL に Chrome/Chromium が無い場合は、まず Chromium を入れてください。
> 例: `sudo apt-get update && sudo apt-get install -y chromium-browser`（環境によりパッケージ名が違う場合あり）

---

## 7. よくあるトラブルシュート

### 7.1 401（Unauthorized）が出る / Dev セッションが効かない

- フロントから API へ **Cookie が送られていない**可能性があります。

  - `withCredentials: true` が API 呼び出しに付いているか
  - `http://localhost`（同一 origin）でアクセスしているか

### 7.2 404（Not Found）で `/api/api/...` のようになっている

- `apiBaseUrl` と API パス組み立ての二重付与が原因です。

  - **API は `/api/v1` に統一**し、`/api` を二重に付けないようにしてください。

### 7.3 500（Internal Server Error）

- backend ログ（`docker compose logs -f backend`）のスタックトレースを確認してください。
- PoC では DB テーブル未作成・DB 初期データ不足が原因になりやすいです。

---

## 8. ロードマップ

- **P0**: Docker Compose で統合起動 / 主要 API が動く / 回帰テストが回る
- **P0.1**: Dev 認証で「操作できる PoC」を成立させる（IdP なし）
- **P1**: **BFF + OIDC** 本実装（例: Keycloak）へ差し替え

---

## 9. セキュリティ注意

- Dev 認証は PoC を素早く触るための仕組みです。
- 本番相当環境では必ず以下を守ってください：

  - `DEV_AUTH_ENABLED=false`
  - `SESSION_SECRET` は十分長くランダム
  - DB 変更はマイグレーションで管理（`AUTO_CREATE_DB=false`）

---

## 10. ライセンス

未確定（PoC / 社内検証用途）。
