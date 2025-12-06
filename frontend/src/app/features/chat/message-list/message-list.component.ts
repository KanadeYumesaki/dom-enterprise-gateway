import { Component, input, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { ChatMessage } from '@core/models/chat.model';

/**
 * MessageListComponent (メッセージ一覧コンポーネント)
 * 
 * 役割:
 * - チャットメッセージの一覧を表示します。
 * - ユーザーメッセージとアシスタントメッセージを区別して表示します。
 * - ストリーミング中のインジケータを表示します。
 * 
 * いつ使うか:
 * - ChatPageComponent 内で、メッセージ履歴を表示するために使用します。
 */
@Component({
    selector: 'app-message-list',
    standalone: true,
    imports: [
        CommonModule,
        MatCardModule,
        MatProgressSpinnerModule,
        MatChipsModule,
        MatIconModule
    ],
    templateUrl: './message-list.component.html',
    styleUrls: ['./message-list.component.scss']
})
export class MessageListComponent {
    /**
     * 表示するメッセージの配列
     * 
     * 親コンポーネント (ChatPageComponent) から渡されます。
     */
    messages = input.required<ChatMessage[]>();

    /**
     * ストリーミング中かどうか
     * 
     * true の場合、「応答を生成中...」のインジケータを表示します。
     */
    isStreaming = input<boolean>(false);

    /**
     * 現在ストリーミング中のメッセージ内容
     * 
     * リアルタイムで更新される応答テキストを表示します。
     */
    streamingContent = input<string>('');

    /**
     * メッセージが空かどうかを判定
     */
    isEmpty = computed(() => this.messages().length === 0 && !this.isStreaming());

    /**
     * メッセージのロール（user/assistant）に応じたCSSクラスを返す
     * 
     * @param message メッセージオブジェクト
     * @returns CSSクラス名
     */
    getMessageClass(message: ChatMessage): string {
        return message.role === 'user' ? 'message-user' : 'message-assistant';
    }

    /**
     * メッセージの送信者名を取得
     * 
     * @param message メッセージオブジェクト
     * @returns 送信者名（日本語）
     */
    getSenderName(message: ChatMessage): string {
        if (message.role === 'user') {
            return 'あなた';
        } else if (message.role === 'assistant') {
            return 'アシスタント';
        }
        return 'システム';
    }

    /**
     * ソースアイコンを取得
     * 
     * @param sourceType ソースの種別
     * @returns Material Icon名
     */
    getSourceIcon(sourceType: string): string {
        switch (sourceType) {
            case 'RAG':
                return 'article';
            case 'Memory':
                return 'psychology';
            case 'Web':
                return 'public';
            case 'Assumption':
                return 'lightbulb';
            default:
                return 'info';
        }
    }
}
