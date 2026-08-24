import json

import streamlit as st
import streamlit.components.v1 as components
from supabase import Client, create_client


# =========================================================
# 基本設定
# =========================================================
st.set_page_config(
    page_title="そろばん計算トレーナー",
    page_icon="🧮",
    layout="wide",
)

BUCKET_NAME = "music"
SIGNED_URL_EXPIRES_IN = 1800  # 30分。10分ゲーム＋待機時間の余裕
BGM_FILES = [
    "0.mp3",
    "1.mp3",
    "2.mp3",
    "3.mp3",
    "4.mp3",
    "5.mp3",
    "6.mp3",
    "7.mp3",
    "8.mp3",
    "9.mp3",
    "10-1.mp3",
    "10-2.mp3",
    "10-3.mp3",
]


# =========================================================
# Supabase
# =========================================================
@st.cache_resource
def get_supabase_client() -> Client:
    """Streamlit Secrets からSupabaseクライアントを作る。"""
    url = st.secrets["SUPABASE_URL"]
    service_role_key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, service_role_key)


@st.cache_data(ttl=1200, show_spinner=False)
def get_bgm_signed_urls() -> dict[str, str]:
    """
    Private Storage内のBGMに対して期限付きSigned URLを発行する。
    Service Role Keyはサーバー側だけで使い、ブラウザには渡さない。
    """
    client = get_supabase_client()
    bucket = client.storage.from_(BUCKET_NAME)

    urls: dict[str, str] = {}
    for filename in BGM_FILES:
        response = bucket.create_signed_url(
            filename,
            SIGNED_URL_EXPIRES_IN,
        )

        signed_url = None
        if isinstance(response, dict):
            signed_url = (
                response.get("signedUrl")
                or response.get("signedURL")
                or response.get("signed_url")
            )
        else:
            signed_url = (
                getattr(response, "signedUrl", None)
                or getattr(response, "signedURL", None)
                or getattr(response, "signed_url", None)
            )

        if not signed_url:
            raise RuntimeError(f"{filename} のSigned URLを取得できませんでした。")

        urls[filename] = signed_url

    return urls


# =========================================================
# 設定確認
# =========================================================
try:
    bgm_urls = get_bgm_signed_urls()
except KeyError:
    st.error(
        "Streamlit Secrets に SUPABASE_URL と "
        "SUPABASE_SERVICE_ROLE_KEY が設定されていません。"
    )
    st.code(
        'SUPABASE_URL = "https://xxxxxxxxxxxx.supabase.co"\n'
        'SUPABASE_SERVICE_ROLE_KEY = "ここにService Role Key"',
        language="toml",
    )
    st.stop()
except Exception as exc:
    st.error("Supabase Storage のBGMを読み込めませんでした。")
    st.caption(str(exc))
    st.info(
        "Supabase Storage の Private Bucket「music」に "
        "0.mp3〜9.mp3、10-1.mp3〜10-3.mp3 があるか確認してください。"
    )
    st.stop()


# =========================================================
# ゲーム本体
# =========================================================
BGM_URLS_JSON = json.dumps(bgm_urls, ensure_ascii=False)

HTML_TEMPLATE = r"""
<div id="soro-app">
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #f7f5ef;
      color: #24231f;
      font-family: system-ui, -apple-system, "Hiragino Sans", "Yu Gothic", sans-serif;
    }
    #soro-app {
      padding: 20px;
      max-width: 1200px;
      margin: 0 auto;
    }
    button, input { font: inherit; }
    button {
      min-height: 44px;
      border: 0;
      border-radius: 12px;
      padding: 10px 15px;
      font-weight: 750;
      cursor: pointer;
      background: #e7e2d7;
      color: #24231f;
    }
    button.primary {
      background: #315f86;
      color: #fff;
    }
    button:disabled {
      opacity: .45;
      cursor: not-allowed;
    }
    .intro {
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: end;
      margin-bottom: 18px;
    }
    .lead {
      max-width: 800px;
      font-size: 14px;
      line-height: 1.75;
      color: #66635d;
    }
    .badge {
      white-space: nowrap;
      border: 1px solid #d6d0c3;
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 13px;
      font-weight: 800;
    }
    .level {
      margin: 22px 0 10px;
      font-size: 20px;
      font-weight: 850;
    }
    .mode-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }
    .mode {
      background: #fff;
      border: 1px solid #ddd7ca;
      border-radius: 18px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      min-height: 180px;
    }
    .mode-number {
      font-size: 12px;
      font-weight: 850;
      letter-spacing: .08em;
      color: #817b70;
    }
    .mode-title {
      font-size: 18px;
      font-weight: 850;
      line-height: 1.4;
      margin: 6px 0 8px;
    }
    .mode-desc {
      font-size: 13px;
      line-height: 1.65;
      color: #66635d;
      flex: 1;
    }
    .mode-meta {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin: 11px 0;
    }
    .chip {
      font-size: 12px;
      font-weight: 750;
      background: #f2eee5;
      border-radius: 999px;
      padding: 5px 8px;
    }
    .workspace {
      display: none;
      margin-top: 12px;
    }
    .workspace.show { display: block; }
    .statusbar {
      display: grid;
      grid-template-columns: minmax(200px, 1fr) auto auto auto auto;
      gap: 12px;
      align-items: center;
      background: #fff;
      border: 1px solid #ddd7ca;
      border-radius: 18px;
      padding: 14px 16px;
    }
    .status-title {
      font-size: 16px;
      font-weight: 850;
    }
    .status-sub {
      font-size: 12px;
      color: #706c64;
      margin-top: 3px;
    }
    .timer {
      font-variant-numeric: tabular-nums;
      font-size: 25px;
      font-weight: 900;
      min-width: 88px;
      text-align: center;
    }
    .timer.warn { color: #a14428; }
    .streak {
      font-size: 14px;
      font-weight: 850;
      white-space: nowrap;
    }
    .bgm-name {
      grid-column: 1 / -1;
      font-size: 12px;
      color: #706c64;
      min-height: 18px;
    }
    .question-card {
      margin-top: 14px;
      background: #fff;
      border: 1px solid #ddd7ca;
      border-radius: 22px;
      padding: 24px;
    }
    .qtop {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }
    .qcount, .score {
      font-size: 13px;
      font-weight: 800;
    }
    .qcount { color: #706c64; }
    .equation {
      text-align: center;
      font-size: clamp(36px, 7vw, 64px);
      font-weight: 900;
      letter-spacing: .02em;
      margin: 30px 0;
    }
    .answer-form {
      display: flex;
      justify-content: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .answer-input {
      width: min(280px, 100%);
      min-height: 62px;
      border: 2px solid #c8c1b4;
      border-radius: 14px;
      background: #fff;
      color: #24231f;
      text-align: center;
      font-size: 30px;
      font-weight: 850;
      padding: 8px 12px;
    }
    .feedback {
      text-align: center;
      min-height: 34px;
      margin-top: 14px;
      font-size: 20px;
      font-weight: 850;
    }
    .feedback.good { color: #28704a; }
    .feedback.bad { color: #a14428; }
    .progress {
      height: 8px;
      background: #e7e2d9;
      border-radius: 999px;
      overflow: hidden;
      margin-top: 18px;
    }
    .bar {
      height: 100%;
      width: 0;
      background: #6d815d;
      transition: width .25s ease;
    }
    .results {
      display: none;
      margin-top: 14px;
      background: #fff;
      border: 1px solid #ddd7ca;
      border-radius: 22px;
      padding: 24px;
    }
    .results.show { display: block; }
    .result-score {
      text-align: center;
      font-size: 46px;
      font-weight: 900;
      margin: 8px 0;
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
      border-radius: 12px;
      padding: 10px 12px;
      background: #f3efe7;
      font-size: 13px;
      line-height: 1.5;
    }
    .review-item.wrong { border-left: 4px solid #a44b32; }
    .review-item.correct { border-left: 4px solid #437454; }
    .actions {
      display: flex;
      justify-content: center;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 18px;
    }
    .hidden { display: none !important; }

    @media (max-width: 760px) {
      #soro-app { padding: 12px; }
      .intro {
        align-items: flex-start;
        flex-direction: column;
      }
      .mode-grid { grid-template-columns: 1fr; }
      .mode { min-height: 0; }
      .statusbar {
        grid-template-columns: 1fr auto;
      }
      .statusbar > button { grid-column: auto; }
      #quitBtn { grid-column: 1 / -1; }
      .review { grid-template-columns: 1fr; }
    }
  </style>

  <div id="menuView">
    <div class="intro">
      <div class="lead">
        各モード20問です。開始すると10分のカウントダウンが始まります。
        正解が続くほどBGMが0→1→…→9→10-Xへ進み、不正解になると0へ戻ります。
      </div>
      <div class="badge">20問 / 10分</div>
    </div>

    <div class="level">初級モード</div>
    <div class="mode-grid">
      <article class="mode">
        <div class="mode-number">BEGINNER 1</div>
        <div class="mode-title">1桁の足し算・引き算</div>
        <div class="mode-desc">0〜9の数を使う加減算。引き算の答えは0以上です。</div>
        <div class="mode-meta"><span class="chip">20問</span><span class="chip">10分</span></div>
        <button type="button" class="primary start-mode" data-mode="b1">はじめる</button>
      </article>
      <article class="mode">
        <div class="mode-number">BEGINNER 2</div>
        <div class="mode-title">2桁の足し算・引き算</div>
        <div class="mode-desc">10〜99の数を使う加減算。繰り上がり・繰り下がりも含みます。</div>
        <div class="mode-meta"><span class="chip">20問</span><span class="chip">10分</span></div>
        <button type="button" class="primary start-mode" data-mode="b2">はじめる</button>
      </article>
      <article class="mode">
        <div class="mode-number">BEGINNER 3</div>
        <div class="mode-title">3桁の足し算・引き算</div>
        <div class="mode-desc">100〜999の数を使う加減算。答えが0未満になる問題は出しません。</div>
        <div class="mode-meta"><span class="chip">20問</span><span class="chip">10分</span></div>
        <button type="button" class="primary start-mode" data-mode="b3">はじめる</button>
      </article>
    </div>

    <div class="level">中級モード</div>
    <div class="mode-grid">
      <article class="mode">
        <div class="mode-number">INTERMEDIATE 1</div>
        <div class="mode-title">1桁の掛け算・割り算</div>
        <div class="mode-desc">1〜9同士の掛け算と、1桁の数で割って整数になる割り算です。</div>
        <div class="mode-meta"><span class="chip">20問</span><span class="chip">10分</span></div>
        <button type="button" class="primary start-mode" data-mode="m1">はじめる</button>
      </article>
      <article class="mode">
        <div class="mode-number">INTERMEDIATE 2</div>
        <div class="mode-title">2桁×1桁 / 3桁÷1桁</div>
        <div class="mode-desc">2桁×1桁の掛け算と、3桁÷1桁で整数になる割り算です。</div>
        <div class="mode-meta"><span class="chip">20問</span><span class="chip">10分</span></div>
        <button type="button" class="primary start-mode" data-mode="m2">はじめる</button>
      </article>
      <article class="mode">
        <div class="mode-number">INTERMEDIATE 3</div>
        <div class="mode-title">2桁×2桁 / 3桁÷2桁</div>
        <div class="mode-desc">2桁同士の掛け算と、3桁÷2桁で整数になる割り算です。</div>
        <div class="mode-meta"><span class="chip">20問</span><span class="chip">10分</span></div>
        <button type="button" class="primary start-mode" data-mode="m3">はじめる</button>
      </article>
    </div>

    <div class="level">上級モード</div>
    <div class="mode-grid">
      <article class="mode">
        <div class="mode-number">ADVANCED 1</div>
        <div class="mode-title">4桁の足し算・引き算</div>
        <div class="mode-desc">1000〜9999の数を使う加減算。引き算の答えは0以上です。</div>
        <div class="mode-meta"><span class="chip">20問</span><span class="chip">10分</span></div>
        <button type="button" class="primary start-mode" data-mode="a1">はじめる</button>
      </article>
      <article class="mode">
        <div class="mode-number">ADVANCED 2</div>
        <div class="mode-title">3桁×2桁 / 4桁÷2桁</div>
        <div class="mode-desc">3桁×2桁の掛け算と、4桁÷2桁で整数になる割り算です。</div>
        <div class="mode-meta"><span class="chip">20問</span><span class="chip">10分</span></div>
        <button type="button" class="primary start-mode" data-mode="a2">はじめる</button>
      </article>
      <article class="mode">
        <div class="mode-number">ADVANCED 3</div>
        <div class="mode-title">3桁×3桁 / 5桁÷3桁</div>
        <div class="mode-desc">3桁同士の掛け算と、5桁÷3桁で整数になる割り算です。</div>
        <div class="mode-meta"><span class="chip">20問</span><span class="chip">10分</span></div>
        <button type="button" class="primary start-mode" data-mode="a3">はじめる</button>
      </article>
    </div>
  </div>

  <section id="workspace" class="workspace" aria-live="polite">
    <div class="statusbar">
      <div>
        <div id="statusTitle" class="status-title"></div>
        <div class="status-sub">20問・制限時間10分</div>
      </div>
      <div id="timer" class="timer">10:00</div>
      <div id="streak" class="streak">連続正解 0</div>
      <button type="button" id="bgmBtn" aria-pressed="true">♪ BGM ON</button>
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
          type="number"
          inputmode="numeric"
          autocomplete="off"
          aria-label="答え"
          placeholder="答え"
        >
        <button type="submit" class="primary">答える</button>
      </form>
      <div id="feedback" class="feedback"></div>
      <div class="progress"><div id="bar" class="bar"></div></div>
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
    const BGM_URLS = __BGM_URLS__;

    const root = document.getElementById("soro-app");
    const $ = (selector) => root.querySelector(selector);

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
      b1: { title: "初級1｜1桁の足し算・引き算" },
      b2: { title: "初級2｜2桁の足し算・引き算" },
      b3: { title: "初級3｜3桁の足し算・引き算" },
      m1: { title: "中級1｜1桁の掛け算・割り算" },
      m2: { title: "中級2｜2桁×1桁 / 3桁÷1桁" },
      m3: { title: "中級3｜2桁×2桁 / 3桁÷2桁" },
      a1: { title: "上級1｜4桁の足し算・引き算" },
      a2: { title: "上級2｜3桁×2桁 / 4桁÷2桁" },
      a3: { title: "上級3｜3桁×3桁 / 5桁÷3桁" }
    };

    let currentMode = null;
    let questions = [];
    let index = 0;
    let score = 0;
    let answers = [];
    let seconds = 600;
    let tick = null;
    let locked = false;
    let correctStreak = 0;
    let bgmOn = true;
    let currentBgmName = "0.mp3";
    let currentTenTrack = null;

    const audio = new Audio();
    audio.loop = true;
    audio.volume = 0.12;
    audio.preload = "auto";

    const rand = (min, max) =>
      Math.floor(Math.random() * (max - min + 1)) + min;

    const chance = () => Math.random() < 0.5;

    const make = (a, op, b) => ({
      a,
      op,
      b,
      answer:
        op === "＋" ? a + b :
        op === "－" ? a - b :
        op === "×" ? a * b :
        a / b
    });

    function addSub(min, max) {
      let a = rand(min, max);
      let b = rand(min, max);
      const op = chance() ? "＋" : "－";

      if (op === "－" && b > a) {
        [a, b] = [b, a];
      }
      return make(a, op, b);
    }

    function mul(aMin, aMax, bMin, bMax) {
      return make(
        rand(aMin, aMax),
        "×",
        rand(bMin, bMax)
      );
    }

    function exactDiv(nMin, nMax, dMin, dMax) {
      for (let tries = 0; tries < 500; tries += 1) {
        const divisor = rand(dMin, dMax);
        const qMin = Math.max(1, Math.ceil(nMin / divisor));
        const qMax = Math.floor(nMax / divisor);

        if (qMin <= qMax) {
          const quotient = rand(qMin, qMax);
          return make(divisor * quotient, "÷", divisor);
        }
      }

      const divisor = dMin;
      const quotient = Math.ceil(nMin / divisor);
      return make(divisor * quotient, "÷", divisor);
    }

    function generate(mode) {
      const out = [];

      for (let i = 0; i < 20; i += 1) {
        let q;

        if (mode === "b1") {
          q = addSub(0, 9);
        } else if (mode === "b2") {
          q = addSub(10, 99);
        } else if (mode === "b3") {
          q = addSub(100, 999);
        } else if (mode === "m1") {
          q = chance()
            ? mul(1, 9, 1, 9)
            : exactDiv(1, 81, 1, 9);
        } else if (mode === "m2") {
          q = chance()
            ? mul(10, 99, 1, 9)
            : exactDiv(100, 999, 1, 9);
        } else if (mode === "m3") {
          q = chance()
            ? mul(10, 99, 10, 99)
            : exactDiv(100, 999, 10, 99);
        } else if (mode === "a1") {
          q = addSub(1000, 9999);
        } else if (mode === "a2") {
          q = chance()
            ? mul(100, 999, 10, 99)
            : exactDiv(1000, 9999, 10, 99);
        } else {
          q = chance()
            ? mul(100, 999, 100, 999)
            : exactDiv(10000, 99999, 100, 999);
        }

        out.push(q);
      }

      return out;
    }

    function desiredBgmName(streak) {
      if (streak <= 0) {
        currentTenTrack = null;
        return "0.mp3";
      }

      if (streak <= 9) {
        currentTenTrack = null;
        return `${streak}.mp3`;
      }

      const pool = ["10-1.mp3", "10-2.mp3", "10-3.mp3"];
      let choices = pool;

      if (currentTenTrack) {
        const alternatives = pool.filter((name) => name !== currentTenTrack);
        if (alternatives.length) choices = alternatives;
      }

      currentTenTrack =
        choices[Math.floor(Math.random() * choices.length)];

      return currentTenTrack;
    }

    function updateBgmButton() {
      bgmBtn.textContent = bgmOn ? "♪ BGM ON" : "♪ BGM OFF";
      bgmBtn.setAttribute("aria-pressed", String(bgmOn));
    }

    function playBgmForStreak(streak, force = false) {
      const name = desiredBgmName(streak);

      if (!force && name === currentBgmName && !audio.paused) {
        return;
      }

      currentBgmName = name;
      bgmName.textContent = `BGM：${name}`;

      const url = BGM_URLS[name];
      if (!url) {
        bgmName.textContent = `BGM：${name}（読み込み失敗）`;
        return;
      }

      audio.pause();
      audio.src = url;
      audio.currentTime = 0;
      audio.loop = true;
      audio.volume = 0.12;

      if (bgmOn) {
        const promise = audio.play();
        if (promise && typeof promise.catch === "function") {
          promise.catch(() => {
            bgmName.textContent =
              `BGM：${name}（再生ボタンを一度押してください）`;
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

      if (bgmOn &&
          workspace.classList.contains("show") &&
          !results.classList.contains("show")) {
        playBgmForStreak(correctStreak, true);
      } else {
        stopBgm();
      }
    }

    function startMode(mode) {
      currentMode = mode;
      questions = generate(mode);
      index = 0;
      score = 0;
      answers = [];
      seconds = 600;
      locked = false;
      correctStreak = 0;
      currentBgmName = "0.mp3";
      currentTenTrack = null;

      menuView.classList.add("hidden");
      workspace.classList.add("show");
      questionCard.classList.remove("hidden");
      results.classList.remove("show");

      $("#statusTitle").textContent = modeInfo[mode].title;
      $("#streak").textContent = "連続正解 0";

      feedback.textContent = "";
      feedback.className = "feedback";

      stopTimer();
      updateTimer();

      tick = setInterval(() => {
        seconds -= 1;
        updateTimer();

        if (seconds <= 0) {
          finish(true);
        }
      }, 1000);

      playBgmForStreak(0, true);
      renderQuestion();
    }

    function renderQuestion() {
      const q = questions[index];

      $("#qCount").textContent = `${index + 1} / 20`;
      $("#score").textContent = `正解 ${score}`;
      bar.style.width = `${(index / 20) * 100}%`;

      equation.textContent = `${q.a} ${q.op} ${q.b} ＝ ?`;
      answerInput.value = "";
      feedback.textContent = "";
      feedback.className = "feedback";
      locked = false;

      setTimeout(() => answerInput.focus(), 0);
    }

    function submitAnswer() {
      if (locked || index >= questions.length) return;

      const raw = answerInput.value.trim();

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

      $("#streak").textContent = `連続正解 ${correctStreak}`;
      playBgmForStreak(correctStreak);

      answers.push({ q, user, ok });

      feedback.textContent = ok
        ? "せいかい！"
        : `答えは ${q.answer}`;

      feedback.className = `feedback ${ok ? "good" : "bad"}`;
      $("#score").textContent = `正解 ${score}`;

      setTimeout(() => {
        index += 1;

        if (index >= questions.length) {
          finish(false);
        } else {
          renderQuestion();
        }
      }, 650);
    }

    function updateTimer() {
      const safeSeconds = Math.max(0, seconds);
      const m = Math.floor(safeSeconds / 60);
      const s = safeSeconds % 60;

      timerEl.textContent =
        `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;

      timerEl.classList.toggle("warn", seconds <= 60);
    }

    function stopTimer() {
      if (tick) {
        clearInterval(tick);
        tick = null;
      }
    }

    function finish(timeup) {
      if (!workspace.classList.contains("show")) return;

      stopTimer();
      stopBgm();
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
      bar.style.width = "100%";

      $("#resultScore").textContent = `${score} / 20`;

      $("#resultNote").textContent = timeup
        ? `10分になりました。正解は${score}問です。`
        : `20問終了。残り時間は${timerEl.textContent}、正解は${score}問です。`;

      const review = $("#review");
      review.innerHTML = "";

      answers.forEach((answer, i) => {
        const div = document.createElement("div");
        div.className =
          `review-item ${answer.ok ? "correct" : "wrong"}`;

        div.textContent =
          `${i + 1}. ${answer.q.a} ${answer.q.op} ${answer.q.b}` +
          ` ＝ ${answer.q.answer}｜` +
          (answer.user === null
            ? "未回答"
            : `回答 ${answer.user}`);

        review.appendChild(div);
      });
    }

    function goMenu() {
      stopTimer();
      stopBgm();

      workspace.classList.remove("show");
      menuView.classList.remove("hidden");
      results.classList.remove("show");
      questionCard.classList.remove("hidden");

      currentMode = null;
    }

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

html = HTML_TEMPLATE.replace("__BGM_URLS__", BGM_URLS_JSON)

components.html(
    html,
    height=1450,
    scrolling=True,
)
