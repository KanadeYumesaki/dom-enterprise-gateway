import { Component, inject, computed, OnInit, PLATFORM_ID } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { StateService } from '../../core/services/state.service';
import { AuthService } from '../../core/services/auth.service';
import { ApiService } from '../../core/services/api.service';
import { OnboardingService } from '../../core/services/onboarding.service';
import { HeaderComponent } from '../header/header.component';
import { SidebarComponent } from '../sidebar/sidebar.component';
import { OnboardingDialogComponent } from '../../core/components/onboarding-dialog/onboarding-dialog.component';

/**
 * MainLayoutComponent (メインレイアウト / シェル)
 * 
 * 役割:
 * - ログイン後のすべての画面の外枠となるコンポーネントです。
 * - ヘッダー、サイドバー、そしてメインコンテンツエリア (router-outlet) を配置します。
 * - StateService から最新のユーザー情報を取得して、各パーツに渡します。
 * 
 * 構成:
 * - mat-sidenav-container: 全体を包むコンテナ
 *   - mat-sidenav: サイドバー (SidebarComponent)
 *   - mat-sidenav-content: メインコンテンツ側
 *     - app-header: ヘッダー (HeaderComponent)
 *     - router-outlet: ページの中身 (Chat, Settingsなど)
 */
@Component({
    selector: 'app-main-layout',
    standalone: true,
    imports: [
        CommonModule,
        RouterModule,
        MatSidenavModule,
        MatDialogModule,
        HeaderComponent,
        SidebarComponent,
        //OnboardingDialogComponent 20251206 7.4対応でコメントアウト
    ],
    templateUrl: './main-layout.component.html',
    styleUrls: ['./main-layout.component.scss']
})
export class MainLayoutComponent implements OnInit {
    private state = inject(StateService);
    private authService = inject(AuthService);
    private apiService = inject(ApiService);
    private onboardingService = inject(OnboardingService);
    private dialog = inject(MatDialog);
    private platformId = inject(PLATFORM_ID);

    /** 現在のユーザー (Signal) */
    user = this.state.currentUser;

    /** ロード中かどうか (Signal) */
    isLoading = this.state.isLoading;

    constructor() { }

    /**
     * 初期化時にユーザー設定を取得し、必要ならオンボーディングを表示する。
     */
    async ngOnInit(): Promise<void> {
        if (!isPlatformBrowser(this.platformId)) {
            return; // SSR 環境ではダイアログやブラウザ依存処理を実行しない
        }
        await this.preloadSettingsAndOnboarding();
    }

    /**
     * ログアウト処理
     * HeaderComponent からイベントを受け取って実行します。
     */
    onLogout(): void {
        this.authService.logout();
    }

    /**
     * UI設定のプリロードとオンボーディング表示判定
     * - SSR / Zoneless 環境でも動くように副作用をサービスに閉じ込める。
     */
    private async preloadSettingsAndOnboarding(): Promise<void> {
        try {
            const settings = await this.apiService.getUserSettings();
            this.state.updateUiSettings({
                theme: settings.theme,
                language: settings.language,
                fontSize: settings.fontSize
            });

            if (this.onboardingService.shouldShowOnboarding(settings)) {
                this.dialog.open(OnboardingDialogComponent, {
                    data: { settings },
                    disableClose: true,
                    width: '420px'
                });
            }
        } catch (error) {
            // ログだけに留め、画面表示は継続する（ガード側で再ログイン誘導済み）
            console.warn('[MainLayout] 設定の取得に失敗しました。オンボーディングはスキップします。', error);
        }
    }
}
