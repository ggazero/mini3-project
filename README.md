# 방탈출 테마 비교 도우미

## 무엇을 하나

방탈출 테마를 고르려는 사람이 **최대 예산**과 **최소 난이도** 조건을 넣으면, 조건에 맞는 테마를 가격 낮은 순 카드로 보여 주는 화면입니다.
「이 조건으로 추천받기」를 누르면 조건에 맞는 후보 중 하나를 AI가 추천하고, 그 이유를 두 줄로 보여 줍니다.

## 배포 주소

https://zero-escape-pick.vercel.app

## 데이터

| 항목 | 내용 |
|---|---|
| 출처 | 방도장 공개 목록 (https://bangdojang.com/browse?done=not_done&view=list) |
| 수집 시점 | 2026-09-28 |
| 원본 행 수 | 30행 (`data/raw.csv`) |
| 정제 후 행 수 | 28행 (`data/clean.csv`, 화면용 `data/data.json`) |

정제한 주요 열

- `price_raw` → `price` : 쉼표(,)와 '원'을 떼고 정수로 바꿨습니다. price는 2인 이용 기준의 1인당 표시 가격입니다.
- `difficulty_raw` → `difficulty` : 숫자 값을 그대로 넣고, 임의로 반올림하지 않았습니다.
- `region_raw` → `region` : 앞뒤 공백만 정리했습니다.
- price 또는 difficulty가 빈칸인 행은 0이나 평균으로 채우지 않고 제거했습니다.

## AI 추천

Gemini를 사용합니다. 브라우저는 조건만 `/api/recommend`(Vercel 서버 함수)로 보내고, 서버가 `data/data.json`으로 후보를 다시 만들어 Gemini를 부릅니다.

AI에게 넘기는 값

- 현재 최대 예산, 현재 최소 난이도
- 조건에 맞는 후보 중 가격 낮은 순 최대 5개의 `name` · `price` · `difficulty` (`detail_url` 등 다른 값은 넘기지 않음)

AI에게 받는 값

- 후보 중 추천 1개의 `name` (후보 표의 이름 그대로)
- 추천 이유 두 줄

지키게 한 규칙

- 선택 기준을 고정해 같은 조건 · 같은 후보 목록이면 같은 추천이 나오게 했습니다.
  - 최소 난이도가 있으면: 최소 난이도에 difficulty가 가장 가까운 후보 → 같으면 price가 낮은 후보 → 같으면 name 오름차순
  - 최소 난이도가 빈칸이면: price가 낮은 후보 → 같으면 difficulty가 높은 후보 → 같으면 name 오름차순
- 후보 표에 없는 테마나 정보는 말하지 않게 했습니다.
- 이유는 한국어 두 줄, 각 줄 40자 이내로 쓰고, 「가격」 · 「난이도」라고 표현하게 했습니다.
- 서버에서 다시 검증합니다. 아래 중 하나라도 어긋나면 추천을 보여 주지 않고 「추천을 확인하지 못했습니다」를 표시합니다.
  - 추천 이름이 후보 5개 안에 있는가
  - 추천 이름이 위 선택 기준으로 고른 답과 같은가
  - 이유 속 숫자가 모두 후보 표의 price · difficulty 값인가
- 후보가 0개면 AI를 부르지 않고 조건 안내만 보여 줍니다. AI 호출이 실패하면 「잠시 뒤 다시 눌러 주세요」를 표시합니다.

API 키는 Vercel 환경변수 `GEMINI_API_KEY`에 넣습니다. 키는 서버 함수에서만 읽고, 화면(`index.html`)에는 들어가지 않습니다.

## 확인한 것

`notes.md`의 M10(조건 필터)과 M14(AI 검증표) 기록 기준입니다.

| 경우 | 조건 | 화면 후보 수 | data.json으로 센 수 | AI 추천 | 후보 안? | 이유 속 가격 · 난이도 |
|---|---|---:|---:|---|---|---|
| 정상 | 예산 30000 · 최소 난이도 3.5 | 5 | 5 | 머니머니패키지 | 예 | 30000 · 3.5 — data.json과 같음 |
| 후보 1개 | 예산 26000 · 최소 난이도 4.0 | 1 | 1 | 멸종위기종 탐사대 | 예 | 26000 · 4.1 — data.json과 같음 |
| 후보 없음 | 예산 25000 · 최소 난이도 4.0 | 0 | 0 | AI를 부르지 않음 (안내 문장만) | — | — |

- 정상 조건은 세 번 다시 확인했고, 세 번 모두 머니머니패키지를 추천했습니다. 추천 이름은 후보 안에 있었고, 이유 속 숫자는 data.json과 같았으며, 지어낸 말은 없었습니다.

## 한계

- 방도장은 추가 목록이 무한스크롤 방식이고 robots.txt에서 `/api/` 경로가 제한되어 있어, 공개 목록 페이지에서 확인 가능한 30행만 수집했습니다.
- price와 difficulty가 비어 있는 2행을 제거해 28개를 분석했습니다.
- Gemini 무료 API 한도에 따라 추천 호출이 실패할 수 있습니다. 이때는 「잠시 뒤 다시 눌러 주세요」가 표시됩니다.

## 실행 안내

명령은 모두 프로젝트 루트(`mini3-project`)에서 실행합니다. Windows는 `python ...`, Mac은 `python3 ...`로 실행합니다.

### 1. 다시 모으기

| 순서 | 파일 이름 | 무엇을 만드나 | 실행 명령 (Windows) | 확인 여부 |
|---:|---|---|---|---|
| 0 | `scripts/00_env_check.py` | 파일을 만들지 않음 — pandas · requests · beautifulsoup4 · matplotlib 설치와 버전 확인 | `python scripts/00_env_check.py` | 확인 안 함 |
| 1 | `scripts/01_collect_p1.py` | `data/raw_p1.csv` (공개 목록 1페이지 수집) | `python scripts/01_collect_p1.py` | 확인 안 함 |
| 2 | `scripts/02_collect.py` | `data/raw.csv` (원본 30행) | `python scripts/02_collect.py` | 확인 안 함 |
| 3 | `scripts/03_clean.py` | `data/clean.csv` (정제 28행) | `python scripts/03_clean.py` | 확인함 |
| 4 | `scripts/04_stats.py` | 파일을 만들지 않음 — price 기초 통계표를 터미널에 출력 | `python scripts/04_stats.py` | 확인 안 함 |
| 5 | `scripts/05_hist.py` | `charts/hist.png` (가격 분포, 2,000원 구간) | `python scripts/05_hist.py` | 확인 안 함 |
| 5 | `scripts/05_hist_half.py` | `charts/hist_half.png` (가격 분포, 1,000원 구간) | `python scripts/05_hist_half.py` | 확인 안 함 |
| 6 | `scripts/06_by_category.py` | `charts/by_category.png` (난이도별 평균 가격) | `python scripts/06_by_category.py` | 확인 안 함 |
| 6 | `scripts/06_by_category_median.py` | `charts/by_category_median.png` (난이도별 평균 · 중앙값) | `python scripts/06_by_category_median.py` | 확인 안 함 |
| 7 | `scripts/07_export_json.py` | `data/data.json` (화면 · AI 추천용 28개) | `python scripts/07_export_json.py` | 확인 안 함 |

> ⚠️ `01_collect_p1.py`, `02_collect.py`는 사이트에 요청을 보낸다 · 페이지 수를 늘리지 않는다.
> 지금 있는 `data/raw.csv`로 다시 만들 때는 3번부터 실행합니다.

확인함 — `python scripts/03_clean.py` 를 실행해 오류 없이 끝났고(종료 코드 0), 행 수 30 → 28 (빈칸 2행 제거 · detail_url 중복 0), `data/clean.csv` 28행 저장을 확인했습니다.

### 2. 화면에 반영하기

화면(`index.html`)은 `data/data.json`과 `charts/hist.png` · `charts/by_category.png`를 그대로 읽어 보여 줍니다. AI 추천 서버 함수(`api/recommend.js`)도 `data/data.json`으로 후보를 만듭니다.

1. 위 순서로 `data/data.json`과 `charts/` 그림을 다시 만듭니다.
2. 바뀐 파일을 커밋하고 GitHub 저장소(`ggazero/mini3-project`)의 `main` 브랜치에 push합니다.
3. Vercel이 새로 배포하면 배포 주소 https://zero-escape-pick.vercel.app 에 반영됩니다.

### 3. AI 연결

AI 추천은 `api/recommend.js`(Vercel 서버 함수, `POST /api/recommend`)가 Gemini를 부르는 방식입니다. API 키는 이 서버 함수에서만 읽고, 화면에는 들어가지 않습니다.

1. Vercel 프로젝트의 Settings → Environment Variables에 이름 `GEMINI_API_KEY`로 Gemini API 키를 넣습니다.
2. Redeploy해야 새 환경변수가 적용됩니다.
3. 키가 없거나 호출이 실패하면 화면에 「잠시 뒤 다시 눌러 주세요」가 표시됩니다.

키 값은 README나 저장소 파일에 쓰지 않습니다. 로컬의 `.env` · `.env.local`은 `.gitignore`로 저장소에 올라가지 않습니다.
