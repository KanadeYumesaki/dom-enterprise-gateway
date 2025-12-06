/**
 * ユーザーのロール定義
 * - admin: 管理者（テナント設定やナレッジ管理が可能）
 * - user: 一般ユーザー
 */
export type UserRole = 'admin' | 'user';

/**
 * ユーザー情報のインターフェース
 * バックエンドの AuthenticatedUser スキーマに対応
 */
export interface User {
    id: string;          // ユーザーの一意なID
    email: string;       // メールアドレス
    name?: string;       // 表示名（任意）
    roles: UserRole[];   // 所持しているロールのリスト
    tenant_id: string;   // 所属するテナントのID
    picture_url?: string; // プロフィール画像のURL（任意）
}
