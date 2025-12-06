import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, throwError, catchError, firstValueFrom } from 'rxjs';
import { environment } from '@environments/environment';
import { ApiError } from '../models/api-error.model';
import {
    ChatMessage,
    ChatMessageRequest,
    ChatSession,
    FileUploadResponse,
    ChatError,
    ChatStreamEvent
} from '../models/chat.model';
import {
    KnowledgeDocument,
    KnowledgeDetail,
    KnowledgeFilter,
    KnowledgeError
} from '../models/knowledge.models';
import { UserSettings, UserSettingsUpdate, SettingsError } from '../models/settings.models';

/**
 * ApiService (API通信サービス)
 * 
 * 役割:
 * - バックエンド (FastAPI) との通信を一元管理します。
 * - HttpClient をラップして、共通のエラーハンドリングやベースURLの管理を行います。
 * - Chat, Knowledge, Settings, Help など全てのAPI通信を提供します。
 * - Backend との型変換（camelCase ↔ snake_case）を自動処理します。
 * 
 * いつ使うか:
 * - コンポーネントやサービスから Backend API を呼び出す際に使用します。
 * - 各API呼び出しは型安全で、自動的にエラーハンドリングされます。
 */
@Injectable({
    providedIn: 'root'
})
export class ApiService {
    private http = inject(HttpClient);
    private baseUrl = environment.apiBaseUrl;

    constructor() { }

    // =========================
    // 基本的な HTTP メソッド
    // =========================

    /**
     * GET リクエストを実行する
     * 
     * 役割:
     * - Backend に対して GET リクエストを送信し、データを取得します。
     * - エラー発生時は自動的に ApiError に変換されます。
     * 
     * @param path APIのエンドポイントパス (例: '/chat/history')。ベースURLは自動付与されます。
     * @param options クエリパラメータやヘッダーなどのオプション
     * @returns Observable<T> レスポンスデータのストリーム
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
     * 役割:
     * - Backend に対して POST リクエストを送信し、データを作成・送信します。
     * - エラー発生時は自動的に ApiError に変換されます。
     * 
     * @param path APIのエンドポイントパス
     * @param body 送信するデータ
     * @param options ヘッダーやクエリパラメータなどのオプション
     * @returns Observable<T> レスポンスデータのストリーム
     */
    post<T>(path: string, body: unknown, options?: {
        headers?: HttpHeaders | { [header: string]: string | string[] };
        params?: HttpParams | { [param: string]: string | number | boolean | readonly (string | number | boolean)[] };
    }): Observable<T> {
        return this.http.post<T>(`${this.baseUrl}${path}`, body, options)
            .pipe(catchError((err) => this.handleError(err, path)));
    }

    /**
     * PUT リクエストを実行する
     * 
     * 役割:
     * - Backend に対して PUT リクエストを送信し、データを更新します。
     * - エラー発生時は自動的に ApiError に変換されます。
     * 
     * @param path APIのエンドポイントパス
     * @param body 更新するデータ
     * @param options ヘッダーなどのオプション
     * @returns Observable<T> レスポンスデータのストリーム
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
     * 役割:
     * - Backend に対して DELETE リクエストを送信し、データを削除します。
     * - エラー発生時は自動的に ApiError に変換されます。
     * 
     * @param path APIのエンドポイントパス
     * @param options ヘッダーなどのオプション
     * @returns Observable<T> レスポンスデータのストリーム
     */
    delete<T>(path: string, options?: {
        headers?: HttpHeaders | { [header: string]: string | string[] };
    }): Observable<T> {
        return this.http.delete<T>(`${this.baseUrl}${path}`, options)
            .pipe(catchError((err) => this.handleError(err, path)));
    }

    // =========================
    // Chat API メソッド (Task 7.2)
    // =========================

    /**
     * チャットメッセージを送信する
     * 
     * 役割:
     * - ユーザーのメッセージを Backend に送信し、DB に保存します。
     * - この API はユーザーメッセージの保存のみを行います。
     * - LLM の応答は別途 getChatStream() で取得します。
     * 
     * いつ使うか:
     * - ユーザーがチャット画面でメッセージを送信したとき
     * 
     * エンドポイント: POST /api/chat/send
     * 
     * @param request チャットメッセージリクエスト（sessionId と message を含む）
     * @returns Promise<ChatMessage> 保存されたユーザーメッセージ
     * @throws ChatError ネットワークエラーやサーバーエラー時
     */
    sendChatMessage(request: ChatMessageRequest): Promise<ChatMessage> {
        return firstValueFrom(
            this.post<ChatMessage>('/api/chat/send', request)
        );
    }

    /**
     * チャットストリームに接続する (SSE)
     * 
     * 役割:
     * - Backend から LLM の応答をリアルタイムでストリーミング受信します。
     * - SSE (Server-Sent Events) を使用します。
     * - トークン単位で onToken コールバックが呼ばれ、完了時に onComplete が呼ばれます。
     * 
     * いつ使うか:
     * - sendChatMessage() 後、LLM の応答を表示するとき
     * 
     * エンドポイント: GET /api/chat/stream/{sessionId}?research_mode={boolean}
     * 
     * @param sessionId セッションID (UUID)
     * @param researchMode リサーチモードを有効にするか (default: false)
     * @param onToken トークンを受信したときのコールバック
     * @param onComplete ストリーム完了時のコールバック
     * @param onError エラー発生時のコールバック
     * @returns EventSource オブジェクト (呼び出し元で close() する必要があります)
     */
    getChatStream(
        sessionId: string,
        researchMode: boolean,
        onToken: (token: string) => void,
        onComplete: () => void,
        onError: (error: ChatError) => void
    ): EventSource {
        const params = new HttpParams().set('research_mode', researchMode.toString());
        const url = `${this.baseUrl}/api/chat/stream/${sessionId}?${params.toString()}`;

        const eventSource = new EventSource(url, { withCredentials: true });

        eventSource.onmessage = (event) => {
            const token = event.data;

            // Backend からの終了マーカーをチェック
            if (token === '[STREAM_END]') {
                onComplete();
                eventSource.close();
                return;
            }

            // Backend からのエラーマーカーをチェック
            if (token.startsWith('ERROR:')) {
                const errorMessage = token.replace('ERROR:', '').trim();
                onError({ kind: 'sse', message: errorMessage });
                eventSource.close();
                return;
            }

            // 通常のトークンとして処理
            onToken(token);
        };

        eventSource.onerror = (event) => {
            onError({
                kind: 'sse',
                message: 'チャットストリーム接続でエラーが発生しました。',
                details: event
            });
            eventSource.close();
        };

        return eventSource;
    }

    /**
     * チャットセッションをリセットする
     * 
     * 役割:
     * - 現在のセッションを終了し、新しいセッションを作成します。
     * - Backend 側で EpisodicMemory への保存が行われます。
     * 
     * いつ使うか:
     * - ユーザーが「新しい会話」ボタンを押したとき
     * 
     * エンドポイント: POST /api/chat/reset/{sessionId}
     * 
     * @param sessionId リセット対象のセッションID (UUID)
     * @returns Promise<ChatSession> 新しく作成されたセッション
     * @throws ChatError ネットワークエラーやサーバーエラー時
     */
    resetChatSession(sessionId: string): Promise<ChatSession> {
        return firstValueFrom(
            this.post<ChatSession>(`/api/chat/reset/${sessionId}`, {})
        );
    }

    /**
     * 新しいチャットセッションを作成する
     * 
     * 役割:
     * - 新しいチャットセッションを作成します（初回起動時など）。
     * 
     * いつ使うか:
     * - アプリケーション初回起動時
     * - セッションが存在しない場合
     * 
     * エンドポイント: POST /api/chat/sessions
     * 
     * @param title セッションタイトル (optional)
     * @returns Promise<ChatSession> 作成されたセッション
     * @throws ChatError ネットワークエラーやサーバーエラー時
     */
    createChatSession(title?: string): Promise<ChatSession> {
        return firstValueFrom(
            this.post<ChatSession>('/api/chat/sessions', { title })
        );
    }

    /**
     * ユーザーのチャットセッション一覧を取得する
     * 
     * 役割:
     * - 現在のユーザーのチャットセッション一覧を取得します。
     * 
     * いつ使うか:
     * - セッション履歴画面を表示するとき
     * 
     * エンドポイント: GET /api/chat/sessions
     * 
     * @returns Promise<ChatSession[]> セッション一覧
     * @throws ChatError ネットワークエラーやサーバーエラー時
     */
    getChatSessions(): Promise<ChatSession[]> {
        return firstValueFrom(
            this.get<ChatSession[]>('/api/chat/sessions')
        );
    }

    /**
     * ファイルをアップロードする
     * 
     * 役割:
     * - チャットに添付されたファイルを Backend にアップロードします。
     * - sessionId を指定すると Ephemeral RAG (セッション限定) に登録されます。
     * - sessionId を指定しない場合は Global RAG に登録されます (管理者向け)。
     * 
     * いつ使うか:
     * - ユーザーがチャット画面でファイルを添付したとき
     * 
     * エンドポイント: POST /api/files/upload?session_id={uuid}
     * 
     * @param file アップロードするファイル
     * @param sessionId セッションID (optional, Ephemeral RAG用)
     * @returns Promise<FileUploadResponse> アップロードされたファイルの情報
     * @throws ChatError ファイルサイズ超過、ネットワークエラー、サーバーエラー時
     */
    async uploadChatFile(file: File, sessionId?: string): Promise<FileUploadResponse> {
        // クライアント側バリデーション (ファイルサイズ上限 5MB)
        const MAX_FILE_SIZE = 5 * 1024 * 1024;
        if (file.size > MAX_FILE_SIZE) {
            throw {
                kind: 'validation',
                message: 'ファイルサイズが大きすぎます。5MB以下のファイルを選択してください。',
                details: { fileName: file.name, fileSize: file.size }
            } as ChatError;
        }

        const formData = new FormData();
        formData.append('file', file);

        let params = new HttpParams();
        if (sessionId) {
            params = params.set('session_id', sessionId);
        }

        return firstValueFrom(
            this.post<FileUploadResponse>('/api/files/upload', formData, {
                params: params as any
            })
        );
    }

    // =========================
    // Knowledge API メソッド (Task 7.3)
    // =========================

    /**
     * ナレッジドキュメント一覧を取得する
     * 
     * 役割:
     * - 管理者がアップロードしたグローバルナレッジの一覧を取得します。
     * - 検索クエリ、ページネーション（skip/limit）でフィルタリング可能です。
     * 
     * いつ使うか:
     * - ナレッジ管理画面を表示するとき
     * 
     * エンドポイント: GET /api/admin/knowledge?search_query={query}&skip={n}&limit={n}
     * 
     * @param filter 検索・ページネーション条件 (optional)
     * @returns Promise<KnowledgeDocument[]> ナレッジドキュメント一覧
     * @throws KnowledgeError ネットワークエラーやサーバーエラー時
     */
    async getKnowledgeList(filter?: KnowledgeFilter): Promise<KnowledgeDocument[]> {
        try {
            let params = new HttpParams();

            if (filter?.searchQuery) {
                params = params.set('search_query', filter.searchQuery);
            }
            if (filter?.skip !== undefined) {
                params = params.set('skip', filter.skip.toString());
            }
            if (filter?.limit !== undefined) {
                params = params.set('limit', filter.limit.toString());
            }

            const response = await firstValueFrom(
                this.get<any[]>('/api/admin/knowledge', { params })
            );

            // Backend の snake_case を Frontend の camelCase に変換
            return response.map(item => ({
                id: item.id,
                tenantId: item.tenant_id,
                fileName: item.filename,  // Backend: filename → Frontend: fileName
                filePath: item.file_path,  // Backend: file_path → Frontend: filePath
                fileType: item.file_type,
                fileSize: item.file_size,
                uploadedByUserId: item.uploaded_by,  // Backend: uploaded_by → Frontend: uploadedByUserId
                isActive: item.is_active,
                createdAt: item.created_at,
                updatedAt: item.updated_at
            }));
        } catch (error: unknown) {
            throw this.apiErrorToKnowledgeError(error as ApiError);
        }
    }

    /**
     * ナレッジドキュメントの詳細を取得する
     * 
     * 役割:
     * - 指定されたIDのナレッジドキュメント詳細を取得します。
     * - プレビューテキストも含まれます（将来実装）。
     * 
     * いつ使うか:
     * - ナレッジ詳細画面を表示するとき
     * 
     * @param id ドキュメントID (UUID)
     * @returns Promise<KnowledgeDetail> ナレッジドキュメント詳細
     * @throws KnowledgeError ドキュメントが見つからない、ネットワークエラー時
     */
    async getKnowledgeDetail(id: string): Promise<KnowledgeDetail> {
        try {
            const allDocuments = await this.getKnowledgeList();
            const doc = allDocuments.find(d => d.id === id);

            if (!doc) {
                throw {
                    kind: 'http-404',
                    message: `ドキュメント (ID: ${id}) が見つかりませんでした。`,
                    details: { id }
                } as KnowledgeError;
            }

            return {
                doc,
                previewText: null  // P1 で実装予定
            };
        } catch (error: unknown) {
            throw this.apiErrorToKnowledgeError(error as ApiError);
        }
    }

    // =========================
    // Settings API メソッド (Task 7.4)
    // =========================

    /**
     * ユーザー設定を取得する
     * 
     * 役割:
     * - 現在のユーザーの設定（テーマ、言語、フォントサイズなど）を取得します。
     * - DB にレコードが無い場合はデフォルト設定を返します。
     * 
     * いつ使うか:
     * - アプリケーション起動時
     * - Settings画面表示時
     * 
     * Backend API: GET /api/user/settings
     * 
     * @returns Promise<UserSettings> ユーザー設定
     * @throws SettingsError ネットワークエラーやサーバーエラー時
     */
    async getUserSettings(): Promise<UserSettings> {
        try {
            const response = await firstValueFrom(
                this.get<any>('/api/user/settings')
            );

            // Backend の snake_case を Frontend の camelCase に変換
            return {
                id: response.id,
                tenantId: response.tenant_id,
                userId: response.user_id,
                theme: response.theme,
                language: response.language,
                fontSize: response.font_size,
                llmProfile: response.llm_profile,
                hasSeenOnboarding: response.has_seen_onboarding,
                onboardingSkipped: response.onboarding_skipped,
                createdAt: response.created_at,
                updatedAt: response.updated_at
            };
        } catch (error: unknown) {
            throw this.apiErrorToSettingsError(error as ApiError);
        }
    }

    /**
     * ユーザー設定を更新する（部分更新対応）
     * 
     * 役割:
     * - ユーザーの設定を更新します。
     * - 部分更新に対応しており、変更したフィールドのみを送信できます。
     * - 例: theme だけを変更しても、他のフィールドは維持されます。
     * 
     * いつ使うか:
     * - Settings画面で保存ボタンが押されたとき
     * 
     * Backend API: POST /api/user/settings
     * 
     * @param settings 更新する設定（部分更新可能）
     * @returns Promise<UserSettings> 更新後のユーザー設定
     * @throws SettingsError バリデーションエラー、ネットワークエラー時
     */
    async updateUserSettings(settings: UserSettingsUpdate): Promise<UserSettings> {
        try {
            // Frontend の camelCase を Backend の snake_case に変換
            const payload: any = {};
            if (settings.theme !== undefined) payload.theme = settings.theme;
            if (settings.language !== undefined) payload.language = settings.language;
            if (settings.fontSize !== undefined) payload.font_size = settings.fontSize;
            if (settings.llmProfile !== undefined) payload.llm_profile = settings.llmProfile;
            if (settings.hasSeenOnboarding !== undefined) payload.has_seen_onboarding = settings.hasSeenOnboarding;
            if (settings.onboardingSkipped !== undefined) payload.onboarding_skipped = settings.onboardingSkipped;

            const response = await firstValueFrom(
                this.post<any>('/api/user/settings', payload)
            );

            // Backend の snake_case を Frontend の camelCase に変換
            return {
                id: response.id,
                tenantId: response.tenant_id,
                userId: response.user_id,
                theme: response.theme,
                language: response.language,
                fontSize: response.font_size,
                llmProfile: response.llm_profile,
                hasSeenOnboarding: response.has_seen_onboarding,
                onboardingSkipped: response.onboarding_skipped,
                createdAt: response.created_at,
                updatedAt: response.updated_at
            };
        } catch (error: unknown) {
            throw this.apiErrorToSettingsError(error as ApiError);
        }
    }

    // =========================
    // Help API メソッド (Task 7.4)
    // =========================

    /**
     * ヘルプコンテンツを取得する
     * 
     * 役割:
     * - ヘルプセクションの一覧または個別セクションを取得します。
     * - sectionId を指定すれば1件、無ければ一覧が返ります。
     * - category でフィルタリング可能（user/admin/all）。
     * 
     * いつ使うか:
     * - Help画面を表示するとき
     * 
     * Backend API: GET /api/help/content?section_id={id}&category={user|admin|all}
     * 
     * @param sectionId セクションID (optional、指定すれば1件取得)
     * @param category カテゴリフィルタ（"user" | "admin" | "all"、default: "user"）
     * @returns Promise<any> HelpSection | HelpSection[]
     * @throws エラー時は通常のHTTPエラー
     */
    async getHelpContent(sectionId?: string, category: 'user' | 'admin' | 'all' = 'user'): Promise<any> {
        try {
            let params = new HttpParams();
            if (sectionId) {
                params = params.set('section_id', sectionId);
            }
            params = params.set('category', category);

            return await firstValueFrom(
                this.get<any>('/api/help/content', { params })
            );
        } catch (error: unknown) {
            throw error;
        }
    }

    // =========================
    // プライベートヘルパーメソッド
    // =========================

    /**
     * エラーハンドリングの共通処理
     * 
     * 役割:
     * - HttpClient から投げられた生のエラーを受け取り、
     * - アプリ専用の ApiError クラスに変換して投げ直します。
     * - 必ずエラーを「握りつぶさず」に呼び出し元へ伝えます。
     * 
     * @param error HttpErrorResponse オブジェクト
     * @param url リクエスト先URL (optional、ログ出力用)
     * @returns Observable<never> エラーをthrowするストリーム
     */
    private handleError(error: HttpErrorResponse, url?: string): Observable<never> {
        let errorMessage = 'An unknown error occurred';
        let statusCode = 500;
        let errorCode: string | undefined;
        let details: unknown;

        if (error.error instanceof ErrorEvent) {
            // クライアント側（ネットワーク切断など）のエラー
            errorMessage = `Network or Client Error: ${error.error.message}`;
            statusCode = 0;
        } else {
            // バックエンドから返された HTTP エラー (4xx, 5xx)
            statusCode = error.status;
            if (typeof error.error === 'object' && error.error !== null) {
                errorMessage = (error.error as any).message || error.message;
                errorCode = (error.error as any).code;
                details = (error.error as any).details;
            } else {
                errorMessage = error.message;
            }
        }

        return throwError(() => new ApiError(errorMessage, statusCode, errorCode, details, url));
    }

    /**
     * ApiError を KnowledgeError に変換する
     * 
     * 役割:
     * - 汎用的な ApiError を、Knowledge 固有のエラーカテゴリに変換します。
     * - 特に 401 / 403 / 404 を詳細に区別します。
     * 
     * @param apiError ApiError オブジェクト
     * @returns KnowledgeError オブジェクト
     */
    private apiErrorToKnowledgeError(apiError: ApiError): KnowledgeError {
        let kind: KnowledgeError['kind'] = 'unknown';
        let message = apiError.message;

        if (apiError.status === 0) {
            kind = 'network';
            message = 'ネットワーク接続に失敗しました。';
        } else if (apiError.status === 401) {
            kind = 'http-401';
            message = 'セッションの有効期限が切れました。';
        } else if (apiError.status === 403) {
            kind = 'http-403';
            message = 'この操作を行う権限がありません。';
        } else if (apiError.status === 404) {
            kind = 'http-404';
            message = 'データが見つかりませんでした。';
        } else if (apiError.status >= 400 && apiError.status < 500) {
            kind = 'http-4xx';
        } else if (apiError.status >= 500) {
            kind = 'http-5xx';
            message = 'サーバー側でエラーが発生しました。';
        }

        return { kind, message, details: apiError.details };
    }

    /**
     * ApiError を SettingsError に変換する
     * 
     * 役割:
     * - 汎用的な ApiError を、Settings 固有のエラーカテゴリに変換します。
     * - 特に 401 / 403 / 422 を詳細に区別します。
     * 
     * @param apiError ApiError オブジェクト
     * @returns SettingsError オブジェクト
     */
    private apiErrorToSettingsError(apiError: ApiError): SettingsError {
        let kind: SettingsError['kind'] = 'unknown';
        let message = apiError.message;

        if (apiError.status === 0) {
            kind = 'network';
            message = 'ネットワーク接続に失敗しました。';
        } else if (apiError.status === 401) {
            kind = 'http-401';
            message = 'セッションの有効期限が切れました。';
        } else if (apiError.status === 403) {
            kind = 'http-403';
            message = 'この操作を行う権限がありません。';
        } else if (apiError.status >= 400 && apiError.status < 500) {
            kind = 'http-4xx';
            message = '入力内容に誤りがあります。';
        } else if (apiError.status >= 500) {
            kind = 'http-5xx';
            message = 'サーバー側でエラーが発生しました。';
        }

        return { kind, message, details: apiError.details };
    }
}
