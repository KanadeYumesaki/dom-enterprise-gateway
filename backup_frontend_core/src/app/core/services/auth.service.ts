import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError, of } from 'rxjs';
import { ApiService } from './api.service';
import { StateService } from './state.service';
import { User } from '../models/user.model';
import { ApiError } from '../models/api-error.model';

/**
 * 認証機能を管理するサービス
 * BFF (Backend For Frontend) パターンを採用しているため、
 * 実際のトークン管理はバックエンド(FastAPI)が行い、Cookie (HttpOnly) で管理される。
 * このサービスはログイン画面への誘導、ユーザー情報の取得、ログアウトのトリガーを担当する。
 */
@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private api = inject(ApiService);
    private state = inject(StateService); // 状態管理サービス
    private router = inject(Router);

    constructor() { }

    /**
     * ログイン処理を開始する
     * BFFのログイン開始エンドポイントへリダイレクトし、OIDCフローを開始する。
     */
    login(): void {
        console.log('[AuthService] Initiating login flow via BFF...');
        // BFFのログインエンドポイントへブラウザをリダイレクトさせる
        // これにより、バックエンドがOIDCプロバイダへリダイレクトを行う
        window.location.href = '/api/auth/login';
    }

    /**
     * ログアウト処理
     * BFFのログアウトエンドポイントを呼び出し、ローカルの状態をクリアする。
     */
    logout(): void {
        console.log('[AuthService] Logging out...');
        this.api.post('/auth/logout', {}).subscribe({
            next: () => {
                console.log('[AuthService] Logout successful on server.');
                this.state.clearUser(); // 状態をクリア
                this.router.navigate(['/login']); // ログイン画面（またはトップ）へ
            },
            error: (err: ApiError) => {
                console.error('[AuthService] Logout failed:', err);
                // 失敗してもクライアント側はログアウト扱いにするなどの安全策をとる
                this.state.clearUser();
                this.router.navigate(['/login']);
            }
        });
    }

    /**
     * 現在ログイン中のユーザー情報を取得する (/api/auth/me)
     * アプリ起動時やガードでのチェック時に呼び出す。
     */
    getCurrentUser(): Observable<User | null> {
        this.state.setLoading(true);
        console.log('[AuthService] Fetching current user...');

        return this.api.get<User>('/auth/me').pipe(
            tap((user) => {
                console.log('[AuthService] User fetched successfully:', user);
                this.state.setUser(user); // 状態を更新
                this.state.setLoading(false);
            }),
            catchError((err: ApiError) => {
                console.warn('[AuthService] Failed to fetch user (maybe not logged in):', err.status);
                this.state.clearUser(); // ユーザーなし状態にする
                this.state.setLoading(false);

                // 401 (Unauthorized) は「未ログイン」なのでエラーとして扱わず、nullを返すのが自然な場合もある
                if (err.status === 401) {
                    return of(null);
                }
                // それ以外のエラーは伝搬させる
                return throwError(() => err);
            })
        );
    }

    /**
     * ログインコールバックの処理（必要に応じて）
     * BFFパターンでは通常、バックエンドがコールバックを受け取ってCookieをセットしてから
     * フロントエンドのルートへリダイレクトするため、ここで明示的な処理は不要なことが多い。
     * もしURLにエラーパラメータなどが付いている場合はここでハンドリングする。
     */
    checkCallbackError(): void {
        const params = new URLSearchParams(window.location.search);
        const error = params.get('error');
        if (error) {
            console.error('[AuthService] Login callback error:', error);
            // ここでユーザーにエラー通知を表示するロジックなどを呼び出す
            // 例: this.notificationService.showError('ログインに失敗しました: ' + error);
        }
    }
}
