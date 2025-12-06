import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MatListModule } from '@angular/material/list';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService } from '@core/services/api.service';
import { HelpSection, HelpError } from '@core/models/help.models';

/**
 * HelpPageComponent (/help)
 *
 * 役割:
 * - ヘルプセクションの一覧と詳細を表示する。
 * - URL クエリパラメータ `section` により初期選択を切り替えられる。
 *
 * いつ呼ばれるか:
 * - `/help` ルートに遷移したとき。
 * - AuthGuard 配下なので認証後のみアクセス可能。
 */
@Component({
    selector: 'app-help-page',
    standalone: true,
    imports: [
        CommonModule,
        MatListModule,
        MatCardModule,
        MatProgressSpinnerModule,
        MatButtonModule,
        MatIconModule,
        MatSnackBarModule
    ],
    templateUrl: './help-page.component.html',
    styleUrls: ['./help-page.component.scss']
})
export class HelpPageComponent implements OnInit {
    private apiService = inject(ApiService);
    private route = inject(ActivatedRoute);
    private router = inject(Router);
    private snackBar = inject(MatSnackBar);

    /** 取得したヘルプセクション一覧 */
    sections = signal<HelpSection[]>([]);
    /** 現在表示中のセクション */
    selected = signal<HelpSection | null>(null);
    /** ロード中フラグ */
    isLoading = signal<boolean>(false);
    /** エラー保持 */
    error = signal<HelpError | null>(null);

    async ngOnInit(): Promise<void> {
        const sectionId = this.route.snapshot.queryParamMap.get('section');
        await this.loadSections(sectionId || undefined);
    }

    /**
     * セクション一覧を読み込み、初期選択を決める
     */
    async loadSections(initialSectionId?: string): Promise<void> {
        this.isLoading.set(true);
        this.error.set(null);

        try {
            const response = await this.apiService.getHelpContent();
            const list = Array.isArray(response) ? response : [response];
            this.sections.set(list);

            const initial =
                list.find(item => item.id === initialSectionId) ??
                list[0] ??
                null;

            this.selected.set(initial);
        } catch (error: unknown) {
            this.handleError(this.mapToHelpError(error));
        } finally {
            this.isLoading.set(false);
        }
    }

    /**
     * セクション選択時のハンドラ
     */
    onSelect(section: HelpSection): void {
        this.selected.set(section);
        // URL のクエリパラメータを更新して共有しやすくする
        this.router.navigate([], {
            queryParams: { section: section.id },
            queryParamsHandling: 'merge'
        });
    }

    /**
     * エラーハンドリング
     * - 401 はログインへ誘導。
     * - その他は Snackbar と再読み込みボタンで対応。
     */
    private handleError(error: HelpError): void {
        this.error.set(error);

        if (error.kind === 'http-401') {
            this.showSnackbar('セッションが切れました。再ログインしてください。', 'error');
            this.router.navigate(['/login']);
            return;
        }

        const message = error.message || 'ヘルプの読み込みに失敗しました。';
        this.showSnackbar(message, 'error');
        console.error('[HelpPage] error:', error);
    }

    /**
     * Snackbar 表示ヘルパー
     */
    private showSnackbar(message: string, type: 'info' | 'error'): void {
        this.snackBar.open(message, '閉じる', {
            duration: type === 'error' ? 5000 : 3000,
            panelClass: type === 'error' ? ['snackbar-error'] : []
        });
    }

    /**
     * ApiError など unknown を HelpError に正規化する
     */
    private mapToHelpError(error: unknown): HelpError {
        const status = (error as any)?.status ?? 500;
        let kind: HelpError['kind'] = 'unknown';

        if (status === 0) {
            kind = 'network';
        } else if (status === 401) {
            kind = 'http-401';
        } else if (status === 403) {
            kind = 'http-403';
        } else if (status === 404) {
            kind = 'http-404';
        } else if (status >= 400 && status < 500) {
            kind = 'http-4xx';
        } else if (status >= 500) {
            kind = 'http-5xx';
        }

        return {
            kind,
            message: (error as any)?.message || 'ヘルプの取得でエラーが発生しました。',
            details: (error as any)?.details
        };
    }
}
