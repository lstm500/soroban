# VERSION: CLEAN-V14-VOICE-FEEDBACK-2026-08-25

import json

import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client


st.set_page_config(
    page_title="そろばん計算トレーナー",
    page_icon="🧮",
    layout="wide",
)

APP_VERSION = "CLEAN-V14-VOICE-FEEDBACK"
BUCKET_NAME = "music"
SIGNED_URL_EXPIRES_IN = 3600

BGM_FILES = [
    "0.mp3", "1.mp3", "2.mp3", "3.mp3", "4.mp3",
    "5.mp3", "6.mp3", "7.mp3", "8.mp3", "9.mp3",
    "10-1.mp3", "10-2.mp3", "10-3.mp3",
]


@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_SERVICE_ROLE_KEY"],
    )


@st.cache_data(ttl=3000, show_spinner=False)
def get_bgm_urls():
    bucket = get_supabase().storage.from_(BUCKET_NAME)
    urls = {}

    for filename in BGM_FILES:
        result = bucket.create_signed_url(filename, SIGNED_URL_EXPIRES_IN)

        if isinstance(result, dict):
            signed_url = (
                result.get("signedURL")
                or result.get("signedUrl")
                or result.get("signed_url")
            )
        else:
            signed_url = (
                getattr(result, "signedURL", None)
                or getattr(result, "signedUrl", None)
                or getattr(result, "signed_url", None)
            )

        if not signed_url:
            raise RuntimeError(f"{filename} のSigned URLを取得できませんでした。")

        urls[filename] = signed_url

    return urls


try:
    BGM_URLS = get_bgm_urls()
except KeyError:
    st.error(
        "Streamlit Secrets に SUPABASE_URL と "
        "SUPABASE_SERVICE_ROLE_KEY を設定してください。"
    )
    st.stop()
except Exception as exc:
    st.error("Supabase Storage のBGMを取得できませんでした。")
    st.caption(str(exc))
    st.stop()


BGM_JSON = json.dumps(BGM_URLS, ensure_ascii=False)
VERSION_JSON = json.dumps(APP_VERSION)

HTML = r"""
<div id="soroban-app">
<style>
  * { box-sizing: border-box; }

  body {
    margin: 0;
    background: #f7f5ef;
    color: #24231f;
    font-family: system-ui, -apple-system, "Hiragino Sans", "Yu Gothic", sans-serif;
  }

  #soroban-app {
    max-width: 1180px;
    margin: 0 auto;
    padding: 16px;
  }

  button, input { font: inherit; }

  button {
    min-height: 46px;
    border: 0;
    border-radius: 12px;
    padding: 10px 16px;
    cursor: pointer;
    font-weight: 800;
    color: #24231f;
    background: #e9e4da;
    touch-action: manipulation;
  }

  button.primary {
    background: #315f86;
    color: #fff;
  }

  button:disabled {
    opacity: .45;
    cursor: not-allowed;
  }

  .version {
    font-size: 11px;
    color: #8a857c;
    margin-bottom: 8px;
  }

  .intro {
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 16px;
    margin-bottom: 18px;
  }

  .lead {
    max-width: 820px;
    font-size: 14px;
    line-height: 1.7;
    color: #66635d;
  }

  .badge {
    white-space: nowrap;
    border: 1px solid #d8d2c6;
    border-radius: 999px;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 850;
  }

  .level-title {
    margin: 22px 0 10px;
    font-size: 20px;
    font-weight: 900;
  }

  .mode-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
  }

  .mode-card {
    display: flex;
    flex-direction: column;
    min-height: 180px;
    padding: 16px;
    border: 1px solid #ddd7ca;
    border-radius: 18px;
    background: #fff;
  }

  .mode-no {
    font-size: 12px;
    font-weight: 900;
    letter-spacing: .08em;
    color: #817b70;
  }

  .mode-name {
    margin: 6px 0 8px;
    font-size: 18px;
    font-weight: 900;
  }

  .mode-desc {
    flex: 1;
    font-size: 13px;
    line-height: 1.6;
    color: #66635d;
  }

  .chips {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin: 10px 0;
  }

  .chip {
    padding: 5px 8px;
    border-radius: 999px;
    background: #f2eee5;
    font-size: 12px;
    font-weight: 800;
  }

  .hidden { display: none !important; }
  .workspace { display: none; }
  .workspace.show { display: block; }

  .statusbar {
    display: grid;
    grid-template-columns: minmax(200px, 1fr) auto auto auto auto;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    border: 1px solid #ddd7ca;
    border-radius: 18px;
    background: #fff;
  }

  .status-title {
    font-size: 16px;
    font-weight: 900;
  }

  .status-sub {
    margin-top: 3px;
    font-size: 12px;
    color: #706c64;
  }

  .timer {
    min-width: 88px;
    text-align: center;
    font-size: 25px;
    font-weight: 950;
    font-variant-numeric: tabular-nums;
  }

  .timer.warn { color: #a14428; }

  .streak {
    white-space: nowrap;
    font-size: 14px;
    font-weight: 900;
  }

  .bgm-name {
    grid-column: 1 / -1;
    font-size: 12px;
    color: #706c64;
  }

  .question-card {
    position: relative;
    min-height: 560px;
    margin-top: 14px;
    padding: 24px;
    border: 2px solid #ddd7ca;
    border-radius: 22px;
    background: #fff;
    transition:
      border-color .25s ease,
      border-width .25s ease,
      box-shadow .25s ease,
      background .25s ease,
      transform .25s ease;
  }

  .question-card.streak5 {
    border: 6px solid #e7aa24 !important;
    background: #fffaf0 !important;
    box-shadow:
      0 0 0 4px rgba(255, 210, 79, .24),
      0 0 28px rgba(227, 165, 35, .52),
      inset 0 0 26px rgba(255, 221, 103, .15) !important;
  }

  .question-card.streak10 {
    border: 8px solid transparent !important;
    background:
      linear-gradient(#fffdf9, #fffdf9) padding-box,
      linear-gradient(
        90deg,
        var(--rb1, #ff3b30),
        var(--rb2, #ff9500),
        var(--rb3, #ffd60a),
        var(--rb4, #34c759),
        var(--rb5, #0a84ff),
        var(--rb6, #5e5ce6),
        var(--rb7, #bf5af2),
        var(--rb8, #ff3b30)
      ) border-box !important;
    background-size: 100% 100%, 300% 100% !important;
    box-shadow:
      0 0 0 6px rgba(255, 214, 10, .28),
      0 0 36px rgba(255, 59, 48, .52),
      0 0 60px rgba(10, 132, 255, .42) !important;
    animation:
      rainbowBorder 2s linear infinite,
      pulseGlow 1s ease-in-out infinite alternate;
  }

  @keyframes rainbowBorder {
    from { background-position: 0 0, 0% 50%; }
    to   { background-position: 0 0, 300% 50%; }
  }

  @keyframes pulseGlow {
    from { transform: scale(1); }
    to   { transform: scale(1.005); }
  }

  .qtop {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }

  .qcount, .score {
    font-size: 13px;
    font-weight: 850;
  }

  .qcount { color: #706c64; }

  .equation {
    margin: 38px 0 22px;
    text-align: center;
    font-size: clamp(42px, 7vw, 68px);
    font-weight: 950;
    letter-spacing: .03em;
  }

  .answer-form {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  .answer-input {
    width: min(280px, 100%);
    min-height: 62px;
    padding: 8px 12px;
    border: 2px solid #c8c1b4;
    border-radius: 14px;
    background: #fff;
    color: #24231f;
    text-align: center;
    font-size: 30px;
    font-weight: 900;
  }

  .keypad-wrap {
    width: min(360px, 100%);
    margin: 16px auto 0;
  }

  .keypad-label {
    margin-bottom: 8px;
    text-align: center;
    font-size: 13px;
    font-weight: 850;
    color: #706c64;
  }

  .keypad {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 9px;
  }

  .keypad button {
    min-height: 62px;
    border: 1px solid #d4cec1;
    background: #f3efe7;
    color: #24231f;
    font-size: 24px;
    font-weight: 900;
    user-select: none;
  }

  .keypad button:active {
    transform: translateY(1px);
    background: #e7e0d4;
  }

  .keypad .key-action {
    background: #e5e0d6;
    font-size: 14px;
  }

  .feedback {
    min-height: 36px;
    margin-top: 14px;
    text-align: center;
    font-size: 20px;
    font-weight: 900;
  }

  .feedback.good { color: #28704a; }
  .feedback.bad { color: #a14428; }

  .progress {
    height: 8px;
    margin-top: 18px;
    overflow: hidden;
    border-radius: 999px;
    background: #e7e2d9;
  }

  .bar {
    width: 0;
    height: 100%;
    background: #6d815d;
    transition: width .25s ease;
  }

  .results {
    display: none;
    margin-top: 14px;
    padding: 24px;
    border: 1px solid #ddd7ca;
    border-radius: 22px;
    background: #fff;
  }

  .results.show { display: block; }

  .result-score {
    margin: 8px 0;
    text-align: center;
    font-size: 46px;
    font-weight: 950;
  }

  .result-note {
    text-align: center;
    color: #66635d;
    line-height: 1.7;
  }

  .review {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin-top: 18px;
  }

  .review-item {
    padding: 10px 12px;
    border-radius: 12px;
    background: #f3efe7;
    font-size: 13px;
    line-height: 1.5;
  }

  .review-item.correct { border-left: 4px solid #437454; }
  .review-item.wrong { border-left: 4px solid #a44b32; }

  .actions {
    display: flex;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 18px;
  }

  @media (prefers-reduced-motion: reduce) {
    .question-card.streak10 { animation: none; }
  }

  @media (max-width: 760px) {
    #soroban-app { padding: 10px; }

    .intro {
      flex-direction: column;
      align-items: flex-start;
    }

    .mode-grid { grid-template-columns: 1fr; }
    .mode-card { min-height: 0; }
    .statusbar { grid-template-columns: 1fr auto; }
    #quitBtn { grid-column: 1 / -1; }
    .review { grid-template-columns: 1fr; }

    .question-card {
      min-height: 540px;
      padding: 18px;
    }

    .equation { margin-top: 32px; }
  }
</style>

<div id="versionLabel" class="version"></div>

<div id="menuView">
  <div class="intro">
    <div class="lead">
      各モード20問・制限時間10分です。
      割り算以外は、計算式を確定する直前に左右の数へ必ず+1します。
      そのため表示される数に0は出ません。
    </div>
    <div class="badge">20問 / 10分</div>
  </div>

  <div class="level-title">初級モード｜足し算のみ</div>
  <div class="mode-grid">
    <article class="mode-card">
      <div class="mode-no">BEGINNER ADD 1</div>
      <div class="mode-name">1桁の足し算</div>
      <div class="mode-desc">最終表示は1〜9の数だけ。足し算のみ20問です。</div>
      <div class="chips"><span class="chip">20問</span><span class="chip">10分</span></div>
      <button type="button" class="primary start-mode" data-mode="ba1">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">BEGINNER ADD 2</div>
      <div class="mode-name">2桁の足し算</div>
      <div class="mode-desc">最終表示は10〜99。足し算のみ20問です。</div>
      <div class="chips"><span class="chip">20問</span><span class="chip">10分</span></div>
      <button type="button" class="primary start-mode" data-mode="ba2">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">BEGINNER ADD 3</div>
      <div class="mode-name">3桁の足し算</div>
      <div class="mode-desc">最終表示は100〜999。足し算のみ20問です。</div>
      <div class="chips"><span class="chip">20問</span><span class="chip">10分</span></div>
      <button type="button" class="primary start-mode" data-mode="ba3">はじめる</button>
    </article>
  </div>

  <div class="level-title">初級モード｜引き算のみ</div>
  <div class="mode-grid">
    <article class="mode-card">
      <div class="mode-no">BEGINNER SUB 1</div>
      <div class="mode-name">1桁の引き算</div>
      <div class="mode-desc">最終表示は1〜9。引き算のみ20問。答えは必ず0以上です。</div>
      <div class="chips"><span class="chip">20問</span><span class="chip">10分</span></div>
      <button type="button" class="primary start-mode" data-mode="bs1">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">BEGINNER SUB 2</div>
      <div class="mode-name">2桁の引き算</div>
      <div class="mode-desc">最終表示は10〜99。引き算のみ20問。答えは必ず0以上です。</div>
      <div class="chips"><span class="chip">20問</span><span class="chip">10分</span></div>
      <button type="button" class="primary start-mode" data-mode="bs2">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">BEGINNER SUB 3</div>
      <div class="mode-name">3桁の引き算</div>
      <div class="mode-desc">最終表示は100〜999。引き算のみ20問。答えは必ず0以上です。</div>
      <div class="chips"><span class="chip">20問</span><span class="chip">10分</span></div>
      <button type="button" class="primary start-mode" data-mode="bs3">はじめる</button>
    </article>
  </div>

  <div class="level-title">中級モード</div>
  <div class="mode-grid">
    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE 1</div>
      <div class="mode-name">1桁の掛け算・割り算</div>
      <div class="mode-desc">1〜9同士の掛け算と、整数になる割り算です。</div>
      <div class="chips"><span class="chip">20問</span><span class="chip">10分</span></div>
      <button type="button" class="primary start-mode" data-mode="m1">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE 2</div>
      <div class="mode-name">2桁×1桁 / 3桁÷1桁</div>
      <div class="mode-desc">2桁×1桁の掛け算と、3桁÷1桁の整数解です。</div>
      <div class="chips"><span class="chip">20問</span><span class="chip">10分</span></div>
      <button type="button" class="primary start-mode" data-mode="m2">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE 3</div>
      <div class="mode-name">2桁×2桁 / 3桁÷2桁</div>
      <div class="mode-desc">2桁同士の掛け算と、3桁÷2桁の整数解です。</div>
      <div class="chips"><span class="chip">20問</span><span class="chip">10分</span></div>
      <button type="button" class="primary start-mode" data-mode="m3">はじめる</button>
    </article>
  </div>

  <div class="level-title">上級モード</div>
  <div class="mode-grid">
    <article class="mode-card">
      <div class="mode-no">ADVANCED 1</div>
      <div class="mode-name">4桁の足し算・引き算</div>
      <div class="mode-desc">最終表示は1000〜9999。引き算の答えは0以上です。</div>
      <div class="chips"><span class="chip">20問</span><span class="chip">10分</span></div>
      <button type="button" class="primary start-mode" data-mode="a1">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">ADVANCED 2</div>
      <div class="mode-name">3桁×2桁 / 4桁÷2桁</div>
      <div class="mode-desc">3桁×2桁の掛け算と、4桁÷2桁の整数解です。</div>
      <div class="chips"><span class="chip">20問</span><span class="chip">10分</span></div>
      <button type="button" class="primary start-mode" data-mode="a2">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">ADVANCED 3</div>
      <div class="mode-name">3桁×3桁 / 5桁÷3桁</div>
      <div class="mode-desc">3桁同士の掛け算と、5桁÷3桁の整数解です。</div>
      <div class="chips"><span class="chip">20問</span><span class="chip">10分</span></div>
      <button type="button" class="primary start-mode" data-mode="a3">はじめる</button>
    </article>
  </div>
</div>

<section id="workspace" class="workspace">
  <div class="statusbar">
    <div>
      <div id="statusTitle" class="status-title"></div>
      <div class="status-sub">20問・制限時間10分</div>
    </div>
    <div id="timer" class="timer">10:00</div>
    <div id="streak" class="streak">連続正解 0</div>
    <button type="button" id="bgmBtn">♪ BGM ON</button>
    <button type="button" id="quitBtn">モード選択へ</button>
    <div id="bgmName" class="bgm-name">BGM：0.mp3</div>
  </div>

  <div id="questionCard" class="question-card">
    <div class="qtop">
      <div id="qCount" class="qcount">1 / 20</div>
      <div id="score" class="score">正解 0</div>
    </div>

    <div id="equation" class="equation"></div>

    <form id="answerForm" class="answer-form">
      <input
        id="answerInput"
        class="answer-input"
        type="text"
        inputmode="none"
        autocomplete="off"
        aria-label="答え"
        placeholder="答え"
        readonly
      >
      <button type="submit" class="primary">答える</button>
    </form>

    <div class="keypad-wrap">
      <div class="keypad-label">数字をタップして入力</div>
      <div id="keypad" class="keypad">
        <button type="button" data-key="7">7</button>
        <button type="button" data-key="8">8</button>
        <button type="button" data-key="9">9</button>
        <button type="button" data-key="4">4</button>
        <button type="button" data-key="5">5</button>
        <button type="button" data-key="6">6</button>
        <button type="button" data-key="1">1</button>
        <button type="button" data-key="2">2</button>
        <button type="button" data-key="3">3</button>
        <button type="button" class="key-action" data-action="clear">クリア</button>
        <button type="button" data-key="0">0</button>
        <button type="button" class="key-action" data-action="backspace">← 1つ消す</button>
      </div>
    </div>

    <div id="feedback" class="feedback"></div>

    <div class="progress">
      <div id="bar" class="bar"></div>
    </div>
  </div>

  <div id="results" class="results">
    <div class="result-note">結果</div>
    <div id="resultScore" class="result-score"></div>
    <div id="resultNote" class="result-note"></div>
    <div id="review" class="review"></div>
    <div class="actions">
      <button type="button" id="retryBtn" class="primary">同じモードをもう一度</button>
      <button type="button" id="menuBtn">モード選択へ</button>
    </div>
  </div>
</section>

<script>
(() => {
  const APP_VERSION = __APP_VERSION__;
  const BGM_URLS = __BGM_URLS__;

  const root = document.getElementById("soroban-app");
  const $ = (selector) => root.querySelector(selector);

  $("#versionLabel").textContent = `APP VERSION: ${APP_VERSION}`;

  const menuView = $("#menuView");
  const workspace = $("#workspace");
  const questionCard = $("#questionCard");
  const results = $("#results");
  const equation = $("#equation");
  const answerInput = $("#answerInput");
  const feedback = $("#feedback");
  const timerEl = $("#timer");
  const bar = $("#bar");
  const bgmBtn = $("#bgmBtn");
  const bgmName = $("#bgmName");

  const modeInfo = {
    ba1: { title: "初級・足し算1｜1桁の足し算" },
    ba2: { title: "初級・足し算2｜2桁の足し算" },
    ba3: { title: "初級・足し算3｜3桁の足し算" },
    bs1: { title: "初級・引き算1｜1桁の引き算" },
    bs2: { title: "初級・引き算2｜2桁の引き算" },
    bs3: { title: "初級・引き算3｜3桁の引き算" },
    m1: { title: "中級1｜1桁の掛け算・割り算" },
    m2: { title: "中級2｜2桁×1桁 / 3桁÷1桁" },
    m3: { title: "中級3｜2桁×2桁 / 3桁÷2桁" },
    a1: { title: "上級1｜4桁の足し算・引き算" },
    a2: { title: "上級2｜3桁×2桁 / 4桁÷2桁" },
    a3: { title: "上級3｜3桁×3桁 / 5桁÷3桁" }
  };

  const RULES = Object.freeze({
    addSubOperandMin: 1,
    subtractionMinAnswer: 0,
    divisionMustBeInteger: true
  });

  let currentMode = null;
  let questions = [];
  let index = 0;
  let score = 0;
  let answers = [];
  let seconds = 600;
  let timerHandle = null;
  let locked = false;
  let correctStreak = 0;
  let bgmOn = true;
  let currentBgm = "0.mp3";
  let lastTenBgm = null;

  const audio = new Audio();
  audio.loop = true;
  audio.volume = 0.12;
  audio.preload = "auto";

  const randInt = (min, max) =>
    Math.floor(Math.random() * (max - min + 1)) + min;

  const coin = () => Math.random() < 0.5;

  function calculate(a, op, b) {
    if (op === "＋") return a + b;
    if (op === "－") return a - b;
    if (op === "×") return a * b;
    return a / b;
  }

  function isValidQuestion(q) {
    if (!q) return false;

    if (q.op === "＋" || q.op === "－") {
      if (q.a < RULES.addSubOperandMin) return false;
      if (q.b < RULES.addSubOperandMin) return false;
    }

    if (q.op === "－" && q.answer < RULES.subtractionMinAnswer) {
      return false;
    }

    if (q.op === "÷") {
      if (q.b <= 0) return false;
      if (RULES.divisionMustBeInteger && !Number.isInteger(q.answer)) {
        return false;
      }
    }

    return true;
  }

  function makeQuestion(rawA, op, rawB) {
    // 割り算以外は、計算式確定直前に左右へ必ず+1。
    const a = op === "÷" ? rawA : rawA + 1;
    const b = op === "÷" ? rawB : rawB + 1;

    const q = {
      a,
      op,
      b,
      answer: calculate(a, op, b)
    };

    if (!isValidQuestion(q)) {
      throw new Error(
        `禁止問題: raw=${rawA} ${op} ${rawB}, final=${a} ${op} ${b}`
      );
    }

    return q;
  }

  function makeAddSub(finalMin, finalMax) {
    const rawMin = Math.max(0, finalMin - 1);
    const rawMax = finalMax - 1;
    const op = coin() ? "＋" : "－";

    if (op === "＋") {
      return makeQuestion(
        randInt(rawMin, rawMax),
        "＋",
        randInt(rawMin, rawMax)
      );
    }

    const rawA = randInt(rawMin, rawMax);
    const rawB = randInt(rawMin, rawA);
    return makeQuestion(rawA, "－", rawB);
  }

  function makeAdditionOnly(finalMin, finalMax) {
    const rawMin = Math.max(0, finalMin - 1);
    const rawMax = finalMax - 1;

    return makeQuestion(
      randInt(rawMin, rawMax),
      "＋",
      randInt(rawMin, rawMax)
    );
  }

  function makeSubtractionOnly(finalMin, finalMax) {
    const rawMin = Math.max(0, finalMin - 1);
    const rawMax = finalMax - 1;

    // rawA >= rawB としておき、最終+1後も大小関係を維持する。
    const rawA = randInt(rawMin, rawMax);
    const rawB = randInt(rawMin, rawA);

    return makeQuestion(rawA, "－", rawB);
  }

  function makeMul(finalAMin, finalAMax, finalBMin, finalBMax) {
    const rawAMin = Math.max(0, finalAMin - 1);
    const rawAMax = finalAMax - 1;
    const rawBMin = Math.max(0, finalBMin - 1);
    const rawBMax = finalBMax - 1;

    return makeQuestion(
      randInt(rawAMin, rawAMax),
      "×",
      randInt(rawBMin, rawBMax)
    );
  }

  function makeExactDivision(numeratorMin, numeratorMax, divisorMin, divisorMax) {
    const divisorStart = Math.max(1, divisorMin);

    for (let tries = 0; tries < 1000; tries += 1) {
      const divisor = randInt(divisorStart, divisorMax);
      const quotientMin = Math.max(1, Math.ceil(numeratorMin / divisor));
      const quotientMax = Math.floor(numeratorMax / divisor);

      if (quotientMin <= quotientMax) {
        const quotient = randInt(quotientMin, quotientMax);
        return makeQuestion(divisor * quotient, "÷", divisor);
      }
    }

    throw new Error("整数になる割り算を生成できませんでした。");
  }

  function makeOneQuestion(mode) {
    if (mode === "ba1") return makeAdditionOnly(1, 9);
    if (mode === "ba2") return makeAdditionOnly(10, 99);
    if (mode === "ba3") return makeAdditionOnly(100, 999);

    if (mode === "bs1") return makeSubtractionOnly(1, 9);
    if (mode === "bs2") return makeSubtractionOnly(10, 99);
    if (mode === "bs3") return makeSubtractionOnly(100, 999);

    if (mode === "m1") {
      return coin()
        ? makeMul(1, 9, 1, 9)
        : makeExactDivision(1, 81, 1, 9);
    }

    if (mode === "m2") {
      return coin()
        ? makeMul(10, 99, 1, 9)
        : makeExactDivision(100, 999, 1, 9);
    }

    if (mode === "m3") {
      return coin()
        ? makeMul(10, 99, 10, 99)
        : makeExactDivision(100, 999, 10, 99);
    }

    if (mode === "a1") return makeAddSub(1000, 9999);

    if (mode === "a2") {
      return coin()
        ? makeMul(100, 999, 10, 99)
        : makeExactDivision(1000, 9999, 10, 99);
    }

    return coin()
      ? makeMul(100, 999, 100, 999)
      : makeExactDivision(10000, 99999, 100, 999);
  }

  function generateQuestions(mode) {
    const out = [];

    while (out.length < 20) {
      const q = makeOneQuestion(mode);
      if (!isValidQuestion(q)) continue;
      out.push(q);
    }

    return out;
  }

  function desiredBgmName(streak) {
    if (streak <= 0) {
      lastTenBgm = null;
      return "0.mp3";
    }

    if (streak <= 9) {
      lastTenBgm = null;
      return `${streak}.mp3`;
    }

    const pool = ["10-1.mp3", "10-2.mp3", "10-3.mp3"];
    const choices = lastTenBgm
      ? pool.filter((name) => name !== lastTenBgm)
      : pool;

    lastTenBgm = choices[Math.floor(Math.random() * choices.length)];
    return lastTenBgm;
  }

  function updateBgmButton() {
    bgmBtn.textContent = bgmOn ? "♪ BGM ON" : "♪ BGM OFF";
  }

  function playBgmForStreak(streak, force = false) {
    const name = desiredBgmName(streak);

    if (!force && name === currentBgm && !audio.paused) return;

    currentBgm = name;
    bgmName.textContent = `BGM：${name}`;

    const url = BGM_URLS[name];
    if (!url) {
      bgmName.textContent = `BGM：${name}（URL取得失敗）`;
      return;
    }

    audio.pause();
    audio.src = url;
    audio.currentTime = 0;
    audio.loop = true;
    audio.volume = 0.12;

    if (bgmOn) {
      const p = audio.play();
      if (p && typeof p.catch === "function") {
        p.catch(() => {
          bgmName.textContent = `BGM：${name}（再生待機）`;
        });
      }
    }
  }

  function stopBgm() {
    audio.pause();
  }

  function toggleBgm() {
    bgmOn = !bgmOn;
    updateBgmButton();

    if (
      bgmOn &&
      workspace.classList.contains("show") &&
      !results.classList.contains("show")
    ) {
      playBgmForStreak(correctStreak, true);
    } else {
      stopBgm();
    }
  }

  function getJapaneseVoice() {
    if (!("speechSynthesis" in window)) return null;

    const voices = window.speechSynthesis.getVoices();

    return (
      voices.find((voice) => voice.lang === "ja-JP") ||
      voices.find((voice) =>
        String(voice.lang || "").toLowerCase().startsWith("ja")
      ) ||
      null
    );
  }

  function speakAnswerFeedback(ok, streak) {
    if (
      !("speechSynthesis" in window) ||
      typeof SpeechSynthesisUtterance === "undefined"
    ) {
      return;
    }

    window.speechSynthesis.cancel();

    const message = ok
      ? `正解！${streak}問連続正解中！`
      : "残念！";

    const utterance = new SpeechSynthesisUtterance(message);

    utterance.lang = "ja-JP";
    utterance.rate = 1.30;
    utterance.pitch = 1.48;
    utterance.volume = 0.95;

    const voice = getJapaneseVoice();
    if (voice) {
      utterance.voice = voice;
    }

    window.speechSynthesis.speak(utterance);
  }

  function setRainbowForStreak(streak) {
    const vars = [
      "--rb1", "--rb2", "--rb3", "--rb4",
      "--rb5", "--rb6", "--rb7", "--rb8"
    ];

    if (streak < 10) {
      vars.forEach((name) => questionCard.style.removeProperty(name));
      return;
    }

    // 10問以降は正解するたび47度ずつ色相をずらす。
    const baseHue = ((streak - 10) * 47) % 360;
    const offsets = [0, 46, 92, 138, 184, 230, 276, 322];

    offsets.forEach((offset, index) => {
      const hue = (baseHue + offset) % 360;
      questionCard.style.setProperty(
        `--rb${index + 1}`,
        `hsl(${hue} 92% 58%)`
      );
    });
  }

  function updateStreakFrame(streak) {
    questionCard.classList.remove("streak5", "streak10");

    questionCard.style.borderColor = "";
    questionCard.style.borderWidth = "";
    questionCard.style.boxShadow = "";

    setRainbowForStreak(streak);

    if (streak >= 10) {
      questionCard.classList.add("streak10");
      questionCard.style.borderWidth = "8px";
      return;
    }

    if (streak >= 5) {
      questionCard.classList.add("streak5");
      questionCard.style.borderColor = "#e7aa24";
      questionCard.style.borderWidth = "6px";
      questionCard.style.boxShadow =
        "0 0 28px rgba(227,165,35,.52)";
    }
  }

  function startMode(mode) {
    currentMode = mode;
    questions = generateQuestions(mode);

    index = 0;
    score = 0;
    answers = [];
    seconds = 600;
    locked = false;
    correctStreak = 0;
    currentBgm = "0.mp3";
    lastTenBgm = null;

    menuView.classList.add("hidden");
    workspace.classList.add("show");
    questionCard.classList.remove("hidden");
    results.classList.remove("show");

    $("#statusTitle").textContent = modeInfo[mode].title;
    $("#streak").textContent = "連続正解 0";

    feedback.textContent = "";
    feedback.className = "feedback";

    updateStreakFrame(0);

    stopTimer();
    updateTimer();

    timerHandle = setInterval(() => {
      seconds -= 1;
      updateTimer();

      if (seconds <= 0) finish(true);
    }, 1000);

    playBgmForStreak(0, true);
    renderQuestion();
  }

  function renderQuestion() {
    const q = questions[index];

    if (!isValidQuestion(q)) {
      throw new Error(
        `表示禁止問題を検出: ${q.a} ${q.op} ${q.b}`
      );
    }

    $("#qCount").textContent = `${index + 1} / 20`;
    $("#score").textContent = `正解 ${score}`;
    bar.style.width = `${(index / 20) * 100}%`;

    equation.textContent = `${q.a} ${q.op} ${q.b} ＝ ?`;
    answerInput.value = "";
    feedback.textContent = "";
    feedback.className = "feedback";
    locked = false;
  }

  function submitAnswer() {
    if (locked || index >= questions.length) return;

    const raw = String(answerInput.value || "").trim();

    if (raw === "") {
      feedback.textContent = "答えを入力してください";
      feedback.className = "feedback bad";
      return;
    }

    const user = Number(raw);
    if (!Number.isFinite(user)) return;

    locked = true;

    const q = questions[index];
    const ok = user === q.answer;

    if (ok) {
      score += 1;
      correctStreak += 1;
    } else {
      correctStreak = 0;
    }

    // 正解時：「正解！○問連続正解中！」
    // 不正解時：「残念！」
    speakAnswerFeedback(ok, correctStreak);

    $("#score").textContent = `正解 ${score}`;
    $("#streak").textContent = `連続正解 ${correctStreak}`;

    updateStreakFrame(correctStreak);
    playBgmForStreak(correctStreak);

    answers.push({ q, user, ok });

    feedback.textContent = ok ? "せいかい！" : `答えは ${q.answer}`;
    feedback.className = `feedback ${ok ? "good" : "bad"}`;

    setTimeout(() => {
      index += 1;

      if (index >= questions.length) {
        finish(false);
      } else {
        renderQuestion();
      }
    }, 850);
  }

  function updateTimer() {
    const safe = Math.max(0, seconds);
    const min = Math.floor(safe / 60);
    const sec = safe % 60;

    timerEl.textContent =
      `${String(min).padStart(2, "0")}:` +
      `${String(sec).padStart(2, "0")}`;

    timerEl.classList.toggle("warn", seconds <= 60);
  }

  function stopTimer() {
    if (timerHandle) {
      clearInterval(timerHandle);
      timerHandle = null;
    }
  }

  function finish(timeup) {
    stopTimer();
    stopBgm();

    if (timeup && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }

    locked = true;

    if (timeup) {
      for (let i = index; i < questions.length; i += 1) {
        answers.push({
          q: questions[i],
          user: null,
          ok: false
        });
      }
    }

    questionCard.classList.add("hidden");
    results.classList.add("show");

    $("#resultScore").textContent = `${score} / 20`;

    $("#resultNote").textContent = timeup
      ? `10分になりました。正解は${score}問です。`
      : `20問終了。残り時間は${timerEl.textContent}、正解は${score}問です。`;

    const review = $("#review");
    review.innerHTML = "";

    answers.forEach((entry, i) => {
      const div = document.createElement("div");
      div.className = `review-item ${entry.ok ? "correct" : "wrong"}`;
      div.textContent =
        `${i + 1}. ${entry.q.a} ${entry.q.op} ${entry.q.b}` +
        ` ＝ ${entry.q.answer}｜` +
        (entry.user === null ? "未回答" : `回答 ${entry.user}`);
      review.appendChild(div);
    });
  }

  function goMenu() {
    stopTimer();
    stopBgm();

    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }

    workspace.classList.remove("show");
    menuView.classList.remove("hidden");
    results.classList.remove("show");
    questionCard.classList.remove("hidden");

    currentMode = null;
    correctStreak = 0;
    updateStreakFrame(0);
  }

  $("#keypad").addEventListener("pointerup", (event) => {
    const button = event.target.closest("button");
    if (!button || locked) return;

    const key = button.dataset.key;
    const action = button.dataset.action;

    if (key !== undefined) {
      const current = String(answerInput.value || "");

      if (current.length < 10) {
        answerInput.value =
          current === "0" ? key : current + key;
      }
      return;
    }

    if (action === "clear") {
      answerInput.value = "";
      return;
    }

    if (action === "backspace") {
      answerInput.value =
        String(answerInput.value || "").slice(0, -1);
    }
  });

  root.querySelectorAll(".start-mode").forEach((button) => {
    button.addEventListener("click", () => {
      startMode(button.dataset.mode);
    });
  });

  $("#answerForm").addEventListener("submit", (event) => {
    event.preventDefault();
    submitAnswer();
  });

  bgmBtn.addEventListener("click", toggleBgm);
  $("#quitBtn").addEventListener("click", goMenu);
  $("#menuBtn").addEventListener("click", goMenu);

  $("#retryBtn").addEventListener("click", () => {
    if (currentMode) startMode(currentMode);
  });

  updateBgmButton();
})();
</script>
</div>
"""

html = (
    HTML
    .replace("__BGM_URLS__", BGM_JSON)
    .replace("__APP_VERSION__", VERSION_JSON)
)

components.html(
    html,
    height=1600,
    scrolling=True,
)
