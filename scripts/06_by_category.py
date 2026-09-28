import sys
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
OUTPUT_PATH = BASE_DIR / "charts" / "by_category.png"

# 정제된 데이터 읽기
df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")

# difficulty별 price 개수·합·평균 (실제 있는 값만 그룹이 됨, 오름차순 정렬)
grouped = df.groupby("difficulty")["price"].agg(["count", "sum", "mean"]).sort_index()

# 그림 준비
fig, ax = plt.subplots(figsize=(12, 6))
# x축 위치에 쓸 범주 이름 (숫자 축이 아니라 실제 값만 범주로 사용)
x_labels = [f"{d:.1f}" for d in grouped.index]
# 막대그래프 그리기
bars = ax.bar(x_labels, grouped["mean"], edgecolor="black")
# 막대 위 두 줄 글자: 평균(소수 둘째 자리)과 n
bar_texts = [f"{m:,.2f}\nn = {c}" for m, c in zip(grouped["mean"], grouped["count"])]
# 막대 위에 글자 표시
ax.bar_label(bars, labels=bar_texts, padding=3, fontsize=8)
# x축 이름
ax.set_xlabel("Difficulty")
# y축 이름
ax.set_ylabel("Average price (KRW)")
# 제목 (n은 실제 행 수)
ax.set_title(f"Average Price by Difficulty (n = {len(df)})")
# 막대 위 두 줄 글자가 잘리지 않게 y축 위쪽 여유
ax.set_ylim(0, grouped["mean"].max() * 1.15)
# y축 눈금을 천 단위 쉼표로 표시
ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
# 여백 정리
fig.tight_layout()
# 파일로 저장 (plt.show() 사용 안 함)
fig.savefig(OUTPUT_PATH, dpi=150)
# 그림 닫기
plt.close(fig)

# 그룹별 마크다운 표 출력
print("| difficulty | 개수 | 합 | 평균 |")
print("|---:|---:|---:|---:|")
# 그룹마다 한 줄씩 출력
for d, row in grouped.iterrows():
    print(f"| {d:.1f} | {int(row['count'])} | {int(row['sum'])} | {row['mean']:.2f} |")

# 개수 합과 전체 행 수 비교
total = int(grouped["count"].sum())
same = "같음" if total == len(df) else "다름"
print()
print(f"서로 다른 difficulty 값: {len(grouped)}개")
print(f"개수 합 {total} / clean.csv 전체 행 수 {len(df)} → {same}")
# 저장 위치 출력
print(f"저장 완료: {OUTPUT_PATH}")
