import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # 화면 없이 파일로만 저장하는 백엔드
import matplotlib.pyplot as plt
from pathlib import Path

# 콘솔 한글 깨짐 방지
sys.stdout.reconfigure(encoding="utf-8")

# 입력/출력 위치 (data 폴더는 읽기만 함, 기존 by_category.png와 다른 파일명)
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "clean.csv"
OUTPUT_PATH = BASE_DIR / "charts" / "by_category_median.png"

# 정제된 데이터 읽기
df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")

# difficulty별 price 개수·평균·중앙값 (실제 있는 값만 그룹이 됨, 오름차순 정렬)
grouped = df.groupby("difficulty")["price"].agg(["count", "mean", "median"]).sort_index()

# 그림 준비
fig, ax = plt.subplots(figsize=(12, 6))
# x축 범주 이름 (실제 값만 범주로 사용)
x_labels = [f"{d:.1f}" for d in grouped.index]
# 중앙값 막대그래프 그리기
bars = ax.bar(x_labels, grouped["median"], edgecolor="black")
# 막대 위 두 줄 글자: 중앙값(소수 둘째 자리)과 n
bar_texts = [f"{m:,.2f}\nn = {c}" for m, c in zip(grouped["median"], grouped["count"])]
# 막대 위에 글자 표시
ax.bar_label(bars, labels=bar_texts, padding=3, fontsize=8)
# x축 이름
ax.set_xlabel("Difficulty")
# y축 이름
ax.set_ylabel("Median price (KRW)")
# 제목 (n은 실제 행 수)
ax.set_title(f"Median Price by Difficulty (n = {len(df)})")
# 막대 위 두 줄 글자가 잘리지 않게 y축 위쪽 여유
ax.set_ylim(0, grouped["median"].max() * 1.15)
# y축 눈금을 천 단위 쉼표로 표시
ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
# 여백 정리
fig.tight_layout()
# 파일로 저장 (plt.show() 사용 안 함)
fig.savefig(OUTPUT_PATH, dpi=150)
# 그림 닫기
plt.close(fig)

# 그룹별 마크다운 표 출력
print("| difficulty | 개수 | 중앙값 |")
print("|---:|---:|---:|")
# 그룹마다 한 줄씩 출력
for d, row in grouped.iterrows():
    print(f"| {d:.1f} | {int(row['count'])} | {row['median']:.2f} |")

# 개수 합과 전체 행 수 비교
total = int(grouped["count"].sum())
same = "같음" if total == len(df) else "다름"
print()
print(f"개수 합 {total} / clean.csv 전체 행 수 {len(df)} → {same}")

# 평균·중앙값 기준 순위 (높은 값이 1위, 같은 값은 같은 순위)
grouped["mean_rank"] = grouped["mean"].rank(ascending=False, method="min").astype(int)
grouped["median_rank"] = grouped["median"].rank(ascending=False, method="min").astype(int)
# 두 순위가 다른 그룹만 고름
changed = grouped[grouped["mean_rank"] != grouped["median_rank"]]

# 평균 vs 중앙값 비교표 출력
print("\n=== 평균 vs 중앙값 순위 비교 (높은 값 = 1위, 동률은 같은 순위) ===")
print("| difficulty | 개수 | 평균 | 평균 순위 | 중앙값 | 중앙값 순위 | 순위 변화 |")
print("|---:|---:|---:|---:|---:|---:|---|")
# 그룹마다 한 줄씩 출력
for d, row in grouped.iterrows():
    # 순위가 같으면 '같음', 다르면 '바뀜'
    mark = "같음" if row["mean_rank"] == row["median_rank"] else "바뀜"
    print(f"| {d:.1f} | {int(row['count'])} | {row['mean']:.2f} | {int(row['mean_rank'])} | {row['median']:.2f} | {int(row['median_rank'])} | {mark} |")
# 순위가 바뀐 그룹 수 출력
print(f"\n순위가 바뀐 그룹: {len(changed)}개" + (f" ({', '.join(f'{d:.1f}' for d in changed.index)})" if len(changed) else ""))

# 가장 큰 price 값 (M05 확인값 35,000원)
max_price = df["price"].max()
# 최대 price가 들어 있는 difficulty 그룹 목록
max_groups = sorted(df.loc[df["price"] == max_price, "difficulty"].unique())
print(f"\n=== price {max_price:,}원이 들어 있는 difficulty 그룹 ===")
print("| difficulty | 그룹 개수 | 그 중 최대값 행 수 | 평균 | 중앙값 | 해당 테마 |")
print("|---:|---:|---:|---:|---:|---|")
# 그룹마다 한 줄씩 출력
for d in max_groups:
    # 해당 그룹에서 최대값인 행들
    hit = df[(df["difficulty"] == d) & (df["price"] == max_price)]
    print(f"| {d:.1f} | {int(grouped.loc[d, 'count'])} | {len(hit)} | {grouped.loc[d, 'mean']:.2f} | {grouped.loc[d, 'median']:.2f} | {', '.join(hit['name'])} |")

# 저장 위치 출력
print(f"\n저장 완료: {OUTPUT_PATH}")
