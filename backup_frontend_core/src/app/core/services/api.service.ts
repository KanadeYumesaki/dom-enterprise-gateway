import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, throwError, catchError } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiError } from '../models/api-error.model';

/**
 * バックエンド API との通信を一元管理するサービス
 * - 共通のベース URL の適用
 * - エラーハンドリングの共通化
 * - SSE (Server-Sent Events) の接続ヘルパー
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
     * @param path APIのエンドポイントパス（例: '/chat/history'）
     * @param params クエリパラメータ（任意）
     */
    get<T>(path: string, params?: HttpParams | { [param: string]: string | number | boolean | readonly (string | number | boolean)[] }): Observable<T> {
        return this.http.get<T>(`${this.baseUrl}${path}`, { params })
            .pipe(catchError(this.handleError));
    }

    /**
     * POST リクエストを実行する
     * @param path APIのエンドポイントパス
     * @param body 送信するデータ
     */
    post<T>(path: string, body: any): Observable<T> {
        return this.http.post<T>(`${this.baseUrl}${path}`, body)
            .pipe(catchError(this.handleError));
    }

    /**
     * PUT リクエストを実行する
     * @param path APIのエンドポイントパス
     * @param body 送信するデータ
     */
    put<T>(path: string, body: any): Observable<T> {
        return this.http.put<T>(`${this.baseUrl}${path}`, body)
            .pipe(catchError(this.handleError));
    }

    /**
     * DELETE リクエストを実行する
     * @param path APIのエンドポイントパス
     */
    delete<T>(path: string): Observable<T> {
        return this.http.delete<T>(`${this.baseUrl}${path}`)
            .pipe(catchError(this.handleError));
    }

    /**
     * SSE (Server-Sent Events) への接続を開始する
     * チャットのストリーミング応答などに使用する。
     * 
     * @param path ストリーミングエンドポイントのパス
     * @returns EventSource オブジェクト。呼び出し元で onmessage などを設定して使う。
     */
    connectSse(path: string): EventSource {
        const url = `${this.baseUrl}${path}`;
        console.log(`[ApiService] Connecting to SSE: ${url}`);

        // EventSourceの生成（ブラウザ標準API）
        // 注意: 標準の EventSource はヘッダー認証（Authorization: Bearer ...）に対応していないことが多い。
        // BFFパターン(Cookie認証)であれば、withCredentials: true が必要になる場合があるが、
        // ここでは標準的な実装とする。必要に応じて polyfill (event-source-polyfill) を検討する。
        const eventSource = new EventSource(url, { withCredentials: true });

        eventSource.onopen = (event) => {
            console.log('[ApiService] SSE connection opened.', event);
        };

        eventSource.onerror = (error) => {
            // SSEのエラーは詳細が取得しにくいが、ログには出しておく
            console.error('[ApiService] SSE connection error:', error);
            // 呼び出し元で close などの判断ができるようにイベントはそのまま流れる
        };

        return eventSource;
    }

    /**
     * エラーハンドリング共通処理
     * HttpClient が投げるエラーを、アプリ独自の ApiError に変換して投げ直す。
     */
    private handleError(error: HttpErrorResponse): Observable<never> {
        let errorMessage = 'An unknown error occurred!';
        let statusCode = 500;
        let errorCode: string | undefined;
        let details: any;

        if (error.error instanceof ErrorEvent) {
            // クライアント側（ネットワーク）のエラー
            errorMessage = `Network Error: ${error.error.message}`;
            statusCode = 0; // 0 はネットワークエラーなどを表す慣例
        } else {
            // バックエンドから返された HTTP エラー (4xx, 5xx)
            statusCode = error.status;
            // バックエンドがJSONで詳細を返している場合、error.error に入っている
            if (typeof error.error === 'object' && error.error !== null) {
                errorMessage = error.error.message || error.message;
                errorCode = error.error.code;
                details = error.error.details;
            } else {
                errorMessage = error.message;
            }

            console.error(`[ApiService] Backend returned code ${statusCode}, body was: `, error.error);
        }

        // ドメイン独自のエラー型に変換して throw する
        return throwError(() => new ApiError(errorMessage, statusCode, errorCode, details));
    }
}
