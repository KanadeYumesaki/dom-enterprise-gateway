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
    login(redirectPath: string = '/'): void {
        console.log('[AuthService] ログイン処理を開始します...');

        // ログイン用のAPIエンドポイント（ブラウザが直接遷移する）
        // リダイレクト先として、アプリのフロントエンドURLを指定する場合もありますが、
        // ここではBFFが良しなに処理する前提、あるいはパラメータで渡す想定の例です。
        // 例: /api/auth/login?redirect_url=http://localhost:4200/
        const redirectUrl = `${window.location.origin}${redirectPath}`;
        const loginEndpoint = `${environment.apiBaseUrl}/auth/login?redirect_uri=${encodeURIComponent(redirectUrl)}`;

        // アプリ内ルーティングではなく、ブラウザレベルでの移動を行います
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
        this.api.post('/auth/logout', {}).subscribe({
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

        return this.api.get<User>('/auth/me').pipe(
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
    handleCallback(): Observable<void> {
        console.log('[AuthService] コールバック処理を開始します (ユーザー情報取得)');
        // fetchCurrentUser の結果を void に変換して返します
        return this.fetchCurrentUser().pipe(
            tap(() => {
                // 必要ならここでホームページなどに移動させる処理を追加しても良いですが、
                // 呼び出し元のコンポーネントで制御するほうが柔軟です。
            }),
            catchError((err) => {
                console.error('[AuthService] コールバック後のユーザー取得に失敗:', err);
                return throwError(() => err);
            }),
            // map(() => void 0) // RxJSのバージョンによっては必要ですが、推論に任せます
            tap(() => { }) as any // 型合わせのための簡易キャスト
        );
    }
}
