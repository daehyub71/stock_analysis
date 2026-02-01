"""
VIP 한국형가치투자 종목 시드 스크립트
- 44개 종목을 stocks_anal 테이블에 입력
- 종목코드 하드코딩 (2025.12.31 기준)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import supabase_db

# VIP 한국형가치투자 종목 리스트 (2025.12.31 기준) - 종목코드 포함
VIP_STOCKS = [
    {"code": "138040", "name": "메리츠금융지주", "sector": "금융", "market": "KOSPI"},
    {"code": "005930", "name": "삼성전자", "sector": "정보기술", "market": "KOSPI"},
    {"code": "383220", "name": "F&F", "sector": "자유소비재", "market": "KOSPI"},
    {"code": "259960", "name": "크래프톤", "sector": "커뮤니케이션서비스", "market": "KOSPI"},
    {"code": "271560", "name": "오리온", "sector": "필수소비재", "market": "KOSPI"},
    {"code": "290650", "name": "엘앤씨바이오", "sector": "헬스케어", "market": "KOSDAQ"},
    {"code": "032350", "name": "롯데관광개발", "sector": "자유소비재", "market": "KOSPI"},
    {"code": "086790", "name": "하나금융지주", "sector": "금융", "market": "KOSPI"},
    {"code": "005385", "name": "현대차우", "sector": "자유소비재", "market": "KOSPI"},
    {"code": "041510", "name": "에스엠", "sector": "커뮤니케이션서비스", "market": "KOSDAQ"},
    {"code": "102710", "name": "이엔에프테크놀로지", "sector": "소재", "market": "KOSDAQ"},
    {"code": "012630", "name": "HDC", "sector": "소재", "market": "KOSPI"},
    {"code": "089030", "name": "테크윙", "sector": "정보기술", "market": "KOSDAQ"},
    {"code": "483650", "name": "달바글로벌", "sector": "소비재", "market": "KOSDAQ"},
    {"code": "251970", "name": "펌텍코리아", "sector": "소재", "market": "KOSDAQ"},
    {"code": "200670", "name": "휴메딕스", "sector": "헬스케어", "market": "KOSDAQ"},
    {"code": "005300", "name": "롯데칠성음료", "sector": "필수소비재", "market": "KOSPI"},
    {"code": "089860", "name": "롯데렌탈", "sector": "산업재", "market": "KOSPI"},
    {"code": "101160", "name": "월덱스", "sector": "정보기술", "market": "KOSDAQ"},
    {"code": "348210", "name": "넥스틴", "sector": "정보기술", "market": "KOSDAQ"},
    {"code": "053610", "name": "프로텍", "sector": "정보기술", "market": "KOSDAQ"},
    {"code": "280360", "name": "롯데웰푸드", "sector": "필수소비재", "market": "KOSPI"},
    {"code": "086390", "name": "유니테스트", "sector": "정보기술", "market": "KOSDAQ"},
    {"code": "002030", "name": "아세아", "sector": "소재", "market": "KOSPI"},
    {"code": "453340", "name": "현대그린푸드", "sector": "필수소비재", "market": "KOSDAQ"},
    {"code": "005810", "name": "풍산홀딩스", "sector": "소재", "market": "KOSPI"},
    {"code": "104830", "name": "원익머트리얼즈", "sector": "소재", "market": "KOSDAQ"},
    {"code": "248070", "name": "솔루엠", "sector": "정보기술", "market": "KOSDAQ"},
    {"code": "051500", "name": "CJ프레시웨이", "sector": "필수소비재", "market": "KOSPI"},
    {"code": "060980", "name": "HL홀딩스", "sector": "자유소비재", "market": "KOSPI"},
    {"code": "353200", "name": "대덕전자", "sector": "정보기술", "market": "KOSPI"},
    {"code": "035150", "name": "백산", "sector": "자유소비재", "market": "KOSPI"},
    {"code": "005720", "name": "넥센", "sector": "자유소비재", "market": "KOSPI"},
    {"code": "204620", "name": "글로벌텍스프리", "sector": "산업재", "market": "KOSDAQ"},
    {"code": "043370", "name": "피에이치에이", "sector": "자유소비재", "market": "KOSDAQ"},
    {"code": "160980", "name": "싸이맥스", "sector": "정보기술", "market": "KOSDAQ"},
    {"code": "272550", "name": "삼양패키징", "sector": "소재", "market": "KOSPI"},
    {"code": "240550", "name": "동방메디컬", "sector": "헬스케어", "market": "KOSDAQ"},
    {"code": "104460", "name": "디와이피엔에프", "sector": "산업재", "market": "KOSDAQ"},
    {"code": "210540", "name": "디와이파워", "sector": "산업재", "market": "KOSDAQ"},
    {"code": "204610", "name": "티쓰리", "sector": "커뮤니케이션서비스", "market": "KOSDAQ"},
    {"code": "460870", "name": "에스엠씨지", "sector": "미디어", "market": "KOSDAQ"},
]


def seed_stocks():
    """VIP 종목 데이터 시드"""
    print("\n" + "="*60)
    print("VIP 한국형가치투자 종목 시드 시작")
    print("="*60 + "\n")

    # 종목 데이터 준비
    stocks_to_insert = []
    for stock in VIP_STOCKS:
        stocks_to_insert.append({
            "code": stock["code"],
            "name": stock["name"],
            "sector": stock["sector"],
            "market": stock["market"],
            "is_active": True,
        })
        print(f"✅ {stock['name']} ({stock['code']}) - {stock['market']}")

    print(f"\n📊 총 {len(stocks_to_insert)}개 종목 준비 완료")

    # Supabase에 입력
    print("\n📤 Supabase stocks_anal 테이블에 입력 중...")
    try:
        count = supabase_db.upsert_stocks_bulk(stocks_to_insert)
        print(f"✅ {count}개 종목 입력 완료!")
        return True
    except Exception as e:
        print(f"❌ 입력 실패: {e}")
        return False


def verify_stocks():
    """입력된 종목 확인"""
    print("\n📋 입력된 종목 확인...")
    try:
        stocks = supabase_db.get_all_stocks()
        print(f"✅ stocks_anal 테이블: {len(stocks)}개 종목")

        if stocks:
            print("\n전체 종목 목록:")
            for i, stock in enumerate(stocks, 1):
                print(f"  {i:2d}. {stock.get('name')} ({stock.get('code')}) - {stock.get('sector')}")

        return len(stocks)
    except Exception as e:
        print(f"❌ 조회 실패: {e}")
        return 0


if __name__ == "__main__":
    print("🚀 VIP 종목 시드 스크립트 시작\n")

    # 시드 실행
    if seed_stocks():
        # 확인
        count = verify_stocks()
        print(f"\n{'='*60}")
        print(f"✅ 시드 완료! 총 {count}개 종목이 stocks_anal 테이블에 입력됨")
        print("="*60)
    else:
        print("\n❌ 시드 실패")
