import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { KnowledgeDetail } from '@core/models/knowledge.models';

/**
 * KnowledgeDetailComponent (ナレッジ詳細表示)
 * 
 * 役割:
 * - 選択されたナレッジドキュメントの詳細情報を表示します。
 * - P0 では基本的なメタデータ（ファイル名・タイプ・サイズ・日時）のみ表示。
 * - P1 でファイル内容のプレビュー機能を追加予定。
 * 
 * いつ使うか:
 * - KnowledgePageComponent 内で、一覧から選択したドキュメントの詳細を表示します。
 */
@Component({
    selector: 'app-knowledge-detail',
    standalone: true,
    imports: [
        CommonModule,
        MatCardModule,
        MatIconModule,
        MatDividerModule
    ],
    templateUrl: './knowledge-detail.component.html',
    styleUrls: ['./knowledge-detail.component.scss']
})
export class KnowledgeDetailComponent {
    /**
     * ナレッジドキュメント詳細
     */
    detail = input.required<KnowledgeDetail>();

    /**
     * ファイルタイプのアイコンを取得
     * 
     * @param fileType MIME type
     * @returns Material Icon名
     */
    getFileIcon(fileType?: string | null): string {
        if (!fileType) return 'insert_drive_file';

        if (fileType.includes('pdf')) return 'picture_as_pdf';
        if (fileType.includes('word') || fileType.includes('document')) return 'description';
        if (fileType.includes('excel') || fileType.includes('spreadsheet')) return 'table_chart';
        if (fileType.includes('powerpoint') || fileType.includes('presentation')) return 'slideshow';
        if (fileType.includes('text')) return 'article';

        return 'insert_drive_file';
    }
}
