import { Component, OnInit, OnDestroy, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ApiService } from '@core/services/api.service';
import {
    ChatMessage,
    ChatSession,
    ChatAttachment,
    ChatError,
    Ic5Lite
} from '@core/models/chat.model';
import { MessageListComponent } from '../message-list/message-list.component';
import { ChatInputComponent } from '../chat-input/chat-input.component';
import { Ic5ViewerComponent, parseIc5Markdown } from '../ic5-viewer/ic5-viewer.component';
import { AttachmentListComponent } from '../attachment-list/attachment-list.component';

/**
 * ChatPageComponent (チャット画面)
 * 
 * 役割:
 * - チャット機能の全体を統括します。
 * - メッセージの送受信、ストリーミング、ファイル添付、セッション管理を担当します。
 * - 子コンポーネント（MessageList, ChatInput, Ic5Viewer, AttachmentList）を組み合わせます。
 * 
 * いつ使うか:
 * - `/chat` ルートでルーティングされたときに表示されます。
 * - AuthGuard により認証済みユーザーのみがアクセスできます。
 */
@Component({
    selector: 'app-chat-page',
    standalone: true,
    imports: [
        CommonModule,
        MatSnackBarModule,
        MatProgressBarModule,
        MatButtonModule,
        MatIconModule,
        MatTooltipModule,
        MessageListComponent,
        ChatInputComponent,
        Ic5ViewerComponent,
        AttachmentListComponent
    ],
    templateUrl: './chat-page.component.html',
    styleUrls: ['./chat-page.component.scss']
})
export class ChatPageComponent implements OnInit, OnDestroy {
    private apiService = inject(ApiService);
    private router = inject(Router);
    private snackBar = inject(MatSnackBar);

    // ========================================
    // State Management (Signals)
    // ========================================

    /** 現在のセッションID */
    currentSessionId = signal<string | null>(null);

    /** メッセージ一覧 */
    messages = signal<ChatMessage[]>([]);

    /** ストリーミング中かどうか */
    isStreaming = signal<boolean>(false);

    /** ストリーミング中のメッセージ内容（リアルタイム更新） */
    streamingContent = signal<string>('');

    /** IC-5ライトデータ */
    ic5 = signal<Ic5Lite | null>(null);

    /** ファイル添付一覧 */
    attachments = signal<ChatAttachment[]>([]);

    /** エラー情報 */
    error = signal<ChatError | null>(null);

    /** 送信中・ビジー状態 */
    isBusy = computed(() => this.isStreaming() || this.attachments().some(a => a.status === 'uploading'));

    /** SSE接続 (EventSource) */
    private eventSource: EventSource | null = null;

    // ========================================
    // Lifecycle Hooks
    // ========================================

    async ngOnInit(): Promise<void> {
        // 初期セッション作成またはリストア
        await this.initializeSession();
    }

    ngOnDestroy(): void {
        // SSE接続をクリーンアップ
        this.closeStream();
    }

    // ========================================
    // Session Management
    // ========================================

    /**
     * セッション初期化
     * 
     * 役割:
     * - 新しいセッションを作成します（または既存セッションをリストアします）。
     * - エラー発生時はユーザーに通知します。
     */
    private async initializeSession(): Promise<void> {
        try {
            const session = await this.apiService.createChatSession('新しいチャット');
            this.currentSessionId.set(session.id);
            console.log('[ChatPage] Session initialized:', session.id);
        } catch (error: unknown) {
            console.error('[ChatPage] Failed to initialize session:', error);
            this.handleError({
                kind: 'http-5xx',
                message: 'セッションの初期化に失敗しました。ページを再読み込みしてください。'
            });
        }
    }

    /**
     * セッションをリセット
     * 
     * 役割:
     * - 現在のセッションを終了し、新しいセッションを開始します。
     * - Backend 側で EpisodicMemory への保存が実行されます。
     */
    async onResetSession(): Promise<void> {
        const sessionId = this.currentSessionId();
        if (!sessionId) return;

        try {
            const newSession = await this.apiService.resetChatSession(sessionId);
            this.currentSessionId.set(newSession.id);
            this.messages.set([]);
            this.streamingContent.set('');
            this.ic5.set(null);
            this.attachments.set([]);
            this.error.set(null);

            this.showSnackbar('セッションをリセットしました。');
            console.log('[ChatPage] Session reset:', newSession.id);
        } catch (error: unknown) {
            console.error('[ChatPage] Failed to reset session:', error);
            this.handleError({
                kind: 'http-5xx',
                message: 'セッションのリセットに失敗しました。'
            });
        }
    }

    // ========================================
    // Message Handling
    // ========================================

    /**
     * メッセージ送信ハンドラ
     * 
     * 役割:
     * - ユーザーメッセージを Backend に送信します。
     * - SSE でストリーミング応答を受信します。
     * - IC-5形式をパースして表示します。
     * 
     * @param payload メッセージテキストとリサーチモードフラグ
     */
    async onSendMessage(payload: { text: string; isResearchMode: boolean }): Promise<void> {
        const sessionId = this.currentSessionId();
        if (!sessionId || this.isBusy()) {
            return;
        }

        try {
            // 1. ユーザーメッセージを送信（DB に保存）
            const userMessage = await this.apiService.sendChatMessage({
                sessionId,
                content: payload.text,
                role: 'user'
            });

            // 2. ローカル状態に追加
            this.messages.update(msgs => [...msgs, userMessage]);

            // 3. SSE ストリームを開始
            await this.startStream(sessionId, payload.isResearchMode);
        } catch (error: unknown) {
            console.error('[ChatPage] Failed to send message:', error);
            this.handleError({
                kind: 'http-5xx',
                message: 'メッセージの送信に失敗しました。'
            });
        }
    }

    /**
     * SSE ストリームを開始
     * 
     * 役割:
     * - Backend から LLM の応答をストリーミング受信します。
     * - トークンをリアルタイムで `streamingContent` に追加します。
     * - 完了時に IC-5 形式をパースします。
     * 
     * @param sessionId セッションID
     * @param researchMode リサーチモードフラグ
     */
    private async startStream(sessionId: string, researchMode: boolean): Promise<void> {
        this.isStreaming.set(true);
        this.streamingContent.set('');
        this.error.set(null);

        this.eventSource = this.apiService.getChatStream(
            sessionId,
            researchMode,
            (token: string) => {
                // トークン受信時
                this.streamingContent.update(content => content + token);
            },
            () => {
                // ストリーム完了時
                this.onStreamComplete();
            },
            (error: ChatError) => {
                // エラー発生時
                this.handleError(error);
                this.isStreaming.set(false);
            }
        );
    }

    /**
     * ストリーム完了時の処理
     * 
     * 役割:
     * - ストリーミングされたMarkdownをパースしてIC-5形式を抽出します。
     * - アシスタントメッセージとしてローカル状態に追加します。
     */
    private onStreamComplete(): void {
        const content = this.streamingContent();

        // IC-5 ライト形式をパース
        const ic5Data = parseIc5Markdown(content);
        this.ic5.set(ic5Data);

        // アシスタントメッセージを追加（疑似的に生成）
        const assistantMessage: ChatMessage = {
            id: `temp-${Date.now()}`, // 実際には Backend から取得すべき
            sessionId: this.currentSessionId()!,
            role: 'assistant',
            content,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };
        this.messages.update(msgs => [...msgs, assistantMessage]);

        // ストリーミング状態をリセット
        this.isStreaming.set(false);
        this.streamingContent.set('');

        console.log('[ChatPage] Stream completed and IC-5 parsed.');
    }

    /**
     * SSE接続をクローズ
     */
    private closeStream(): void {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            console.log('[ChatPage] SSE stream closed.');
        }
    }

    // ========================================
    // File Attachment Handling
    // ========================================

    /**
     * ファイル添付ハンドラ
     * 
     * 役割:
     * - 選択されたファイルをアップロードします。
     * - Ephemeral RAG に登録します（sessionId を指定）。
     * 
     * @param files 選択されたファイル一覧
     */
    async onAttachFiles(files: File[]): Promise<void> {
        const sessionId = this.currentSessionId();
        if (!sessionId) return;

        // ファイルごとに一時的な ChatAttachment を作成
        const newAttachments: ChatAttachment[] = files.map(file => ({
            id: `temp-${Date.now()}-${Math.random()}`,
            fileName: file.name,
            fileSize: file.size,
            status: 'pending'
        }));

        this.attachments.update(atts => [...atts, ...newAttachments]);

        // 各ファイルを順次アップロード
        for (const attachment of newAttachments) {
            const file = files.find(f => f.name === attachment.fileName);
            if (!file) continue;

            try {
                // ステータス更新: uploading
                this.updateAttachmentStatus(attachment.id, 'uploading');

                // アップロード実行
                const response = await this.apiService.uploadChatFile(file, sessionId);

                // ステータス更新: uploaded
                this.updateAttachmentStatus(attachment.id, 'uploaded', response.id);

                console.log('[ChatPage] File uploaded:', response);
            } catch (error: unknown) {
                console.error('[ChatPage] File upload failed:', error);

                // ステータス更新: failed
                const chatError = error as ChatError;
                this.updateAttachmentStatus(attachment.id, 'failed', undefined, chatError);
            }
        }
    }

    /**
     * ファイル削除ハンドラ
     * 
     * @param id 削除するファイルのクライアント側ID
     */
    onRemoveAttachment(id: string): void {
        this.attachments.update(atts => atts.filter(a => a.id !== id));
    }

    /**
     * 添付ファイルのステータスを更新
     * 
     * @param id ファイルID
     * @param status 新しいステータス
     * @param documentId アップロード成功時のドキュメントID
     * @param error エラー情報
     */
    private updateAttachmentStatus(
        id: string,
        status: ChatAttachment['status'],
        documentId?: string,
        error?: ChatError
    ): void {
        this.attachments.update(atts =>
            atts.map(a =>
                a.id === id
                    ? { ...a, status, documentId, error }
                    : a
            )
        );
    }

    // ========================================
    // Error Handling
    // ========================================

    /**
     * エラーハンドリング共通処理
     * 
     * 役割:
     * - エラーを状態に保存し、ユーザーに Snackbar で通知します。
     * 
     * @param error ChatError オブジェクト
     */
    private handleError(error: ChatError): void {
        this.error.set(error);
        this.showSnackbar(error.message, 'error');
    }

    /**
     * Snackbar 表示
     * 
     * @param message メッセージ
     * @param type 種別（info / error）
     */
    private showSnackbar(message: string, type: 'info' | 'error' = 'info'): void {
        this.snackBar.open(message, '閉じる', {
            duration: type === 'error' ? 5000 : 3000,
            panelClass: type === 'error' ? ['snackbar-error'] : []
        });
    }
}
