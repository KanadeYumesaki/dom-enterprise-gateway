import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, throwError, catchError } from 'rxjs';
import { environment } from '@environments/environment';
import { ApiError } from '../models/api-error.model';

/**
 * ApiService (API通信サービス)
 * 
 * 役割:
 * - バックエンド (FastAPI) との通信を一元管理します。
 * - HttpClient をラップして、共通のエラーハンドリングやベースURLの管理を行います。
 * - チャットのストリーミング用に SSE (Server-Sent Events) の接続ヘルパーも提供します。
 */
@Injectable({
    providedIn: 'root'
})
export class ApiService {
    private http = inject(HttpClient);
    private baseUrl = environment.apiBaseUrl;

    constructor() { }

    /**
     * GET リクエストを実行する
     * 
     * @param path APIのエンドポイントパス (例: '/chat/history')。ベースURLは自動付与されます。
     * @param options クエリパラメータやヘッダーなどのオプション
     */
    get<T>(path: string, options?: {
        headers?: HttpHeaders | { [header: string]: string | string[] };
        params?: HttpParams | { [param: string]: string | number | boolean | readonly (string | number | boolean)[] };
    }): Observable<T> {
        return this.http.get<T>(`${this.baseUrl}${path}`, options)
            .pipe(catchError((err) => this.handleError(err, path)));
    }

    /**
     * POST リクエストを実行する
     * 
     * @param path APIのエンドポイントパス
     * @param body 送信するデータ
     * @param options オプション
     */
    post<T>(path: string, body: unknown, options?: {
        headers?: HttpHeaders | { [header: string]: string | string[] };
    }): Observable<T> {
        return this.http.post<T>(`${this.baseUrl}${path}`, body, options)
            .pipe(catchError((err) => this.handleError(err, path)));
    }

    /**
     * PUT リクエストを実行する
     * 
     * @param path APIのエンドポイントパス
     * @param body 更新するデータ
     */
    put<T>(path: string, body: unknown, options?: {
        headers?: HttpHeaders | { [header: string]: string | string[] };
    }): Observable<T> {
        return this.http.put<T>(`${this.baseUrl}${path}`, body, options)
            .pipe(catchError((err) => this.handleError(err, path)));
    }

    /**
     * DELETE リクエストを実行する
     * 
     * @param path APIのエンドポイントパス
     */
    delete<T>(path: string, options?: {
        headers?: HttpHeaders | { [header: string]: string | string[] };
    }): Observable<T> {
        return this.http.delete<T>(`${this.baseUrl}${path}`, options)
            .pipe(catchError((err) => this.handleError(err, path)));
    }

    /**
     * SSE (Server-Sent Events) に接続する
     * 
     * 役割:
     * - チャットの回答など、サーバーから少しずつ送られてくるデータを受信します。
     * - EventSource オブジェクトを生成して返します（呼び出し元で close() する必要があります）。
     * 
     * @param path 接続先のパス (例: '/chat/stream/session-123')
     * @param onMessage メッセージを受信したときに呼ばれる関数
     * @param onError エラーが発生したときに呼ばれる関数
     * @returns 作成された EventSource オブジェクト
     */
    connectToSse(
        path: string,
        onMessage: (data: string) => void,
        onError: (error: ApiError) => void
    ): EventSource {
        const url = `${this.baseUrl}${path}`;
        console.log(`[ApiService] Connecting to SSE: ${url}`);

        // BFFパターンでは Cookie 認証を使うため、withCredentials: true が重要になる場合があります。
        // 標準の EventSource はヘッダー追加ができないため、Cookieのみが頼りです。
        // 開発環境と本番環境の違い（CORSなど）に注意が必要です。
        const eventSource = new EventSource(url, { withCredentials: true });

        // 接続確立時のログ
        eventSource.onopen = () => {
            console.log('[ApiService] SSE connection established.');
        };

        // メッセージ受信時
        eventSource.onmessage = (event) => {
            // 受信した生データをコールバックに渡します
            onMessage(event.data);
        };

        // エラー発生時
        eventSource.onerror = (event) => {
            console.error('[ApiService] SSE error:', event);

            // SSEのエラーイベントは詳細情報が少ないですが、
            // 接続切れやタイムアウトなどが考えられます。
            // ここではステータス0（ネットワークエラー扱い）として ApiError を生成します。
            const apiError = new ApiError(
                'SSE接続エラーが発生しました。',
                0, // ステータス不明のため0
                'SSE_ERROR',
                event,
                url
            );
            onError(apiError);

            // 必要に応じて eventSource.close() を呼び出し元で行ってください。
        };

        return eventSource;
    }

    /**
     * エラーハンドリングの共通処理
     * 
     * 役割:
     * - HttpClient から投げられた生のエラーを受け取り、
     * - アプリ専用の ApiError クラスに変換して投げ直します。
     * - 必ずエラーを「握りつぶさず」に呼び出し元へ伝えます。
     */
    private handleError(error: HttpErrorResponse, url?: string): Observable<never> {
        let errorMessage = 'An unknown error occurred';
        let statusCode = 500;
        let errorCode: string | undefined;
        let details: unknown;

        if (error.error instanceof ErrorEvent) {
            // クライアント側（ネットワーク切断など）のエラー
            errorMessage = `Network or Client Error: ${error.error.message}`;
            statusCode = 0; // 0 はネットワークエラーなどを表す慣例
        } else {
            // バックエンドから返された HTTP エラー (4xx, 5xx)
            statusCode = error.status;

            // バックエンドが JSON でエラー詳細を返しているかチェック
            if (typeof error.error === 'object' && error.error !== null) {
                // { "message": "...", "code": "...", "details": ... } のような形式を想定
                errorMessage = (error.error as any).message || error.message;
                errorCode = (error.error as any).code;
                details = (error.error as any).details;
            } else {
                errorMessage = error.message;
            }

            console.error(`[ApiService] API Error (${statusCode}) at ${url}:`, errorMessage);
        }

        // 独自のエラークラスに変換して throw する
        return throwError(() => new ApiError(errorMessage, statusCode, errorCode, details, url));
    }
}
