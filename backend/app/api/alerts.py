"""
Alerts API
- 점수 변화 감지
- 이메일 알림 설정 및 발송
"""

from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, EmailStr

from app.db import supabase_db

router = APIRouter()


class EmailSettings(BaseModel):
    """이메일 알림 설정"""
    email: EmailStr
    enabled: bool = True
    threshold: float = 5.0


class SendAlertRequest(BaseModel):
    """알림 이메일 발송 요청"""
    email: EmailStr
    threshold: float = 5.0


@router.get("/score-changes")
async def get_score_changes(
    threshold: float = Query(5.0, ge=1.0, le=50.0, description="변화 임계값"),
):
    """
    점수 변화 감지

    전일 대비 임계값 이상 변화한 종목 조회
    """
    try:
        changes = supabase_db.get_score_changes(threshold)
        return {
            "threshold": threshold,
            "count": len(changes),
            "changes": changes,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-alert-email")
async def send_alert_email(request: SendAlertRequest):
    """
    알림 이메일 발송

    점수 변화가 임계값 이상인 종목에 대해 이메일 알림 발송
    """
    try:
        from app.services.email_service import send_score_alert_email

        changes = supabase_db.get_score_changes(request.threshold)

        if not changes:
            return {
                "sent": False,
                "message": "변화가 임계값 이상인 종목이 없습니다.",
                "threshold": request.threshold,
            }

        success = await send_score_alert_email(
            to_email=request.email,
            changes=changes,
            threshold=request.threshold,
        )

        return {
            "sent": success,
            "message": "이메일이 발송되었습니다." if success else "이메일 발송에 실패했습니다.",
            "email": request.email,
            "changesCount": len(changes),
        }
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="이메일 서비스를 사용할 수 없습니다. SMTP 설정을 확인해주세요."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
