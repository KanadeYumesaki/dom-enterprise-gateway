import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { AuthService } from '../../../core/services/auth.service';

/**
 * LoginPageComponent (ログイン画面)
 * 
 * 役割:
 * - ユーザーが最初に訪れる画面です。
 * - 「ログインする」ボタンを表示し、クリックされると AuthService を通じて
 *   OIDC認証フロー（バックエンドへのリダイレクト）を開始します。
 * 
 * どのタイミングで呼ばれるか:
 * - 未ログイン状態でルート (/) にアクセスしたときに、AuthGuard によってここに飛ばされます。
 * - または直接 /login にアクセスしたとき。
 */
@Component({
    selector: 'app-login-page',
    standalone: true,
    imports: [CommonModule, MatCardModule, MatButtonModule],
    templateUrl: './login-page.component.html',
    styleUrls: ['./login-page.component.scss']
})
export class LoginPageComponent {
    private authService = inject(AuthService);

    /** エラーメッセージ（ユーザーに表示するもの） */
    errorMessage: string | null = null;

    constructor() { }

    /**
     * ログインボタンがクリックされたときに呼ばれます。
     * 
     * 動作:
     * - AuthService.login() を呼び出します。
     * - 基本的にはブラウザがリダイレクトされますが、
     *   万が一呼び出しに失敗した場合（ネットワークエラーなど）はエラーを表示します。
     */
    onLogin(): void {
        this.errorMessage = null; // エラー表示をリセット

        try {
            this.authService.login();
        } catch (error: any) {
            // 想定されるエラーハンドリング
            console.error('[LoginPage] ログイン開始時にエラーが発生しました:', error);

            // エラーパターンに応じたメッセージの出し分け
            if (error.name === 'NetworkError' || error.status === 0) {
                this.errorMessage = '通信エラーです。ネットワークを確認して、もう一度お試しください。';
            } else {
                // その他のエラー (4xx, 5xx など)
                this.errorMessage = 'ログイン処理でエラーが発生しました。時間をおいて再度お試しください。';
            }
        }
    }
}
