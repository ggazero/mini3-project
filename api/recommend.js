// Vercel 서버리스 함수: POST /api/recommend
// 브라우저는 조건(최대 예산 · 최소 난이도)만 보낸다.
// 후보 목록은 여기서 data/data.json 으로 다시 만들고, GEMINI_API_KEY 도 여기서만 읽는다.

const fs = require("fs");
const path = require("path");

// 모델 이름과 호출 방식: https://ai.google.dev/gemini-api/docs/models ,
// https://ai.google.dev/gemini-api/docs/text-generation (Interactions API) 기준
const MODEL = "gemini-3.5-flash-lite";
const GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/interactions";
const MAX_CANDIDATES = 5;

let cachedItems = null;
function loadItems() {
  if (!cachedItems) {
    const file = path.join(process.cwd(), "data", "data.json");
    cachedItems = JSON.parse(fs.readFileSync(file, "utf8"));
  }
  return cachedItems;
}

// 빈칸(null · "")은 조건 없음. 숫자가 아니면 undefined (= 잘못된 입력)
function parseCondition(v) {
  if (v === null || v === undefined || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : undefined;
}

// 화면과 같은 필터 규칙 + 고정된 정렬: price 낮은 순 → difficulty 높은 순 → name 코드 순
function buildCandidates(items, maxPrice, minDiff) {
  return items
    .filter((it) => (maxPrice === null || Number(it.price) <= maxPrice)
      && (minDiff === null || Number(it.difficulty) >= minDiff))
    .sort((a, b) => Number(a.price) - Number(b.price)
      || Number(b.difficulty) - Number(a.difficulty)
      || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0))
    .slice(0, MAX_CANDIDATES)
    .map((it) => ({ name: it.name, price: Number(it.price), difficulty: Number(it.difficulty) }));
}

const compareName = (a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
// 소수 계산 오차(예: 3.6 - 3.5 = 0.10000000000000009)를 없애려고 0.001 단위로 반올림한다.
const gap = (difficulty, minDiff) => Math.round(Math.abs(difficulty - minDiff) * 1000);

// 고정 선택 기준 (AI 에게도 같은 기준을 준다):
// 최소 난이도가 있으면: 1) |difficulty - 최소 난이도| 가 가장 작은 것 2) 같으면 price 낮은 것 3) 그래도 같으면 name 오름차순
// 최소 난이도가 빈칸이면: 1) price 낮은 것 2) 같으면 difficulty 높은 것 3) 그래도 같으면 name 오름차순
function expectedPick(candidates, minDiff) {
  const order = minDiff === null
    ? (a, b) => a.price - b.price || b.difficulty - a.difficulty || compareName(a, b)
    : (a, b) => gap(a.difficulty, minDiff) - gap(b.difficulty, minDiff) || a.price - b.price || compareName(a, b);
  return candidates.slice().sort(order)[0];
}

const SYSTEM_INSTRUCTION = [
  "너는 방탈출 테마 추천 도우미다. 사용자가 준 후보 표 안에서만 하나를 고른다.",
  "선택 기준 (항상 이 순서로 적용하고, 같은 후보 표에는 항상 같은 답을 낸다):",
  "[최소 난이도가 숫자로 주어진 경우]",
  "1. 후보마다 차이 = difficulty - 최소 난이도 를 계산하고, 차이가 가장 작은 후보를 고른다.",
  "   difficulty 가 최소 난이도와 똑같은 후보는 차이가 0 이므로 가장 작다. (예: 최소 난이도 3.5 이면 difficulty 3.5 가 3.6 보다 가깝다)",
  "2. 차이가 같으면 price 가 더 낮은 후보를 고른다.",
  "3. 그래도 같으면 name 오름차순(문자 코드 순)으로 앞선 후보를 고른다.",
  "[최소 난이도가 '조건 없음'인 경우]",
  "1. price 가 가장 낮은 후보를 고른다.",
  "2. price 가 같으면 difficulty 가 더 높은 후보를 고른다.",
  "3. 그래도 같으면 name 오름차순(문자 코드 순)으로 앞선 후보를 고른다.",
  "규칙:",
  "- name 은 후보 표의 name 을 한 글자도 바꾸지 말고 그대로 쓴다.",
  "- reasons 는 정확히 두 문장이다. 각 문장은 한국어 한 줄이고, 공백과 문장부호를 포함해 40자 이내로 짧게 쓴다.",
  "- reasons 는 한국어로만 쓴다. price, difficulty, name 같은 영문 필드명은 쓰지 않는다.",
  "- price 는 반드시 '가격', difficulty 는 반드시 '난이도'라고 쓴다. (예: '난이도 3.5로 최소 난이도에 가장 가깝습니다.')",
  "- 이유에 쓰는 숫자는 후보 표에 있는 price 와 difficulty 값만 쓴다. 후보 개수, 순위, 예산, 최소 난이도, 계산한 차이 값, 날짜 같은 다른 숫자는 쓰지 않는다.",
  "- 후보 표에 없는 테마, 지역, 장르, 후기, 인원, 시간 같은 정보는 절대 말하지 않는다.",
].join("\n");

const RESPONSE_SCHEMA = {
  type: "object",
  properties: {
    name: { type: "string" },
    reasons: { type: "array", items: { type: "string" }, minItems: 2, maxItems: 2 },
  },
  required: ["name", "reasons"],
};

function buildInput(maxPrice, minDiff, candidates) {
  // difficulty 는 data.json 처럼 항상 소수 한 자리로 보여준다 (3 → 3.0). 비교 · 검증은 숫자 그대로 한다.
  const lines = candidates.map((c, i) => `${i + 1} | ${c.name} | ${c.price} | ${c.difficulty.toFixed(1)}`);
  return [
    `최대 예산: ${maxPrice === null ? "조건 없음" : maxPrice}`,
    `최소 난이도: ${minDiff === null ? "조건 없음" : minDiff}`,
    "",
    "후보 표 (번호 | name | price | difficulty):",
    ...lines,
    "",
    "선택 기준대로 하나를 골라 JSON 으로 답하라.",
  ].join("\n");
}

// 이유 문장 속 숫자가 모두 후보 표의 price · difficulty 값인지 확인
function reasonsUseOnlyTableNumbers(reasons, candidates) {
  const allowed = new Set();
  for (const c of candidates) { allowed.add(c.price); allowed.add(c.difficulty); }
  return reasons.every((r) => (r.replace(/(\d),(?=\d{3})/g, "$1").match(/\d+(?:\.\d+)?/g) || [])
    .every((n) => allowed.has(Number(n))));
}

function extractText(interaction) {
  const parts = [];
  for (const step of interaction.steps || []) {
    if (step.type !== "model_output") continue;
    for (const c of step.content || []) if (c.type === "text" && c.text) parts.push(c.text);
  }
  return parts.join("");
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ ok: false, reason: "method_not_allowed" });
  }

  const body = typeof req.body === "string" ? JSON.parse(req.body || "{}") : (req.body || {});
  const maxPrice = parseCondition(body.maxPrice);
  const minDiff = parseCondition(body.minDifficulty);
  if (maxPrice === undefined || minDiff === undefined) {
    return res.status(400).json({ ok: false, reason: "bad_input" });
  }

  const candidates = buildCandidates(loadItems(), maxPrice, minDiff);
  if (candidates.length === 0) {
    return res.status(200).json({ ok: false, reason: "no_candidates" });
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    console.error("GEMINI_API_KEY 가 설정되어 있지 않습니다.");
    return res.status(503).json({ ok: false, reason: "ai_unavailable" });
  }

  let text;
  try {
    const r = await fetch(GEMINI_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-goog-api-key": apiKey },
      body: JSON.stringify({
        model: MODEL,
        system_instruction: SYSTEM_INSTRUCTION,
        input: buildInput(maxPrice, minDiff, candidates),
        generation_config: { temperature: 0, seed: 7 },
        response_format: { type: "text", mime_type: "application/json", schema: RESPONSE_SCHEMA },
      }),
    });
    if (!r.ok) {
      console.error("Gemini 호출 실패", r.status, (await r.text()).slice(0, 500));
      return res.status(r.status === 429 ? 429 : 503).json({ ok: false, reason: "ai_unavailable" });
    }
    text = extractText(await r.json());
  } catch (err) {
    console.error("Gemini 호출 오류", err);
    return res.status(503).json({ ok: false, reason: "ai_unavailable" });
  }

  let answer;
  try { answer = JSON.parse(text); } catch { answer = null; }

  const names = candidates.map((c) => c.name);
  const valid = answer
    && typeof answer.name === "string"
    && names.includes(answer.name)
    && answer.name === expectedPick(candidates, minDiff).name
    && Array.isArray(answer.reasons)
    && answer.reasons.length === 2
    && answer.reasons.every((s) => typeof s === "string" && s.trim() !== "" && !s.includes("\n"))
    && reasonsUseOnlyTableNumbers(answer.reasons, candidates);

  if (!valid) {
    console.error("추천 검증 실패", text.slice(0, 500));
    return res.status(200).json({ ok: false, reason: "unverified" });
  }

  return res.status(200).json({
    ok: true,
    name: answer.name,
    reasons: answer.reasons.map((s) => s.trim()),
    candidates: names,
  });
};
