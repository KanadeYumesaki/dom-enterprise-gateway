/**
 * Chat関連のデータモデル定義
 * 
 * 役割:
 * - Backend (FastAPI) の Pydantic スキーマと整合した型定義を提供します。
 * - チャット画面で扱うメッセージ、セッション、IC-5形式、エラーなどの型を定義します。
 * 
 * いつ使うか:
 * - ApiService でのリクエスト/レスポンス型として使用
 * - ChatComponent やその子コンポーネントで状態管理に使用
 */

/**
 * チャットメッセージの role (送信者)
 */
export type ChatMessageRole = 'user' | 'assistant' | 'system';

/**
 * ソースの種別（参照元の情報）
 */
export type ChatSourceType = 'RAG' | 'Memory' | 'Assumption' | 'Web' | 'Other';

/**
 * チャットメッセージの参照ソース
 * 
 * LLMがどこから情報を得たかを示します。
 */
export interface ChatSource {
    /** ソースの種別 */
    type: ChatSourceType;
    /** ソースのタイトルまたはラベル */
    title: string;
    /** ドキュメントIDなどの識別子 (optional) */
    identifier?: string;
}

/**
 * チャットメッセージ (Response)
 * 
 * Backend の ChatMessageResponse に対応
 */
export interface ChatMessage {
    /** メッセージID (UUID) */
    id: string;
    /** セッションID (UUID) */
    sessionId: string;
    /** 送信者 (user / assistant / system) */
    role: ChatMessageRole;
    /** メッセージ本文 */
    content: string;
    /** LLMの生レスポンス (optional) */
    rawLlmResponse?: Record<string, unknown> | null;
    /** 参照ソース一覧 (optional) */
    sources?: ChatSource[];
    /** 作成日時 (ISO 8601) */
    createdAt: string;
    /** 更新日時 (ISO 8601) */
    updatedAt: string;
}

/**
 * チャットメッセージ送信リクエスト
 * 
 * Backend の ChatMessageCreate に対応
 */
export interface ChatMessageRequest {
    /** セッションID */
    sessionId: string;
    /** メッセージ内容 */
    content: string;
    /** 送信者 (通常は 'user') */
    role: ChatMessageRole;
}

/**
 * チャットセッション (Response)
 * 
 * Backend の ChatSessionResponse に対応
 */
export interface ChatSession {
    /** セッションID (UUID) */
    id: string;
    /** ユーザーID (UUID) */
    userId: string;
    /** テナントID (UUID) */
    tenantId: string;
    /** セッションタイトル (optional) */
    title?: string | null;
    /** アクティブ状態 */
    isActive: boolean;
    /** 作成日時 (ISO 8601) */
    createdAt: string;
    /** 更新日時 (ISO 8601) */
    updatedAt: string;
}

/**
 * IC-5 ライト形式の構造
 * 
 * Markdown で返される IC-5 形式をパースした結果を保持します。
 */
export interface Ic5Lite {
    /** Decision セクションの内容 */
    decision: string;
    /** Why セクションの内容 */
    why: string;
    /** Next 3 Actions の配列 */
    nextActions: string[];
    /** パース元の Markdown 全体 (デバッグ用) */
    rawMarkdown: string;
    /** パース時の警告メッセージ (optional) */
    parseWarnings?: string[];
}

/**
 * チャット添付ファイルの状態
 */
export type ChatAttachmentStatus = 'pending' | 'uploading' | 'uploaded' | 'failed';

/**
 * チャット添付ファイル
 * 
 * クライアント側でファイルアップロードの状態を管理するために使用します。
 */
export interface ChatAttachment {
    /** クライアント側の一時ID */
    id: string;
    /** ファイル名 */
    fileName: string;
    /** ファイルサイズ (bytes) */
    fileSize: number;
    /** アップロード状態 */
    status: ChatAttachmentStatus;
    /** アップロード失敗時のエラー (optional) */
    error?: ChatError;
    /** Backend から返されたドキュメントID (optional, uploaded後に設定) */
    documentId?: string;
}

/**
 * エラーの種別
 * 
 * エラーを次のカテゴリに分類して扱います:
 * - network: オフ ライン / DNS / CORS 等
 * - timeout: 明示的なタイムアウト
 * - http-4xx: Validation / 認証 / 認可 / 404 / 429 等
 * - http-5xx: サーバ内部エラー / 依存サービス障害
 * - parse: JSON パースエラーや想定外スキーマ
 * - sse: SSE ストリーム中断・再接続失敗
 * - validation: フロント側バリデーションエラー
 * - unknown: 予期しない例外
 */
export type ChatErrorKind =
    | 'network'
    | 'timeout'
    | 'http-4xx'
    | 'http-5xx'
    | 'parse'
    | 'sse'
    | 'validation'
    | 'unknown';

/**
 * チャットエラー
 * 
 * エラーの種別とメッセージ、詳細情報を保持します。
 */
export interface ChatError {
    /** エラー種別 */
    kind: ChatErrorKind;
    /** ユーザー向けエラーメッセージ (日本語) */
    message: string;
    /** 詳細情報 (optional, デバッグ用) */
    details?: unknown;
}

/**
 *ファイルアップロードレスポンス
 * 
 * Backend の FileUploadResponse に対応
 */
export interface FileUploadResponse {
    /** ドキュメントID (UUID) */
    id: string;
    /** テナントID (UUID) */
    tenantId: string;
    /** ファイル名 */
    fileName: string;
    /** ファイルパス (Backend内部パス) */
    filePath: string;
    /** ファイルタイプ (MIME type, optional) */
    fileType?: string | null;
    /** ファイルサイズ (string表現, 例: "10MB", optional) */
    fileSize?: string | null;
    /** アップロード実行ユーザーID (UUID, optional) */
    uploadedByUserId?: string | null;
    /** アクティブ状態 */
    isActive: boolean;
    /** 作成日時 (ISO 8601) */
    createdAt: string;
    /** 更新日時 (ISO 8601) */
    updatedAt: string;
}

/**
 * SSEストリームイベント
 * 
 * Backend から送信される SSE イベントの型を定義します。
 */
export interface ChatStreamEvent {
    /** イベント種別 */
    type: 'token' | 'complete' | 'error';
    /** トークンデータ (type === 'token' の場合) */
    token?: string;
    /** エラーメッセージ (type === 'error' の場合) */
    error?: string;
}
