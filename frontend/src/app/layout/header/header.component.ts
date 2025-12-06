import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { User } from '../../core/models/user.model';
import { environment } from '../../../environments/environment';

/**
 * HeaderComponent (ヘッダー)
 * 
 * 役割:
 * - アプリケーションの上部バー (App Bar) です。
 * - アプリ名の表示、現在のユーザー情報の表示、ログアウトボタンを提供します。
 * 
 * どのタイミングで呼ばれるか:
 * - メインレイアウト (MainLayoutComponent) の一部として常に表示されます。
 */
@Component({
    selector: 'app-header',
    standalone: true,
    imports: [CommonModule, MatToolbarModule, MatButtonModule, MatIconModule],
    templateUrl: './header.component.html',
    styleUrls: ['./header.component.scss']
})
export class HeaderComponent {
    /** 現在ログインしているユーザー情報 (親コンポーネントから受け取る) */
    @Input() user: User | null = null;

    /** ログアウトボタンが押されたことを親に伝えるイベント */
    @Output() logout = new EventEmitter<void>();

    /** 環境ラベル (DEV / STG / PROD) - 開発環境かどうかで表示を変える用 */
    // environment.ts に production フラグがあるのでそれを利用する例
    isProduction = environment.production;

    constructor() { }

    /**
     * ログアウトボタンクリック時
     */
    onLogout(): void {
        // 実際の処理は親 (MainLayout -> AuthService) に任せます
        this.logout.emit();
    }

    /**
     * ユーザーのロール表示用ヘルパー
     * (例: adminなら '管理者', userなら '一般' など)
     */
    get roleLabel(): string {
        if (!this.user?.roles) return '';
        return this.user.roles.includes('admin') ? 'Admin' : 'User';
    }
}
