from typing import Literal
from pydantic import BaseModel

class HelpSection(BaseModel):
    """
    ヘルプセクションのスキーマ。
    
    役割:
    - ヘルプコンテンツの1セクション分を表します。
    - GET /api/help/content のレスポンスで使用します。
    
    フィールド説明:
    - id: セクション識別子（例: "intro", "chat", "files"）
    - title: セクションタイトル（例: "はじめに"、"チャット機能"）
    - content: Markdown形式のヘルプ本文
    - order: 表示順序（昇順ソート用）
    - category: "user" (一般ユーザー向け) または "admin" (管理者向け)
    
    データソース:
    - P0 では help_content_outline.md を手動でPython dictに変換し、
      HelpService から返却します。
    - P1 では help_sections テーブルから読み込む拡張も可能です。
    """
    id: str  # セクションID（例: "intro", "chat", "files"）
    title: str
    content: str  # Markdown形式
    order: int  # 表示順序
    category: Literal["user", "admin"] = "user"  # P1 で admin 用ヘルプ追加を想定
