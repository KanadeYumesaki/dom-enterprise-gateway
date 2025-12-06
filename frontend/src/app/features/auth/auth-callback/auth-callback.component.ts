import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatButtonModule } from '@angular/material/button';
import { AuthService } from '../../../core/services/auth.service';
import { ApiError } from '../../../core/models/api-error.model';

/**
 * AuthCallbackComponent (認証コールバック画面)
 * 
 * 役割:
 * - OIDC認証（Googleなどでログイン）が終わったあと、最初にブラウザが戻ってくる場所です。
 * - ここでバックエンドとのセッション確立確認（ユーザー情報の取得）を行います。
 * - 成功したら、チャット画面（メイン画面）へ移動します。
 * 
 * どのタイミングで呼ばれるか:
 * - バックエンドが認証を完了して、ブラウザを /auth/callback にリダイレクトしたとき。
 */
@Component({
    selector: 'app-auth-callback',
    standalone: true,
    imports: [CommonModule, MatCardModule, MatProgressSpinnerModule, MatButtonModule],
    templateUrl: './auth-callback.component.html',
    styleUrls: ['./auth-callback.component.scss']
})
export class AuthCallbackComponent implements OnInit {
    private authService = inject(AuthService);
    private router = inject(Router);

    /** 処理中かどうか */
    isLoading = true;

    /** エラーメッセージ */
    errorMessage: string | null = null;

    constructor() { }

    /**
     * 画面が表示された直後に実行されます。
     */
    ngOnInit(): void {
        // URLにエラーパラメータが含まれているかチェック (例: ?error=access_denied)
        const params = new URLSearchParams(window.location.search);
        const errorParam = params.get('error');

        if (errorParam) {
            this.handleError(new Error(`Callback Error Parameter: ${errorParam}`) as any);
            return;
        }

        this.processCallback();
    }

    /**
     * コールバック処理を実行します。
     */
    private processCallback(): void {
        this.authService.handleCallback().subscribe({
            next: () => {
                console.log('[AuthCallback] 認証成功。メイン画面へ遷移します。');
                this.router.navigate(['/']); // MainLayout (デフォルト子ルート /chat へ)
            },
            error: (err: ApiError) => {
                this.handleError(err);
            }
        });
    }

    /**
     * エラー発生時の処理
     * エラーの種類に応じてメッセージを出し分けます。
     */
    private handleError(err: ApiError): void {
        console.error('[AuthCallback] callback processing failed:', err);
        this.isLoading = false;

        if (err.status === 0) {
            // ネットワークエラー / サーバーダウン
            this.errorMessage = '通信エラーです。再試行してください。';
        } else if (err.status === 401 || err.status === 403) {
            // 認証失敗
            this.errorMessage = '認証に失敗しました。もう一度ログインしてください。';
        } else {
            // その他のエラー
            this.errorMessage = '予期せぬエラーが発生しました。';
        }
    }

    /**
     * 「ログイン画面に戻る」ボタンのアクション
     */
    goBackToLogin(): void {
        this.router.navigate(['/login']);
    }
}
