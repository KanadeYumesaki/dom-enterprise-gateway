import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { ApiService } from '@core/services/api.service';
import {
    KnowledgeDocument,
    KnowledgeDetail,
    KnowledgeFilter,
    KnowledgeError
} from '@core/models/knowledge.models';
import { KnowledgeFilterFormComponent } from '../knowledge-filter-form/knowledge-filter-form.component';
import { KnowledgeListComponent } from '../knowledge-list/knowledge-list.component';
import { KnowledgeDetailComponent } from '../knowledge-detail/knowledge-detail.component';

/**
 * KnowledgePageComponent (ナレッジ管理画面)
 * 
 * 役割:
 * - ナレッジ管理機能の全体を統括します。
 * - 一覧表示・検索・詳細表示を担当します。
 * - 管理者専用画面（AdminGuard により保護）。
 * 
 * いつ使うか:
 * - `/knowledge` ルートでルーティングされたときに表示されます。
 * - AdminGuard により管理者のみがアクセスできます。
 */
@Component({
    selector: 'app-knowledge-page',
    standalone: true,
    imports: [
        CommonModule,
        MatSnackBarModule,
        MatProgressBarModule,
        MatButtonModule,
        MatIconModule,
        MatDividerModule,
        KnowledgeFilterFormComponent,
        KnowledgeListComponent,
        KnowledgeDetailComponent
    ],
    templateUrl: './knowledge-page.component.html',
    styleUrls: ['./knowledge-page.component.scss']
})
export class KnowledgePageComponent implements OnInit {
    private apiService = inject(ApiService);
    private snackBar = inject(MatSnackBar);

    // ========================================
    // State Management (Signals)
    // ========================================

    /** ナレッジドキュメント一覧 */
    documents = signal<KnowledgeDocument[]>([]);

    /** 選択中のドキュメント詳細 */
    selectedDetail = signal<KnowledgeDetail | null>(null);

    /** ロード中フラグ */
    isLoading = signal<boolean>(false);

    /** エラー情報 */
    error = signal<KnowledgeError | null>(null);

    /** 現在の検索フィルタ */
    currentFilter = signal<KnowledgeFilter>({});

    // ========================================
    // Lifecycle Hooks
    // ========================================

    async ngOnInit(): Promise<void> {
        // 初期表示: 全ドキュメント取得
        await this.loadDocuments();
    }

    // ========================================
    // Document Loading
    // ========================================

    /**
     * ドキュメント一覧を読み込み
     * 
     * @param filter 検索・フィルタ条件 (optional)
     */
    async loadDocuments(filter?: KnowledgeFilter): Promise<void> {
        this.isLoading.set(true);
        this.error.set(null);

        try {
            const documents = await this.apiService.getKnowledgeList(filter);
            this.documents.set(documents);
            this.currentFilter.set(filter || {});
            console.log('[KnowledgePage] Loaded documents:', documents.length);
        } catch (error: unknown) {
            console.error('[KnowledgePage] Failed to load documents:', error);
            this.handleError(error as KnowledgeError);
        } finally {
            this.isLoading.set(false);
        }
    }

    /**
     * ドキュメント詳細を読み込み
     * 
     * @param id ドキュメントID
     */
    async loadDocumentDetail(id: string): Promise<void> {
        this.isLoading.set(true);
        this.error.set(null);

        try {
            const detail = await this.apiService.getKnowledgeDetail(id);
            this.selectedDetail.set(detail);
            console.log('[KnowledgePage] Loaded detail for:', id);
        } catch (error: unknown) {
            console.error('[KnowledgePage] Failed to load detail:', error);
            this.handleError(error as KnowledgeError);
        } finally {
            this.isLoading.set(false);
        }
    }

    // ========================================
    // Event Handlers
    // ========================================

    /**
     * 検索イベントハンドラ
     * 
     * @param filter 検索フィルタ
     */
    onSearch(filter: KnowledgeFilter): void {
        this.loadDocuments(filter);
        // 検索時は詳細表示をクリア
        this.selectedDetail.set(null);
    }

    /**
     * ドキュメント選択イベントハンドラ
     * 
     * @param id ドキュメントID
     */
    onSelectDocument(id: string): void {
        this.loadDocumentDetail(id);
    }

    /**
     * 詳細表示を閉じる
     */
    onCloseDetail(): void {
        this.selectedDetail.set(null);
    }

    // ========================================
    // Error Handling
    // ========================================

    /**
     * エラーハンドリング共通処理
     * 
     * 役割:
     * - エラーを状態に保存し、ユーザーに Snackbar で通知します。
     * - 401 / 403 の場合は適切にログイン / アクセス拒否を処理します。
     * 
     * @param error KnowledgeError オブジェクト
     */
    private handleError(error: KnowledgeError): void {
        this.error.set(error);

        // エラー種別に応じた処理
        if (error.kind === 'http-401') {
            // 401: 再ログインを促す
            this.showSnackbar(error.message, 'error');
            // TODO: Auth フローで再ログイン処理
        } else if (error.kind === 'http-403') {
            // 403: 管理者権限なしを通知
            this.showSnackbar(error.message, 'error');
            // AdminGuard で既にリダイレクトされているはずだが、念のため
        } else {
            // その他のエラー
            this.showSnackbar(error.message, 'error');
        }
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
