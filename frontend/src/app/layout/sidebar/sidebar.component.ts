import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { User } from '../../core/models/user.model';

/**
 * SidebarComponent (サイドバー / ナビゲーション)
 * 
 * 役割:
 * - アプリケーションの左側に表示されるメニューです。
 * - 各機能画面（チャット、履歴、設定など）へのリンクを提供します。
 * - ユーザーの権限（管理者かどうか）に応じてメニューの表示/非表示を切り替えます。
 */
@Component({
    selector: 'app-sidebar',
    standalone: true,
    imports: [CommonModule, RouterModule, MatListModule, MatIconModule],
    templateUrl: './sidebar.component.html',
    styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent {
    /** 親コンポーネントから受け取るユーザー情報 */
    @Input() user: User | null = null;

    constructor() { }

    /**
     * 管理者かどうかを判定するヘルパー
     * (Knowledgeメニューの表示制御などに使用)
     */
    get isAdmin(): boolean {
        return this.user?.roles?.includes('admin') ?? false;
    }
}
