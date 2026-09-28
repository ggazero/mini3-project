import sys
import json
import pandas as pd
from pathlib import Path

# 콘솔 한글 깨짐 방지
sys.stdout.reconfigure(encoding="utf-8")

# 입력/출력 위치 (clean.csv는 읽기만 함)
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "clean.csv"
OUTPUT_PATH = BASE_DIR / "data" / "data.json"

# 내보낼 열
COLUMNS = ["name", "price", "difficulty", "detail_url"]

# 정제된 데이터 읽기
df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")
# 필요한 4개 열만 고름
out = df[COLUMNS]

# 한 행을 한 객체로 만든 목록 (price는 int, difficulty는 float 숫자형으로 변환)
records = [
    {
        "name": str(r["name"]),  # 이름 (문자열)
        "price": int(r["price"]),  # 가격 (정수)
        "difficulty": float(r["difficulty"]),  # 체감난이도 (실수, 반올림 안 함)
        "detail_url": str(r["detail_url"]),  # 상세 주소 (문자열)
    }
    for _, r in out.iterrows()  # 모든 행을 순서대로 변환
]

# UTF-8로 저장 (한글 그대로, 들여쓰기 2칸)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

# 저장한 파일을 다시 읽기
with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
    loaded = json.load(f)

# 1·2. JSON 항목 수와 clean.csv 행 수 비교
same_count = "같음" if len(loaded) == len(df) else "다름"
print("| JSON 항목 수 | clean.csv 전체 행 수 | 판정 |")
print("|---:|---:|---|")
print(f"| {len(loaded)} | {len(df)} | {same_count} |")

# 첫 항목과 clean.csv 첫 줄 비교
first_json = loaded[0]  # data.json 첫 항목
first_csv = df.iloc[0]  # clean.csv 첫 줄
print()
print("| 열 | data.json 첫 항목 | clean.csv 첫 줄 | 판정 |")
print("|---|---|---|---|")
# 4개 열을 하나씩 비교
for col in COLUMNS:
    # JSON 값 (자료형 이름도 함께 표시)
    j = first_json[col]
    # CSV 값
    c = first_csv[col]
    # 값이 같은지 판정
    same = "같음" if j == c else "다름"
    print(f"| {col} | {j!r} ({type(j).__name__}) | {c!r} | {same} |")

# 저장 위치 출력
print(f"\n저장 완료: {OUTPUT_PATH}")
