import { Component, input, output, signal, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatPaginatorModule, MatPaginator } from '@angular/material/paginator';
import { MatSortModule, MatSort } from '@angular/material/sort';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { KnowledgeDocument } from '@core/models/knowledge.models';

/**
 * KnowledgeListComponent (ナレッジ一覧テーブル)
 * 
 * 役割:
 * - ナレッジドキュメントの一覧を MatTable で表示します。
 * - ページネーション・ソート機能を提供します。
 * - 行クリックで詳細表示を通知します。
 * 
 * いつ使うか:
 * - KnowledgePageComponent 内で、ドキュメント一覧の表示に使用します。
 */
@Component({
    selector: 'app-knowledge-list',
    standalone: true,
    imports: [
        CommonModule,
        MatTableModule,
        MatPaginatorModule,
        MatSortModule,
        MatButtonModule,
        MatIconModule,
        MatTooltipModule
    ],
    templateUrl: './knowledge-list.component.html',
    styleUrls: ['./knowledge-list.component.scss']
})
export class KnowledgeListComponent implements AfterViewInit {
    /**
     * ナレッジドキュメント一覧
     */
    documents = input.required<KnowledgeDocument[]>();

    /**
     * ロード中フラグ
     */
    isLoading = input<boolean>(false);

    /**
     * ドキュメント選択イベント
     */
    selectDocument = output<string>();

    /**
     * テーブルのカラム定義
     */
    displayedColumns: string[] = ['fileName', 'fileType', 'fileSize', 'createdAt', 'actions'];

    /**
     * MatTable のデータソース
     */
    dataSource = new MatTableDataSource<KnowledgeDocument>([]);

    /**
     * ページネーター
     */
    @ViewChild(MatPaginator) paginator!: MatPaginator;

    /**
     * ソート
     */
    @ViewChild(MatSort) sort!: MatSort;

    ngAfterViewInit(): void {
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
    }

    /**
     * documents が変更されたら dataSource を更新
     */
    ngOnChanges(): void {
        this.dataSource.data = this.documents();
    }

    /**
     * 詳細表示ボタンクリック
     * 
     * @param id ドキュメントID
     */
    onViewDetail(id: string): void {
        this.selectDocument.emit(id);
    }

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
