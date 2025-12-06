export const environment = {
    production: false,
    // BFFのAPIベースURL（開発環境用）
    // プロキシ設定などを使う場合は '/api' そのままで良いことも多いですが、
    // 明示的にホストを指定する場合の例として記載しています。
    apiBaseUrl: '/api',

    // OIDC（認証）関連の設定（BFFパターンなのでフロントエンドで直接使うことは少ないかもしれませんが、定義場所として用意）
    oidcAuthority: 'https://accounts.google.com', // 例: IdPのURL
    oidcClientId: 'dummy-client-id',             // 例: クライアントID
    redirectUri: 'http://localhost:4200/callback' // ログイン後のリダイレクト先
};
