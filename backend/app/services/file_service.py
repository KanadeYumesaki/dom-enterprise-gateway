import os
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import UUID
import mimetypes

from fastapi import UploadFile, HTTPException, status
from langchain_core.documents import Document

from app.core.config import settings
from app.models.knowledge import KnowledgeDocument # KnowledgeDocument modelをインポート

# テキスト抽出のモック/プレースホルダー
async def extract_text_from_pdf(file_path: Path) -> str:
    # PDF抽出ライブラリ (例: pypdf, pdfminer.six) を使用する
    # PoCではダミーを返す
    return f"Extracted text from PDF: {file_path.name}. (Placeholder content)"

async def extract_text_from_docx(file_path: Path) -> str:
    # DOCX抽出ライブラリ (例: python-docx) を使用する
    # PoCではダミーを返す
    return f"Extracted text from DOCX: {file_path.name}. (Placeholder content)"

async def extract_text_from_xlsx(file_path: Path) -> str:
    # XLSX抽出ライブラリ (例: openpyxl) を使用する
    # PoCではダミーを返す
    return f"Extracted text from XLSX: {file_path.name}. (Placeholder content)"

async def extract_text_from_pptx(file_path: Path) -> str:
    # PPTX抽出ライブラリ (例: python-pptx) を使用する
    # PoCではダミーを返す
    return f"Extracted text from PPTX: {file_path.name}. (Placeholder content)"


class FileService:
    """
    ファイル操作（保存、テキスト抽出、バリデーション）を管理するサービス。
    """
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIRECTORY)
        self.upload_dir.mkdir(parents=True, exist_ok=True) # ディレクトリが存在しない場合は作成

    async def _get_file_extension(self, filename: str) -> Optional[str]:
        return Path(filename).suffix.lstrip('.').lower()

    async def validate_file(self, file: UploadFile):
        """
        ファイルのサイズと拡張子をバリデーションします。
        """
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0) # ファイルポインタを先頭に戻す

        if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds the limit of {settings.MAX_FILE_SIZE_MB}MB."
            )
        
        file_extension = await self._get_file_extension(file.filename)
        if file_extension not in settings.ALLOWED_FILE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file_extension}' not allowed. Allowed types are: {', '.join(settings.ALLOWED_FILE_EXTENSIONS)}"
            )
        
        return file_size, file_extension

    async def save_file(self, file: UploadFile, tenant_id: UUID, user_id: UUID) -> KnowledgeDocument:
        """
        アップロードされたファイルを保存し、KnowledgeDocumentメタデータを返します。
        """
        file_size, file_extension = await self.validate_file(file)

        # テナントとユーザーごとにサブディレクトリを作成し、ファイル名をUUIDで保存
        tenant_dir = self.upload_dir / str(tenant_id)
        tenant_dir.mkdir(parents=True, exist_ok=True)
        
        unique_filename = f"{uuid4()}.{file_extension}"
        file_path = tenant_dir / unique_filename

        try:
            with open(file_path, "wb") as buffer:
                while chunk := await file.read(1024 * 1024): # 1MBずつ読み込み
                    buffer.write(chunk)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")

        mime_type = mimetypes.guess_type(file.filename)[0]

        # KnowledgeDocumentオブジェクトを生成 (まだDBには保存しない)
        knowledge_doc = KnowledgeDocument(
            id=uuid4(),
            tenant_id=tenant_id,
            file_name=file.filename,
            file_path=str(file_path),
            file_type=mime_type if mime_type else f"application/{file_extension}",
            file_size=str(file_size), # バイト数を文字列として保存
            uploaded_by_user_id=user_id,
            is_active=True
        )
        return knowledge_doc

    async def extract_text_from_knowledge_document(self, knowledge_doc: KnowledgeDocument) -> str:
        """
        KnowledgeDocumentからテキストを抽出します。
        """
        file_path = Path(knowledge_doc.file_path)
        file_extension = await self._get_file_extension(file_path.name)

        if file_extension == "pdf":
            return await extract_text_from_pdf(file_path)
        elif file_extension == "docx":
            return await extract_text_from_docx(file_path)
        elif file_extension == "xlsx":
            return await extract_text_from_xlsx(file_path)
        elif file_extension == "pptx":
            return await extract_text_from_pptx(file_path)
        elif file_extension in ["txt", "md"]:
            return file_path.read_text(encoding='utf-8')
        else:
            return "" # 未対応のファイル形式

    async def delete_file_from_storage(self, file_path: Path):
        """
        指定されたパスのファイルをストレージから削除します。
        """
        if file_path.exists() and file_path.is_file():
            os.remove(file_path)
