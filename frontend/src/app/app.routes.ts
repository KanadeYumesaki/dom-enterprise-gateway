import { Routes } from '@angular/router';
import { Component } from '@angular/core';

// 一時的なスタブコンポーネント (Auth callback用)
// Task 7.x で本格的なコンポーネントに置き換えます。
@Component({
    standalone: true,
    template: '<p>ログイン処理中...</p>'
})
export class AuthCallbackStubComponent { }

export const routes: Routes = [
    // 認証コールバック用ルート (IdPから戻ってくる場所)
    {
        path: 'auth/callback',
        component: AuthCallbackStubComponent
    },

    // デフォルトルートなど (今は仮)
    // { path: '', component: ChatComponent ... }
];
