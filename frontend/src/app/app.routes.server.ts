import { RenderMode, ServerRoute } from '@angular/ssr';

/**
 * サーバーサイドルーティング設定
 * 
 * RenderMode の種類:
 * - Prerender: ビルド時に静的HTMLを生成（認証ガード等があると問題になる場合あり）
 * - Server: リクエスト時に動的にSSRを実行
 * - Client: クライアント側のみでレンダリング（SSRスキップ）
 * 
 * 認証ガードを使用している場合、SSR時にユーザー情報がないためリダイレクトループや
 * レンダリング失敗が発生する可能性があります。Client モードを使用することで
 * ブラウザ側でのみルーティングが実行されます。
 */
export const serverRoutes: ServerRoute[] = [
  {
    path: '**',
    renderMode: RenderMode.Client  // クライアント側のみでレンダリング
  }
];
