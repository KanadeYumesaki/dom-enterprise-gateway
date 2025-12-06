/**
 * Settings (ユーザー設定) 関連のデータモデル定義
 * 
 * 役割:
 * - Backend の user_settings API と整合した型定義を提供します。
 * - Settings画面で扱うユーザー設定の型を定義します。
 * 
 * いつ使うか:
 * - ApiService でのリクエスト/レスポンス型として使用
 * - SettingsPageComponent で状態管理に使用
 */

/**
 * ユーザー設定（Backend の UserSettingsRead に対応）
 */
export interface UserSettings {
    /** 設定ID (UUID) */
    id: string;
    /** テナントID (UUID) */
    tenantId: string;
    /** ユーザーID (UUID) */
    userId: string;
    /** UIテーマ */
    theme: 'light' | 'dark';
    /** UI言語 */
    language: 'ja' | 'en';
    /** フォントサイズ */
    fontSize: 'small' | 'medium' | 'large';
    /** LLMプロファイル (P1拡張用) */
    llmProfile?: string | null;
    /** オンボーディングツアーを見たか */
    hasSeenOnboarding: boolean;
    /** オンボーディングツアーをスキップしたか */
    onboardingSkipped: boolean;
    /** 作成日時 */
    createdAt: string;
    /** 更新日時 */
    updatedAt?: string | null;
}

/**
 * ユーザー設定更新用（部分更新対応）
 * 
 * Backend の UserSettingsUpdate に対応。
 * 全フィールドが Optional なので、変更したいフィールドのみ送信できます。
 */
export interface UserSettingsUpdate {
    theme?: 'light' | 'dark';
    language?: 'ja' | 'en';
    fontSize?: 'small' | 'medium' | 'large';
    llmProfile?: string | null;
    hasSeenOnboarding?: boolean;
    onboardingSkipped?: boolean;
}

/**
 * Settings API のエラー型
 */
export interface SettingsError {
    kind: 'network' | 'http-401' | 'http-403' | 'http-4xx' | 'http-5xx' | 'unknown';
    message: string;
    details?: unknown;
}
