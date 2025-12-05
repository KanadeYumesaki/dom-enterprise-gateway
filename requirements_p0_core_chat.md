# DOM Enterprise Gateway – PoC Core Chat 要件書
`requirements_p0_core_chat.md`  
Version: 1.1 (PoC-P0 / P1 併記, Agentic Research + Ephemeral RAG 反映)

---

## 0. 概要

### 0.1 プロジェクト概要

- 名称: **DOM Enterprise Gateway (PoC Core Chat)**
- 目的:
  - OAuth2 認証されたユーザーが、
    **マルチエージェント（DOM / Helper / Research / Answer） + LangChain v1 + メモリ + RAG** を通じて
    エンタープライズ向けのチャット支援を受ける。
  - 回答は IC-5 ライト形式（Decision / Why / Next 3 Actions）で構造化され、
    参照ソース・メモリ・ナレッジに基づく説明責任を持つ。
  - すべて Docker 上で起動でき、DB を作り直さずに拡張できる。

- ターゲットユーザー:
  - 開発者・コンサル・社内の高度ユーザー
  - 初心者も使えるが、PoCではプロユーザーを優先

- フェーズ:
  - **P0 = PoC Core Chat**（本ファイルの主対象）
  - P1+ = 将来拡張（本ファイル内では「(P1)」などで明示）

---

## 1. 前提・制約

### 1.1 技術スタック（PoC）

- Backend
  - Python **3.12**
  - FastAPI
  - **LangChain v1**（Runnable / LCEL / RAG / Agent 実装に必須）
  - SQLAlchemy + Alembic
- Frontend
  - Angular（最新版 LTS）
- Infrastructure
  - PostgreSQL 15+（pgvector 拡張 or 互換）
  - Redis（Ephemeral / ロック / キャッシュ）
  - Docker / docker-compose（PoC）
- LLM
  - P0: **Gemini** を Main / Helper 両方に使用
  - LlmClient 抽象を導入し、将来 GPT / Claude / DeepSeek などに切り替え可能にする。

### 1.2 エージェント構成（P0）

- Domain Orchestrator Meister (DOM)
- Helper Meister（要約・クエリ生成・タグ付け）
- Research Meister（RAG 検索・要約）
- Answer Meister（IC-5 形式での最終回答）

### 1.3 優先度ラベル

- (P0): PoC で必ず実装
- (P1): 将来拡張として仕様に記載（PoC では実装しなくてもよい）

---

## 2. 機能要件 (Functional Requirements)

### 2.1 認証・認可 (Auth / RBAC)

**FR-AUTH-1 (P0)** OAuth2.0 / OIDC 認証  
- ユーザーは、企業の IdP / OAuth2.0 / OIDC を用いてログインできる。
- FastAPI は BFF パターンでトークンを扱い、フロントエンドに生トークンを露出しない。

**FR-AUTH-2 (P0)** RBAC / テナント分離  
- `user` / `admin` ロールを持ち、テナント単位でデータが分離される。
- 管理者のみアクセス可能な API / 画面（テナント設定・ナレッジ管理 etc.）を持つ。

**FR-AUTH-3 (P0)** 初期管理者のブートストラップ  
- システムは環境変数 `INITIAL_ADMIN_EMAIL` を参照し、
  初回ログインしたユーザーのメールアドレスがこれと一致した場合、そのユーザーを `admin` ロールとして登録する。
  - `users` テーブルに存在しなければ作成し、`role = admin` を付与。
  - 既に存在する場合も `role = admin` を保証。
- その他のユーザーは、初回ログイン時に `role = user` で自動登録（JIT Provisioning）される。

---

### 2.2 コアチャット & オーケストレーション

**FR-CHAT-1 (P0)** チャット送受信とストリーミング  
- ログイン済みユーザーはチャット画面からメッセージを送信できる。
- 応答はストリーミング（SSE または WebSocket）で返す。
- 1 回のユーザー入力に対して 1 つの `chat_session` 内に `chat_message` が追加される。

**FR-CHAT-2 (P0)** IC-5 ライト形式での回答（Markdown ベース）  
- Answer Meister は、少なくとも以下を含む **Markdown 形式** の回答を生成する：
  - `## Decision` セクション（結論）
  - `## Why` セクション（理由・背景）
  - `## Next 3 Actions` セクション（次の 3 ステップ。番号付きリスト推奨）
- フロントエンドはストリーミングされた Markdown を受信し、クライアント側でパースして各セクションを表示する。
- P0 では内部 JSON 構造は **必須ではない**。必要であれば Markdown から Decision / Why / Next 3 Actions を抽出する。

**FR-CHAT-3 (P1)** IC-5 フル形式  
- 複雑な問いではフル IC-5（Decision / Why / Options / Risks / Next 3 Actions）を返す。
- P1 以降で、構造化出力（JSON）とのハイブリッドを検討してよい。

---

### 2.3 RAG / ナレッジ / LangChain v1

**FR-RAG-1 (P0)** LangChain v1 ベースの RAG  
- 社内ナレッジは `knowledge_documents` + ベクトルストアに保存。
- LangChain v1 の以下パターンで RAG を実装：
  - DocumentLoader → TextSplitter → Embedding → VectorStore
  - LCEL / Runnable による RAG チェーン
- P0 の Research Meister は、この RAG チェーンを **1回** 実行するシングルターン RAG とする。

**FR-RAG-2 (P0)** ソース種別の明示  
- 各回答には、参照したソースの一覧を付与する：
  - 種別: RAG / Memory / Assumption / (将来) Web
  - タイトル or ラベル
  - 識別子 (doc_id 等)

**FR-RAG-EPH-1 (P0)** セッション限定 Ephemeral RAG（添付ファイル用）  
- チャットに添付されたファイルは、アップロード後に **セッション専用のベクトルインデックス** に登録される。
  - キー: `session_id`
  - LangChain v1 の VectorStore（例: pgvector / in-memory）を利用。
- LLM に渡すコンテキストは、ユーザーの質問に対する検索結果の **上位 K 件（例: 3〜5チャンク）** のみを含める。
- 1 回の LLM 呼び出しあたりのコンテキストトークン数は、**上限（例: 6〜8K tokens）** を超えないよう制限する。
- このセッション専用インデックスは、セッション終了時または一定期間経過後（例: 24 時間）に削除される。
- P0 では、添付ファイル由来テキストは長期ナレッジ（knowledge_documents）には保存されない。

**FR-RAG-3 (P1)** 高度な Agentic RAG  
- DOM がクエリを分解し、Helper がクエリ展開、Research が複数回検索、Answer が統合する高度な Agentic RAG。
- 複数ターンで再検索・仮説検証・統合を行う（ReAct 的パターンを含みうる）。

---

### 2.4 Agentic Research モード（リサーチ専用エージェント）

**FR-AGENT-1（P0）** 「リサーチモード」専用の簡易エージェント

- 通常のチャットは、既定どおり **シングルターン RAG（FR-RAG-1）** を用いる。
- これとは別に、ユーザーが明示的に以下のいずれかを行った場合、
  「リサーチモード（agentic モード）」を有効にする：
  - チャット画面で「高度リサーチモード」トグルを ON にする。
  - `/research` のようなスラッシュコマンドを使用する。

- リサーチモード時の挙動:
  1. **DOM Meister**:
     - ユーザーの問いを解析し、最大 3〜4 ステップ程度の **簡易プラン** を立てる。
       - 例: 「現状整理 → RAG 検索1 → クエリ変形 → RAG 検索2 → 統合」
  2. **Helper Meister**:
     - プランにしたがって RAG 用クエリを生成・変形する。
  3. **Research Meister**:
     - LangChain v1 の RAG チェーンを **最大 2〜3 回** 実行し、
       各ステップ結果を要約した中間ノートを作る。
  4. **Answer Meister**:
     - 中間ノートを統合し、IC-5 ライト形式（Markdown）で最終回答する。
     - 必要に応じて「内部でどんなステップを踏んだか」の簡易サマリを付ける。

- 制約:
  - 1 回のユーザーリクエストにつき：
    - LLM 呼び出し回数（DOM / Helper / Research / Answer 合計）: 最大 5 回程度。
    - RAG 呼び出し回数: 最大 2〜3 回。
    - サーバ側タイムアウト: 1 リクエストあたり 20〜30 秒の上限。
  - 通常モードとの違いが UI で分かるようにする（バッジ表示など）。

---

### 2.5 ファイルアップロード / ナレッジ登録

#### 2.5.1 チャットへのファイル添付

**FR-FILE-1 (P0)** セッション内ファイル添付  
- ユーザーはチャット送信時に **最大 10 ファイル** を添付可能。
- 制限（デフォルト値。環境変数で変更可能とする）:
  - 1 ファイル最大サイズ: **5MB**
  - 1 リクエスト合計サイズ: **15MB**
- 次のいずれかに該当する場合、リクエスト全体を拒否しエラーメッセージを返す：
  - ファイル数 > 10
  - 各ファイル or 合計サイズが上限超過
- 添付されたファイルのテキストは、そのまま LLM コンテキストに丸ごと詰めるのではなく、
  **FR-RAG-EPH-1 の Ephemeral RAG** を通じて利用する。

**FR-FILE-2 (P0)** 添付ファイル形式  
- PoC でサポートする形式：
  - `.pdf`（テキスト抽出可能なもの）
  - `.txt`（UTF-8）
  - `.md`
  - `.docx`
  - `.pptx`
  - `.xlsx`
- 画像やスキャン PDF (OCR 必須) は P1 以降。P0 ではエラー or 警告。

#### 2.5.2 ナレッジ登録（RAG 用）

**FR-FILE-3 (P1)** ナレッジ登録フロー  
- 権限を持つユーザー（例: admin）は、ファイルを社内ナレッジとして登録できる。
- プロセス:
  - ファイルアップロード（FR-FILE-1 と同じ制限。ただし設定値は別でもよい）
  - LangChain v1 で読み込み・分割
  - `knowledge_documents` とベクトルストアに保存

**FR-KB-1 (P0)** ナレッジ一覧（管理者画面）  
- 管理者は、自テナントのナレッジを一覧表示可能：
  - タイトル
  - 元ファイル名
  - ソース種別
  - 言語
  - ファイルサイズ
  - 登録者
  - 登録日時

**FR-KB-2 (P0)** ナレッジ詳細・テキストプレビュー  
- 詳細画面で以下を確認できる：
  - メタ情報（ファイル名 / MIME / サイズ / 言語 / 登録者 etc.）
  - チャンク数
  - Embedding モデル名
  - 抽出されたテキストの先頭 N 文字（例: 4,000 文字）

**FR-KB-3 (P0)** ナレッジ検索・フィルタリング  
- 管理者はナレッジを以下条件で検索可能：
  - タイトル・元ファイル名キーワード
  - 登録者
  - 言語
  - ソース種別
  - 登録日範囲

**FR-KB-DEL-1 (P1)** ナレッジ・ソフトデリート  
- 管理者はナレッジを無効化（`is_active = false`）でき、RAG 対象から除外する。
- 操作は `audit_logs` に記録。

**FR-KB-VERS-1 (P1)** バージョン管理と重複アップロード  
- `doc_key` / `version` / `is_latest` を `knowledge_documents` に持たせ、
  同じ doc_key の新規登録は新バージョンとして扱う。

---

### 2.6 メモリ / 検索（Structured / Episodic / Ephemeral）

**FR-MEM-1 (P0)** 短期記憶（コンテキスト）  
- 現在の `chat_session` の履歴を LLM に渡す短期記憶として保持。
- 長くなった場合、Helper が要約して縮約する。

**FR-MEM-2 (P0)** StructuredMemory  
- `structured_memory` にテナント/ユーザー/プロジェクト設定・プロファイル等を保存。
- DOM はチャット開始時・適宜、StructuredMemory をプロンプトに反映する。

**FR-MEM-3 (P0)** EpisodicMemory  
- セッション終了時（保存して終了 / `/reset`）に、Helper が要約を生成して `episodic_memory` に保存：
  - summary_text
  - topic_tags
  - importance (1〜5)
  - source_session_id

**FR-MEM-SEARCH-1 (P0)** EpisodicMemory 検索（ユーザー向け）  
- ユーザーは「メモリ」画面から自分の EpisodicMemory をキーワード検索できる。
- 検索対象: `summary_text` / `topic_tags`。
- 結果には日付・要約冒頭・重要度を表示。

**FR-MEM-SEARCH-2 (P1)** StructuredMemory 検索  
- StructuredMemory を key / ユーザー / テナントなどで検索・一覧可能。

**FR-MEM-5 (P1)** 関連メモ候補の提示  
- DOM は EpisodicMemory 検索を内部的に呼び出し、
  関連しそうなメモ候補を UI に提示し、ユーザーが選択したものだけコンテキストに取り込む。

---

### 2.7 セッション終了 / Reset

**FR-RESET-1 (P0)** 保存して終了 / 保存せず終了  
- ユーザーは「保存して終了」「保存せず終了」を選択可能。
- 保存して終了:
  - Helper が要約 → EpisodicMemory へ保存
  - StructuredMemory に必要な変更があれば反映
- 保存せず終了:
  - 長期メモリには保存しない。

**FR-RESET-2 (P0)** `/reset` と Reset インバリアント  
- `/reset` 実行時:
  1. セッション要約 → EpisodicMemory 保存
  2. 保存が **完全成功** した場合のみ、短期記憶をクリアして新セッション開始
  3. 失敗した場合はセッション継続 + エラー表示
- 「保存成功しない限り short-term を消さない」を Reset インバリアントとする。

**FR-RESET-3 (P0)** 保存せず強制リセット  
- `/reset` の保存処理が連続して失敗する場合などに備え、
  ユーザーは **「保存せずに強制リセット」** を選択できる。
- 挙動:
  - EpisodicMemory への保存処理を行わず、現在のセッションを `closed` として終了。
  - 短期記憶コンテキストを破棄し、新しい `session_id` でチャットを開始。
- UI:
  - 通常の `/reset` 実行が複数回失敗した際や、メニューから明示的に選んだ場合のみ表示するなど、
    誤操作を避ける設計とする。

---

### 2.8 フィードバック / AgentOps

**FR-FEED-1 (P0)** 👍/👎 + コメント  
- 各アシスタント回答に対して、ユーザーは：
  - 👍 / 👎
  - 任意コメント（テキスト）
  を付与できる。
- フィードバックは `feedback_events` に保存：
  - session_id, message_id, user_id, rating, comment, agent_run_id, created_at

**FR-FEED-2 (P1)** AgentOps ダッシュボード統合  
- フィードバックを集計し、モデル別・カテゴリ別のスコアを可視化。

---

### 2.9 設定・パーソナライズ (User / Tenant Settings)

#### 2.9.1 ユーザー設定

**FR-SET-USER-1 (P0)** 表示設定  
- ユーザー設定画面から以下を変更できる：
  - フォントサイズ（小 / 標準 / 大）
  - テーマ（ライト / ダーク）
  - UI 言語（日本語 / 英語）
- 設定は `user_settings` または StructuredMemory に保存され、次回ログイン時に反映。

**FR-SET-USER-2 (P0〜P1)** LLM プロファイル選択  
- ユーザーは「LLM プロファイル」を選択できるが、
  **管理者が事前定義したプロファイルの中からのみ選択**できる。
- 例: `標準` / `コスト節約` / `精度重視` など。
- DOM / LlmClient は選択されたプロファイルに応じてモデルやパラメータを選ぶ。

#### 2.9.2 管理者設定

**FR-SET-ADMIN-1 (P1)** テナント設定画面  
- 管理者は以下を設定可能：
  - Main LLM / Helper LLM プロバイダ（PoCでは実質 Gemini 固定でもよい）
  - RAG ON/OFF
  - 外部 Web ON/OFF
  - メモリ保持期間（日数）
  - ユーザーに見せる LLM プロファイルの定義

**FR-SET-ADMIN-2 (P1)** レート制御ポリシー  
- ユーザーごとの 1日あたり最大リクエスト数
- テナントごとの月間トークン上限（目標値）

---

### 2.10 i18n / 多言語対応

**FR-I18N-1 (P0)** UI i18n 基盤  
- Angular に i18n 機構（公式 i18n or ngx-translate）を入れ、UI 文言は翻訳ファイルで管理。
- 日本語をデフォルトとし、英語リソースは最低限用意。

**FR-I18N-2 (P1)** 回答の翻訳 / 言語切替  
- 回答に対して「英語で再表示」「日本語で再表示」ボタン。
- 多言語 RAG との連携は P1+。

---

### 2.11 ヘルプ・オンボーディング

**FR-HELP-1 (P0)** アプリ内ヘルプセンター  
- ヘッダーから「ヘルプ」画面を開き、以下のセクションを表示：
  - はじめに
  - チャットの使い方
  - ファイル添付・ナレッジ登録
  - メモリと `/reset`
  - 設定の使い方
  - フィードバックの意味
  - FAQ / トラブルシューティング
  - （リサーチモードの使い方）

**FR-HELP-2 (P0)** コンテキストヘルプ  
- 各主要画面に「?」アイコンを置き、クリックでヘルプセンターの該当セクションへジャンプ。

**FR-HELP-3 (P0)** 初回オンボーディングツアー  
- 初回ログイン時に 3〜5 ステップのチュートリアルオーバーレイを表示。
- 「次へ」「スキップ」「二度と表示しない」を選択可能。フラグを `user_settings` に保存。

**FR-HELP-4 (P0)** サンプルプロンプト・テンプレート  
- チャット入力欄のプレースホルダで複数のサンプルプロンプトを表示。
- 上部に「よく使うテンプレート」エリアを用意し、クリックで入力欄に挿入できる。

**FR-HELP-5 (P0)** エンプティステートのガイド  
- セッション一覧・ナレッジ一覧・メモリ画面が空のとき、「次に何をすべきか」を説明するメッセージを表示。

**FR-HELP-6 (P0)** エラーメッセージとヘルプリンク  
- エラーメッセージは人間が分かる日本語で表示し、必要に応じて該当ヘルプセクションへのリンクを付与。

**FR-HELP-7 (P1)** 管理者向けヘルプ  
- 管理者専用のヘルプセクション（テナント設定・ナレッジ運用・ログの見方など）。

**FR-HELP-8 (P1)** ヘルプ内検索  
- ヘルプ画面で、タイトル・本文キーワードによる簡易検索。

---

### 2.12 セキュリティ・コンテンツ安全性

**FR-SAFE-1 (P0)** コンテンツ安全ポリシー  
- 自傷行為、違法行為、差別、露骨な成人向けコンテンツなどの禁止カテゴリに対し、
  LLM 側の Safety とプロンプトガードレールの両方で応答を制限。
- 禁止カテゴリに該当する場合は、安全な代替メッセージを返す。

**FR-SAFE-2 (P1)** Safety ログとダッシュボード  
- ブロックイベントを記録し、管理者がカテゴリ別件数を確認できる。

**FR-PROMPT-VERS-1 (P0)** Prompt / Policy バージョン記録  
- 各 `chat_session` に、利用した System Prompt / llm-policy / tenant_settings のバージョンを紐づける。

**FR-TOOL-GOV-1 (P1)** ツール登録と権限管理  
- エージェントが使用できるツールは登録済みのものに限定し、
  どのエージェント・テナントから利用可能かメタデータで管理。

**FR-OFFBOARD-1 (P1)** テナント終了・データ削除ポリシー  
- テナント終了時に、データ削除 or 一定期間保管のポリシーを選択可能。
- 削除対象には chat_sessions / messages / memories / knowledge / AgentOps ログなどが含まれる。

---

## 3. 非機能要件 (NFR)

### 3.1 性能・UX

**NFR-PERF-1 (P0)** レイテンシ  
- 通常モード：
  - チャット送信からストリーミング開始まで、体感 **2〜5 秒以内** を目標とする。
- リサーチモード（FR-AGENT-1）：
  - 内部で複数ステップを実行するため、ストリーミング開始がやや遅くなる可能性があるが、
    ユーザーには「高度リサーチ中」のインジケータを表示する。
- RAG が重い場合も、即時に「処理中」インジケータを表示する。

---

### 3.2 信頼性・Reset 整合性

**NFR-REL-1 (P0)** 営業時間中の安定稼働  
- 24/7 は必須とせず、PoC では「平日日中に実用的に使える」ことを目標とする。

**NFR-RESET-CONSISTENCY-1 (P0)** Reset 排他制御  
- `/reset` / 「保存して終了」は `session_id` ベースのロックを行い、同時実行を防ぐ。
- トランザクション単位で EpisodicMemory 保存の成功を確認できた場合のみ、短期記憶を破棄。

---

### 3.3 セキュリティ・プライバシー

**NFR-SEC-1 (P0)** At-Rest 暗号化  
- 保存される全データ（DB・ベクトルストア・バックアップ）は At-Rest 暗号化。
- 特に PII を含むカラムはアプリ側でも暗号化を検討。

**NFR-SEC-2 (P0)** PII フィルタ  
- 入力テキストは PII Service でマスク / トークン化し、外部 LLM やログにはマスク後の値のみ送る。

**NFR-ERR-1〜3 (P0)** エラー・例外ハンドリング標準  
- エラーカテゴリ（validation/auth/llm/rag/external/unexpected）ごとにエラーコードとレスポンス形式を統一。
- `except Exception: pass` 禁止。想定例外ごとに適切なログ・ユーザーメッセージを返却。
- 想定外例外は共通ハンドラでログ + 500。

**NFR-SECRET-1 (P0)** シークレット管理  
- LLM API キー・DB パスワード等のシークレットは環境変数 or シークレットマネージャから注入し、
  ソースコードやイメージにハードコードしない。

---

### 3.4 ログ・メトリクス・Observability

**NFR-OBS-1 (P0)** トレース ID  
- すべてのリクエストに `trace_id` を付与し、Backend ログ・AgentOps ログ間で相互参照可能にする。

**NFR-OBS-2 (P0)** PII マスキングログ  
- ログには PII を直接出力せず、ハッシュ化 / マスク済み文字列だけを残す。

**NFR-OBS-3 (P1)** メトリクス収集  
- リクエスト数・エラー率・LLM トークン数・レイテンシなどの基本メトリクスを採取し、
  ダッシュボードで可視化。

---

### 3.5 スキーマ・マイグレーション

**NFR-SCHEMA-1 (P0)** Alembic 管理  
- DB スキーマ変更はすべて Alembic マイグレーションで管理し、手作業の DROP/CREATE を禁止。

**NFR-SCHEMA-2 (P0)** 追加的変更優先  
- 破壊的変更（カラム削除・名前変更）は「新カラム追加 → 移行 → 後日削除」の段階的手順を徹底。
- PoC 以降も DB 作り直しなしで運用できるようにする。

---

### 3.6 デプロイ・環境分離（Docker / ENV）

**NFR-DEP-1 (P0)** docker-compose 一発起動  
- `docker-compose up` で Backend / Frontend / DB / Redis をまとめて起動できる。

**NFR-DEP-2 (P0)** マルチステージビルド  
- Backend / Frontend の Dockerfile はマルチステージビルドを利用し、実行イメージをスリム化。

**NFR-ENV-1 (P0)** 環境分離  
- `dev` / `stg` / `prod` 環境を論理的に分離。
- `prod` データを `dev` で直接利用することを禁止（必要なら匿名化データを利用）。

---

### 3.7 PDF・日本語文字化け対策（将来）

**NFR-PDF-1 (P1〜P2)** PDF 出力時のフォント埋め込み  
- PDF 出力機能を実装する場合、Noto Sans/Serif CJK JP 等を埋め込み、
  日本語が「■」に文字化けしないようにする。

---

### 3.8 モデル・ライブラリアップデート

**NFR-UPGRADE-1 (P1)** アップデート時のテスト  
- Gemini モデルや LangChain / FastAPI / Angular のメジャーアップデート時には、
  代表的ユースケースに対するリグレッションテストを実施。

---

## 4. インタフェース概要 (API 概要 – P0)

※詳細な I/F 仕様は別途 `api_design_p0_core_chat.md` で定義するが、ここで主要エンドポイントを列挙する。

- `POST /api/chat/send`
  - チャット送信 + ファイル添付
  - パラメータに「リサーチモード」のフラグまたは `/research` コマンドを含める場合あり
- `GET /api/chat/stream/{session_id}`
  - 応答ストリーミング（Markdown）
- `POST /api/chat/reset`
  - `/reset` 操作（通常 / 強制）
- `POST /api/feedback`
  - 👍/👎 + コメント
- `GET /api/memory/episodic/search`
  - EpisodicMemory 検索
- `GET /api/admin/knowledge`
  - ナレッジ一覧・検索
- `GET /api/admin/knowledge/{id}`
  - ナレッジ詳細・プレビュー
- `GET/POST /api/user/settings`
  - ユーザー設定取得・更新
- `GET/POST /api/admin/tenant-settings` (P1)
  - テナント設定取得・更新
- `GET /api/help/content`
  - ヘルプセンター用コンテンツ取得（静的でもよい）

---

## 5. 範囲外 / 将来検討

- 画像・スキャン PDF の OCR 取り込み
- 高度な Agentic RAG / 自己改善ループ（FR-RAG-3 の本格実装）
- フル AI ガバナンス（EU AI Act 完全準拠）
- 外部モニタリングサービスとの統合（Datadog / Prometheus など）
- エージェント自動評価・自動チューニング（本格的な AgentOps）
