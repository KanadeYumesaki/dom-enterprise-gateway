# 機能要件: DOM Enterprise Gateway P0 Core Chat

## 1. 概要
このドキュメントは、「DOM Enterprise Gateway PoC Core Chat」機能が満たすべき要件を定義します。システムは、認証されたユーザーがマルチエージェント、RAG、長期メモリを通じて高度なチャット支援を受けるための、ガバナンス付きLLMゲートウェイとして機能します。

---

## 2. 認証・認可 (Auth / RBAC)

### 2.1. OAuth2.0/OIDC認証
- **REQ-AUTH-1:** ユーザーがシステムにアクセスしようとしたとき、**DOM Enterprise Gatewayは**、企業のIDプロバイダ(IdP)を利用したOAuth2.0 / OIDCプロトコル経由でユーザーを認証するものとする。
- **REQ-AUTH-2:** **DOM Enterprise Gatewayバックエンドは**、BFF (Backend for Frontend) パターンを採用し、アクセストークンを直接フロントエンドに公開しないものとする。

### 2.2. ロールベースアクセス制御 (RBAC) とテナント分離
- **REQ-AUTH-3:** **DOM Enterprise Gatewayは**、各ユーザーに `user` または `admin` のいずれかのロールを割り当てるものとする。
- **REQ-AUTH-4:** ユーザーのロールが `admin` である場合、**DOM Enterprise Gatewayは**、管理者専用のAPIエンドポイントおよびUI画面へのアクセスを許可するものとする。
- **REQ-AUTH-5:** **DOM Enterprise Gatewayは**、チャット履歴、メモリ、ナレッジドキュメントを含むすべてのリソースへのアクセスを、ユーザーが所属するテナント単位で完全に分離するものとする。

### 2.3. 初期管理者の自動登録
- **REQ-AUTH-6:** システム起動時に環境変数 `INITIAL_ADMIN_EMAIL` が設定されている場合、そのメールアドレスを持つユーザーが初回ログインしたときに、**DOM Enterprise Gatewayは**、そのユーザーを `admin` ロールとして自動的に登録（または更新）するものとする。
- **REQ-AUTH-7:** `INITIAL_ADMIN_EMAIL` に該当しないユーザーが初回ログインしたとき、**DOM Enterprise Gatewayは**、そのユーザーを `user` ロールで自動的にプロビジョニングするものとする。

---

## 3. コアチャットとオーケストレーション

### 3.1. チャットの送受信
- **REQ-CHAT-1:** 認証済みのユーザーがメッセージを送信したとき、**DOM Enterprise Gatewayは**、そのメッセージを現在のチャットセッションに追加し、アシスタントからの応答を生成するものとする。
- **REQ-CHAT-2:** アシスタントが応答を生成している間、**DOM Enterprise Gatewayは**、その応答をストリーミング（Server-Sent EventsまたはWebSocket）でフロントエンドに送信するものとする。

### 3.2. IC-5ライト形式の回答
- **REQ-CHAT-3:** アシスタントが最終回答を生成するとき、**DOM Enterprise Gatewayは**、少なくとも「## Decision」（結論）、「## Why」（理由・背景）、「## Next 3 Actions」（次の3つのアクション）のセクションを含むMarkdown形式のテキストを生成するものとする。

---

## 4. RAG (Retrieval-Augmented Generation) とナレッジ

### 4.1. 基本的なRAG機能
- **REQ-RAG-1:** ユーザーの質問に回答するためにナレッジ検索が必要な場合、**DOM Enterprise Gatewayは**、LangChain v1のRAGチェーン（DocumentLoader → TextSplitter → Embedding → VectorStore）を実行し、取得した情報を基に応答を生成するものとする（シングルターンRAG）。

### 4.2. 参照ソースの明示
- **REQ-RAG-2:** **DOM Enterprise Gatewayは**、生成するすべての回答に、その根拠となった参照ソース（例：RAG、Memory、Assumption）の一覧を添付するものとする。

### 4.3. セッション限定のEphemeral RAG
- **REQ-RAG-3:** ユーザーがチャットセッションにファイルを添付したとき、**DOM Enterprise Gatewayは**、そのファイルから抽出したテキストを当該セッション専用の一時的なベクトルインデックスに登録するものとする。
- **REQ-RAG-4:** 質問に関連するコンテキストをLLMに渡す際、**DOM Enterprise Gatewayは**、セッション専用インデックスから検索した上位K件のチャンクのみを含めるものとする。
- **REQ-RAG-5:** チャットセッションが終了したとき、**DOM Enterprise Gatewayは**、そのセッション専用の一時的なベクトルインデックスを削除するものとする。

### 4.4. Agentic Researchモード
- **REQ-RAG-6:** ユーザーが「高度リサーチモード」を有効にした状態で質問したとき、**DOM Enterprise Gatewayは**、(1)問いを分析して簡易プランを立て、(2)プランに基づきRAGクエリを生成・変形し、(3)RAGチェーンを最大2〜3回実行して情報を収集・要約し、(4)最終的な回答を統合・生成する、という複数ステップのエージェント処理を実行するものとする。
- **REQ-RAG-7:** Agentic Researchモードの実行中、**DOM Enterprise Gatewayは**、UI上に「高度リサーチ中」であることを示すインジケータを表示するものとする。

---

## 5. ファイル管理

### 5.1. チャットへのファイル添付
- **REQ-FILE-1:** ユーザーがチャットでファイルを添付しようとしたとき、**DOM Enterprise Gatewayは**、1リクエストあたりのファイル数が10個以下、各ファイルサイズが5MB以下、合計サイズが15MB以下であるか検証するものとする。
- **REQ-FILE-2:** もしファイル数またはサイズが上限を超えた場合、**DOM Enterprise Gatewayは**、リクエストを拒否し、理由を説明するエラーメッセージをユーザーに表示するものとする。
- **REQ-FILE-3:** **DOM Enterprise Gatewayは**、少なくとも `.pdf`, `.txt`, `.md`, `.docx`, `.pptx`, `.xlsx` 形式のファイル添付をサポートするものとする。

### 5.2. ナレッジ管理 (管理者向け)
- **REQ-FILE-4:** ロールが `admin` のユーザーがナレッジ管理画面にアクセスしたとき、**DOM Enterprise Gatewayは**、登録済みのナレッジドキュメントの一覧（タイトル、ファイル名、登録者、登録日など）を表示するものとする。
- **REQ-FILE-5:** ロールが `admin` のユーザーがナレッジを検索したとき、**DOM Enterprise Gatewayは**、キーワード、登録者、言語、日付範囲によるフィルタリング機能を提供するものとする。
- **REQ-FILE-6:** ロールが `admin` のユーザーが特定のナレッジドキュメントを選択したとき、**DOM Enterprise Gatewayは**、そのメタ情報と抽出されたテキストのプレビューを表示するものとする。
- **REQ-FILE-7:** ロールが `admin` のユーザーが新しいナレッジファイルをアップロードしたとき、**DOM Enterprise Gatewayは**、既存のファイルとハッシュまたはファイル名＋パスが一致する場合、上書き／別バージョンとして保存／キャンセルのいずれかを選択できることとする。
- **REQ-FILE-8:** ロールが `admin` のユーザーがナレッジの削除を指示したとき、**DOM Enterprise Gatewayは**、RAG の検索対象から即時に除外しつつ、監査ログに記録すること（物理削除か論理削除かもここで指定）。
- **REQ-FILE-9:** ロールが `admin` のユーザーが「再インデックス」を実行したとき、**DOM Enterprise Gatewayは**、該当ドキュメントのベクトル生成を再実行することとする。

---

## 6. メモリ管理

### 6.1. メモリの種類
- **REQ-MEM-1:** ユーザーとの対話中、**DOM Enterprise Gatewayは**、現在のセッションの会話履歴を短期記憶としてLLMのコンテキストに含めるものとする。
- **REQ-MEM-2:** **DOM Enterprise Gatewayは**、テナントやユーザーのプロファイル、プロジェクト設定などを構造化メモリ(StructuredMemory)として永続化し、適宜プロンプトに反映するものとする。
- **REQ-MEM-3:** セッションが「保存して終了」または `/reset` で終了するとき、**DOM Enterprise Gatewayは**、そのセッションの要約をエピソード記憶(EpisodicMemory)として保存するものとする。

### 6.2. メモリの検索
- **REQ-MEM-4:** ユーザーがメモリ画面にアクセスしたとき、**DOM Enterprise Gatewayは**、ユーザー自身のEpisodicMemoryをキーワードで検索する機能を提供するものとする。

### 6.3. セッション終了とReset
- **REQ-MEM-5:** ユーザーが「保存して終了」を選択したとき、**DOM Enterprise Gatewayは**、セッションの要約をEpisodicMemoryに保存してからセッションを閉じるものとする。
- **REQ-MEM-6:** ユーザーが `/reset` コマンドを実行したとき、**DOM Enterprise Gatewayは**、まずセッションの要約をEpisodicMemoryに保存し、その保存が成功した場合にのみ短期記憶をクリアして新しいセッションを開始するものとする（Resetインバリアント）。
- **REQ-MEM-7:** もし `/reset` 時の要約保存が連続して失敗した場合、**DOM Enterprise Gatewayは**、「保存せずに強制リセット」するオプションをユーザーに提示するものとする。
- **REQ-MEM-8:** セッションがタイムアウトまたはブラウザの異常終了により切断された場合、**DOM Enterprise Gatewayは**、Ephemeral Session Store から直近 N 件のメッセージを復元し、ユーザーが一定時間内（例: 30 分）であれば同じセッションを再開できるようにすること。
- **REQ-MEM-9:** ロールが admin のユーザーは、テナント内の StructuredMemory / EpisodicMemory を対象に、ユーザー・プロジェクト・タグ・期間などで検索・閲覧できること（内容には PII マスク適用済であること）。
- **REQ-MEM-10:** ユーザーは、自身のチャットセッションログおよび関連する EpisodicMemory を、Markdown または JSON 形式でエクスポートできること。
- **REQ-MEM-11:** 管理者は、特定プロジェクトまたは期間に紐づくメモリを、監査・バックアップ目的でエクスポートできること。
---

## 7. UI/UX とヘルプ

### 7.1. フィードバック
- **REQ-UX-1:** **DOM Enterprise Gatewayは**、アシスタントの各回答に対して、ユーザーが「👍/👎」評価とテキストコメントを送信できる機能を提供するものとする。

### 7.2. ユーザー設定
- **REQ-UX-2:** ユーザーが設定画面にアクセスしたとき、**DOM Enterprise Gatewayは**、UIの表示言語（日本語/英語）、テーマ（ライト/ダーク）、フォントサイズ（小/標準/大）を変更するオプションを提供するものとする。

### 7.3. ヘルプとオンボーディング
- **REQ-UX-3:** ユーザーがヘルプセンターにアクセスしたとき、**DOM Enterprise Gatewayは**、「はじめに」「チャットの使い方」「ファイル添付」「メモリとReset」「設定」「FAQ」などのトピックを含むヘルプコンテンツを表示するものとする。
- **REQ-UX-4:** ユーザーが初めてログインしたとき、**DOM Enterprise Gatewayは**、システムの主要機能を紹介する3〜5ステップのオンボーディングツアーを表示するものとする。
- **REQ-UX-5:** **DOM Enterprise Gatewayは**、チャット入力欄にサンプルプロンプトをプレースホルダとして表示し、クリックで入力可能なテンプレートを提供するものとする。
- **REQ-UX-6:** システムでエラーが発生したとき、**DOM Enterprise Gatewayは**、人間が理解可能な日本語のエラーメッセージと、関連するヘルプページへのリンクを表示するものとする。
- **REQ-UX-7:** DOM Enterprise Gateway は、各回答に対する 👍/👎 評価およびコメントを、セッションID・ユーザーID・タイムスタンプとともに永続化し、将来の AgentOps 評価・モデル改善に利用できるようにすること。

---

## 8. 非機能要件

### 8.1. セキュリティ
- **REQ-NFR-1:** **DOM Enterprise Gatewayは**、LLMにテキストを渡す前、およびログに記録する前に、個人情報(PII)をマスクする処理をはさむものとする。
- **REQ-NFR-2:** **DOM Enterprise Gatewayは**、APIキーやDBパスワードなどのシークレット情報を、ソースコードにハードコードせず、環境変数またはシークレット管理システム経由で読み込むものとする。
- **REQ-NFR-3:** **DOM Enterprise Gatewayは**、自傷行為、違法行為、差別といった安全でないコンテンツの生成をブロックし、代替の安全なメッセージを返すものとする。

### 8.2. 信頼性と性能
- **REQ-NFR-4:** 通常のチャットモードにおいて、ユーザーがメッセージを送信してから応答のストリーミングが開始されるまでの体感時間を、**DOM Enterprise Gatewayは**、5秒以内に収めることを目標とする。
- **REQ-NFR-5:** **DOM Enterprise Gatewayは**、すべてのデータベーススキーマの変更をAlembicマイグレーションスクリプトを通じて管理するものとする。

### 8.3. 運用・保守
- **REQ-NFR-6:** **DOM Enterprise Gatewayは**、`docker-compose up` コマンド一発で、バックエンド、フロントエンド、データベース、キャッシュを含むすべてのサービスが起動可能であるものとする。
- **REQ-NFR-7:** **DOM Enterprise Gatewayは**、すべてのAPIリクエストとバックグラウンド処理のログに、追跡用のトレースIDを付与するものとする。
- **REQ-NFR-8:** DOM Enterprise Gateway は、ユーザー単位・テナント単位でのレートリミット（例: 1 分あたりのリクエスト数）および日次クォータ（例: 1 日あたりの実行回数またはトークン数）を設定できること。
- **REQ-NFR-9:** レートリミット超過時には、HTTP 429 と人間に分かるメッセージを返し、可能であれば残り時間を UI に表示すること。
- **REQ-NFR-10:** DOM Enterprise Gateway は、保存されるすべてのデータ（DB・ベクトルストア・ファイルストレージ）を at-rest 暗号化で保護すること。
- **REQ-NFR-11:** すべてのクライアント〜サーバー通信は TLS(HTTPS) 経由で行うこと。

### 8.4. 監査ログ
- **REQ-GOV-1:** DOM Enterprise Gateway は、各チャット回答ごとに内部的な Explanation Object（Decision, Why, Sources, 使用メモリ, 実行モードなど）を生成し、管理者が閲覧できるように永続化すること。
- **REQ-GOV-2:** reset 実行、ポリシー変更、ナレッジ削除などの重要操作は、誰が・いつ・何をしたかを含む監査ログとして保存し、管理者画面から検索・閲覧できること。