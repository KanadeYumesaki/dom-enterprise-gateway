/**
 * Help セクション表示用の型定義
 *
 * 役割:
 * - `/api/help/content` のレスポンスを型安全に扱うためのモデル。
 * - フロント側で一覧表示／詳細表示に利用する。
 *
 * いつ使われるか:
 * - HelpPageComponent が初期表示時に ApiService 経由で取得し、左ペインの一覧や右ペインの本文に表示する。
 */
export interface HelpSection {
    /** セクション ID (UUID 想定) */
    id: string;
    /** タイトル（左ペイン一覧で表示） */
    title: string;
    /** 本文（Markdown/プレーンテキスト） */
    content: string;
    /** カテゴリ user / admin / all */
    category?: 'user' | 'admin' | 'all';
    /** 最終更新日時 (ISO 8601) */
    updatedAt?: string;
}

/**
 * Help API 用のエラー型
 *
 * 役割:
 * - エラーを分類して UI で適切な文言を出すためのカテゴリ。
 */
export interface HelpError {
    kind: 'network' | 'http-401' | 'http-403' | 'http-404' | 'http-4xx' | 'http-5xx' | 'unknown';
    message: string;
    details?: unknown;
}
