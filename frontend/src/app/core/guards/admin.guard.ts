import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { StateService } from '../services/state.service';

/**
 * AdminGuard (管理者権限ガード)
 * 
 * 役割:
 * - ルートに管理者権限チェックを適用します。
 * - 現在のユーザーが管理者でない場合、`/chat` へリダイレクトします。
 * 
 * いつ使うか:
 * - `/knowledge` などの管理者専用ルートに `canActivate: [adminGuard]` を設定します。
 * 
 * 例:
 * ```typescript
 * {
 *   path: 'knowledge',
 *   component: KnowledgePageComponent,
 *   canActivate: [adminGuard]
 * }
 * ```
 */
export const adminGuard: CanActivateFn = (route, state) => {
    const stateService = inject(StateService);
    const router = inject(Router);

    // StateService から現在のユーザー情報を取得
    const currentUser = stateService.currentUser();

    // ユーザーが認証されていない場合は false を返す（authGuard が先に処理するはず）
    if (!currentUser) {
        console.warn('[AdminGuard] No authenticated user found. Redirecting to /chat.');
        router.navigate(['/chat']);
        return false;
    }

    // ユーザーが管理者かチェック
    // TODO: Backend の AuthenticatedUser に is_admin フラグまたは role を追加予定
    // 暫定的に、特定のメールアドレスまたは環境変数で管理者を判定する
    const isAdmin = currentUser.is_admin === true;

    if (!isAdmin) {
        console.warn('[AdminGuard] User is not an admin. Redirecting to /chat.');
        router.navigate(['/chat']);
        return false;
    }

    // 管理者の場合はアクセスを許可
    return true;
};
