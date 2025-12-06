import { Component, output, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';

/**
 * ChatInputComponent (チャット入力コンポーネント)
 * 
 * 役割:
 * - ユーザーがメッセージを入力し、送信するためのUIを提供します。
 * - ファイル添付ボタンを表示します（実際のアップロードは親から制御）。
 * - リサーチモードのトグルを提供します。
 * - サンプルプロンプト（テンプレート）の挿入機能を提供します。
 * 
 * いつ使うか:
 * - ChatPageComponent 内で、ユーザー入力を受け付けるために使用します。
 */
@Component({
    selector: 'app-chat-input',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatIconModule,
        MatSlideToggleModule,
        MatTooltipModule,
        MatChipsModule
    ],
    templateUrl: './chat-input.component.html',
    styleUrls: ['./chat-input.component.scss']
})
export class ChatInputComponent {
    /**
     * 送信ボタンが無効かどうか
     * 
     * 親コンポーネント (ChatPageComponent) から渡されます。
     * ストリーミング中などは true になります。
     */
    isBusy = input<boolean>(false);

    /**
     * メッセージ送信イベント
     * 
     * @param text メッセージ内容
     * @param isResearchMode リサーチモードが有効か
     */
    send = output<{ text: string; isResearchMode: boolean }>();

    /**
     * ファイル添付イベント
     * 
     * @param files 選択されたファイル一覧
     */
    attachFiles = output<File[]>();

    /**
     * テンプレート使用イベント
     * 
     * @param template テンプレート文字列
     */
    useTemplate = output<string>();

    /**
     * 入力中のメッセージテキスト
     */
    messageText = signal<string>('');

    /**
     * リサーチモードが有効かどうか
     */
    isResearchMode = signal<boolean>(false);

    /**
     * サンプルプロンプトのテンプレート
     * 
     * help_content_outline.md の「サンプルプロンプト」に基づいて定義します。
     */
    templates: string[] = [
        'この問題を分析して、3つの解決案を提案してください。',
        '○○について、初心者にもわかるように説明してください。',
        'このドキュメントの要点を5つにまとめてください。'
    ];

    /**
     * メッセージ送信ハンドラ
     * 
     * 役割:
     * - 入力テキストが空でない場合にのみ送信イベントを発行します。
     * - 送信後、入力欄をクリアします。
     */
    onSend(): void {
        const text = this.messageText().trim();
        if (!text || this.isBusy()) {
            return;
        }

        this.send.emit({
            text,
            isResearchMode: this.isResearchMode()
        });

        // 入力欄をクリア
        this.messageText.set('');
    }

    /**
     * ファイル選択ハンドラ
     * 
     * 役割:
     * - file input要素から選択されたファイルを取得し、親に通知します。
     * 
     * @param event File input change event
     */
    onFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        if (input.files && input.files.length > 0) {
            const files = Array.from(input.files);
            this.attachFiles.emit(files);

            // input をリセット（同じファイルを再選択可能にする）
            input.value = '';
        }
    }

    /**
     * テンプレート使用ハンドラ
     * 
     * 役割:
     * - 選択されたサンプルプロンプトを入力欄に挿入します。
     * 
     * @param template テンプレート文字列
     */
    onUseTemplate(template: string): void {
        this.messageText.set(template);
    }

    /**
     * Enterキー押下時のハンドラ
     * 
     * 役割:
     * - Shift+Enter: 改行
     * - Enter のみ: 送信
     * 
     * @param event キーボードイベント
     */
    onKeydown(event: KeyboardEvent): void {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.onSend();
        }
    }
}
