import pytest
from app.services.help import HelpService
from app.schemas.help import HelpSection

class TestHelpService:
    """
    HelpService のユニットテスト。
    
    テスト観点:
    - 一覧取得（全て / category filtering）
    - 個別セクション取得（存在する / 存在しない）
    """
    
    def test_list_sections_user_category(self):
        """
        category="user" で一般ユーザー向けセクションのみ取得できることを確認。
        """
        service = HelpService()
        
        sections = service.list_sections(category="user")
        
        assert len(sections) > 0
        assert all(s.category == "user" for s in sections)
        # order でソートされているか確認
        orders = [s.order for s in sections]
        assert orders == sorted(orders)
    
    def test_list_sections_admin_category(self):
        """
        category="admin" で管理者向けセクションのみ取得できることを確認。
        """
        service = HelpService()
        
        sections = service.list_sections(category="admin")
        
        assert len(sections) > 0
        assert all(s.category == "admin" for s in sections)
    
    def test_list_sections_all_category(self):
        """
        category="all" で全セクション取得できることを確認。
        """
        service = HelpService()
        
        all_sections = service.list_sections(category="all")
        user_sections = service.list_sections(category="user")
        admin_sections = service.list_sections(category="admin")
        
        assert len(all_sections) == len(user_sections) + len(admin_sections)
    
    def test_get_section_existing(self):
        """
        存在するセクションIDで取得できることを確認。
        """
        service = HelpService()
        
        section = service.get_section("intro")
        
        assert section is not None
        assert section.id == "intro"
        assert section.title == "はじめに"
        assert len(section.content) > 0
    
    def test_get_section_not_found(self):
        """
        存在しないセクションIDで None が返ることを確認。
        """
        service = HelpService()
        
        section = service.get_section("nonexistent_section_id")
        
        assert section is None
    
    def test_all_sections_have_required_fields(self):
        """
        全セクションが必須フィールドを持つことを確認。
        """
        service = HelpService()
        
        all_sections = service.list_sections(category="all")
        
        for section in all_sections:
            assert section.id
            assert section.title
            assert section.content
            assert isinstance(section.order, int)
            assert section.category in ["user", "admin"]
