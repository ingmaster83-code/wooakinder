#!/usr/bin/env python3
"""
process_data.py - 유치원알리미 원본(header+body 배열)을 Jekyll 페이지 생성용 JSON으로 가공

입력: _rawdata/kinder_raw.json
출력: _rawdata/kinder.json (개별 페이지 생성용), search_index.json (검색/지역목록용)

사용법:
  python scripts/process_data.py
"""
import json, re, hashlib, sys
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
RAW = ROOT / "_rawdata" / "kinder_raw.json"
OUT = ROOT / "_rawdata" / "kinder.json"
SEARCH_INDEX_OUT = ROOT / "search_index.json"

SIDO_PREFIXES = [
    ("서울특별시", "서울"), ("부산광역시", "부산"), ("인천광역시", "인천"),
    ("대구광역시", "대구"), ("광주광역시", "광주"), ("대전광역시", "대전"),
    ("울산광역시", "울산"), ("세종특별자치시", "세종"),
    ("경기도", "경기"),
    ("강원특별자치도", "강원"), ("강원도", "강원"),
    ("충청북도", "충북"), ("충청남도", "충남"),
    ("전북특별자치도", "전북"), ("전라북도", "전북"), ("전라남도", "전남"),
    ("경상북도", "경북"), ("경상남도", "경남"),
    ("제주특별자치도", "제주"), ("제주도", "제주"),
]


def guess_sido_sggu(addr: str):
    text = addr or ""
    UNIFIED_PREFIX = "전남광주통합특별시"
    if text.startswith(UNIFIED_PREFIX):
        rest = text[len(UNIFIED_PREFIX):].strip()
        sggu = rest.split()[0] if rest else ""
        short = "광주" if sggu.endswith("구") else "전남"
        return short, sggu
    for prefix, short in SIDO_PREFIXES:
        if text.startswith(prefix):
            rest = text[len(prefix):].strip()
            sggu = rest.split()[0] if rest else ""
            return short, sggu
    return "", ""


def make_slug(name: str, addr: str) -> str:
    slug = re.sub(r"[^\w가-힣\s-]", "", name).strip()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    h = hashlib.md5(f"{name}|{addr}".encode("utf-8")).hexdigest()[:6]
    return f"{slug}-{h}" if slug else h


def fmt_time(raw: str) -> str:
    """'0900시0900분~1700시1700분' 같은 중복 표기를 '09:00~17:00'로 정규화."""
    if not raw:
        return ""
    m = re.findall(r"(\d{2})(\d{2})시", raw)
    if len(m) >= 2:
        (h1, mi1), (h2, mi2) = m[0], m[1]
        return f"{h1}:{mi1}~{h2}:{mi2}"
    return raw.strip()


def num(v):
    try:
        n = int(v)
        return n if n > 0 else 0
    except (TypeError, ValueError):
        return 0


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    header = raw["header"]
    idx = {name: i for i, name in enumerate(header)}
    rows = raw["body"]

    items = []
    seen_slugs = Counter()
    skipped = 0
    for r in rows:
        def g(field):
            i = idx.get(field)
            return r[i] if i is not None and i < len(r) else None

        # 필드명 주의: Jekyll 내장 Page.name과 충돌하므로 "kinderName" 사용
        kinder_name = str(g("유치원명") or "").strip()
        addr = str(g("주소") or "").strip()
        if not kinder_name or not addr:
            skipped += 1
            continue

        sido_nm, sggu_nm = guess_sido_sggu(addr)
        if not sido_nm or not sggu_nm:
            skipped += 1
            continue

        slug = make_slug(kinder_name, addr)
        seen_slugs[slug] += 1
        if seen_slugs[slug] > 1:
            slug = f"{slug}-{seen_slugs[slug]}"

        classes = {
            "age3": num(g("만3세학급수")), "age4": num(g("만4세학급수")),
            "age5": num(g("만5세학급수")), "mixed": num(g("혼합학급수")),
            "special": num(g("특수학급수")),
        }
        students = {
            "age3": num(g("만3세원아수")), "age4": num(g("만4세원아수")),
            "age5": num(g("만5세원아수")), "mixed": num(g("혼합원아수")),
            "special": num(g("특수원아수")),
        }
        total_students = sum(students.values())
        total_classes = sum(classes.values())

        lat = str(g("위도") or "").strip()
        lng = str(g("경도") or "").strip()

        items.append({
            "kinderName": kinder_name,
            "foundType": str(g("설립유형") or "").strip(),
            "principal": str(g("원장명") or "").strip(),
            "openDate": str(g("개원일") or "").strip(),
            "addr": addr,
            "tel": str(g("전화번호") or "").strip(),
            "homepage": str(g("홈페이지") or "").strip(),
            "operHours": fmt_time(str(g("운영시간") or "").strip()),
            "capacity": num(g("인가총정원수")),
            "totalStudents": total_students,
            "totalClasses": total_classes,
            "classes": classes,
            "students": students,
            "lat": lat,
            "lng": lng,
            "sido_nm": sido_nm,
            "sggu_nm": sggu_nm,
            "slug": slug,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    print(f"유치원 {len(items):,}개 저장 → {OUT}  (제외: {skipped}건)")

    sido_counts = Counter(i["sido_nm"] for i in items)
    print("\n시도별 수:")
    for s, cnt in sido_counts.most_common():
        print(f"  {s}: {cnt}개")

    index = [
        {
            "n": i["kinderName"], "slug": i["slug"],
            "doShort": i["sido_nm"], "sigungu": i["sggu_nm"],
            "addr": i["addr"], "found": i["foundType"],
        }
        for i in items
    ]
    SEARCH_INDEX_OUT.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    print(f"\n검색 인덱스 {len(index)}건 저장 → {SEARCH_INDEX_OUT}")


if __name__ == "__main__":
    main()
