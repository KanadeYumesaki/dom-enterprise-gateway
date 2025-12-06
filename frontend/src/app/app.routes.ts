import { Routes } from '@angular/router';
import { Component } from '@angular/core';
import { LoginPageComponent } from './features/auth/login-page/login-page.component';
import { AuthCallbackComponent } from './features/auth/auth-callback/auth-callback.component';
import { MainLayoutComponent } from './layout/main-layout/main-layout.component';
import { authGuard } from './core/guards/auth.guard';

// 一時的なプレースホルダコンポーネント (未実装機能用)
@Component({
    standalone: true,
    template: `
    <div style="padding: 24px;">
      <h2>Construction in Progress</h2>
      <p>この機能は現在開発中です (Task 7.2 以降で実装予定)。</p>
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
            { path: 'chat', component: WipComponent },
            { path: 'sessions', component: WipComponent },
            { path: 'memory', component: WipComponent },
            { path: 'knowledge', component: WipComponent },
            { path: 'settings', component: WipComponent },
            { path: 'help', component: WipComponent },
        ]
    },

    // 不明なパスはホームへ
    { path: '**', redirectTo: '' }
];
