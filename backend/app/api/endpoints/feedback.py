from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List, Optional
from uuid import UUID

from app.schemas.auth import AuthenticatedUser
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.dependencies import get_current_user
from app.services.feedback_service import FeedbackService
from app.dependencies import get_feedback_service

router = APIRouter()

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED, summary="ユーザーフィードバックを送信")
async def submit_feedback(
    feedback_in: FeedbackCreate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    feedback_service: Annotated[FeedbackService, Depends(get_feedback_service)]
):
    """
    ユーザーからのフィードバック（評価とコメント）を送信します。
    """
    new_feedback = await feedback_service.create_feedback(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        feedback_in=feedback_in
    )
    return new_feedback

@router.get("/feedback/{session_id}", response_model=List[FeedbackResponse], summary="セッションIDでフィードバックを取得")
async def get_feedback_for_session(
    session_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    feedback_service: Annotated[FeedbackService, Depends(get_feedback_service)]
):
    """
    特定のセッションIDに紐づくフィードバックを取得します。
    """
    feedback_list = await feedback_service.get_feedback_by_session_id(session_id)
    # ユーザーが自身のテナントのフィードバックのみ見れるようにフィルタリング
    filtered_feedback = [
        f for f in feedback_list if f.tenant_id == current_user.tenant_id and f.user_id == current_user.id
    ]
    return [FeedbackResponse.model_validate(f) for f in filtered_feedback]

@router.get("/feedback/message/{message_id}", response_model=Optional[FeedbackResponse], summary="メッセージIDでフィードバックを取得")
async def get_feedback_for_message(
    message_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    feedback_service: Annotated[FeedbackService, Depends(get_feedback_service)]
):
    """
    特定のメッセージIDに紐づくフィードバックを取得します。
    """
    feedback = await feedback_service.get_feedback_by_message_id(message_id)
    if not feedback or feedback.tenant_id != current_user.tenant_id or feedback.user_id != current_user.id:
        return None # 権限なしまたは見つからない場合はNoneを返す
    return FeedbackResponse.model_validate(feedback)
