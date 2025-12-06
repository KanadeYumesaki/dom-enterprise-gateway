import { Injectable, inject } from '@angular/core';
import { ApiService } from './api.service';
import { StateService } from './state.service';
import { UserSettings, UserSettingsUpdate } from '../models/settings.models';

/**
 * OnboardingService (簡易オンボーディング判定・更新)
 *
 * 役割:
 * - 初回利用者向けの案内を出すべきかどうかを判定する。
 * - 「見た」「スキップした」状態を Backend の user_settings に反映する。
 *
 * いつ呼ばれるか:
 * - MainLayoutComponent や ChatPageComponent の初期化時に、ユーザー設定を読み込んだあとで呼び出す想定。
 * - ダイアログやツアー UI から「開始」「スキップ」の操作を受け取ったときに使用する。
 */
@Injectable({
    providedIn: 'root'
})
export class OnboardingService {
    private apiService = inject(ApiService);
    private state = inject(StateService);

    /**
     * オンボーディングを表示すべきか判定する
     * - hasSeenOnboarding / onboardingSkipped がどちらも false のときのみ true。
     */
    shouldShowOnboarding(settings: UserSettings): boolean {
        return !settings.hasSeenOnboarding && !settings.onboardingSkipped;
    }

    /**
     * 「見た」とマークする
     * - Backend の user_settings を更新し、StateService の UI 設定も同期する。
     */
    async markOnboardingSeen(): Promise<UserSettings> {
        const updated = await this.saveAndSync({ hasSeenOnboarding: true, onboardingSkipped: false });
        return updated;
    }

    /**
     * 「スキップ」をマークする
     * - ユーザーが案内を閉じた場合に呼び出す。
     */
    async skipOnboarding(): Promise<UserSettings> {
        const updated = await this.saveAndSync({ onboardingSkipped: true, hasSeenOnboarding: false });
        return updated;
    }

    /**
     * Backend へ保存し、StateService の UI 設定を同期させる共通処理。
     * SSR 環境でも動くように副作用はサービス内に閉じておく。
     */
    private async saveAndSync(payload: UserSettingsUpdate): Promise<UserSettings> {
        const updated = await this.apiService.updateUserSettings(payload);
        this.state.updateUiSettings({
            theme: updated.theme,
            language: updated.language,
            fontSize: updated.fontSize
        });
        return updated;
    }
}
