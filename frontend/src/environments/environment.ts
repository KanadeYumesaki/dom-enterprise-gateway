export const environment = {
    /** 本番モードかどうか。Angularの最適化などに影響します。 */
    production: true,

    /**
     * バックエンドAPIのベースURL
     * BFFパターンの場合、フロントエンドと同じドメインの `/api` にプロキシすることが一般的です。
     */
    apiBaseUrl: '/api',

    /** OIDCプロバイダのURL (例: Google, Auth0, Keycloakなど) */
    oidcAuthority: 'https://accounts.google.com',

    /** OIDCのクライアントID */
    oidcClientId: 'your-production-client-id',

    /** ログイン後のリダイレクト先URI */
    redirectUri: 'https://your-domain.com/auth/callback'
};
