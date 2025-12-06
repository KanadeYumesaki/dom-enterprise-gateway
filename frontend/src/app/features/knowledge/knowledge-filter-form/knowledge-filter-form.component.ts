import { Component, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { debounceTime, distinctUntilChanged } from 'rxjs';
import { KnowledgeFilter } from '@core/models/knowledge.models';

/**
 * KnowledgeFilterFormComponent (ナレッジ検索フォーム)
 * 
 * 役割:
 * - ファイル名検索フォームを提供します。
 * - デバウンス機能により、入力後300msで自動検索を発火します。
 * - 検索クリア機能を提供します。
 * 
 * いつ使うか:
 * - KnowledgePageComponent 内で、検索条件の入力UIとして使用します。
 */
@Component({
    selector: 'app-knowledge-filter-form',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatIconModule
    ],
    templateUrl: './knowledge-filter-form.component.html',
    styleUrls: ['./knowledge-filter-form.component.scss']
})
export class KnowledgeFilterFormComponent {
    /**
     * 検索クエリ変更イベント
     * 
     * デバウンス後に親コンポーネントへ通知します。
     */
    search = output<KnowledgeFilter>();

    /**
     * 検索フォームコントロール
     */
    searchControl = new FormControl<string>('');

    /**
     * 検索中フラグ
     */
    isSearching = signal<boolean>(false);

    constructor() {
        // デバウンス処理: 入力後300msで検索イベントを発火
        this.searchControl.valueChanges
            .pipe(
                debounceTime(300),
                distinctUntilChanged()
            )
            .subscribe(value => {
                this.onSearch(value || '');
            });
    }

    /**
     * 検索実行
     * 
     * @param query 検索クエリ
     */
    private onSearch(query: string): void {
        this.search.emit({
            searchQuery: query || undefined
        });
    }

    /**
     * 検索クリア
     */
    onClear(): void {
        this.searchControl.setValue('');
    }
}
