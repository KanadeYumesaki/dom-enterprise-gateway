import { Injectable, computed, signal, WritableSignal } from '@angular/core';
import { User } from '../models/user.model';

/**
 * UIの表示設定を管理する型
 */
export interface UiSettings {
    /** テーマ設定 ('light' または 'dark') */
    theme: 'light' | 'dark';
    /** 言語設定 ('ja' または 'en') */
    language: 'ja' | 'en';
    /** 文字サイズ ('small', 'medium', 'large') */
    fontSize: 'small' | 'medium' | 'large';
}

/**
 * StateService (グローバル状態管理)
 * 
 * 役割:
 * - アプリケーション全体で共有したいデータ（ログインユーザー、設定、ロード中フラグなど）を一元管理します。
 * - Angular Signals を使って、データが変わったら自動的に画面も更新されるようにします。
 * 
 * なぜメソッド経由で更新するの？:
 * - どこからでも自由に書き換えられると、いつ誰がデータを変えたか分からなくなり、バグの原因になります。
 * - 「更新するときは必ずこのメソッドを通す」と決めることで、ログを出したり、保存処理を挟んだりしやすくなります。
 */
@Injectable({
    providedIn: 'root'
})
export class StateService {

    // --- 内部的な状態 (Private Signals) ---
    // 外部からは直接書き換えられないように private にします。

    /** 現在ログインしているユーザー情報 (未ログイン時は null) */
    private readonly _currentUser: WritableSignal<User | null> = signal<User | null>(null);

    /** 画面全体をブロックするような読み込み中かどうか */
    private readonly _isLoading: WritableSignal<boolean> = signal<boolean>(false);

    /** UIの表示設定（テーマや文字サイズ） */
    private readonly _uiSettings: WritableSignal<UiSettings> = signal<UiSettings>({
        theme: 'light',
        language: 'ja',
        fontSize: 'medium'
    });

    // --- 公開用の状態 (Public Computed Signals) ---
    // 外部コンポーネントはこれらを読み取ります（書き込み不可）。

    /** 現在のユーザー情報 (読み取り専用) */
    readonly currentUser = this._currentUser.asReadonly();

    /** ローディング中かどうか (読み取り専用) */
    readonly isLoading = this._isLoading.asReadonly();

    /** UI設定 (読み取り専用) */
    readonly uiSettings = this._uiSettings.asReadonly();

    /** ログイン済みかどうか（currentUser があるかどうかで自動計算） */
    readonly isLoggedIn = computed(() => !!this._currentUser());

    /** 管理者かどうか（currentUser の roles に 'admin' が含まれるかで自動計算） */
    readonly isAdmin = computed(() => {
        const user = this._currentUser();
        return user?.roles.includes('admin') ?? false;
    });

    constructor() {
        // 将来的には、ここで LocalStorage から設定を読み込む処理などを追加します。
        // console.log('[StateService] Initialized');
    }

    // --- 更新用のアクション (Actions) ---

    /**
     * ユーザー情報をセットする
     * - ログイン成功時や、プロフィール更新時に呼び出します。
     */
    setCurrentUser(user: User | null): void {
        console.log('[StateService] setCurrentUser:', user?.id ?? 'null');
        this._currentUser.set(user);
    }

    /**
     * ローディング状態を切り替える
     * - API通信の開始時に true、終了時に false にします。
     */
    setLoading(isLoading: boolean): void {
        // ログがうるさくなりすぎる場合はコメントアウトしてください
        // console.log('[StateService] setLoading:', isLoading);
        this._isLoading.set(isLoading);
    }

    /**
     * UI設定を部分的に更新する
     * - 例: updateUiSettings({ theme: 'dark' }) とすると、テーマだけが変わります。
     */
    updateUiSettings(partial: Partial<UiSettings>): void {
        console.log('[StateService] updateUiSettings:', partial);
        this._uiSettings.update(current => ({
            ...current,
            ...partial
        }));
        // ここで LocalStorage に保存すると便利です
    }
}
