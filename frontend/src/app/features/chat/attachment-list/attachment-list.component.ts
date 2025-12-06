import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ChatAttachment } from '@core/models/chat.model';

/**
 * AttachmentListComponent (添付ファイル一覧コンポーネント)
 * 
 * 役割:
 * - アップロード中・完了・失敗したファイルの一覧を表示します。
 * - 各ファイルのステータス（pending/uploading/uploaded/failed）を視覚的に表示します。
 * - ファイル削除ボタンを提供します。
 * 
 * いつ使うか:
 * - ChatPageComponent 内で、ファイル添付の状態を表示するために使用します。
 */
@Component({
    selector: 'app-attachment-list',
    standalone: true,
    imports: [
        CommonModule,
        MatListModule,
        MatIconModule,
        MatButtonModule,
        MatProgressBarModule,
        MatTooltipModule
    ],
    templateUrl: './attachment-list.component.html',
    styleUrls: ['./attachment-list.component.scss']
})
export class AttachmentListComponent {
    /**
     * 添付ファイルの一覧
     * 
     * 親コンポーネント (ChatPageComponent) から渡されます。
     */
    attachments = input.required<ChatAttachment[]>();

    /**
     * ファイル削除イベント
     * 
     * @param id 削除するファイルのクライアント側ID
     */
    remove = output<string>();

    /**
     * ファイルサイズを人間が読める形式に変換
     * 
     * @param bytes バイト数
     * @returns フォーマットされた文字列（例: "1.5 MB"）
     */
    formatFileSize(bytes: number): string {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    /**
     * ステータスに応じたアイコンを取得
     * 
     * @param status ファイルのアップロード状態
     * @returns Material Icon名
     */
    getStatusIcon(status: ChatAttachment['status']): string {
        switch (status) {
            case 'pending':
                return 'schedule';
            case 'uploading':
                return 'cloud_upload';
            case 'uploaded':
                return 'check_circle';
            case 'failed':
                return 'error';
            default:
                return 'attach_file';
        }
    }

    /**
     * ステータスに応じたCSSクラスを取得
     * 
     * @param status ファイルのアップロード状態
     * @returns CSSクラス名
     */
    getStatusClass(status: ChatAttachment['status']): string {
        return `status-${status}`;
    }

    /**
     * ファイル削除ハンドラ
     * 
     * @param id 削除するファイルのクライアント側ID
     */
    onRemove(id: string): void {
        this.remove.emit(id);
    }
}
