/**
 * API呼び出し時に発生したエラーを表現するクラス
 * HTTPステータスコードや、バックエンドからのエラーメッセージを保持します。
 */
export class ApiError extends Error {
    /**
     * @param message エラーメッセージ（開発者向け、またはログ用）
     * @param status HTTPステータスコード（例: 400, 404, 500）。ネットワークエラーの場合は 0 など。
     * @param code アプリケーション固有のエラーコード（バックエンドが返す場合）
     * @param details 詳細なエラー情報やバリデーションエラーの中身など
     */
    constructor(
        public override message: string,
        public status: number,
        public code?: string,
        public details?: any
    ) {
        super(message);
        this.name = 'ApiError';

        // プロトタイプチェーンの修正（TypeScriptでErrorを継承する場合のお作法）
        Object.setPrototypeOf(this, ApiError.prototype);
    }

    /**
     * ユーザー向けのエラーメッセージを取得するメソッド（簡易実装）
     * ステータスコードに応じて、画面に表示すべきメッセージを返します。
     */
    getUserMessage(): string {
        if (this.status === 0) {
            return 'サーバーに接続できません。インターネット接続を確認してください。';
        }
        if (this.status === 401) {
            return 'セッションの有効期限が切れました。再度ログインしてください。';
        }
        if (this.status === 403) {
            return 'この操作を行う権限がありません。';
        }
        if (this.status >= 500) {
            return 'サーバー側でエラーが発生しました。しばらく待ってから再試行してください。';
        }
        return this.message || '予期せぬエラーが発生しました。';
    }
}
