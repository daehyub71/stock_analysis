"""
Email Service
- SMTP를 이용한 이메일 발송
- 점수 변화 알림 이메일 포맷
"""

import asyncio
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import settings


async def send_email(to: str, subject: str, html_body: str) -> bool:
    """
    이메일 발송 (aiosmtplib 사용)

    Returns: 성공 여부
    """
    if not settings.smtp_host or not settings.smtp_from_email:
        print("❌ SMTP settings not configured")
        return False

    try:
        import aiosmtplib

        message = MIMEMultipart("alternative")
        message["From"] = settings.smtp_from_email
        message["To"] = to
        message["Subject"] = subject

        html_part = MIMEText(html_body, "html", "utf-8")
        message.attach(html_part)

        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user or None,
            password=settings.smtp_password or None,
            start_tls=settings.smtp_port == 587,
            use_tls=settings.smtp_port == 465,
        )
        print(f"✅ Email sent to {to}")
        return True

    except ImportError:
        print("❌ aiosmtplib not installed. Run: pip install aiosmtplib")
        return False
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def format_score_change_email(changes: list[dict], threshold: float) -> str:
    """점수 변화 알림 HTML 이메일 생성"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    up_changes = [c for c in changes if c["change"] > 0]
    down_changes = [c for c in changes if c["change"] < 0]

    rows_html = ""
    for c in changes:
        color = "#16a34a" if c["change"] > 0 else "#dc2626"
        arrow = "▲" if c["change"] > 0 else "▼"
        rows_html += f"""
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 12px; font-weight: 600;">{c['stockName']}</td>
            <td style="padding: 12px; color: #6b7280;">{c['stockCode']}</td>
            <td style="padding: 12px; text-align: center;">{c['prevScore']}</td>
            <td style="padding: 12px; text-align: center; font-weight: 600;">{c['currScore']}</td>
            <td style="padding: 12px; text-align: center; color: {color}; font-weight: 700;">
                {arrow} {c['change']:+.1f}
            </td>
            <td style="padding: 12px; text-align: center;">{c['grade']}</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f9fafb; padding: 20px;">
        <div style="max-width: 640px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #3b82f6, #6366f1); padding: 24px; color: white;">
                <h1 style="margin: 0; font-size: 20px;">종목분석 점수 변화 알림</h1>
                <p style="margin: 8px 0 0; opacity: 0.9; font-size: 14px;">{now} 기준 | 임계값: {threshold}점 이상 변화</p>
            </div>

            <!-- Summary -->
            <div style="padding: 20px 24px; background: #f0f9ff; border-bottom: 1px solid #e5e7eb;">
                <div style="display: inline-block; margin-right: 24px;">
                    <span style="color: #6b7280; font-size: 13px;">변화 종목</span>
                    <div style="font-size: 24px; font-weight: 700; color: #1e40af;">{len(changes)}건</div>
                </div>
                <div style="display: inline-block; margin-right: 24px;">
                    <span style="color: #6b7280; font-size: 13px;">상승</span>
                    <div style="font-size: 18px; font-weight: 600; color: #16a34a;">{len(up_changes)}건</div>
                </div>
                <div style="display: inline-block;">
                    <span style="color: #6b7280; font-size: 13px;">하락</span>
                    <div style="font-size: 18px; font-weight: 600; color: #dc2626;">{len(down_changes)}건</div>
                </div>
            </div>

            <!-- Table -->
            <div style="padding: 0 24px 24px;">
                <table style="width: 100%; border-collapse: collapse; margin-top: 16px;">
                    <thead>
                        <tr style="background: #f9fafb; border-bottom: 2px solid #e5e7eb;">
                            <th style="padding: 10px 12px; text-align: left; color: #6b7280; font-size: 13px;">종목명</th>
                            <th style="padding: 10px 12px; text-align: left; color: #6b7280; font-size: 13px;">코드</th>
                            <th style="padding: 10px 12px; text-align: center; color: #6b7280; font-size: 13px;">전일</th>
                            <th style="padding: 10px 12px; text-align: center; color: #6b7280; font-size: 13px;">당일</th>
                            <th style="padding: 10px 12px; text-align: center; color: #6b7280; font-size: 13px;">변화</th>
                            <th style="padding: 10px 12px; text-align: center; color: #6b7280; font-size: 13px;">등급</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>

            <!-- Footer -->
            <div style="padding: 16px 24px; background: #f9fafb; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 12px; text-align: center;">
                Stock Analysis Dashboard - 자동 생성 알림
            </div>
        </div>
    </body>
    </html>
    """


async def send_score_alert_email(
    to_email: str,
    changes: list[dict],
    threshold: float = 5.0,
) -> bool:
    """점수 변화 알림 이메일 발송"""
    subject = f"[종목분석] 점수 변화 알림 - {len(changes)}개 종목 ({threshold}점 이상)"
    html_body = format_score_change_email(changes, threshold)
    return await send_email(to_email, subject, html_body)
