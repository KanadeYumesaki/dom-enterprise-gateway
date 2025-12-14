import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError, of } from 'rxjs';
import { ApiService } from './api.service';
import { StateService } from './state.service';
import { User } from '../models/user.model';
import { ApiError } from '../models/api-error.model';
import { environment } from '@environments/environment';

/**
 * AuthService (認証サービス)
 * 
 * 役割:
 * - ユーザーのログイン・ログアウト処理を行います。
 * - バックエンド (BFF) の認証APIを呼び出します。
 * - ログイン中のユーザー情報を取得し、StateService に保存します。
 */
@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private api = inject(ApiService);
    private state = inject(StateService);
    private router = inject(Router);

    constructor() { }

    /**
     * ログインフローを開始します (OIDC)。
     * 
     * 動作:
     * - ブラウザをバックエンドのログインエンドポイントへリダイレクトさせます。
     * - バックエンドはそこからさらに IdP (Googleなど) へリダイレクトします。
     * 
     * @param redirectPath ログイン完了後に戻ってくるアプリ内のパス (デフォルトは '/')
     */
    login(redirectPath: string = '/auth/callback'): void {
        console.log('[AuthService] ログイン処理を開始します...');
        if (typeof window === 'undefined') {
            console.warn('[AuthService] window が無いためログインリダイレクトをスキップしました (SSR)。');
            return;
        }

        const redirectUrl = `${window.location.origin}${redirectPath}`;
        const loginEndpoint = `${environment.apiBaseUrl}/v1/auth/login?redirect_uri=${encodeURIComponent(redirectUrl)}`;

        window.location.href = loginEndpoint;
    }

    /**
     * ログアウト処理を行います。
     * 
     * 動作:
     * - バックエンドのログアウトAPIを呼び出してセッション（Cookie）を削除します。
     * - フロントエンドの状態（StateService）もクリアします。
     * - 最後にログイン画面（またはトップ）へ移動します。
     */
    logout(): void {
        console.log('[AuthService] ログアウトしています...');
        this.api.post('/v1/auth/logout', {}).subscribe({
            next: () => {
                console.log('[AuthService] ログアウト成功');
                this.finalizeLogout();
            },
            error: (err: ApiError) => {
                // エラーが出ても、クライアント側ではログアウト扱いにして安全側に倒します
                console.error('[AuthService] ログアウト中にエラーが発生しましたが続行します:', err);
                this.finalizeLogout();
            }
        });
    }

    private finalizeLogout(): void {
        this.state.setCurrentUser(null);
        this.router.navigate(['/login']); // 必要に応じてルートを変更してください
    }

    /**
     * 現在ログイン中のユーザー情報を取得します。
     * 
     * いつ使うか:
     * - アプリの起動時（リロード時）
     * - OIDCのコールバックから戻ってきた直後
     * 
     * エラー処理:
     * - 401 (未ログイン) の場合はエラーとせず、null を返して正常終了します。
     * - それ以外のエラー（ネットワーク障害など）はそのままエラーとして投げます。
     */
    fetchCurrentUser(): Observable<User | null> {
        this.state.setLoading(true);
        console.log('[AuthService] ユーザー情報を取得中...');

        return this.api.get<User>('/v1/auth/me').pipe(
            tap((user) => {
                console.log('[AuthService] ユーザー情報を取得しました:', user.id);
                this.state.setCurrentUser(user);
                this.state.setLoading(false);
            }),
            catchError((err: ApiError) => {
                this.state.setLoading(false);

                // 401 Unauthorized は「ログインしていない」という意味なので
                // エラーではなく「ユーザーなし (null)」として扱います。
                if (err.status === 401) {
                    console.log('[AuthService] 未ログイン状態です。');
                    this.state.setCurrentUser(null);
                    return of(null);
                }

                // それ以外のエラーは本当に問題があるので、呼び出し元に伝えます。
                console.error('[AuthService] ユーザー取得に失敗しました:', err);
                this.state.setCurrentUser(null);
                return throwError(() => err);
            })
        );
    }

    /**
     * OIDCコールバックのハンドリングを行います。
     * 
     * 動作:
     * - バックエンドが認証を完了させてCookieをセットした状態で、
     *   フロントエンドの /auth/callback などに戻ってきたときに呼び出します。
     * - ユーザー情報を取得しに行き、成功すれば状態を更新します。
     */
    handleCallback(): Observable<User> {
        console.log('[AuthService] コールバック処理を開始します');
        const params = new URLSearchParams(window.location.search);
        const state = params.get('state');
        const code = params.get('code');

        if (!state || !code) {
            const err = { status: 400, message: 'Missing state or code' } as any;
            console.error('[AuthService] state / code が不足しています');
            return throwError(() => err);
        }

        return this.api.get<User>('/v1/auth/callback', { params: { state, code } }).pipe(
            tap((user) => {
                this.state.setCurrentUser(user);
            }),
            catchError((err: ApiError) => {
                console.error('[AuthService] コールバック処理に失敗:', err);
                return throwError(() => err);
            })
        );
    }
}
