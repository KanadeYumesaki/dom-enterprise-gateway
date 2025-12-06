export const environment = {
    /** 開発モードです。デバッグ情報が多く出ることがあります。 */
    production: false,

    /**
     * バックエンドAPIのベースURL (開発環境用)
     * `ng serve` のプロキシ設定 (proxy.conf.json) を使う場合は '/api' でOKです。
     * 直接バックエンドを指定する場合は 'http://localhost:8000/api' などになります。
     */
    apiBaseUrl: '/api',

    /** OIDCプロバイダのURL (ダミー) */
    oidcAuthority: 'https://accounts.google.com',

    /** OIDCのクライアントID (ダミー) */
    oidcClientId: 'dev-client-id',

    /** ログイン後のリダイレクト先URI (開発用) */
    redirectUri: 'http://localhost:4200/auth/callback'
};
