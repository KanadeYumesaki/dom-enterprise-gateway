import { Component, Inject, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { UserSettings } from '@core/models/settings.models';
import { OnboardingService } from '@core/services/onboarding.service';

/**
 * OnboardingDialogComponent (簡易オンボーディング案内)
 *
 * 役割:
 * - 初回ログイン時に Settings / Help / Knowledge への導線を簡単に案内する。
 * - 「始める」「スキップ」操作を OnboardingService 経由で Backend に反映する。
 *
 * いつ表示されるか:
 * - MainLayoutComponent 初期化時に OnboardingService.shouldShowOnboarding() が true の場合。
 * - ボタン操作後はダイアログを閉じ、呼び出し元で最新設定を反映する。
 */
@Component({
    selector: 'app-onboarding-dialog',
    standalone: true,
    imports: [CommonModule, MatDialogModule, MatButtonModule],
    templateUrl: './onboarding-dialog.component.html',
    styleUrls: ['./onboarding-dialog.component.scss']
})
export class OnboardingDialogComponent {
    private onboardingService = inject(OnboardingService);
    private dialogRef = inject(MatDialogRef<OnboardingDialogComponent>);

    constructor(@Inject(MAT_DIALOG_DATA) public data: { settings: UserSettings }) { }

    /** ダイアログ内で現在の設定を参照するためのアクセサ */
    get settings(): UserSettings {
        return this.data.settings;
    }

    /** 「始める」ボタン押下時に hasSeenOnboarding を true にする */
    async onStart(): Promise<void> {
        try {
            await this.onboardingService.markOnboardingSeen();
            this.dialogRef.close('seen');
        } catch (error) {
            console.error('[OnboardingDialog] mark seen failed', error);
            this.dialogRef.close('error');
        }
    }

    /** 「あとで / スキップ」押下時に onboardingSkipped を true にする */
    async onSkip(): Promise<void> {
        try {
            await this.onboardingService.skipOnboarding();
            this.dialogRef.close('skipped');
        } catch (error) {
            console.error('[OnboardingDialog] skip failed', error);
            this.dialogRef.close('error');
        }
    }
}
