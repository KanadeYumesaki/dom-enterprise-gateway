import { Component, input, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTabsModule } from '@angular/material/tabs';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { Ic5Lite } from '@core/models/chat.model';

/**
 * Ic5ViewerComponent (IC-5ライト表示コンポーネント)
 * 
 * 役割:
 * - IC-5ライト形式（Decision / Why / Next 3 Actions）をパースして表示します。
 * - Backendから返されるMarkdownをパースし、各セクションを見やすく表示します。
 * 
 * いつ使うか:
 * - ChatPageComponent 内で、LLMの応答をIC-5形式で表示するために使用します。
 */
@Component({
    selector: 'app-ic5-viewer',
    standalone: true,
    imports: [
        CommonModule,
        MatCardModule,
        MatTabsModule,
        MatIconModule,
        MatListModule
    ],
    templateUrl: './ic5-viewer.component.html',
    styleUrls: ['./ic5-viewer.component.scss']
})
export class Ic5ViewerComponent {
    /**
     * IC-5ライトデータ
     * 
     * 親コンポーネント (ChatPageComponent) から渡されます。
     * nullの場合は何も表示しません。
     */
    ic5 = input<Ic5Lite | null>(null);

    /**
     * IC-5データが存在するかどうか
     */
    hasIc5 = computed(() => this.ic5() !== null);

    /**
     * パース警告が存在するかどうか
     */
    hasWarnings = computed(() => {
        const ic5Data = this.ic5();
        return ic5Data?.parseWarnings && ic5Data.parseWarnings.length > 0;
    });
}

/**
 * IC-5ライト形式のMarkdownをパースするユーティリティ関数
 * 
 * 役割:
 * - Markdown形式のテキストから Decision / Why / Next 3 Actions を抽出します。
 * 
 * @param markdown Markdownテキスト
 * @returns パースされたIc5Liteオブジェクト
 */
export function parseIc5Markdown(markdown: string): Ic5Lite {
    const warnings: string[] = [];
    let decision = '';
    let why = '';
    const nextActions: string[] = [];

    // ## Decision セクションを抽出
    const decisionMatch = markdown.match(/##\s*Decision\s*\n+([\s\S]*?)(?=##|$)/i);
    if (decisionMatch) {
        decision = decisionMatch[1].trim();
    } else {
        warnings.push('Decision セクションが見つかりませんでした。');
    }

    // ## Why セクションを抽出
    const whyMatch = markdown.match(/##\s*Why\s*\n+([\s\S]*?)(?=##|$)/i);
    if (whyMatch) {
        why = whyMatch[1].trim();
    } else {
        warnings.push('Why セクションが見つかりませんでした。');
    }

    // ## Next 3 Actions セクションを抽出
    const actionsMatch = markdown.match(/##\s*Next\s+3\s+Actions?\s*\n+([\s\S]*?)(?=##|$)/i);
    if (actionsMatch) {
        const actionsText = actionsMatch[1].trim();
        // 番号付きリスト（1. / 2. / 3.）または箇条書き（- / *）を抽出
        const actionItems = actionsText.match(/(?:^\d+\.\s*|\s*[-*]\s+)(.+)$/gm);
        if (actionItems) {
            actionItems.forEach(item => {
                const cleaned = item.replace(/^\d+\.\s*|\s*[-*]\s+/, '').trim();
                if (cleaned) {
                    nextActions.push(cleaned);
                }
            });
        }
    } else {
        warnings.push('Next 3 Actions セクションが見つかりませんでした。');
    }

    return {
        decision,
        why,
        nextActions,
        rawMarkdown: markdown,
        parseWarnings: warnings.length > 0 ? warnings : undefined
    };
}
