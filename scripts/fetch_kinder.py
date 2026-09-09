#!/usr/bin/env python3
"""
fetch_kinder.py - 유치원알리미(교육부) 공시자료 다운로드
https://e-childschoolinfo.moe.go.kr/openData.do 의 "공시자료 다운로드" 폼이 호출하는
비로그인 GET 엔드포인트를 그대로 사용 (SNS 인증 필요한 건 별도 OpenAPI 쪽이고,
이 다운로드 경로는 인증 없이 바로 받아짐 — 2026-09-09 확인).

공시항목: 05=일반 현황(유치원명·주소·전화번호·운영시간·학급수·정원·위경도 등)
공시차수는 반기별로 갱신되므로(2026년 1차/2차...) 재수집 시 TIMING_CODE 확인 필요 —
https://e-childschoolinfo.moe.go.kr/openData.do 에서 최신 공시차수를 select로 확인하고
브라우저 네트워크탭에서 timingListCode 값을 다시 캡처할 것.

출력: _rawdata/kinder_raw.json (원본 header+body 그대로)

사용법:
  python scripts/fetch_kinder.py
"""
import sys, json
from pathlib import Path
import requests

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
OUT = ROOT / "_rawdata" / "kinder_raw.json"

TIMING_CODE = "20261"  # 2026년 1차
GONGSI_CODE = "05"      # 일반 현황

URL = "https://e-childschoolinfo.moe.go.kr/download/getTotalOpenData.do"
PARAMS = {
    "combineSidoName": "전체 시/도",
    "combineSidoCode": "99",
    "timingListCode": TIMING_CODE,
    "gongsiListCode": GONGSI_CODE,
    "safetyListCode": "",
    "ExcelCsv": "3",  # 1=Excel, 2=CSV, 3=JSON
}


def main():
    print(f"=== 유치원알리미 일반현황({TIMING_CODE}) 다운로드 시작 ===")
    resp = requests.get(URL, params=PARAMS, timeout=90, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    if len(resp.content) < 100_000:
        raise SystemExit(
            f"다운로드 실패로 추정 — 응답 크기가 너무 작음 ({len(resp.content)} bytes). "
            "timingListCode가 만료됐을 수 있음 — openData.do에서 최신 공시차수로 다시 캡처할 것."
        )
    data = resp.json()
    header = data.get("header", [])
    body = data.get("body", [])
    if not body:
        raise SystemExit("body가 비어있습니다 — 응답 구조가 바뀌었을 수 있음.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"header": header, "body": body}, ensure_ascii=False), encoding="utf-8")
    print(f"저장 완료: {OUT} ({len(body):,}건, 필드 {len(header)}개)")


if __name__ == "__main__":
    main()
