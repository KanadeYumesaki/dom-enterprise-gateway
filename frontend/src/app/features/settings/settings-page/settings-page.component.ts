import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatRadioModule } from '@angular/material/radio';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService } from '@core/services/api.service';
import { StateService } from '@core/services/state.service';
import { UserSettings, UserSettingsUpdate, SettingsError } from '@core/models/settings.models';

/**
 * SettingsPageComponent (/settings)
 *
 * 役割:
 * - ユーザーの UI 設定（テーマ・言語・フォントサイズ・オンボーディング状態）を表示・更新する。
 * - 更新後は StateService にも反映し、他画面へ即時伝播させる。
 *
 * いつ呼ばれるか:
 * - `/settings` ルートに遷移したときに表示される。
 * - AuthGuard 配下なので、ログイン後のユーザーのみアクセス可能。
 */
@Component({
    selector: 'app-settings-page',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatCardModule,
        MatFormFieldModule,
        MatSelectModule,
        MatRadioModule,
        MatSlideToggleModule,
        MatButtonModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatSnackBarModule
    ],
    templateUrl: './settings-page.component.html',
    styleUrls: ['./settings-page.component.scss']
})
export class SettingsPageComponent implements OnInit {
    private apiService = inject(ApiService);
    private state = inject(StateService);
    private snackBar = inject(MatSnackBar);
    private router = inject(Router);
    private fb = inject(FormBuilder);

    /** 現在の設定値 */
    settings = signal<UserSettings | null>(null);
    /** ローディング状態 */
    isLoading = signal<boolean>(false);
    /** 保存中状態 */
    isSaving = signal<boolean>(false);
    /** エラー保持 */
    error = signal<SettingsError | null>(null);

    /** 設定フォーム (Reactive Forms) */
    form = this.fb.group({
        theme: this.fb.control<'light' | 'dark'>('light', { validators: [Validators.required] }),
        language: this.fb.control<'ja' | 'en'>('ja', { validators: [Validators.required] }),
        fontSize: this.fb.control<'small' | 'medium' | 'large'>('medium', { validators: [Validators.required] }),
        hasSeenOnboarding: this.fb.control<boolean>(false),
        onboardingSkipped: this.fb.control<boolean>(false)
    });

    async ngOnInit(): Promise<void> {
        await this.loadSettings();
    }

    /**
     * 設定をサーバーから取得しフォームに反映する
     */
    async loadSettings(): Promise<void> {
        this.isLoading.set(true);
        this.error.set(null);

        try {
            const result = await this.apiService.getUserSettings();
            this.settings.set(result);
            this.form.patchValue({
                theme: result.theme,
                language: result.language,
                fontSize: result.fontSize,
                hasSeenOnboarding: result.hasSeenOnboarding,
                onboardingSkipped: result.onboardingSkipped
            });

            // グローバル UI 設定にも反映
            this.state.updateUiSettings({
                theme: result.theme,
                language: result.language,
                fontSize: result.fontSize
            });
        } catch (error: unknown) {
            this.handleError(error as SettingsError);
        } finally {
            this.isLoading.set(false);
        }
    }

    /**
     * 保存ボタンクリック時の処理
     * - 変更差分のみ送信し、成功時は StateService にも反映する。
     */
    async onSave(): Promise<void> {
        const current = this.settings();
        if (!current) return;

        const value = this.form.value;
        const payload: UserSettingsUpdate = {};

        if (value.theme && value.theme !== current.theme) payload.theme = value.theme;
        if (value.language && value.language !== current.language) payload.language = value.language;
        if (value.fontSize && value.fontSize !== current.fontSize) payload.fontSize = value.fontSize;
        if (
            value.hasSeenOnboarding !== null &&
            value.hasSeenOnboarding !== undefined &&
            value.hasSeenOnboarding !== current.hasSeenOnboarding
        ) {
            payload.hasSeenOnboarding = value.hasSeenOnboarding;
        }
        if (
            value.onboardingSkipped !== null &&
            value.onboardingSkipped !== undefined &&
            value.onboardingSkipped !== current.onboardingSkipped
        ) {
            payload.onboardingSkipped = value.onboardingSkipped;
        }
        if (Object.keys(payload).length === 0) {
            this.showSnackbar('変更はありません。', 'info');
            return;
        }

        this.isSaving.set(true);
        this.error.set(null);

        try {
            const updated = await this.apiService.updateUserSettings(payload);
            this.settings.set(updated);
            this.form.patchValue({
                theme: updated.theme,
                language: updated.language,
                fontSize: updated.fontSize,
                hasSeenOnboarding: updated.hasSeenOnboarding,
                onboardingSkipped: updated.onboardingSkipped
            });
            this.state.updateUiSettings({
                theme: updated.theme,
                language: updated.language,
                fontSize: updated.fontSize
            });
            this.showSnackbar('設定を保存しました。', 'info');
        } catch (error: unknown) {
            this.handleError(error as SettingsError);
        } finally {
            this.isSaving.set(false);
        }
    }

    /**
     * エラーハンドリング
     * - 401 はログインへ誘導、それ以外は Snackbar 表示。
     */
    private handleError(error: SettingsError): void {
        this.error.set(error);

        if (error.kind === 'http-401') {
            this.showSnackbar('セッションが切れました。再ログインしてください。', 'error');
            this.router.navigate(['/login']);
            return;
        }

        const message = error.message || '設定の取得／保存中にエラーが発生しました。';
        this.showSnackbar(message, 'error');
        console.error('[SettingsPage] error:', error);
    }

    /**
     * Snackbar 表示ヘルパー
     */
    private showSnackbar(message: string, type: 'info' | 'error'): void {
        this.snackBar.open(message, '閉じる', {
            duration: type === 'error' ? 5000 : 3000,
            panelClass: type === 'error' ? ['snackbar-error'] : []
        });
    }
}
