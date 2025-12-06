import { Component, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { StateService } from '../../core/services/state.service';
import { AuthService } from '../../core/services/auth.service';
import { HeaderComponent } from '../header/header.component';
import { SidebarComponent } from '../sidebar/sidebar.component';

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
        HeaderComponent,
        SidebarComponent
    ],
    templateUrl: './main-layout.component.html',
    styleUrls: ['./main-layout.component.scss']
})
export class MainLayoutComponent {
    private state = inject(StateService);
    private authService = inject(AuthService);

    /** 現在のユーザー (Signal) */
    user = this.state.currentUser;

    /** ロード中かどうか (Signal) */
    isLoading = this.state.isLoading;

    constructor() { }

    /**
     * ログアウト処理
     * HeaderComponent からイベントを受け取って実行します。
     */
    onLogout(): void {
        this.authService.logout();
    }
}
