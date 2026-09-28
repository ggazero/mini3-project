import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # 화면 없이 파일로만 저장하는 백엔드
import matplotlib.pyplot as plt
from pathlib import Path

# 콘솔 한글 깨짐 방지
sys.stdout.reconfigure(encoding="utf-8")

# 입력/출력 위치 (data 폴더는 읽기만 함)
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "clean.csv"
OUTPUT_PATH = BASE_DIR / "charts" / "hist.png"

# 구간 경계 (왼쪽 포함, 오른쪽 미포함, 마지막 구간만 35000 포함)
BINS = [25000, 27000, 29000, 31000, 33000, 35000]

# 정제된 데이터 읽기
df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")
# 가격 열만 꺼냄
prices = df["price"]

# 구간별 개수 계산 (np.histogram은 마지막 구간만 오른쪽 끝을 포함함)
counts, edges = np.histogram(prices, bins=BINS)

# 그림 준비
fig, ax = plt.subplots(figsize=(8, 5))
# 같은 구간으로 히스토그램 그리기
_, _, patches = ax.hist(prices, bins=BINS, edgecolor="black")
# 막대 위에 개수 표시
ax.bar_label(patches, labels=[str(c) for c in counts], padding=3)
# x축 눈금을 구간 경계값으로 설정
ax.set_xticks(BINS)
# x축 눈금 글자를 천 단위 쉼표로 표시
ax.set_xticklabels([f"{b:,}" for b in BINS])
# x축 이름
ax.set_xlabel("Price (KRW)")
# y축 이름
ax.set_ylabel("Number of themes")
# 제목 (n은 실제 행 수)
ax.set_title(f"Bangdojang Price Distribution (n = {len(df)})")
# 막대 위 숫자가 잘리지 않게 y축 위쪽 여유
ax.set_ylim(0, counts.max() + 2)
# 여백 정리
fig.tight_layout()
# 파일로 저장 (plt.show() 사용 안 함)
fig.savefig(OUTPUT_PATH, dpi=150)
# 그림 닫기
plt.close(fig)

# 구간 표기 목록
labels = []
# 경계를 두 개씩 묶어 구간 이름 만들기
for i in range(len(BINS) - 1):
    # 마지막 구간만 '이하'
    end_word = "이하" if i == len(BINS) - 2 else "미만"
    # 구간 이름 추가
    labels.append(f"{BINS[i]:,} 이상 {BINS[i + 1]:,} {end_word}")

# 마크다운 표 출력
print("| 구간 | 개수 |")
print("|---|---:|")
# 구간별 개수 출력
for label, c in zip(labels, counts):
    print(f"| {label} | {c} |")
# 빈도 합계
total = counts.sum()
print(f"| 합계 | {total} |")

# 빈도 합과 전체 행 수 비교
same = "같음" if total == len(df) else "다름"
print()
print(f"빈도 합 {total} / clean.csv 전체 행 수 {len(df)} → {same}")
# 저장 위치 출력
print(f"저장 완료: {OUTPUT_PATH}")
