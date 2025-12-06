/**
 * Knowledge (ナレッジ) 関連のデータモデル定義
 * 
 * 役割:
 * - Backend (FastAPI) の Pydantic スキーマと整合した型定義を提供します。
 * - ナレッジ管理画面で扱うドキュメント一覧・詳細・フィルタの型を定義します。
 * 
 * いつ使うか:
 * - ApiService でのリクエスト/レスポンス型として使用
 * - KnowledgePageComponent やその子コンポーネントで状態管理に使用
 */

/**
 * ナレッジドキュメント (一覧表示用)
 * 
 * Backend の FileUploadResponse に対応
 * （KnowledgeDocument モデルと同じ構造）
 */
export interface KnowledgeDocument {
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
 * ナレッジドキュメント詳細 (P0: メタデータ表示 / P1: ファイル内容プレビュー)
 * 
 * 役割:
 * - 一覧から選択した1件の詳細情報を保持します。
 * - P0 では基本的なメタデータのみ表示。
 * - P1 でファイル内容のテキストプレビューを拡張予定。
 */
export interface KnowledgeDetail {
    /** ドキュメント基本情報 */
    doc: KnowledgeDocument;
    /** 
     * ファイル内容のプレビューテキスト (optional)
     * 
     * P0 では null または空文字列。
     * P1 で Backend からファイル内容の抽出テキストを取得し、ここに格納する予定。
     */
    previewText?: string | null;
}

/**
 * ナレッジドキュメント検索・フィルタ条件
 * 
 * Backend の GET /api/admin/knowledge クエリパラメータに対応
 */
export interface KnowledgeFilter {
    /** ファイル名検索クエリ */
    searchQuery?: string;
    /** ページネーション: スキップ件数 */
    skip?: number;
    /** ページネーション: 取得上限 */
    limit?: number;
}

/**
 * エラーの種別
 * 
 * Knowledge API のエラーを次のカテゴリに分類します:
 * - network: オフライン / DNS / CORS 等
 * - timeout: 明示的なタイムアウト
 * - http-401: 認証エラー（トークン期限切れ等）
 * - http-403: 権限エラー（管理者権限なし）
 * - http-404: リソース未発見
 * - http-4xx: その他のクライアントエラー
 * - http-5xx: サーバ内部エラー / 依存サービス障害
 * - parse: JSON パースエラーや想定外スキーマ
 * - unknown: 予期しない例外
 */
export type KnowledgeErrorKind =
    | 'network'
    | 'timeout'
    | 'http-401'
    | 'http-403'
    | 'http-404'
    | 'http-4xx'
    | 'http-5xx'
    | 'parse'
    | 'unknown';

/**
 * ナレッジAPIエラー
 * 
 * エラーの種別とメッセージ、詳細情報を保持します。
 */
export interface KnowledgeError {
    /** エラー種別 */
    kind: KnowledgeErrorKind;
    /** ユーザー向けエラーメッセージ (日本語) */
    message: string;
    /** 詳細情報 (optional, デバッグ用) */
    details?: unknown;
}
