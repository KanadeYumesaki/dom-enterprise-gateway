/**
 * API呼び出し時に発生したエラーを表現するクラス
 * 
 * 役割:
 * - HTTPステータスコードやバックエンドからのエラー詳細をまとめて持ち運びます。
 * - 画面に表示するための「わかりやすい日本語メッセージ」を提供します。
 */
export class ApiError extends Error {
    /**
     * @param message 開発者向けの英語エラーメッセージ（ログ用）
     * @param status HTTPステータスコード (0はネットワークエラーなど)
     * @param code バックエンドが定義した固有のエラーコード (任意)
     * @param details バリデーションエラーの詳細など (任意)
     * @param url エラーが発生したリクエストURL (任意)
     */
    constructor(
        public override message: string,
        public status: number,
        public code?: string,
        public details?: unknown,
        public url?: string
    ) {
        super(message);
        this.name = 'ApiError';

        // プロトタイプチェーンの修正（TypeScriptでErrorを継承する場合のお作法）
        // これをしないと instanceof ApiError が正しく動作しないことがあります。
        Object.setPrototypeOf(this, ApiError.prototype);
    }

    /**
     * ユーザー向けの親切な日本語メッセージを返します。
     * ステータスコードに応じて内容を切り替えます。
     */
    get displayMessage(): string {
        // ネットワークエラー (ステータス 0)
        if (this.status === 0) {
            return 'サーバーに接続できませんでした。インターネット接続を確認するか、しばらく待ってから再試行してください。';
        }

        // 認証エラー (401 Unauthorized)
        if (this.status === 401) {
            return 'セッションの有効期限が切れました。もう一度ログインしてください。';
        }

        // 権限エラー (403 Forbidden)
        if (this.status === 403) {
            return 'この操作を行う権限がありません。';
        }

        // クライアントエラー (400系)
        if (this.status >= 400 && this.status < 500) {
            // 404 Not Found など
            if (this.status === 404) {
                return 'データが見つかりませんでした。';
            }
            return '入力内容に誤りがあるか、処理できないリクエストです。';
        }

        // サーバーエラー (500系)
        if (this.status >= 500) {
            return 'サーバー側でエラーが発生しました。システム管理者に連絡するか、しばらく待ってから再試行してください。';
        }

        // それ以外
        return '予期せぬエラーが発生しました。';
    }
}
