import re
import pandas as pd
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

URL = "https://bangdojang.com/browse?done=not_done&view=list"

response = requests.get(URL, timeout=10)

print("status:", response.status_code)

if response.status_code != 200:
    print("수집 중단")
    raise SystemExit

html = response.text

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

scraped_at = datetime.now(
    ZoneInfo("Asia/Seoul")
).strftime("%Y-%m-%d %H:%M:%S")

for match in matches:
    item = match.groupdict()

    price_raw = (
        f"{int(item['price']):,}원"
        if item["price"] != "null"
        else ""
    )

    difficulty_raw = (
    f"{float(item['difficulty']):.1f}"
    if item["difficulty"] != "null"
    else ""
)

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

print("수집 행 수:", len(df))
print(df.head())

if len(df) > 0:
    df.to_csv(
        "data/raw_p1.csv",
        index=False,
        encoding="utf-8-sig"
    )
    print("data/raw_p1.csv 저장 완료")
else:
    print("0행이라 CSV를 저장하지 않았습니다.")