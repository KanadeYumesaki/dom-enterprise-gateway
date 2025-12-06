import { inject } from '@angular/core';
import { CanMatchFn, Router, UrlTree } from '@angular/router';
import { StateService } from '../services/state.service';
import { map, take } from 'rxjs';

/**
 * AuthGuard (認証ガード)
 * 
 * 役割: 【画面に入る前の番人】
 * ユーザーがログインが必要な画面（メインレイアウト内のチャット画面など）にアクセスしようとしたとき、
 * 「本当にログインしているか？」をチェックします。
 * 
 * 動作:
 * - StateService に保存されている currentUser を確認します。
 * - もしユーザーがいれば、そのまま通します (true)。
 * - もしユーザーがいなければ、ログイン画面 (/login) へ強制的に移動させます (UrlTree)。
 * 
 * なぜ必要か:
 * 未ログインの人がチャット画面を見たり操作したりできないようにするためです。
 * BFFパターンではCookieで認証されていますが、フロントエンド側でも状態を見て
 * 適切な画面へ案内する必要があります。
 */
export const authGuard: CanMatchFn = (route, segments) => {
    const state = inject(StateService);
    const router = inject(Router);

    console.log('[AuthGuard] 認証チェックを実行します...');

    // StateServiceのcurrentUserシグナル、またはObservableを使って判定します。
    // ここではシンプルに state.currentUser() (Signal) をチェックする形でも良いですが、
    // currentUser が非同期でロードされる可能性を考慮し、ここでは単純な同期チェックまたは
    // 必要に応じて API を叩く実装への拡張性を残します。
    // P0段階では「StateServiceにユーザーがいなければ未ログイン」とみなします。

    const user = state.currentUser();

    if (user) {
        console.log('[AuthGuard] ユーザー認証済み。アクセスを許可します。');
        return true;
    }

    // エラーハンドリング / 未ログイン時の対応
    // ユーザーがいない場合はログを出力し、ログイン画面へ安全にリダイレクトします。
    console.warn('[AuthGuard] ユーザー情報がありません。ログイン画面へリダイレクトします。');

    // UrlTree を返すことで、Angular Router が指定されたパスへ遷移させます。
    return router.createUrlTree(['/login']);
};
