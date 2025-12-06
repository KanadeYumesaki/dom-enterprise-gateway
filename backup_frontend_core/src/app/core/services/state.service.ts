import { Injectable, computed, signal } from '@angular/core';
import { User } from '../models/user.model';

/**
 * UIの設定（テーマなど）を管理する型
 */
export interface UiSettings {
    theme: 'light' | 'dark';
    language: 'ja' | 'en';
    fontSize: 'small' | 'medium' | 'large';
}

/**
 * アプリケーション全体の共有状態を管理するサービス
 * Angular Signals を使用して、リアクティブな状態管理を実現します。
 * NgRx などの複雑なライブラリを使わず、シンプルにストアの役割を果たします。
 */
@Injectable({
    providedIn: 'root'
})
export class StateService {

    // --- State Definitions (Signals) ---

    // 現在ログインしているユーザー（未ログイン時は null）
    private currentUserSignal = signal<User | null>(null);

    // アプリ全体で画面ブロックするようなロード中かどうか
    private isLoadingSignal = signal<boolean>(false);

    // UI設定（デフォルト値）
    private uiSettingsSignal = signal<UiSettings>({
        theme: 'light',
        language: 'ja',
        fontSize: 'medium'
    });

    // --- Computed Values (Selectors) ---

    // 読み取り専用のシグナルとして公開（コンポーネントから直接 set させないため）
    readonly currentUser = this.currentUserSignal.asReadonly();
    readonly isLoading = this.isLoadingSignal.asReadonly();
    readonly uiSettings = this.uiSettingsSignal.asReadonly();

    /** ログイン済みかどうかを派生 */
    readonly isLoggedIn = computed(() => !!this.currentUserSignal());

    /** 管理者かどうかを派生 */
    readonly isAdmin = computed(() => {
        const user = this.currentUserSignal();
        return user ? user.roles.includes('admin') : false;
    });

    constructor() {
        // 将来的に、Local Storage から設定を復元するロジックなどをここに書く
        // console.log('[StateService] Initialized');
    }

    // --- Updaters (Actions) ---

    /**
     * ユーザー情報を更新する
     * ログイン成功時やプロファイル更新時に呼ぶ
     */
    setUser(user: User): void {
        console.log('[StateService] Setting user:', user.id);
        this.currentUserSignal.set(user);
    }

    /**
     * ユーザー情報をクリアする
     * ログアウト時に呼ぶ
     */
    clearUser(): void {
        console.log('[StateService] Clearing user');
        this.currentUserSignal.set(null);
    }

    /**
     * ローディング状態を切り替える
     * @param loading true: ロード中, false: 完了
     */
    setLoading(loading: boolean): void {
        this.isLoadingSignal.set(loading);
    }

    /**
     * UI設定を部分的に更新する
     * @param settings 更新したい設定のオブジェクト（部分的でOK）
     */
    updateUiSettings(settings: Partial<UiSettings>): void {
        this.uiSettingsSignal.update(current => ({
            ...current,
            ...settings
        }));
        // 必要に応じてここで LocalStorage に保存する
    }
}
