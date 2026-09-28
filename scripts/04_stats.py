import sys
import pandas as pd
from pathlib import Path

# 콘솔 한글 깨짐 방지
sys.stdout.reconfigure(encoding="utf-8")

# 입력 위치 (읽기만 하고 수정하지 않음)
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "clean.csv"

# 정제된 데이터 읽기
df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")

# 기초 통계 계산
count = df["price"].count()  # 빈칸이 아닌 price 개수
min_price = df["price"].min()  # 최소값
max_price = df["price"].max()  # 최대값
mean_price = df["price"].mean()  # 평균
median_price = df["price"].median()  # 중앙값


# 특정 price 값을 가진 행들의 "name(region)" 목록 만들기 (같은 값이 여러 행이면 모두 표시)
def rows_with(value):
    # price가 value와 같은 행만 고름
    matched = df[df["price"] == value]
    # 각 행을 "name(region)" 형태로 이어 붙임
    return ", ".join(f"{r['name']}({r['region']})" for _, r in matched.iterrows())


# 마크다운 표 출력
print("| 항목 | 값 |")
print("|---|---|")
print(f"| 개수 | {count} |")  # 개수 줄
print(f"| 최소 | {min_price} — {rows_with(min_price)} |")  # 최소값과 해당 행
print(f"| 최대 | {max_price} — {rows_with(max_price)} |")  # 최대값과 해당 행
print(f"| 평균 | {mean_price:.2f} |")  # 평균 (소수 둘째 자리)
print(f"| 중앙값 | {median_price} |")  # 중앙값 (계산된 값 그대로)

# price 개수와 전체 행 수 비교
total_rows = len(df)  # clean.csv 전체 행 수
same = "같음" if count == total_rows else "다름"  # 같음/다름 판정
print()
print("| price 개수 | clean.csv 전체 행 수 | 판정 |")
print("|---:|---:|---|")
print(f"| {count} | {total_rows} | {same} |")
