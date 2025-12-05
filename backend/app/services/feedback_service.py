from uuid import UUID
from typing import Optional, List

from app.repositories.feedback import FeedbackRepository
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate

class FeedbackService:
    """
    ユーザーからのフィードバックを管理するサービス。
    """
    def __init__(self, feedback_repo: FeedbackRepository):
        self.feedback_repo = feedback_repo

    async def create_feedback(
        self, user_id: UUID, tenant_id: UUID, feedback_in: FeedbackCreate
    ) -> Feedback:
        """
        新しいフィードバックを作成します。
        """
        feedback_data = feedback_in.model_dump()
        feedback_data["user_id"] = user_id
        feedback_data["tenant_id"] = tenant_id
        return await self.feedback_repo.create(feedback_data)

    async def get_feedback_by_session_id(self, session_id: UUID) -> List[Feedback]:
        """
        セッションIDに基づいてフィードバックを取得します。
        """
        return await self.feedback_repo.get_by_session_id(session_id)

    async def get_feedback_by_message_id(self, message_id: UUID) -> Optional[Feedback]:
        """
        メッセージIDに基づいて単一のフィードバックを取得します。
        """
        return await self.feedback_repo.get_by_message_id(message_id)
