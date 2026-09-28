import sys
import pandas as pd
from pathlib import Path

# 콘솔 한글 깨짐 방지
sys.stdout.reconfigure(encoding="utf-8")

# 입력/출력 위치
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "raw.csv"
OUTPUT_PATH = BASE_DIR / "data" / "clean.csv"

# 원본 읽기 (raw.csv는 읽기만 하고 수정하지 않음)
raw = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")

# 정제용 복사본 (원본 열은 그대로 유지)
df = raw.copy()

# 규칙 1: price_raw에서 쉼표와 '원'을 떼고 정수로 변환
price_text = df["price_raw"].astype("string").str.replace(",", "", regex=False).str.replace("원", "", regex=False).str.strip()
# 숫자로 바꿀 수 없는 값은 NaN으로 둠 (0이나 평균으로 채우지 않음)
df["price"] = pd.to_numeric(price_text, errors="coerce").astype("Int64")

# 규칙 2: difficulty_raw는 숫자 값 그대로 사용 (반올림하지 않음)
df["difficulty"] = pd.to_numeric(df["difficulty_raw"], errors="coerce")

# 규칙 3: region_raw는 앞뒤 공백만 정리
df["region"] = df["region_raw"].astype("string").str.strip()


# 한 행의 제거 사유 만들기
def drop_reason(row):
    # 사유를 모을 목록
    reasons = []
    # price_raw 빈칸 여부
    if pd.isna(row["price_raw"]) or str(row["price_raw"]).strip() == "":
        reasons.append("price_raw 빈칸")
    # price_raw는 있는데 숫자로 못 바꾼 경우
    elif pd.isna(row["price"]):
        reasons.append(f"price_raw 숫자 변환 불가({row['price_raw']})")
    # difficulty_raw 빈칸 여부
    if pd.isna(row["difficulty_raw"]) or str(row["difficulty_raw"]).strip() == "":
        reasons.append("difficulty_raw 빈칸")
    # difficulty_raw는 있는데 숫자로 못 바꾼 경우
    elif pd.isna(row["difficulty"]):
        reasons.append(f"difficulty_raw 숫자 변환 불가({row['difficulty_raw']})")
    # 사유들을 하나의 문자열로 합침
    return ", ".join(reasons)


# 규칙 4: 행마다 제거 사유 계산
df["drop_reason"] = df.apply(drop_reason, axis=1)
# 사유가 있는 행이 제거 대상
bad_mask = df["drop_reason"] != ""

# 제거 대상 행과 사유를 먼저 출력
print("=== 제거 대상 (빈칸/변환 불가) ===")
print(f"{bad_mask.sum()}행")
# 제거 대상 행을 하나씩 출력
for idx, row in df[bad_mask].iterrows():
    print(f"- 행 {idx}: {row['name']} / {row['region']} / price={row['price']} / difficulty={row['difficulty']} / 사유: {row['drop_reason']}")

# 제거 대상 행 빼기
clean = df[~bad_mask].copy()

# 규칙 5: detail_url 중복은 처음 한 행만 남김
dup_mask = clean.duplicated(subset="detail_url", keep="first")
# 중복으로 제거되는 행 출력
print("\n=== 제거 대상 (detail_url 중복) ===")
print(f"{dup_mask.sum()}행")
# 중복 행을 하나씩 출력
for idx, row in clean[dup_mask].iterrows():
    print(f"- 행 {idx}: {row['name']} / 사유: detail_url 중복 ({row['detail_url']})")
# 중복 행 빼기
clean = clean[~dup_mask]

# 사유 열은 저장하지 않음
clean = clean.drop(columns="drop_reason")

# 저장할 열 순서: 원본 열 뒤에 새 열 추가
clean = clean[list(raw.columns) + ["region", "price", "difficulty"]]

# 처리 전후 비교 1: 행 수
print("\n=== 1. 행 수 ===")
print(pd.DataFrame({"처리 전": [len(raw)], "처리 후": [len(clean)]}, index=["행 수"]).to_string())

# 처리 전후 비교 2: 데이터형
print("\n=== 2. 데이터형 ===")
print(pd.DataFrame({"처리 전": raw.dtypes.astype(str), "처리 후": clean.dtypes.astype(str)}).reindex(clean.columns).fillna("-").to_string())

# 처리 전후 비교 3: 열별 빈칸 수
print("\n=== 3. 열별 빈칸 수 ===")
# 처리 전에 없던 열은 '-'로 표시
before_na = [int(raw[c].isna().sum()) if c in raw.columns else "-" for c in clean.columns]
print(pd.DataFrame({"처리 전": before_na, "처리 후": clean.isna().sum().tolist()}, index=clean.columns).to_string())

# 처리 전후 비교 4: detail_url 중복 수
print("\n=== 4. detail_url 중복 수 ===")
print(pd.DataFrame({"처리 전": [raw["detail_url"].duplicated().sum()], "처리 후": [clean["detail_url"].duplicated().sum()]}, index=["중복 수"]).to_string())

# clean.csv로 저장
clean.to_csv(OUTPUT_PATH, encoding="utf-8-sig", index=False)
print(f"\n저장 완료: {OUTPUT_PATH} ({len(clean)}행)")
