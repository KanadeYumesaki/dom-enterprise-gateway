from typing import Literal
from app.schemas.help import HelpSection

# ヘルプコンテンツの静的定義
# データソース: help_content_outline.md を手動で変換
# P1 では help_sections テーブルから読み込む拡張も可能

HELP_SECTIONS_DATA = [
    {
        "id": "intro",
        "title": "はじめに",
        "content": """# DOM Enterprise Gateway へようこそ

このシステムは、エンタープライズ向けの AI チャットゲートウェイです。

## 主な機能
- **チャット**: AI との対話機能
- **ナレッジ検索**: アップロードされたドキュメントから情報を取得
- **メモリ管理**: 会話履歴とナレッジの永続化
""",
        "order": 1,
        "category": "user"
    },
    {
        "id": "chat",
        "title": "チャット機能",
        "content": """# チャット機能の使い方

## メッセージ送信
1. 画面下部の入力欄にメッセージを入力
2. Enter キーまたは送信ボタンで送信
3. AI からの応答がリアルタイムで表示されます

## ファイル添付
- メッセージと一緒にファイルを添付できます
- 対応形式: PDF, Word, Excel, テキストファイル
""",
        "order": 2,
        "category": "user"
    },
    {
        "id": "files",
        "title": "ファイル管理",
        "content": """# ファイルのアップロードと管理

## アップロード方法
1. チャット入力欄の添付ボタンをクリック
2. ファイルを選択してアップロード
3. アップロードしたファイルは自動的にナレッジベースに登録されます

## 対応形式
- PDF
- Microsoft Word (.docx)
- Microsoft Excel (.xlsx)
- テキストファイル (.txt, .md)
""",
        "order": 3,
        "category": "user"
    },
    {
        "id": "memory",
        "title": "メモリとセッション",
        "content": """# メモリとセッション管理

## セッション
- チャット履歴はセッション単位で保存されます
- 新しいセッションを作成することで、文脈をリセットできます

## メモリ
- 構造化メモリ: ユーザー設定やプロファイル情報
- エピソード記憶: 会話履歴とコンテキスト
""",
        "order": 4,
        "category": "user"
    },
    {
        "id": "settings",
        "title": "設定",
        "content": """# ユーザー設定

## UI設定
- **テーマ**: Light / Dark
- **言語**: 日本語 / English
- **フォントサイズ**: Small / Medium / Large

## オンボーディング
- 初回ログイン時にガイドツアーが表示されます
- スキップまたは完了後、再表示しないよう設定できます
""",
        "order": 5,
        "category": "user"
    },
    {
        "id": "faq",
        "title": "FAQ",
        "content": """# よくある質問

## Q: チャットの応答が遅い場合は？
A: ネットワーク接続を確認してください。大きなファイルを添付している場合、処理に時間がかかることがあります。

## Q: 以前の会話を見るには？
A: セッション一覧から過去のセッションを選択できます。

## Q: ファイルがアップロードできない
A: ファイルサイズとファイル形式を確認してください。最大ファイルサイズは 10MB です。
""",
        "order": 6,
        "category": "user"
    },
    {
        "id": "admin_knowledge",
        "title": "管理者: ナレッジ管理",
        "content": """# ナレッジ管理（管理者専用）

## ナレッジドキュメント一覧
- システム内のすべてのドキュメントを確認できます
- ファイル名で検索可能
- 詳細情報（アップロード日時、ファイルサイズ等）を表示

## 権限
- この機能は管理者権限が必要です
""",
        "order": 7,
        "category": "admin"
    }
]

class HelpService:
    """
    ヘルプコンテンツ提供サービス。
    
    役割:
    - ヘルプセクションの一覧取得・個別取得を提供します。
    - P0 では静的データ（HELP_SECTIONS_DATA）をソースとします。
    
    P1 拡張:
    - help_sections テーブルから動的に読み込む
    - コンテンツの管理画面を追加
    - 多言語対応
    """
    
    def __init__(self):
        """
        HelpService の初期化。
        
        静的データを HelpSection Pydantic モデルに変換します。
        """
        self.sections = [HelpSection(**data) for data in HELP_SECTIONS_DATA]
    
    def list_sections(self, category: Literal["user", "admin", "all"] = "user") -> list[HelpSection]:
        """
        ヘルプセクションの一覧を取得します。
        
        Args:
            category: フィルタリングするカテゴリ
                - "user": ユーザー向けセクションのみ
                - "admin": 管理者向けセクションのみ
                - "all": すべてのセクション
        
        Returns:
            HelpSection のリスト（order 昇順でソート済み）
        """
        if category == "all":
            filtered = self.sections
        else:
            filtered = [s for s in self.sections if s.category == category]
        
        # order でソート
        return sorted(filtered, key=lambda x: x.order)
    
    def get_section(self, section_id: str) -> HelpSection | None:
        """
        指定された ID のヘルプセクションを取得します。
        
        Args:
            section_id: セクションID（例: "intro", "chat"）
        
        Returns:
            HelpSection または None（見つからない場合）
        """
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

def get_help_service() -> HelpService:
    """
    HelpService の依存性注入用ファクトリ。
    
    P0 では状態を持たないため、毎回新しいインスタンスを返します。
    """
    return HelpService()
