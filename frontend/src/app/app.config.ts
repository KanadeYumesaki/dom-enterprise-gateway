// src/app/app.config.ts
import { ApplicationConfig, provideZonelessChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import {
  provideHttpClient,
  withFetch,
  withInterceptorsFromDi,
} from '@angular/common/http';
import {
  provideClientHydration,
  withEventReplay,
} from '@angular/platform-browser';

import { routes } from './app.routes';

/**
 * アプリケーション全体の共通設定 (main.ts で利用)
 *
 * 設定内容:
 * - ゾーンレス変更検知 (Zoneless Change Detection)
 * - ルーティング
 * - HTTPクライアント (fetch API利用 + DIインターセプター対応)
 * - クライアントハイドレーション (SSR用 + イベントリプレイ)
 */
export const appConfig: ApplicationConfig = {
  providers: [
    // ✅ Zone.js を使わない変更検知を有効化（Angular 20.2 以降で安定版）
    provideZonelessChangeDetection(),

    // ルーティング設定
    provideRouter(routes),

    // SSR + Fetch 対応の HttpClient
    provideHttpClient(
      withFetch(),
      withInterceptorsFromDi(),
    ),

    // SSR からブラウザへのハイドレーション＋イベントリプレイ
    provideClientHydration(withEventReplay()),
  ],
};
