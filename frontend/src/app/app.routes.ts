import { Routes } from '@angular/router';
import { Component } from '@angular/core';
import { LoginPageComponent } from './features/auth/login-page/login-page.component';
import { AuthCallbackComponent } from './features/auth/auth-callback/auth-callback.component';
import { MainLayoutComponent } from './layout/main-layout/main-layout.component';
import { ChatPageComponent } from './features/chat/chat-page/chat-page.component';
import { KnowledgePageComponent } from './features/knowledge/knowledge-page/knowledge-page.component';
import { SettingsPageComponent } from './features/settings/settings-page/settings-page.component';
import { HelpPageComponent } from './features/help/help-page/help-page.component';
import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';

// 一時的なプレースホルダコンポーネント（未実装画面用）
@Component({
    standalone: true,
    template: `
    <div style="padding: 24px;">
      <h2>Construction in Progress</h2>
      <p>この画面は現在開発中です (Task 7.4 以降で実装予定)。</p>
    </div>
  `
})
export class WipComponent { }

export const routes: Routes = [
    // ログイン画面
    {
        path: 'login',
        component: LoginPageComponent
    },

    // 認証コールバック (IdPから戻る場所)
    {
        path: 'auth/callback',
        component: AuthCallbackComponent
    },

    // メインアプリ (認証ガード付き)
    {
        path: '',
        component: MainLayoutComponent,
        canMatch: [authGuard], // ガード: 未ログインなら login へ
        children: [
            { path: '', redirectTo: 'chat', pathMatch: 'full' },
            { path: 'chat', component: ChatPageComponent }, // Task 7.2 完了
            { path: 'sessions', component: WipComponent },
            { path: 'memory', component: WipComponent },
            {
                path: 'knowledge',
                component: KnowledgePageComponent,
                canActivate: [adminGuard] // Task 7.3 完了: 管理者のみ閲覧可
            },
            { path: 'settings', component: SettingsPageComponent },
            { path: 'help', component: HelpPageComponent },
        ]
    },

    // 不明なパスはホームへ
    { path: '**', redirectTo: '' }
];
