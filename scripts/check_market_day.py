#!/usr/bin/env python3
"""
KRX 거래일 체크 스크립트
- 주말 제외
- 공휴일 제외 (pykrx 활용)
"""

import os
import sys
from datetime import datetime, timedelta

def check_trading_day(target_date: str = None) -> bool:
    """거래일 여부 확인"""
    try:
        from pykrx import stock

        if target_date:
            date = datetime.strptime(target_date, "%Y-%m-%d")
        else:
            # KST 기준 오늘
            date = datetime.utcnow() + timedelta(hours=9)

        date_str = date.strftime("%Y%m%d")

        # 해당 월의 거래일 목록 조회
        year_month = date.strftime("%Y%m")
        trading_days = stock.get_previous_business_days(
            fromdate=f"{year_month}01",
            todate=f"{year_month}31"
        )

        # date_str이 거래일 목록에 있는지 확인
        is_trading = date_str in [d.strftime("%Y%m%d") for d in trading_days]

        return is_trading

    except Exception as e:
        print(f"Error checking trading day: {e}", file=sys.stderr)
        # 에러 시 주말만 체크
        if target_date:
            date = datetime.strptime(target_date, "%Y-%m-%d")
        else:
            date = datetime.utcnow() + timedelta(hours=9)

        # 주말이면 거래일 아님
        return date.weekday() < 5  # 0-4: 월-금


def main():
    target_date = os.environ.get("TARGET_DATE", "").strip() or None

    is_trading = check_trading_day(target_date)

    # GitHub Actions output
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"is_trading_day={'true' if is_trading else 'false'}\n")

    print(f"Target Date: {target_date or 'today'}")
    print(f"Is Trading Day: {is_trading}")

    # 거래일이 아니면 종료 코드 0 (성공이지만 스킵)
    sys.exit(0)


if __name__ == "__main__":
    main()
