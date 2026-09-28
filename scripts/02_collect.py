import re
import pandas as pd
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

# 수집할 공개 목록 페이지
URL = "https://bangdojang.com/browse?done=not_done&view=list"

# 저장 위치
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "data" / "raw.csv"

# 공개 목록 페이지 1회 요청
response = requests.get(URL, timeout=10)

print("응답 상태:", response.status_code)

# 응답 실패 시 저장하지 않고 종료
if response.status_code != 200:
    print("수집 중단")
    raise SystemExit

html = response.text

# 목록 HTML 안의 테마 데이터 추출
pattern = re.compile(
    r'\{\\"id\\":\\"(?P<id>[^"]+)\\"'
    r',\\"name\\":\\"(?P<name>[^"]*)\\"'
    r',\\"store\\":\\"[^"]*\\"'
    r',\\"region\\":\\"(?P<region>[^"]*)\\"'
    r'.*?'
    r'\\"price\\":(?P<price>null|\d+)'
    r'.*?'
    r'\\"commDifficulty\\":(?P<difficulty>null|[\d.]+)',
    re.DOTALL
)

matches = list(pattern.finditer(html))

rows = []

# 한국 시간으로 수집 시각 기록
scraped_at = datetime.now(
    ZoneInfo("Asia/Seoul")
).strftime("%Y-%m-%d %H:%M:%S")

for match in matches:
    item = match.groupdict()

    # 화면에 보이는 가격 형식으로 저장
    price_raw = (
        f"{int(item['price']):,}원"
        if item["price"] != "null"
        else ""
    )

    # 상세 화면에 보이는 체감난이도처럼 소수 첫째 자리로 저장
    difficulty_raw = (
        f"{float(item['difficulty']):.1f}"
        if item["difficulty"] != "null"
        else ""
    )

    # 테마 ID를 이용해 상세 페이지 주소 생성
    detail_url = f"https://bangdojang.com/theme/{item['id']}"

    rows.append({
        "name": item["name"],
        "region_raw": item["region"],
        "price_raw": price_raw,
        "difficulty_raw": difficulty_raw,
        "detail_url": detail_url,
        "scraped_at": scraped_at
    })

df = pd.DataFrame(rows)

print("첫 목록 요청:", len(df), "행")
print("총 수집 행 수:", len(df))

# 0행이면 CSV를 만들지 않음
if len(df) == 0:
    print("0행이라 raw.csv를 저장하지 않았습니다.")
    raise SystemExit

# 현재 사이트는 추가 목록이 무한스크롤로 로드됨
# robots.txt에서 /api/가 제한되어 있어 추가 API 요청은 하지 않음
print("수집 제한: 추가 목록은 무한스크롤 방식이며 /api/ 경로는 요청하지 않음")

# 원본 데이터 저장
df.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)

print("data/raw.csv 저장 완료")
print()
print("앞 3행:")
print(df.head(3))