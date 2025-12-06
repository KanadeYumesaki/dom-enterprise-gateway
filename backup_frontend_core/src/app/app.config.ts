import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

import { routes } from './app.routes';

/**
 * Angular アプリケーションのグローバル設定
 * Standalone Component ベースのメイン設定ファイル (main.ts から呼ばれる)
 */
export const appConfig: ApplicationConfig = {
    providers: [
        // Change Detection の最適化（ゾーン圧縮）
        provideZoneChangeDetection({ eventCoalescing: true }),

        // ルーティング設定の提供
        provideRouter(routes),

        // HttpClient の提供（これがないと HttpClient を注入できない）
        // インターセプターをDI経由で使う設定を含めている
        provideHttpClient(withInterceptorsFromDi()),

        // Angular Material 用のアニメーション設定
        provideAnimationsAsync()
    ]
};
