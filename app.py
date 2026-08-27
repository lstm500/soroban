# VERSION: CLEAN-V43-LEARNING-MODE-2026-08-28

import json

import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client


st.set_page_config(
    page_title="そろばん計算トレーナー",
    page_icon="🧮",
    layout="wide",
)

APP_VERSION = "CLEAN-V43-LEARNING-MODE"
BUCKET_NAME = "music"
SIGNED_URL_EXPIRES_IN = 3600

BGM_FILES = [
    "1.mp3", "2.mp3", "3.mp3",
    "4.mp3", "5.mp3", "6.mp3",
    "7.mp3", "8.mp3", "9.mp3",
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


st.caption(f"APP VERSION: {APP_VERSION}")


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

  /* =====================================================
     APP TOP
     ===================================================== */
  .app-home {
    padding: 22px 0 12px;
  }

  .home-title {
    margin: 6px 0 8px;
    text-align: center;
    font-size: clamp(26px, 5vw, 42px);
    font-weight: 1000;
    letter-spacing: .02em;
  }

  .home-sub {
    margin: 0 auto 22px;
    max-width: 760px;
    text-align: center;
    color: #6d675f;
    font-size: 14px;
    line-height: 1.7;
  }

  .home-mode-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }

  .home-mode-btn {
    min-height: 168px;
    padding: 22px 18px;
    border: 2px solid #d6cfc2;
    border-radius: 22px;
    background: #fff;
    text-align: left;
    box-shadow: 0 8px 24px rgba(60, 50, 40, .07);
  }

  .home-mode-btn.primary-home {
    background: #315f86;
    color: #fff;
    border-color: #315f86;
  }

  .home-mode-kicker {
    display: block;
    margin-bottom: 10px;
    font-size: 11px;
    font-weight: 950;
    letter-spacing: .1em;
    opacity: .72;
  }

  .home-mode-name {
    display: block;
    margin-bottom: 9px;
    font-size: clamp(22px, 4vw, 32px);
    font-weight: 1000;
  }

  .home-mode-desc {
    display: block;
    font-size: 13px;
    line-height: 1.6;
    opacity: .86;
  }

  .subview-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin: 0 0 14px;
  }

  .subview-topbar-title {
    font-size: 14px;
    font-weight: 950;
    color: #5f5951;
  }

  .top-back-btn {
    min-height: 38px;
    padding: 7px 11px;
    font-size: 12px;
    background: #eee9df;
  }

  /* =====================================================
     LEARNING MODE
     ===================================================== */
  .learning-view {
    display: none;
  }

  .learning-view.show {
    display: block;
  }

  .learning-hero {
    padding: 18px 18px 16px;
    border: 1px solid #dcd5c8;
    border-radius: 20px;
    background: #fff;
  }

  .learning-hero h2 {
    margin: 0 0 6px;
    font-size: clamp(24px, 4vw, 34px);
  }

  .learning-hero p {
    margin: 0;
    color: #6b655d;
    line-height: 1.7;
    font-size: 13px;
  }

  .learning-progress-summary {
    margin-top: 12px;
    font-size: 12px;
    font-weight: 850;
    color: #5d574f;
  }

  .learning-progress-track {
    height: 10px;
    margin-top: 7px;
    overflow: hidden;
    border-radius: 999px;
    background: #ebe6dd;
  }

  .learning-progress-bar {
    width: 0%;
    height: 100%;
    border-radius: inherit;
    background: #5d8c62;
    transition: width .3s ease;
  }

  .learning-category-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
    margin-top: 16px;
  }

  .learning-category-card {
    display: flex;
    flex-direction: column;
    min-height: 208px;
    padding: 18px;
    border: 1px solid #ddd7ca;
    border-radius: 20px;
    background: #fff;
  }

  .learning-category-symbol {
    font-size: 34px;
    font-weight: 1000;
    line-height: 1;
  }

  .learning-category-title {
    margin: 10px 0 5px;
    font-size: 21px;
    font-weight: 1000;
  }

  .learning-category-desc {
    flex: 1;
    color: #6b655d;
    font-size: 13px;
    line-height: 1.6;
  }

  .learning-stars {
    margin: 10px 0;
    font-size: 14px;
    font-weight: 950;
    letter-spacing: .06em;
    color: #7e6c35;
  }

  .learning-stage-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin-top: 14px;
  }

  .learning-stage-card {
    position: relative;
    min-height: 154px;
    padding: 16px;
    border: 1px solid #ddd7ca;
    border-radius: 18px;
    background: #fff;
  }

  .learning-stage-card.locked {
    opacity: .53;
    background: #f1eee8;
  }

  .learning-stage-card.cleared {
    border-color: #a8c4a7;
    background: #f7fbf5;
  }

  .learning-stage-no {
    font-size: 11px;
    font-weight: 950;
    letter-spacing: .08em;
    color: #8a8277;
  }

  .learning-stage-title {
    margin: 6px 0 5px;
    font-size: 17px;
    font-weight: 950;
  }

  .learning-stage-desc {
    min-height: 38px;
    color: #6d675f;
    font-size: 12px;
    line-height: 1.55;
  }

  .learning-stage-status {
    margin-top: 8px;
    font-size: 12px;
    font-weight: 900;
  }

  .learning-stage-card button {
    width: 100%;
    margin-top: 10px;
    min-height: 40px;
    padding: 7px 10px;
  }

  .learning-lesson-head {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 12px;
    align-items: center;
    margin: 4px 0 14px;
  }

  .learning-lesson-kicker {
    font-size: 11px;
    font-weight: 950;
    color: #81796f;
    letter-spacing: .08em;
  }

  .learning-lesson-title {
    margin-top: 4px;
    font-size: clamp(22px, 4vw, 30px);
    font-weight: 1000;
  }

  .learning-video-card,
  .learning-explain-card,
  .learning-quiz-card {
    margin-top: 12px;
    padding: 16px;
    border: 1px solid #ddd7ca;
    border-radius: 20px;
    background: #fff;
  }

  .learning-video-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 10px;
    font-size: 15px;
    font-weight: 950;
  }

  .learning-video-badge {
    padding: 5px 8px;
    border-radius: 999px;
    background: #e8f0e2;
    color: #355635;
    font-size: 11px;
    font-weight: 900;
  }

  .learning-step-text {
    min-height: 52px;
    margin: 8px 0 10px;
    text-align: center;
    font-size: 16px;
    line-height: 1.6;
    font-weight: 900;
    color: #4b463f;
  }

  .learning-frame-counter {
    text-align: center;
    font-size: 11px;
    color: #847c72;
  }

  .learning-video-controls {
    display: flex;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 10px;
  }

  .learning-video-controls button {
    min-height: 38px;
    padding: 7px 11px;
    font-size: 12px;
  }

  .learning-soroban-wrap {
    overflow-x: auto;
    padding: 4px 2px 8px;
  }

  .learning-soroban-board {
    --rod-width: 64px;
    position: relative;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    gap: 5px;
    min-width: max-content;
    padding: 12px 14px 8px;
    border: 5px solid #73543a;
    border-radius: 14px;
    background: #e8c895;
    box-shadow:
      inset 0 0 0 2px rgba(255,255,255,.35),
      0 6px 15px rgba(72, 54, 37, .12);
  }

  .learning-soroban-board::before {
    content: "";
    position: absolute;
    left: 7px;
    right: 7px;
    top: 78px;
    height: 8px;
    border-radius: 5px;
    background: #66452f;
    z-index: 3;
  }

  .learning-point-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }

  .learning-point {
    padding: 12px;
    border-radius: 14px;
    background: #f7f4ee;
  }

  .learning-point.trouble {
    background: #fff6df;
  }

  .learning-point-label {
    margin-bottom: 5px;
    font-size: 12px;
    font-weight: 950;
  }

  .learning-point-text {
    color: #5f5951;
    font-size: 13px;
    line-height: 1.65;
  }

  .learning-rule-box {
    margin-top: 10px;
    padding: 12px 14px;
    border-left: 5px solid #6f936c;
    border-radius: 10px;
    background: #f3f8f1;
    font-size: 14px;
    font-weight: 900;
    line-height: 1.65;
  }

  .learning-quiz-question {
    margin-bottom: 10px;
    font-size: 16px;
    font-weight: 950;
    line-height: 1.55;
  }

  .learning-quiz-options {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .learning-quiz-option {
    min-height: 54px;
    font-size: 16px;
  }

  .learning-quiz-option.correct-choice {
    background: #dff1e3;
    color: #285a36;
  }

  .learning-quiz-option.wrong-choice {
    background: #f4ded8;
    color: #8a3d28;
  }

  .learning-quiz-feedback {
    min-height: 34px;
    margin-top: 10px;
    text-align: center;
    font-size: 15px;
    font-weight: 950;
  }

  .learning-clear-actions {
    display: none;
    gap: 8px;
    margin-top: 10px;
  }

  .learning-clear-actions.show {
    display: flex;
  }

  .learning-clear-actions button {
    flex: 1;
  }

  @media (max-width: 640px) {
    .home-mode-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }

    .home-mode-btn {
      min-height: 148px;
      padding: 14px 10px;
    }

    .home-mode-name {
      font-size: 20px;
    }

    .home-mode-desc {
      font-size: 11px;
    }

    .learning-category-grid,
    .learning-stage-grid,
    .learning-point-grid {
      grid-template-columns: 1fr;
    }

    .learning-quiz-options {
      grid-template-columns: 1fr;
    }
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

  .time-limit-control {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 10px;
    flex-wrap: wrap;
    margin: 10px 0 20px;
  }

  .time-limit-label {
    color: #66635d;
    font-size: 13px;
    font-weight: 850;
  }

  .time-limit-toggle {
    min-height: 42px;
    padding: 8px 14px;
    border-radius: 999px;
    border: 1px solid #cfc7b9;
    background: #fff;
    color: #2e2b27;
    font-size: 13px;
    font-weight: 900;
  }

  .time-limit-toggle.off {
    background: #ece8df;
    color: #56504a;
  }

  #soroban-app.untimed-mode .ranking-open-btn {
    display: none;
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
    grid-template-columns: minmax(200px, 1fr) auto auto auto auto auto;
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

  .voice-btn.on {
    background: #dff1e3;
    color: #285a36;
    border: 1px solid #a9cfb3;
  }

  .voice-status {
    grid-column: 1 / -1;
    font-size: 12px;
    color: #706c64;
  }

  .voice-status.listening {
    color: #2f6a43;
    font-weight: 900;
  }

  .bgm-name {
    grid-column: 1 / -1;
    font-size: 12px;
    color: #706c64;
  }

  .question-card.voice-waiting .qtop,
  .question-card.voice-waiting .equation,
  .question-card.voice-waiting .hint-launch,
  .question-card.voice-waiting .abacus-hint,
  .question-card.voice-waiting .answer-form,
  .question-card.voice-waiting .keypad,
  .question-card.voice-waiting .feedback {
    visibility: hidden !important;
  }

  .question-card.voice-waiting::after {
    content: "ゴワサン！";
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    font-size: clamp(34px, 7vw, 64px);
    font-weight: 1000;
    letter-spacing: .08em;
    color: #5c5144;
    pointer-events: none;
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

  .question-card.streak6,
  .question-card.streak10 {
    border: 7px solid transparent !important;
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
    animation: rainbowBorder 2.2s linear infinite;
  }

  .question-card.streak6 {
    box-shadow: none !important;
  }

  .question-card.streak10 {
    box-shadow: none;
  }

  /* 10問連続正解以上：
     レインボー枠は常時、発光は新しい問題が出た瞬間だけ。 */
  .question-card.streak10.question-flash {
    animation:
      rainbowBorder 2.2s linear infinite;
  }

  .question-card.streak10.question-flash::before {
    content: "";
    position: absolute;
    inset: -14px;
    border-radius: 32px;
    pointer-events: none;
    z-index: 20;
    opacity: 0;
    border: 6px solid rgba(255,255,255,.94);
    box-shadow:
      0 0 18px 7px rgba(255, 214, 10, .75),
      0 0 38px 15px rgba(255, 59, 48, .58),
      0 0 62px 22px rgba(10, 132, 255, .46),
      inset 0 0 22px rgba(191, 90, 242, .42);
    animation:
      questionFlashHalo 1.15s cubic-bezier(.16,.8,.25,1);
  }

  @keyframes rainbowBorder {
    from { background-position: 0 0, 0% 50%; }
    to   { background-position: 0 0, 300% 50%; }
  }

  @keyframes questionFlashHalo {
    0% {
      opacity: 0;
      transform: scale(.975);
    }
    16% {
      opacity: 1;
      transform: scale(1.015);
    }
    42% {
      opacity: .95;
      transform: scale(1.025);
    }
    100% {
      opacity: 0;
      transform: scale(1.045);
    }
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

  .weak-badge {
    display: none;
    margin-left: 8px;
    padding: 5px 9px;
    border-radius: 999px;
    background: #fff1c9;
    color: #805b00;
    font-size: 12px;
    font-weight: 900;
  }

  .weak-badge.show {
    display: inline-block;
  }

  .equation {
    margin: 38px 0 22px;
    text-align: center;
    font-size: clamp(42px, 7vw, 68px);
    font-weight: 950;
    letter-spacing: .03em;
  }

  .hint-launch {
    display: flex;
    justify-content: center;
    margin: -4px 0 14px;
  }

  .hint-btn {
    background: #e8f0e2;
    color: #345233;
    border: 1px solid #c9d8c0;
  }

  .abacus-hint {
    display: none;
    width: min(760px, 100%);
    margin: 0 auto 18px;
    padding: 14px;
    border: 2px solid #d7c69e;
    border-radius: 18px;
    background: #fffaf0;
  }

  .abacus-hint.show {
    display: block;
    animation: hintOpen .22s ease-out;
  }

  @keyframes hintOpen {
    from {
      opacity: 0;
      transform: translateY(-6px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .hint-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
  }

  .hint-title {
    font-size: 15px;
    font-weight: 950;
  }

  .hint-step {
    min-height: 42px;
    margin: 8px 0 10px;
    text-align: center;
    font-size: 16px;
    font-weight: 900;
    line-height: 1.55;
    color: #4c473e;
  }

  .hint-actions {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }

  .hint-actions button {
    min-height: 36px;
    padding: 7px 10px;
    font-size: 12px;
  }

  .soroban-scroll {
    overflow-x: auto;
    padding: 4px 2px 8px;
  }

  .soroban-board {
    --rod-width: 64px;
    position: relative;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    gap: 5px;
    min-width: max-content;
    padding: 12px 14px 8px;
    border: 5px solid #73543a;
    border-radius: 14px;
    background: #e8c895;
    box-shadow:
      inset 0 0 0 2px rgba(255,255,255,.35),
      0 6px 15px rgba(72, 54, 37, .12);
  }

  .soroban-board::before {
    content: "";
    position: absolute;
    left: 7px;
    right: 7px;
    top: 78px;
    height: 8px;
    border-radius: 5px;
    background: #66452f;
    z-index: 3;
  }

  .soroban-rod {
    position: relative;
    width: var(--rod-width);
    height: 202px;
    border-radius: 12px;
    transition:
      background .25s ease,
      box-shadow .25s ease;
  }

  .soroban-rod.active {
    background: rgba(255, 238, 155, .58);
    box-shadow:
      inset 0 0 0 2px rgba(236, 175, 37, .78),
      0 0 16px rgba(236, 175, 37, .38);
  }

  .rod-line {
    position: absolute;
    left: 50%;
    top: 5px;
    bottom: 30px;
    width: 3px;
    transform: translateX(-50%);
    border-radius: 2px;
    background: #6b4b33;
    z-index: 1;
  }

  .soroban-bead {
    position: absolute;
    left: 50%;
    width: 48px;
    height: 16px;
    transform: translateX(-50%);
    border: 2px solid #8d4929;
    border-radius: 50% 50% 44% 44%;
    background:
      linear-gradient(
        180deg,
        #ef9b5c 0%,
        #c86735 54%,
        #a84d27 100%
      );
    box-shadow:
      inset 0 2px 2px rgba(255,255,255,.38),
      0 2px 3px rgba(77,40,21,.24);
    z-index: 4;
    transition:
      top .58s cubic-bezier(.22,.8,.24,1),
      filter .22s ease,
      transform .22s ease;
  }

  .soroban-rod.active .soroban-bead {
    filter: saturate(1.14) brightness(1.04);
  }

  .upper-bead {
    top: 13px;
  }

  .lower-bead {
    top: 112px;
  }

  .rod-place {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 5px;
    text-align: center;
    font-size: 12px;
    font-weight: 950;
    color: #604a39;
  }

  .hint-legend {
    margin-top: 8px;
    text-align: center;
    font-size: 11px;
    line-height: 1.5;
    color: #71695f;
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

  .score-stage {
    position: relative;
    overflow: hidden;
    margin: 10px auto 14px;
    padding: 22px 12px 18px;
    border: 2px solid #e1d6bf;
    border-radius: 22px;
    background:
      radial-gradient(circle at 50% 20%, #fff8d4 0, #fff 56%);
    text-align: center;
  }

  .score-caption {
    margin-bottom: 4px;
    font-size: 14px;
    font-weight: 900;
    color: #74654e;
  }

  .result-score {
    min-height: 74px;
    margin: 6px 0;
    text-align: center;
    font-size: clamp(54px, 10vw, 88px);
    line-height: 1;
    font-weight: 1000;
    letter-spacing: .02em;
    font-variant-numeric: tabular-nums;
    transform-origin: center;
  }

  .result-score.roulette {
    animation: scoreRoulette .16s linear infinite;
    filter: blur(.35px);
  }

  .result-score.reveal {
    animation: scoreReveal .85s cubic-bezier(.18,.9,.2,1.25);
    text-shadow:
      0 3px 0 rgba(255,255,255,.9),
      0 0 18px rgba(255, 189, 35, .55),
      0 0 34px rgba(255, 96, 52, .34);
  }

  @keyframes scoreRoulette {
    0%   { transform: perspective(500px) rotateX(0deg) scale(1); }
    50%  { transform: perspective(500px) rotateX(90deg) scale(1.04); }
    100% { transform: perspective(500px) rotateX(180deg) scale(1); }
  }

  @keyframes scoreReveal {
    0%   { transform: scale(.35) rotate(-7deg); opacity: .2; }
    55%  { transform: scale(1.32) rotate(3deg); opacity: 1; }
    75%  { transform: scale(.94) rotate(-1deg); }
    100% { transform: scale(1) rotate(0); }
  }

  .score-formula {
    min-height: 44px;
    margin-top: 8px;
    font-size: 13px;
    line-height: 1.65;
    color: #685f55;
  }

  .score-stage.score-rainbow {
    border: 7px solid transparent;
    background:
      radial-gradient(circle at 50% 20%, #fff8d4 0, #fff 56%) padding-box,
      linear-gradient(
        90deg,
        #ff3b30,
        #ff9500,
        #ffd60a,
        #34c759,
        #0a84ff,
        #5e5ce6,
        #bf5af2,
        #ff3b30
      ) border-box;
    background-size: 100% 100%, 300% 100%;
    animation: scoreRainbow 2s linear infinite;
  }

  .score-stage.babaan {
    animation: scoreStageBang .72s ease-out;
  }

  .score-stage.score-rainbow.babaan {
    animation:
      scoreStageBang .72s ease-out,
      scoreRainbow 2s linear infinite;
  }

  @keyframes scoreRainbow {
    from { background-position: 0 0, 0% 50%; }
    to   { background-position: 0 0, 300% 50%; }
  }

  @keyframes scoreStageBang {
    0%   { transform: scale(1); }
    24%  { transform: scale(1.035); }
    45%  { transform: scale(.985); }
    100% { transform: scale(1); }
  }

  .confetti-piece {
    position: absolute;
    top: -16px;
    width: 9px;
    height: 16px;
    border-radius: 2px;
    pointer-events: none;
    z-index: 8;
    animation: confettiFall 1.8s ease-in forwards;
  }

  @keyframes confettiFall {
    0% {
      transform: translate3d(0, -10px, 0) rotate(0deg);
      opacity: 1;
    }
    100% {
      transform: translate3d(var(--drift), 240px, 0) rotate(var(--spin));
      opacity: 0;
    }
  }

  .result-note {
    text-align: center;
    color: #66635d;
    line-height: 1.7;
  }

  .ranking-panel {
    margin: 18px auto;
    padding: 14px;
    border: 1px solid #ddd7ca;
    border-radius: 16px;
    background: #fbfaf7;
  }

  .ranking-panel-title {
    margin-bottom: 8px;
    font-size: 14px;
    font-weight: 950;
    color: #554d43;
  }

  .ranking-note {
    margin-bottom: 8px;
    font-size: 10px;
    line-height: 1.5;
    color: #857d73;
  }

  .ranking-list {
    display: grid;
    gap: 5px;
    max-height: 330px;
    overflow-y: auto;
    padding-right: 2px;
  }

  .ranking-empty {
    padding: 12px 6px;
    text-align: center;
    font-size: 11px;
    color: #928b82;
  }

  .ranking-row {
    display: grid;
    grid-template-columns: 25px minmax(0, 1fr) auto;
    align-items: center;
    gap: 7px;
    padding: 7px 8px;
    border: 1px solid #e7e1d7;
    border-radius: 10px;
    background: #fff;
  }

  .ranking-place {
    text-align: center;
    font-size: 10px;
    font-weight: 900;
    color: #8b8174;
  }

  .ranking-main {
    min-width: 0;
  }

  /* ランキング内の点数は意図的に小さく表示 */
  .ranking-score {
    font-size: 17px;
    line-height: 1.15;
    font-weight: 950;
    font-variant-numeric: tabular-nums;
    color: #463f37;
  }

  .ranking-detail {
    margin-top: 2px;
    font-size: 9px;
    line-height: 1.45;
    color: #91887d;
  }

  .ranking-delete {
    min-height: 28px !important;
    padding: 4px 7px !important;
    font-size: 9px !important;
    color: #765d59;
    background: #fff;
    border: 1px solid #d9c9c6;
  }

  .mode-challenge-count {
    margin: 8px 0 5px;
    text-align: right;
    font-size: 10px;
    font-weight: 800;
    color: #8b8378;
  }

  .ranking-open-btn {
    width: 100%;
    margin-top: 7px;
    min-height: 34px;
    padding: 6px 10px;
    font-size: 11px;
    color: #62594f;
    background: #f7f4ee;
    border: 1px solid #ddd5c8;
  }

  .ranking-modal {
    display: none;
    position: fixed;
    inset: 0;
    z-index: 1000;
    padding: 24px;
    background: rgba(38, 34, 30, .38);
    align-items: center;
    justify-content: center;
  }

  .ranking-modal.show {
    display: flex;
  }

  .ranking-dialog {
    width: min(560px, 96vw);
    max-height: 82vh;
    overflow: hidden;
    padding: 18px;
    border-radius: 18px;
    background: #fff;
    box-shadow: 0 20px 60px rgba(0,0,0,.2);
  }

  .ranking-dialog-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 10px;
  }

  .ranking-dialog-title {
    min-width: 0;
    font-size: 15px;
    font-weight: 950;
  }

  .ranking-dialog-close {
    min-height: 30px !important;
    padding: 5px 9px !important;
    font-size: 10px !important;
  }

  .ranking-dialog .ranking-list {
    max-height: 60vh;
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

<div id="homeView" class="app-home">
  <div class="home-title">そろばん</div>
  <div class="home-sub">
    計算に挑戦するか、珠の動かし方を順番に学ぶかを選んでください。
  </div>

  <div class="home-mode-grid">
    <button type="button" id="homeChallengeBtn" class="home-mode-btn primary-home">
      <span class="home-mode-kicker">CHALLENGE</span>
      <span class="home-mode-name">チャレンジモード</span>
      <span class="home-mode-desc">
        これまでの計算トレーニング。12問に挑戦し、得点やランキングを記録します。
      </span>
    </button>

    <button type="button" id="homeLearningBtn" class="home-mode-btn">
      <span class="home-mode-kicker">LEARNING</span>
      <span class="home-mode-name">学習モード</span>
      <span class="home-mode-desc">
        足し算・引き算・掛け算・割り算の珠の動きを動画のようなアニメーションで学びます。
      </span>
    </button>
  </div>
</div>

<div id="menuView" class="hidden">
  <div class="subview-topbar">
    <button type="button" id="challengeTopBtn" class="top-back-btn">← TOPへ</button>
    <div class="subview-topbar-title">チャレンジモード</div>
  </div>
  <div class="intro">
    <div class="lead">
      各モード12問です。
      割り算以外は、計算式を確定する直前に左右の数へ必ず+1します。
      そのため表示される数に0は出ません。
    </div>
    <div id="modeTimeBadge" class="badge">12問 / 5分</div>
  </div>

  <div class="time-limit-control">
    <span class="time-limit-label">時間制限</span>
    <button type="button" id="timeLimitBtn" class="time-limit-toggle">
      5分
    </button>
  </div>

  <div class="level-title">初級モード｜足し算のみ</div>
  <div class="mode-grid">
    <article class="mode-card">
      <div class="mode-no">BEGINNER ADD 1</div>
      <div class="mode-name">1桁の足し算</div>
      <div class="mode-desc">最終表示は1〜9の数だけ。足し算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="ba1">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">BEGINNER ADD 2</div>
      <div class="mode-name">2桁の足し算</div>
      <div class="mode-desc">最終表示は10〜99。足し算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="ba2">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">BEGINNER ADD 3</div>
      <div class="mode-name">3桁の足し算</div>
      <div class="mode-desc">最終表示は100〜999。足し算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="ba3">はじめる</button>
    </article>
  </div>

  <div class="level-title">初級モード｜引き算のみ</div>
  <div class="mode-grid">
    <article class="mode-card">
      <div class="mode-no">BEGINNER SUB 1</div>
      <div class="mode-name">1桁の引き算</div>
      <div class="mode-desc">最終表示は1〜9。引き算のみ12問。答えは必ず0以上です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="bs1">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">BEGINNER SUB 2</div>
      <div class="mode-name">2桁の引き算</div>
      <div class="mode-desc">最終表示は10〜99。引き算のみ12問。答えは必ず0以上です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="bs2">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">BEGINNER SUB 3</div>
      <div class="mode-name">3桁の引き算</div>
      <div class="mode-desc">最終表示は100〜999。引き算のみ12問。答えは必ず0以上です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="bs3">はじめる</button>
    </article>
  </div>

  <div class="level-title">中級モード｜掛け算のみ</div>
  <div class="mode-grid">
    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE MUL 1</div>
      <div class="mode-name">1桁×1桁</div>
      <div class="mode-desc">1〜9同士の掛け算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="mm1">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE MUL 2</div>
      <div class="mode-name">2桁×1桁</div>
      <div class="mode-desc">2桁×1桁の掛け算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="mm2">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE MUL 3</div>
      <div class="mode-name">2桁×2桁</div>
      <div class="mode-desc">2桁同士の掛け算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="mm3">はじめる</button>
    </article>
  </div>

  <div class="level-title">中級モード｜割り算のみ</div>
  <div class="mode-grid">
    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE DIV 1</div>
      <div class="mode-name">1〜81 ÷ 1桁</div>
      <div class="mode-desc">1〜81を1桁で割り、答えが整数になる割り算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="md1">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE DIV 2</div>
      <div class="mode-name">3桁÷1桁</div>
      <div class="mode-desc">100〜999を1桁で割り、答えが整数になる割り算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="md2">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE DIV 3</div>
      <div class="mode-name">3桁÷2桁</div>
      <div class="mode-desc">100〜999を2桁で割り、答えが整数になる割り算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="md3">はじめる</button>
    </article>
  </div>

  <div class="level-title">上級モード</div>
  <div class="mode-grid">
    <article class="mode-card">
      <div class="mode-no">ADVANCED 1</div>
      <div class="mode-name">4桁の足し算・引き算</div>
      <div class="mode-desc">最終表示は1000〜9999。引き算の答えは0以上です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="a1">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">ADVANCED 2</div>
      <div class="mode-name">3桁×2桁 / 4桁÷2桁</div>
      <div class="mode-desc">3桁×2桁の掛け算と、4桁÷2桁の整数解です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="a2">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">ADVANCED 3</div>
      <div class="mode-name">3桁×3桁 / 5桁÷3桁</div>
      <div class="mode-desc">3桁同士の掛け算と、5桁÷3桁の整数解です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip time-chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="a3">はじめる</button>
    </article>
  </div>

  <div id="rankingModal" class="ranking-modal" aria-hidden="true">
    <div class="ranking-dialog">
      <div class="ranking-dialog-head">
        <div id="rankingModalTitle" class="ranking-dialog-title">
          過去の得点ランキング
        </div>
        <button type="button" id="rankingModalClose" class="ranking-dialog-close">
          閉じる
        </button>
      </div>
      <div class="ranking-note">
        このブラウザに保存された記録です。親御さんの記録などは「削除」で1件ずつ消せます。
      </div>
      <div id="rankingModalList" class="ranking-list"></div>
    </div>
  </div>
</div>


<div id="learningView" class="learning-view">
  <div class="subview-topbar">
    <button type="button" id="learningTopBtn" class="top-back-btn">← TOPへ</button>
    <div class="subview-topbar-title">学習モード</div>
  </div>

  <div id="learningCategoryView">
    <div class="learning-hero">
      <h2>珠の動かし方を順番に学ぶ</h2>
      <p>
        まず動画のような珠の動きを見て、ポイントを確認し、最後に理解チェックをします。
        各計算はSTEP 1から少しずつ難しくなります。
      </p>
      <div id="learningOverallText" class="learning-progress-summary"></div>
      <div class="learning-progress-track">
        <div id="learningOverallBar" class="learning-progress-bar"></div>
      </div>
    </div>

    <div id="learningCategoryGrid" class="learning-category-grid"></div>
  </div>

  <div id="learningStageView" class="hidden">
    <div class="learning-lesson-head">
      <div>
        <div id="learningStageKicker" class="learning-lesson-kicker"></div>
        <div id="learningStageHeading" class="learning-lesson-title"></div>
      </div>
      <button type="button" id="learningStageBackBtn">← 計算の種類へ</button>
    </div>

    <div id="learningStageGrid" class="learning-stage-grid"></div>
  </div>

  <div id="learningLessonView" class="hidden">
    <div class="learning-lesson-head">
      <div>
        <div id="learningLessonKicker" class="learning-lesson-kicker"></div>
        <div id="learningLessonTitle" class="learning-lesson-title"></div>
      </div>
      <button type="button" id="learningLessonBackBtn">← STEP一覧へ</button>
    </div>

    <div class="learning-video-card">
      <div class="learning-video-title">
        <span>珠の動き動画</span>
        <span class="learning-video-badge">自動アニメーション</span>
      </div>

      <div id="learningStepText" class="learning-step-text"></div>

      <div class="learning-soroban-wrap">
        <div id="learningSorobanBoard" class="learning-soroban-board"></div>
      </div>

      <div id="learningFrameCounter" class="learning-frame-counter"></div>

      <div class="learning-video-controls">
        <button type="button" id="learningReplayBtn">↻ もう一度</button>
        <button type="button" id="learningPauseBtn">Ⅱ 一時停止</button>
      </div>
    </div>

    <div class="learning-explain-card">
      <div class="learning-point-grid">
        <div class="learning-point">
          <div class="learning-point-label">今回の基本</div>
          <div id="learningBasicText" class="learning-point-text"></div>
        </div>
        <div class="learning-point trouble">
          <div class="learning-point-label">つまずきやすいところ</div>
          <div id="learningTroubleText" class="learning-point-text"></div>
        </div>
      </div>

      <div id="learningRuleBox" class="learning-rule-box"></div>
    </div>

    <div class="learning-quiz-card">
      <div class="learning-video-title">
        <span>理解チェック</span>
        <span class="learning-video-badge">クリアで ★</span>
      </div>
      <div id="learningQuizQuestion" class="learning-quiz-question"></div>
      <div id="learningQuizOptions" class="learning-quiz-options"></div>
      <div id="learningQuizFeedback" class="learning-quiz-feedback"></div>

      <div id="learningClearActions" class="learning-clear-actions">
        <button type="button" id="learningAgainBtn">動画をもう一度</button>
        <button type="button" id="learningNextBtn" class="primary">次のSTEPへ</button>
      </div>
    </div>
  </div>
</div>

<section id="workspace" class="workspace">
  <div class="statusbar">
    <div>
      <div id="statusTitle" class="status-title"></div>
      <div id="statusSub" class="status-sub">12問・制限時間5分</div>
    </div>
    <div id="timer" class="timer">5:00</div>
    <div id="streak" class="streak">連続正解 0</div>
    <button type="button" id="voiceBtn" class="voice-btn">🎤 音声回答 OFF</button>
    <button type="button" id="bgmBtn">♪ BGM ON</button>
    <button type="button" id="quitBtn">モード選択へ</button>
    <div id="voiceStatus" class="voice-status">音声回答：OFF</div>
    <div id="bgmName" class="bgm-name">BGM：準備中</div>
  </div>

  <div id="questionCard" class="question-card">
    <div class="qtop">
      <div>
        <span id="qCount" class="qcount">1 / 12</span>
        <span id="weakBadge" class="weak-badge">にがて克服</span>
      </div>
      <div id="score" class="score">正解 0</div>
    </div>

    <div id="equation" class="equation"></div>

    <div class="hint-launch">
      <button type="button" id="hintBtn" class="hint-btn">
        珠ヒントを見る
      </button>
    </div>

    <div id="abacusHint" class="abacus-hint">
      <div class="hint-head">
        <div class="hint-title">そろばんの珠の動かし方</div>
        <div class="hint-actions">
          <button type="button" id="hintReplayBtn">もう一度</button>
          <button type="button" id="hintCloseBtn">閉じる</button>
        </div>
      </div>

      <div id="hintStep" class="hint-step"></div>

      <div class="soroban-scroll">
        <div id="sorobanBoard" class="soroban-board"></div>
      </div>

      <div class="hint-legend">
        黄色く光っている位の珠が、いま動いているところです。
      </div>
    </div>

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

    <div id="scoreStage" class="score-stage">
      <div class="score-caption">チャレンジスコア</div>
      <div id="resultScore" class="result-score">---</div>
      <div id="scoreFormula" class="score-formula"></div>
    </div>

    <div id="resultNote" class="result-note"></div>

    <div id="resultRankingPanel" class="ranking-panel">
      <div class="ranking-panel-title">このモードの過去の得点ランキング</div>
      <div class="ranking-note">
        点数は小さめに表示しています。不要な記録は1件ずつ削除できます。
      </div>
      <div id="resultRankingList" class="ranking-list"></div>
    </div>

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

  const homeView = $("#homeView");
  const menuView = $("#menuView");
  const learningView = $("#learningView");
  const learningCategoryView = $("#learningCategoryView");
  const learningStageView = $("#learningStageView");
  const learningLessonView = $("#learningLessonView");
  const learningCategoryGrid = $("#learningCategoryGrid");
  const learningStageGrid = $("#learningStageGrid");
  const learningOverallText = $("#learningOverallText");
  const learningOverallBar = $("#learningOverallBar");
  const learningStageKicker = $("#learningStageKicker");
  const learningStageHeading = $("#learningStageHeading");
  const learningLessonKicker = $("#learningLessonKicker");
  const learningLessonTitle = $("#learningLessonTitle");
  const learningStepText = $("#learningStepText");
  const learningSorobanBoard = $("#learningSorobanBoard");
  const learningFrameCounter = $("#learningFrameCounter");
  const learningBasicText = $("#learningBasicText");
  const learningTroubleText = $("#learningTroubleText");
  const learningRuleBox = $("#learningRuleBox");
  const learningQuizQuestion = $("#learningQuizQuestion");
  const learningQuizOptions = $("#learningQuizOptions");
  const learningQuizFeedback = $("#learningQuizFeedback");
  const learningClearActions = $("#learningClearActions");
  const learningPauseBtn = $("#learningPauseBtn");
  const learningNextBtn = $("#learningNextBtn");

  const workspace = $("#workspace");
  const questionCard = $("#questionCard");
  const results = $("#results");
  const equation = $("#equation");
  const answerInput = $("#answerInput");
  const feedback = $("#feedback");
  const timerEl = $("#timer");
  const statusSub = $("#statusSub");
  const timeLimitBtn = $("#timeLimitBtn");
  const modeTimeBadge = $("#modeTimeBadge");
  const bar = $("#bar");
  const scoreStage = $("#scoreStage");
  const resultScore = $("#resultScore");
  const scoreFormula = $("#scoreFormula");
  const resultRankingList = $("#resultRankingList");
  const resultRankingPanel = $("#resultRankingPanel");
  const rankingModal = $("#rankingModal");
  const rankingModalTitle = $("#rankingModalTitle");
  const rankingModalList = $("#rankingModalList");

  const voiceBtn = $("#voiceBtn");
  const voiceStatus = $("#voiceStatus");
  const bgmBtn = $("#bgmBtn");
  const bgmName = $("#bgmName");
  const hintBtn = $("#hintBtn");
  const abacusHint = $("#abacusHint");
  const hintStep = $("#hintStep");
  const sorobanBoard = $("#sorobanBoard");

  const modeInfo = {
    ba1: { title: "初級・足し算1｜1桁の足し算" },
    ba2: { title: "初級・足し算2｜2桁の足し算" },
    ba3: { title: "初級・足し算3｜3桁の足し算" },
    bs1: { title: "初級・引き算1｜1桁の引き算" },
    bs2: { title: "初級・引き算2｜2桁の引き算" },
    bs3: { title: "初級・引き算3｜3桁の引き算" },
    mm1: { title: "中級・掛け算1｜1桁×1桁" },
    mm2: { title: "中級・掛け算2｜2桁×1桁" },
    mm3: { title: "中級・掛け算3｜2桁×2桁" },
    md1: { title: "中級・割り算1｜1〜81÷1桁" },
    md2: { title: "中級・割り算2｜3桁÷1桁" },
    md3: { title: "中級・割り算3｜3桁÷2桁" },
    a1: { title: "上級1｜4桁の足し算・引き算" },
    a2: { title: "上級2｜3桁×2桁 / 4桁÷2桁" },
    a3: { title: "上級3｜3桁×3桁 / 5桁÷3桁" }
  };

  const LEARNING_PROGRESS_STORAGE_KEY =
    "soroban_tutorial_progress_v1";

  const learningCategories = {
    add: {
      symbol: "＋",
      title: "足し算",
      desc: "一珠・五珠から、5の補数、10の補数、2桁の繰り上がりへ進みます。",
      lessons: [
        {
          id: "add1",
          title: "1〜4をそのまま足す",
          desc: "使える一珠を、そのまま梁へ寄せる基本。",
          basic: "足したい数だけ一珠が残っているときは、同じ位の一珠を梁へ寄せます。まずは珠を数えず、形で1〜4を見分けることが大切です。",
          trouble: "指で珠を1個ずつ数え続けると速くなりません。『2の形』『3の形』を一目で見る練習をします。",
          rule: "足せる珠がある → そのまま足す。",
          frames: [
            { value: 2, place: 1, text: "まず 2 を置きます。" },
            { value: 3, place: 1, text: "＋2 の1個目。1の珠を1つ梁へ寄せます。" },
            { value: 4, place: 1, text: "＋2 の2個目。もう1つ寄せて 4 です。" }
          ],
          quiz: { q: "2 ＋ 2 の答えは？", options: ["3", "4", "5"], answer: "4" }
        },
        {
          id: "add2",
          title: "5珠と1珠を組み合わせる",
          desc: "5〜9の形をすばやく作る。",
          basic: "5は上の五珠を梁へ寄せます。6〜9は『5＋一珠』の形です。たとえば8は、五珠1つと一珠3つです。",
          trouble: "6〜9を一珠6個のように考えないこと。『5といくつ』で見ると珠の形が安定します。",
          rule: "6〜9は『5 ＋ 1〜4』で見る。",
          frames: [
            { value: 5, place: 1, text: "まず 5。上の五珠を梁へ寄せます。" },
            { value: 6, place: 1, text: "＋3 の1個目。一珠を1つ寄せます。" },
            { value: 7, place: 1, text: "2個目を寄せます。" },
            { value: 8, place: 1, text: "3個目を寄せて 8 です。" }
          ],
          quiz: { q: "そろばんの 8 は『5 ＋ いくつ』？", options: ["2", "3", "4"], answer: "3" }
        },
        {
          id: "add3",
          title: "5の補数で足す",
          desc: "一珠が足りないときに『＋5 − 補数』を使う。",
          basic: "同じ位で一珠が足りないときは、5を足して余分な分を引きます。2＋4なら、4の5に対する補数は1なので『＋5 −1』です。",
          trouble: "『何を引くか』を毎回数えないこと。1と4、2と3を5の組として覚えます。",
          rule: "＋4 ＝ ＋5 −1 ／ ＋3 ＝ ＋5 −2。",
          frames: [
            { value: 2, place: 1, text: "2 ＋ 4。2を置きます。" },
            { value: 7, place: 1, text: "4をそのまま足せないので、まず ＋5。2 → 7。" },
            { value: 6, place: 1, text: "5では1多いので −1。答えは 6。" }
          ],
          quiz: { q: "2 ＋ 4 は、そろばんではどの動き？", options: ["＋5−1", "＋5−2", "＋10−4"], answer: "＋5−1" }
        },
        {
          id: "add4",
          title: "10の補数で繰り上がる",
          desc: "9を超えるときに『＋10 − 補数』を使う。",
          basic: "一の位で9を超えるときは、十の位へ1を足して、一の位から10の補数を引きます。8＋7なら7の10の補数は3です。",
          trouble: "先に一の位を無理に動かそうとすると混乱します。『十の位を1上げる → 一の位を補数だけ引く』の順に固定します。",
          rule: "＋7 ＝ ＋10 −3 ／ ＋8 ＝ ＋10 −2 ／ ＋9 ＝ ＋10 −1。",
          frames: [
            { value: 8, place: 1, text: "8 ＋ 7。まず8を置きます。" },
            { value: 18, place: 10, text: "7を足すと10を超えるので、十の位へ ＋10。" },
            { value: 15, place: 1, text: "7の補数は3。一の位から −3。答えは15。" }
          ],
          quiz: { q: "8 ＋ 7 で使う10の補数は？", options: ["2", "3", "4"], answer: "3" }
        },
        {
          id: "add5",
          title: "2桁の繰り上がり",
          desc: "十の位と一の位を分けて処理する。",
          basic: "2桁は大きい位から足します。36＋27なら、まず＋20で56。そのあと一の位の＋7を『＋10−3』で処理します。",
          trouble: "20と7を一度に処理しようとしないこと。『十の位 → 一の位』と分けると、どこで繰り上がったかが見えます。",
          rule: "2桁は位ごとに分解。大きい位から順番に。",
          frames: [
            { value: 36, place: null, text: "36 ＋ 27。まず36を置きます。" },
            { value: 56, place: 10, text: "27の十の位、＋20。36 → 56。" },
            { value: 66, place: 10, text: "一の位で＋7。まず ＋10。56 → 66。" },
            { value: 63, place: 1, text: "7の補数3を −3。答えは63。" }
          ],
          quiz: { q: "36 ＋ 27 で最初に足すのは？", options: ["7", "20", "27全部"], answer: "20" }
        }
      ]
    },
    sub: {
      symbol: "－",
      title: "引き算",
      desc: "そのまま引くところから、5の補数、10の補数、2桁の繰り下がりへ。",
      lessons: [
        {
          id: "sub1",
          title: "そのまま引く",
          desc: "取れる一珠があるときは直接梁から離す。",
          basic: "引きたい数だけ一珠が梁に寄っているときは、その珠を梁から離します。",
          trouble: "答えの珠を新しく作るのではなく、『今ある珠から取る』と考えます。",
          rule: "取れる珠がある → そのまま引く。",
          frames: [
            { value: 4, place: 1, text: "4 − 2。まず4を置きます。" },
            { value: 3, place: 1, text: "一珠を1つ梁から離します。" },
            { value: 2, place: 1, text: "もう1つ離して、答えは2。" }
          ],
          quiz: { q: "4 − 2 の答えは？", options: ["1", "2", "3"], answer: "2" }
        },
        {
          id: "sub2",
          title: "5珠から直接引く",
          desc: "8−3など、五珠を残して一珠を取る。",
          basic: "8は5＋3です。8−3なら、一珠3つをそのまま梁から離せば5が残ります。",
          trouble: "五珠まで動かしてしまわないこと。まず『取れる一珠が何個あるか』を見ます。",
          rule: "8 −3 → 一珠3つをそのまま取る。",
          frames: [
            { value: 8, place: 1, text: "8は『5＋3』の形です。" },
            { value: 7, place: 1, text: "一珠を1つ取ります。" },
            { value: 6, place: 1, text: "2つ目を取ります。" },
            { value: 5, place: 1, text: "3つ目を取って5。" }
          ],
          quiz: { q: "8 − 3 では、最初にどの珠を見る？", options: ["一珠", "十の位", "全部動かす"], answer: "一珠" }
        },
        {
          id: "sub3",
          title: "5の補数で引く",
          desc: "一珠だけでは引けないときに『−5＋補数』。",
          basic: "7−4では、一珠は2個しかないため4を直接取れません。そこで−5して、4の5に対する補数1を＋1します。",
          trouble: "『−5したから終わり』ではありません。必ず補数を戻します。",
          rule: "−4 ＝ −5 ＋1 ／ −3 ＝ −5 ＋2。",
          frames: [
            { value: 7, place: 1, text: "7 − 4。7を置きます。" },
            { value: 2, place: 1, text: "4を直接取れないので、まず −5。7 → 2。" },
            { value: 3, place: 1, text: "4の補数1を ＋1。答えは3。" }
          ],
          quiz: { q: "7 − 4 の珠の動きは？", options: ["−5＋1", "−5＋2", "−10＋4"], answer: "−5＋1" }
        },
        {
          id: "sub4",
          title: "10の補数で繰り下がる",
          desc: "一の位だけでは引けないときに『−10＋補数』。",
          basic: "12−7では一の位の2から7を引けません。十の位から1を下げて−10し、一の位へ7の10の補数3を足します。",
          trouble: "『借りた10』を頭の中だけで処理しないこと。十の位の珠を実際に1つ下げる動きを先にします。",
          rule: "−7 ＝ −10 ＋3 ／ −8 ＝ −10 ＋2 ／ −9 ＝ −10 ＋1。",
          frames: [
            { value: 12, place: 1, text: "12 − 7。まず12を置きます。" },
            { value: 2, place: 10, text: "一の位だけでは引けないので、十の位から −10。" },
            { value: 5, place: 1, text: "7の補数3を一の位へ ＋3。答えは5。" }
          ],
          quiz: { q: "12 − 7 で足し戻す数は？", options: ["2", "3", "7"], answer: "3" }
        },
        {
          id: "sub5",
          title: "2桁の繰り下がり",
          desc: "43−28を位ごとに処理する。",
          basic: "43−28なら、まず−20で23。そのあと−8は一の位だけでは引けないので『−10＋2』にします。",
          trouble: "28を一気に引かないこと。十の位20と一の位8を分ければ、補数を使う場所が明確になります。",
          rule: "2桁の引き算も、大きい位から順番に。",
          frames: [
            { value: 43, place: null, text: "43 − 28。まず43を置きます。" },
            { value: 23, place: 10, text: "十の位の −20。43 → 23。" },
            { value: 13, place: 10, text: "一の位の−8は直接できないので、まず −10。" },
            { value: 15, place: 1, text: "8の補数2を ＋2。答えは15。" }
          ],
          quiz: { q: "43 − 28 で最初に引くのは？", options: ["8", "20", "28全部"], answer: "20" }
        }
      ]
    },
    mul: {
      symbol: "×",
      title: "掛け算",
      desc: "九九→部分積→位取り。答えをどの位の珠へ置くかを段階的に学びます。",
      lessons: [
        {
          id: "mul1",
          title: "九九の答えを珠に置く",
          desc: "3×4＝12を十の位・一の位に置く。",
          basic: "掛け算ではまず九九で答えを作ります。12なら十の位に1、一の位に2を置きます。",
          trouble: "『12』を一の位に12個置こうとしないこと。必ず十の位1、一の位2に分けます。",
          rule: "九九の答えも、位に分けて珠へ置く。",
          frames: [
            { value: 0, place: null, text: "3 × 4。九九で答えは12です。" },
            { value: 10, place: 10, text: "12の十の位、1を置きます。" },
            { value: 12, place: 1, text: "一の位に2を置いて12。" }
          ],
          quiz: { q: "3 × 4 の答え12。十の位に置く数は？", options: ["1", "2", "12"], answer: "1" }
        },
        {
          id: "mul2",
          title: "2桁×1桁の部分積",
          desc: "23×4を20×4と3×4に分ける。",
          basic: "23×4は『20×4＝80』と『3×4＝12』に分けます。部分積を位をそろえて足すと92です。",
          trouble: "2×4＝8を『8』として一の位へ置かないこと。2は十の位なので、20×4＝80です。",
          rule: "元の数字の位を、掛けた後も忘れない。",
          frames: [
            { value: 0, place: null, text: "23 × 4。まず20×4を考えます。" },
            { value: 80, place: 10, text: "20 × 4 ＝ 80。80を置きます。" },
            { value: 90, place: 10, text: "次に3×4＝12。まず十の位の10を加えます。" },
            { value: 92, place: 1, text: "一の位の2を加えて92。" }
          ],
          quiz: { q: "23 × 4 で、20 × 4 は？", options: ["8", "80", "800"], answer: "80" }
        },
        {
          id: "mul3",
          title: "2桁×2桁",
          desc: "24×13を×10と×3に分ける。",
          basic: "24×13は、24×10＝240と24×3＝72に分けます。240＋72＝312です。",
          trouble: "13を『1と3』として同じ位に扱わないこと。1は十の位なので×10です。",
          rule: "2桁の掛ける数は『十の位の部分積＋一の位の部分積』。",
          frames: [
            { value: 0, place: null, text: "24 × 13。13を10と3に分けます。" },
            { value: 240, place: 10, text: "24 × 10 ＝ 240。" },
            { value: 310, place: 10, text: "24 × 3 ＝72。まず70を加えます。" },
            { value: 312, place: 1, text: "残り2を加えて312。" }
          ],
          quiz: { q: "24 × 13 で、最初の大きな部分積は？", options: ["24×1", "24×10", "24×3"], answer: "24×10" }
        },
        {
          id: "mul4",
          title: "0がある数の位取り",
          desc: "40×6で、4ではなく40を掛けていると意識する。",
          basic: "40×6は4×6＝24を使いますが、4は十の位です。答えは24ではなく240です。",
          trouble: "途中の0を『何もしないから無視』して位まで消してしまうこと。0は珠を置かなくても、位は残ります。",
          rule: "0の珠は置かなくても、0が示す位は消えない。",
          frames: [
            { value: 0, place: null, text: "40 × 6。4×6＝24を使います。" },
            { value: 200, place: 100, text: "40の4は十の位。答え24も1桁左へずれて240。" },
            { value: 240, place: 10, text: "十の位に4を置いて240。" }
          ],
          quiz: { q: "40 × 6 の答えは？", options: ["24", "240", "2400"], answer: "240" }
        }
      ]
    },
    div: {
      symbol: "÷",
      title: "割り算",
      desc: "商を見つけ、位をそろえて答えの珠を置くところから始めます。",
      lessons: [
        {
          id: "div1",
          title: "1桁÷1桁",
          desc: "8÷4＝2。何個分あるかを考える。",
          basic: "割り算は『4が8の中に何個あるか』を考えます。4×2＝8なので商は2です。",
          trouble: "引き算を何回も繰り返すだけにしないこと。九九の逆として『4×いくつ＝8』を使います。",
          rule: "割り算は九九を逆向きに使う。",
          frames: [
            { value: 0, place: null, text: "8 ÷ 4。4×いくつで8になるか考えます。" },
            { value: 2, place: 1, text: "4×2＝8なので、商は2。答えの珠に2を置きます。" }
          ],
          quiz: { q: "8 ÷ 4 は？", options: ["2", "3", "4"], answer: "2" }
        },
        {
          id: "div2",
          title: "2桁÷1桁",
          desc: "84÷4を十の位から見る。",
          basic: "84÷4は、大きい位から見ます。8十÷4＝2十、次に4÷4＝1。答えは21です。",
          trouble: "84を一気に考えようとしないこと。十の位→一の位に分けます。",
          rule: "割り算も大きい位から商を決める。",
          frames: [
            { value: 0, place: null, text: "84 ÷ 4。まず8十を4で割ります。" },
            { value: 20, place: 10, text: "8十 ÷4＝2十。十の位へ2。" },
            { value: 21, place: 1, text: "残る4 ÷4＝1。一の位へ1。答え21。" }
          ],
          quiz: { q: "84 ÷ 4 の十の位の商は？", options: ["1", "2", "4"], answer: "2" }
        },
        {
          id: "div3",
          title: "3桁÷1桁",
          desc: "156÷3を左から順に処理する。",
          basic: "156÷3は、15十÷3＝5十、6÷3＝2と見ます。商は52です。",
          trouble: "最初の1だけを3で割れないから止まらないこと。必要なら次の桁と合わせて15として見ます。",
          rule: "先頭の数字が割れなければ、次の桁までまとめる。",
          frames: [
            { value: 0, place: null, text: "156 ÷ 3。先頭の1だけでは3で割れません。" },
            { value: 50, place: 10, text: "15を3で割ると5。十の位に5を置きます。" },
            { value: 52, place: 1, text: "残る6を3で割ると2。答え52。" }
          ],
          quiz: { q: "156 ÷ 3 で、最初に『15』を見る理由は？", options: ["1だけでは3で割れない", "6があるから", "いつも15を見る"], answer: "1だけでは3で割れない" }
        },
        {
          id: "div4",
          title: "2桁で割る",
          desc: "144÷12で商を見当づける。",
          basic: "2桁で割るときは『12×いくつなら今見ている数を超えないか』を考えます。144÷12は12です。",
          trouble: "大きすぎる商を置いてから戻す回数を減らすため、まず上の桁を使って商を見当づけます。",
          rule: "商は『割る数×商が、今の数を超えない最大』を探す。",
          frames: [
            { value: 0, place: null, text: "144 ÷ 12。まず商の十の位を考えます。" },
            { value: 10, place: 10, text: "12×10＝120。144を超えないので十の位に1。" },
            { value: 12, place: 1, text: "残り24には12が2個。商は12。" }
          ],
          quiz: { q: "144 ÷ 12 の商は？", options: ["10", "12", "14"], answer: "12" }
        }
      ]
    }
  };

  let learningProgress = loadTutorialProgress();
  let learningCurrentCategory = null;
  let learningCurrentLessonIndex = 0;
  let learningRods = [];
  let learningAnimationToken = 0;
  let learningAnimationPaused = false;
  let learningCurrentFrame = 0;

  const RULES = Object.freeze({
    addSubOperandMin: 1,
    subtractionMinAnswer: 0,
    divisionMustBeInteger: true
  });

  const TOTAL_QUESTIONS = 12;

  // =====================================================
  // 自動レベルアップ・苦手克服
  // =====================================================
  const LEARNING_STORAGE_KEY = "soroban_learning_stats_v1";
  const RANKING_STORAGE_KEY = "soroban_score_rankings_v1";
  const CHALLENGE_COUNT_STORAGE_KEY = "soroban_challenge_counts_v1";
  const MAX_RANKING_ENTRIES_PER_MODE = 100;

  // 最初の5問（1〜5問目）には苦手克服問題を入れない。
  // その後の7問の中へ、最大5問を分散して入れる。
  const WEAKNESS_SLOTS = new Set([5, 6, 8, 9, 11]);

  // 苦手克服問題として1回正解した時点で克服扱い。
  // 一度克服した問題は、それ以降の苦手克服枠には出さない。
  const RECOVERY_STREAK_TO_MASTER = 1;

  // 同じ種類の学習内でのみ自動レベルアップする。
  const NEXT_MODE = Object.freeze({
    ba1: "ba2",
    ba2: "ba3",
    bs1: "bs2",
    bs2: "bs3",
    mm1: "mm2",
    mm2: "mm3",
    md1: "md2",
    md2: "md3",
    a2: "a3"
  });

  let currentMode = null;
  let questions = [];
  let index = 0;
  let score = 0;
  let answers = [];
  let seconds = 300;
  let timerHandle = null;
  let timeLimitEnabled = true;
  let locked = false;
  let correctStreak = 0;
  let maxCorrectStreak = 0;
  let scoreAnimationToken = 0;
  let bgmOn = true;
  let currentBgm = null;
  let currentBgmGroupKey = null;

  let learningStats = loadLearningStats();
  let scoreRankings = loadScoreRankings();
  let challengeCounts = loadChallengeCounts();
  let sessionWeakAsked = 0;
  let sessionWeakCorrect = 0;
  let promotedMode = null;
  let sessionRankingSaved = false;
  let sessionChallengeRecorded = false;
  let rankingModalMode = null;

  let inAppBackGuardReady = false;
  let handlingBrowserBack = false;

  let hintRunToken = 0;
  let hintDigitCount = 1;
  let hintRods = [];

  let voiceAnswerEnabled = false;
  let voiceRecognition = null;
  let voiceRecognitionRunning = false;
  let voicePauseForFeedback = false;
  let voiceCalloutRunning = false;
  let voiceRestartTimer = null;

  const BGM_VOLUME_VOICE_ON = 0.06;
  const BGM_VOLUME_VOICE_OFF = 0.06;

  let bgmKeepAliveTimer = null;

  class BgmEngine {
    constructor(urls) {
      this.urls = urls;
      this.ctx = null;
      this.masterGain = null;
      this.buffers = new Map();

      this.currentName = null;
      this.currentSource = null;
      this.currentSourceGain = null;

      this.playGeneration = 0;
      this.targetVolume = BGM_VOLUME_VOICE_OFF;
    }

    ensureContext() {
      const AudioContextClass =
        window.AudioContext ||
        window.webkitAudioContext;

      if (!AudioContextClass) {
        return false;
      }

      if (!this.ctx) {
        this.ctx = new AudioContextClass({
          latencyHint: "interactive"
        });

        this.masterGain =
          this.ctx.createGain();

        this.masterGain.gain.value =
          this.targetVolume;

        this.masterGain.connect(
          this.ctx.destination
        );
      }

      // resume() は非同期だが、ここでは呼び出し自体を
      // ユーザー操作と同じイベント内で開始する。
      if (this.ctx.state !== "running") {
        this.ctx.resume().catch(() => {});
      }

      return true;
    }

    async ensureRunning() {
      if (!this.ensureContext()) {
        return false;
      }

      if (this.ctx.state !== "running") {
        try {
          await this.ctx.resume();
        } catch (error) {
          return false;
        }
      }

      return this.ctx.state === "running";
    }

    setVolume(value, rampSeconds = 0.12) {
      this.targetVolume = value;

      if (
        !this.ctx ||
        !this.masterGain
      ) {
        return;
      }

      const now = this.ctx.currentTime;
      const gain = this.masterGain.gain;

      gain.cancelScheduledValues(now);
      gain.setValueAtTime(
        Math.max(0.0001, gain.value),
        now
      );
      gain.linearRampToValueAtTime(
        value,
        now + rampSeconds
      );
    }

    async loadBuffer(name) {
      if (this.buffers.has(name)) {
        return this.buffers.get(name);
      }

      const url = this.urls[name];

      if (!url) {
        throw new Error(
          `BGM URLがありません: ${name}`
        );
      }

      const ready =
        await this.ensureRunning();

      if (!ready) {
        throw new Error(
          "Web Audioを開始できません。"
        );
      }

      const response = await fetch(
        url,
        {
          method: "GET",
          cache: "force-cache",
          mode: "cors"
        }
      );

      if (!response.ok) {
        throw new Error(
          `BGM取得失敗: ${response.status}`
        );
      }

      const arrayBuffer =
        await response.arrayBuffer();

      const decoded =
        await this.ctx.decodeAudioData(
          arrayBuffer.slice(0)
        );

      this.buffers.set(name, decoded);
      return decoded;
    }

    async play(name, force = false) {
      if (!name) {
        return false;
      }

      this.ensureContext();

      if (
        !force &&
        this.currentName === name &&
        this.currentSource
      ) {
        await this.ensureRunning();
        return true;
      }

      const generation =
        ++this.playGeneration;

      let buffer;

      try {
        buffer =
          await this.loadBuffer(name);
      } catch (error) {
        console.error(
          "BGM load error",
          error
        );
        return false;
      }

      if (
        generation !==
        this.playGeneration
      ) {
        return false;
      }

      const ready =
        await this.ensureRunning();

      if (!ready) {
        return false;
      }

      const newSource =
        this.ctx.createBufferSource();

      const newSourceGain =
        this.ctx.createGain();

      newSource.buffer = buffer;
      newSource.loop = true;

      newSourceGain.gain.value = 0.0001;

      newSource.connect(newSourceGain);
      newSourceGain.connect(
        this.masterGain
      );

      const oldSource =
        this.currentSource;

      const oldSourceGain =
        this.currentSourceGain;

      const now = this.ctx.currentTime;

      newSource.start(0);

      newSourceGain.gain.setValueAtTime(
        0.0001,
        now
      );

      newSourceGain.gain.linearRampToValueAtTime(
        1.0,
        now + 0.18
      );

      this.currentName = name;
      this.currentSource = newSource;
      this.currentSourceGain =
        newSourceGain;

      if (
        oldSource &&
        oldSourceGain
      ) {
        try {
          oldSourceGain.gain
            .cancelScheduledValues(now);

          oldSourceGain.gain
            .setValueAtTime(
              Math.max(
                0.0001,
                oldSourceGain.gain.value
              ),
              now
            );

          oldSourceGain.gain
            .linearRampToValueAtTime(
              0.0001,
              now + 0.18
            );

          setTimeout(() => {
            try {
              oldSource.stop();
            } catch (error) {}
            try {
              oldSource.disconnect();
            } catch (error) {}
            try {
              oldSourceGain.disconnect();
            } catch (error) {}
          }, 230);
        } catch (error) {}
      }

      return true;
    }

    async keepAlive() {
      const ready =
        await this.ensureRunning();

      if (!ready) {
        return false;
      }

      // マイク開始時にブラウザがAudioContextを
      // 一時停止しても、ここでは同じ再生ノードを維持する。
      // BGMのpause/startは行わない。
      return true;
    }

    stop() {
      ++this.playGeneration;

      if (this.currentSource) {
        try {
          this.currentSource.stop();
        } catch (error) {}

        try {
          this.currentSource.disconnect();
        } catch (error) {}
      }

      if (this.currentSourceGain) {
        try {
          this.currentSourceGain.disconnect();
        } catch (error) {}
      }

      this.currentSource = null;
      this.currentSourceGain = null;
      this.currentName = null;
    }

    hasActiveSource() {
      return Boolean(
        this.currentSource &&
        this.currentName
      );
    }
  }

  const bgmEngine =
    new BgmEngine(BGM_URLS);

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

  function loadChallengeCounts() {
    try {
      const raw =
        localStorage.getItem(
          CHALLENGE_COUNT_STORAGE_KEY
        );

      if (!raw) {
        return {};
      }

      const parsed =
        JSON.parse(raw);

      if (
        !parsed ||
        typeof parsed !== "object" ||
        Array.isArray(parsed)
      ) {
        return {};
      }

      return parsed;
    } catch (error) {
      return {};
    }
  }

  function saveChallengeCounts() {
    try {
      localStorage.setItem(
        CHALLENGE_COUNT_STORAGE_KEY,
        JSON.stringify(
          challengeCounts
        )
      );
    } catch (error) {
      // 保存できなくてもゲーム自体は継続する。
    }
  }

  function getChallengeCount(mode) {
    return Math.max(
      0,
      Math.floor(
        Number(
          challengeCounts[mode]
        ) || 0
      )
    );
  }

  function incrementChallengeCount(mode) {
    const next =
      getChallengeCount(mode) + 1;

    challengeCounts[mode] = next;
    saveChallengeCounts();

    updateModeChallengeCountLabels();

    return next;
  }

  function modeVoiceName(mode) {
    const title =
      modeInfo[mode]?.title ||
      mode;

    return String(title)
      .split("｜")[0];
  }

  function updateModeChallengeCountLabels() {
    root
      .querySelectorAll(
        ".mode-challenge-count"
      )
      .forEach((node) => {
        const mode =
          node.dataset.mode;

        if (!mode) {
          return;
        }

        node.textContent =
          `総チャレンジ ${getChallengeCount(mode)}回`;
      });
  }

  function setupModeChallengeCountLabels() {
    root
      .querySelectorAll(
        ".start-mode"
      )
      .forEach((startButton) => {
        const mode =
          startButton.dataset.mode;

        if (!mode) {
          return;
        }

        const card =
          startButton.closest(
            ".mode-card"
          );

        if (!card) {
          return;
        }

        if (
          card.querySelector(
            `.mode-challenge-count[data-mode="${mode}"]`
          )
        ) {
          return;
        }

        const label =
          document.createElement(
            "div"
          );

        label.className =
          "mode-challenge-count";

        label.dataset.mode =
          mode;

        startButton.insertAdjacentElement(
          "beforebegin",
          label
        );
      });

    updateModeChallengeCountLabels();
  }

  function loadScoreRankings() {
    try {
      const raw =
        localStorage.getItem(
          RANKING_STORAGE_KEY
        );

      if (!raw) {
        return { modes: {} };
      }

      const parsed =
        JSON.parse(raw);

      if (
        !parsed ||
        typeof parsed !== "object"
      ) {
        return { modes: {} };
      }

      if (
        !parsed.modes ||
        typeof parsed.modes !== "object"
      ) {
        parsed.modes = {};
      }

      return parsed;
    } catch (error) {
      return { modes: {} };
    }
  }

  function saveScoreRankings() {
    try {
      localStorage.setItem(
        RANKING_STORAGE_KEY,
        JSON.stringify(
          scoreRankings
        )
      );
    } catch (error) {
      // 保存できなくてもゲーム自体は継続する。
    }
  }

  function rankingEntriesForMode(mode) {
    const entries =
      scoreRankings.modes[mode];

    if (!Array.isArray(entries)) {
      return [];
    }

    return [...entries].sort(
      (a, b) =>
        (b.score - a.score) ||
        (b.correctCount - a.correctCount) ||
        (b.maxStreak - a.maxStreak) ||
        (b.remainingSeconds - a.remainingSeconds) ||
        (a.playedAt - b.playedAt)
    );
  }

  function addScoreRanking(
    mode,
    scoreInfo,
    timeup
  ) {
    if (!mode || !scoreInfo) {
      return;
    }

    if (
      !scoreRankings.modes[mode] ||
      !Array.isArray(
        scoreRankings.modes[mode]
      )
    ) {
      scoreRankings.modes[mode] = [];
    }

    const entry = {
      id:
        `${Date.now()}-` +
        Math.random()
          .toString(36)
          .slice(2, 9),
      score:
        Number(scoreInfo.finalScore) || 0,
      correctCount:
        Number(scoreInfo.correctCount) || 0,
      maxStreak:
        Number(scoreInfo.maxStreak) || 0,
      remainingSeconds:
        Number(scoreInfo.remainingSeconds) || 0,
      wrongCount:
        Number(scoreInfo.wrongCount) || 0,
      timeup:
        Boolean(timeup),
      playedAt:
        Date.now()
    };

    scoreRankings.modes[mode].push(
      entry
    );

    scoreRankings.modes[mode] =
      rankingEntriesForMode(mode)
        .slice(
          0,
          MAX_RANKING_ENTRIES_PER_MODE
        );

    saveScoreRankings();
  }

  function deleteRankingEntry(
    mode,
    entryId
  ) {
    const entries =
      scoreRankings.modes[mode];

    if (!Array.isArray(entries)) {
      return;
    }

    scoreRankings.modes[mode] =
      entries.filter(
        (entry) =>
          entry.id !== entryId
      );

    saveScoreRankings();

    if (currentMode === mode) {
      renderResultRanking(mode);
    }

    if (rankingModalMode === mode) {
      renderRankingList(
        rankingModalList,
        mode
      );
    }
  }

  function formatRankingTime(
    secondsValue
  ) {
    const safe =
      Math.max(
        0,
        Math.floor(
          Number(secondsValue) || 0
        )
      );

    const minutes =
      Math.floor(safe / 60);

    const secondsPart =
      safe % 60;

    return (
      `${minutes}:` +
      String(secondsPart)
        .padStart(2, "0")
    );
  }

  function formatRankingDate(
    timestamp
  ) {
    try {
      return new Date(timestamp)
        .toLocaleString(
          "ja-JP",
          {
            month: "numeric",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit"
          }
        );
    } catch (error) {
      return "";
    }
  }

  function renderRankingList(
    container,
    mode
  ) {
    if (!container) {
      return;
    }

    container.innerHTML = "";

    const entries =
      rankingEntriesForMode(mode);

    if (entries.length === 0) {
      const empty =
        document.createElement(
          "div"
        );

      empty.className =
        "ranking-empty";

      empty.textContent =
        "まだ得点記録がありません。";

      container.appendChild(empty);
      return;
    }

    entries.forEach(
      (entry, index) => {
        const row =
          document.createElement(
            "div"
          );

        row.className =
          "ranking-row";

        const place =
          document.createElement(
            "div"
          );

        place.className =
          "ranking-place";

        place.textContent =
          `${index + 1}`;

        const main =
          document.createElement(
            "div"
          );

        main.className =
          "ranking-main";

        const scoreEl =
          document.createElement(
            "div"
          );

        scoreEl.className =
          "ranking-score";

        scoreEl.textContent =
          `${entry.score.toLocaleString()}点`;

        const detail =
          document.createElement(
            "div"
          );

        detail.className =
          "ranking-detail";

        detail.textContent =
          `${entry.correctCount}/${TOTAL_QUESTIONS}正解` +
          ` ・ 最高${entry.maxStreak}連続` +
          ` ・ 残り${formatRankingTime(entry.remainingSeconds)}` +
          ` ・ ${formatRankingDate(entry.playedAt)}`;

        const deleteBtn =
          document.createElement(
            "button"
          );

        deleteBtn.type =
          "button";

        deleteBtn.className =
          "ranking-delete";

        deleteBtn.textContent =
          "削除";

        deleteBtn.addEventListener(
          "click",
          () => {
            const ok =
              window.confirm(
                "この得点記録を削除しますか？"
              );

            if (!ok) {
              return;
            }

            deleteRankingEntry(
              mode,
              entry.id
            );
          }
        );

        main.appendChild(scoreEl);
        main.appendChild(detail);

        row.appendChild(place);
        row.appendChild(main);
        row.appendChild(deleteBtn);

        container.appendChild(row);
      }
    );
  }

  function renderResultRanking(mode) {
    renderRankingList(
      resultRankingList,
      mode
    );
  }

  function openRankingModal(mode) {
    rankingModalMode = mode;

    rankingModalTitle.textContent =
      `${modeInfo[mode].title}｜得点ランキング`;

    renderRankingList(
      rankingModalList,
      mode
    );

    rankingModal.classList.add(
      "show"
    );

    rankingModal.setAttribute(
      "aria-hidden",
      "false"
    );
  }

  function closeRankingModal() {
    rankingModalMode = null;

    rankingModal.classList.remove(
      "show"
    );

    rankingModal.setAttribute(
      "aria-hidden",
      "true"
    );
  }

  function setupModeRankingButtons() {
    root
      .querySelectorAll(
        ".start-mode"
      )
      .forEach((startButton) => {
        const mode =
          startButton.dataset.mode;

        if (!mode) {
          return;
        }

        const button =
          document.createElement(
            "button"
          );

        button.type =
          "button";

        button.className =
          "ranking-open-btn";

        button.dataset.mode =
          mode;

        button.textContent =
          "過去の得点ランキング（5分）";

        button.addEventListener(
          "click",
          () => {
            openRankingModal(mode);
          }
        );

        startButton.insertAdjacentElement(
          "afterend",
          button
        );
      });
  }

  function loadLearningStats() {
    try {
      const raw = localStorage.getItem(LEARNING_STORAGE_KEY);
      if (!raw) {
        return { problems: {} };
      }

      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object") {
        return { problems: {} };
      }

      if (!parsed.problems || typeof parsed.problems !== "object") {
        parsed.problems = {};
      }

      return parsed;
    } catch (error) {
      return { problems: {} };
    }
  }

  function saveLearningStats() {
    try {
      localStorage.setItem(
        LEARNING_STORAGE_KEY,
        JSON.stringify(learningStats)
      );
    } catch (error) {
      // 保存できない環境でもゲーム自体は継続する。
    }
  }

  function problemKey(mode, q) {
    return `${mode}|${q.op}|${q.a}|${q.b}`;
  }

  function getProblemStat(mode, q) {
    const key = problemKey(mode, q);

    if (!learningStats.problems[key]) {
      learningStats.problems[key] = {
        key,
        mode,
        a: q.a,
        b: q.b,
        op: q.op,
        attempts: 0,
        correct: 0,
        wrong: 0,
        recoveryStreak: 0,
        mastered: false,
        lastAt: 0
      };
    }

    return learningStats.problems[key];
  }

  function recordAnswer(mode, q, ok) {
    const stat = getProblemStat(mode, q);

    stat.attempts += 1;
    stat.lastAt = Date.now();

    if (ok) {
      stat.correct += 1;

      if (q.isWeakness) {
        stat.recoveryStreak += 1;

        if (stat.recoveryStreak >= RECOVERY_STREAK_TO_MASTER) {
          stat.mastered = true;
        }
      }
    } else {
      stat.wrong += 1;
      stat.recoveryStreak = 0;
      stat.mastered = false;
    }

    saveLearningStats();
  }

  function getWeakCandidates(mode) {
    return Object.values(learningStats.problems)
      .filter((stat) =>
        stat.mode === mode &&
        stat.wrong > 0 &&
        !stat.mastered
      )
      .sort((a, b) => {
        const scoreA =
          a.wrong * 4 -
          a.correct +
          Math.max(0, 2 - a.recoveryStreak) * 2;

        const scoreB =
          b.wrong * 4 -
          b.correct +
          Math.max(0, 2 - b.recoveryStreak) * 2;

        if (scoreB !== scoreA) {
          return scoreB - scoreA;
        }

        return b.lastAt - a.lastAt;
      });
  }

  function statToWeakQuestion(stat) {
    const q = makeQuestionFromFinal(
      stat.a,
      stat.op,
      stat.b
    );

    q.isWeakness = true;
    q.weaknessKey = stat.key;

    return q;
  }

  function makeQuestionFromFinal(a, op, b) {
    const q = {
      a,
      op,
      b,
      answer: calculate(a, op, b),
      isWeakness: false,
      weaknessKey: null
    };

    if (!isValidQuestion(q)) {
      throw new Error(
        `苦手問題の復元に失敗: ${a} ${op} ${b}`
      );
    }

    return q;
  }

  function getWeaknessQuestion(mode) {
    const active = getWeakCandidates(mode);

    // 未克服の苦手だけを出題する。
    // 苦手克服問題として1回正解して mastered=true になった問題は
    // getWeakCandidates() の対象外になるため、二度と苦手枠には出ない。
    if (active.length === 0) {
      return null;
    }

    const source = active[0];

    return statToWeakQuestion(source);
  }

  function makeQuestionForIndex(questionIndex, mode) {
    // 1〜5問目は必ず通常問題。
    if (questionIndex < 5) {
      const q = makeOneQuestion(mode);
      q.isWeakness = false;
      return q;
    }

    // 6問目以降の指定スロットでは苦手問題を優先。
    if (WEAKNESS_SLOTS.has(questionIndex)) {
      const weak = getWeaknessQuestion(mode);

      if (weak) {
        sessionWeakAsked += 1;
        return weak;
      }
    }

    const q = makeOneQuestion(mode);
    q.isWeakness = false;
    return q;
  }

  function shouldLevelUp(mode, finalScore) {
    const activeWeakLeft = getWeakCandidates(mode).length;

    // 苦手克服問題が出た場合：
    // 出た苦手問題をすべてクリアし、未克服が残っておらず、
    // 全体でも10/12以上なら次のレベルへ。
    if (sessionWeakAsked > 0) {
      return (
        sessionWeakCorrect === sessionWeakAsked &&
        activeWeakLeft === 0 &&
        finalScore >= 10
      );
    }

    // 苦手が記録されていない場合は11/12以上でレベルアップ。
    return activeWeakLeft === 0 && finalScore >= 11;
  }

  function makeOneQuestion(mode) {
    if (mode === "ba1") return makeAdditionOnly(1, 9);
    if (mode === "ba2") return makeAdditionOnly(10, 99);
    if (mode === "ba3") return makeAdditionOnly(100, 999);

    if (mode === "bs1") return makeSubtractionOnly(1, 9);
    if (mode === "bs2") return makeSubtractionOnly(10, 99);
    if (mode === "bs3") return makeSubtractionOnly(100, 999);

    if (mode === "mm1") {
      return makeMul(1, 9, 1, 9);
    }

    if (mode === "mm2") {
      return makeMul(10, 99, 1, 9);
    }

    if (mode === "mm3") {
      return makeMul(10, 99, 10, 99);
    }

    if (mode === "md1") {
      return makeExactDivision(1, 81, 1, 9);
    }

    if (mode === "md2") {
      return makeExactDivision(100, 999, 1, 9);
    }

    if (mode === "md3") {
      return makeExactDivision(100, 999, 10, 99);
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
    // 問題はセッション中に1問ずつ生成する。
    // これにより最初の5問で見つかった苦手も、
    // 6問目以降の苦手克服問題へ反映できる。
    return [];
  }

  function placeName(place) {
    const names = {
      1: "一の位",
      10: "十の位",
      100: "百の位",
      1000: "千の位",
      10000: "万の位",
      100000: "十万の位",
      1000000: "百万の位"
    };

    return names[place] || `${place}の位`;
  }

  function shortPlaceName(place) {
    const names = {
      1: "一",
      10: "十",
      100: "百",
      1000: "千",
      10000: "万",
      100000: "十万",
      1000000: "百万"
    };

    return names[place] || "";
  }

  function buildSorobanBoard(digitCount) {
    hintDigitCount = Math.max(1, digitCount);
    hintRods = [];
    sorobanBoard.innerHTML = "";

    for (let i = 0; i < hintDigitCount; i += 1) {
      const place = 10 ** (hintDigitCount - 1 - i);

      const rod = document.createElement("div");
      rod.className = "soroban-rod";
      rod.dataset.place = String(place);

      const line = document.createElement("div");
      line.className = "rod-line";
      rod.appendChild(line);

      const upper = document.createElement("div");
      upper.className = "soroban-bead upper-bead";
      rod.appendChild(upper);

      const lowers = [];

      for (let j = 0; j < 4; j += 1) {
        const bead = document.createElement("div");
        bead.className = "soroban-bead lower-bead";
        bead.style.top = `${112 + j * 18}px`;
        rod.appendChild(bead);
        lowers.push(bead);
      }

      const label = document.createElement("div");
      label.className = "rod-place";
      label.textContent = shortPlaceName(place);
      rod.appendChild(label);

      sorobanBoard.appendChild(rod);

      hintRods.push({
        rod,
        place,
        upper,
        lowers
      });
    }
  }

  function setRodDigit(rodInfo, digit) {
    const safeDigit = Math.max(0, Math.min(9, Number(digit) || 0));
    const upperOn = safeDigit >= 5;
    const lowerCount = safeDigit % 5;

    rodInfo.upper.style.top =
      upperOn ? "50px" : "13px";

    rodInfo.lowers.forEach((bead, index) => {
      const top = index < lowerCount
        ? 89 + index * 18
        : 121 + index * 18;

      bead.style.top = `${top}px`;
    });
  }

  function showSorobanNumber(value, activePlace = null) {
    const safeValue = Math.max(
      0,
      Math.floor(Math.abs(Number(value) || 0))
    );

    const digits = String(safeValue)
      .padStart(hintDigitCount, "0")
      .slice(-hintDigitCount)
      .split("")
      .map(Number);

    hintRods.forEach((rodInfo, index) => {
      setRodDigit(rodInfo, digits[index]);

      rodInfo.rod.classList.toggle(
        "active",
        activePlace !== null &&
        rodInfo.place === activePlace
      );
    });
  }

  function decomposeByPlace(value) {
    const out = [];
    const digits = String(Math.abs(Math.floor(value))).split("");

    digits.forEach((char, index) => {
      const digit = Number(char);
      if (digit === 0) return;

      const place =
        10 ** (digits.length - 1 - index);

      out.push({
        digit,
        place,
        amount: digit * place
      });
    });

    return out;
  }

  function buildAddSubHintSteps(q) {
    const steps = [
      {
        value: q.a,
        activePlace: null,
        text: `まず ${q.a} をそろばんに置きます。`
      }
    ];

    const parts = decomposeByPlace(q.b);
    let current = q.a;

    parts.forEach((part) => {
      if (q.op === "＋") {
        current += part.amount;

        steps.push({
          value: current,
          activePlace: part.place,
          text:
            `${placeName(part.place)}で ${part.amount} を足します。` +
            ` 光っている位の珠の動きを見てね。`
        });
      } else {
        current -= part.amount;

        steps.push({
          value: current,
          activePlace: part.place,
          text:
            `${placeName(part.place)}で ${part.amount} をひきます。` +
            ` 光っている位の珠の動きを見てね。`
        });
      }
    });

    steps.push({
      value: q.answer,
      activePlace: null,
      text: `この珠の形で完成です。`
    });

    return steps;
  }

  function buildResultPlacementSteps(q) {
    const answer = Math.max(0, Math.floor(q.answer));
    const parts = decomposeByPlace(answer);

    const steps = [
      {
        value: 0,
        activePlace: null,
        text:
          q.op === "×"
            ? "掛け算では、答えの珠の置き方を位ごとに見てみます。"
            : "割り算では、答えの珠の置き方を位ごとに見てみます。"
      }
    ];

    let current = 0;

    parts.forEach((part) => {
      current += part.amount;

      steps.push({
        value: current,
        activePlace: part.place,
        text:
          `${placeName(part.place)}に ${part.digit} を置きます。`
      });
    });

    steps.push({
      value: answer,
      activePlace: null,
      text: "この珠の形で完成です。"
    });

    return steps;
  }

  function buildHintSteps(q) {
    if (q.op === "＋" || q.op === "－") {
      return buildAddSubHintSteps(q);
    }

    return buildResultPlacementSteps(q);
  }

  function stopSorobanHintAnimation() {
    hintRunToken += 1;
  }

  function hideSorobanHint() {
    stopSorobanHintAnimation();
    abacusHint.classList.remove("show");
    hintStep.textContent = "";
    sorobanBoard.innerHTML = "";
    hintRods = [];
  }

  function runSorobanHint() {
    if (index >= TOTAL_QUESTIONS || !questions[index]) {
      return;
    }

    const q = questions[index];
    const steps = buildHintSteps(q);

    const maxValue = Math.max(
      q.a,
      q.b,
      Math.abs(q.answer),
      ...steps.map((step) => Math.abs(step.value))
    );

    const digitCount = Math.max(
      1,
      String(Math.floor(maxValue)).length
    );

    stopSorobanHintAnimation();
    const token = hintRunToken;

    buildSorobanBoard(digitCount);
    abacusHint.classList.add("show");

    // 1周を約5秒にする。
    // ステップ数に応じて自動的に間隔を調整する。
    const cycleMs = 5000;
    const stepDelay = Math.max(
      550,
      Math.floor(cycleMs / Math.max(1, steps.length))
    );

    let stepIndex = 0;

    const showStep = () => {
      if (
        token !== hintRunToken ||
        !abacusHint.classList.contains("show")
      ) {
        return;
      }

      const step = steps[stepIndex];

      hintStep.textContent = step.text;

      showSorobanNumber(
        step.value,
        step.activePlace
      );

      stepIndex += 1;

      if (stepIndex >= steps.length) {
        stepIndex = 0;
      }

      // ヒントを閉じる／次の問題へ進むまで自動ループ。
      setTimeout(showStep, stepDelay);
    };

    showStep();
  }

  function getTargetBgmVolume() {
    // 音声回答ON/OFFともにBGMは6%固定。
    return voiceAnswerEnabled
      ? BGM_VOLUME_VOICE_ON
      : BGM_VOLUME_VOICE_OFF;
  }

  function refreshBgmVolume() {
    bgmEngine.setVolume(
      getTargetBgmVolume()
    );
  }

  function startBgmKeepAlive() {
    if (bgmKeepAliveTimer) {
      return;
    }

    bgmKeepAliveTimer =
      setInterval(() => {
        if (
          !bgmOn ||
          !voiceAnswerEnabled ||
          !workspace.classList.contains("show") ||
          results.classList.contains("show")
        ) {
          return;
        }

        // 音声認識中にブラウザがAudioContextを
        // suspendしていないか定期的に確認する。
        bgmEngine.keepAlive();

        if (
          currentBgm &&
          !bgmEngine.hasActiveSource()
        ) {
          bgmEngine.play(
            currentBgm,
            true
          );
        }

        refreshBgmVolume();
      }, 400);
  }

  function stopBgmKeepAlive() {
    if (!bgmKeepAliveTimer) {
      return;
    }

    clearInterval(
      bgmKeepAliveTimer
    );

    bgmKeepAliveTimer = null;
  }

  function chooseRandomTrack(tracks) {
    return tracks[
      Math.floor(
        Math.random() * tracks.length
      )
    ];
  }

  function desiredBgmName(streak) {
    let groupKey;
    let tracks;

    if (streak <= 2) {
      groupKey = "1-3";
      tracks = [
        "1.mp3",
        "2.mp3",
        "3.mp3"
      ];
    } else if (streak <= 5) {
      groupKey = "4-6";
      tracks = [
        "4.mp3",
        "5.mp3",
        "6.mp3"
      ];
    } else if (streak <= 9) {
      groupKey = "7-9";
      tracks = [
        "7.mp3",
        "8.mp3",
        "9.mp3"
      ];
    } else {
      groupKey = "10";
      tracks = [
        "10-1.mp3",
        "10-2.mp3",
        "10-3.mp3"
      ];
    }

    // 同じ連続正解帯の中では、選んだ曲をそのまま流す。
    if (
      currentBgmGroupKey === groupKey &&
      currentBgm &&
      tracks.includes(currentBgm)
    ) {
      return currentBgm;
    }

    // 次の帯に入った時だけ、その帯からランダム選択。
    currentBgmGroupKey = groupKey;

    return chooseRandomTrack(tracks);
  }

  function updateBgmButton() {
    bgmBtn.textContent =
      bgmOn
        ? "♪ BGM ON"
        : "♪ BGM OFF";
  }

  function playBgmForStreak(
    streak,
    force = false
  ) {
    const name =
      desiredBgmName(streak);

    currentBgm = name;

    bgmName.textContent =
      `BGM：${name}`;

    if (!bgmOn) {
      return;
    }

    // ここではマイク状態にかかわらず
    // BGM再生ノードを継続する。
    bgmEngine.setVolume(
      getTargetBgmVolume(),
      0.08
    );

    bgmEngine
      .play(name, force)
      .then((ok) => {
        if (!ok) {
          bgmName.textContent =
            `BGM：${name}（再生できません）`;
          return;
        }

        refreshBgmVolume();
      })
      .catch(() => {
        bgmName.textContent =
          `BGM：${name}（再生できません）`;
      });
  }

  function stopBgm() {
    stopBgmKeepAlive();
    bgmEngine.stop();
  }

  function toggleBgm() {
    bgmOn = !bgmOn;
    updateBgmButton();

    if (
      bgmOn &&
      workspace.classList.contains("show") &&
      !results.classList.contains("show")
    ) {
      // BGMボタンはユーザー操作なので、
      // このイベント内でAudioContextを起動する。
      bgmEngine.ensureContext();

      playBgmForStreak(
        correctStreak,
        true
      );

      if (voiceAnswerEnabled) {
        startBgmKeepAlive();
      }
    } else {
      stopBgm();
    }
  }


  function getSpeechRecognitionClass() {
    return (
      window.SpeechRecognition ||
      window.webkitSpeechRecognition ||
      null
    );
  }

  function japaneseDigitValue(char) {
    const values = {
      "〇": 0,
      "零": 0,
      "一": 1,
      "二": 2,
      "三": 3,
      "四": 4,
      "五": 5,
      "六": 6,
      "七": 7,
      "八": 8,
      "九": 9
    };

    if (
      Object.prototype.hasOwnProperty
        .call(values, char)
    ) {
      return values[char];
    }

    return null;
  }

  function japaneseIntegerToNumber(input) {
    const original =
      String(input || "");

    const compact =
      original
        .replace(
          /[,\s、。,.]/g,
          ""
        )
        .replace(
          /マイナス|minus/gi,
          "-"
        );

    if (!compact) {
      return null;
    }

    // 「15」のように数字で認識された場合。
    const direct =
      compact.match(/-?\d+/);

    if (direct) {
      const value =
        Number(direct[0]);

      return Number.isFinite(value)
        ? value
        : null;
    }

    // ひらがな認識も漢数字へ寄せる。
    const normalized =
      compact
        .replace(/いち/g, "一")
        .replace(/に/g, "二")
        .replace(/さん/g, "三")
        .replace(/よん|し/g, "四")
        .replace(/ご/g, "五")
        .replace(/ろく/g, "六")
        .replace(/なな|しち/g, "七")
        .replace(/はち/g, "八")
        .replace(/きゅう|く/g, "九")
        .replace(/れい|ぜろ/g, "零")
        .replace(/じゅう/g, "十")
        .replace(/ひゃく/g, "百")
        .replace(/せん/g, "千")
        .replace(/まん/g, "万");

    if (
      !/[一二三四五六七八九〇零十百千万]/
        .test(normalized)
    ) {
      return null;
    }

    let total = 0;
    let section = 0;
    let number = 0;

    const negative =
      normalized.startsWith("-");

    const chars =
      normalized
        .replace("-", "");

    for (const char of chars) {
      const digit =
        japaneseDigitValue(char);

      if (digit !== null) {
        number = digit;
        continue;
      }

      if (
        char === "十" ||
        char === "百" ||
        char === "千"
      ) {
        const unit =
          char === "十"
            ? 10
            : char === "百"
              ? 100
              : 1000;

        section +=
          (number || 1) * unit;

        number = 0;
        continue;
      }

      if (char === "万") {
        section += number;

        total +=
          (section || 1) *
          10000;

        section = 0;
        number = 0;
      }
    }

    const value =
      total +
      section +
      number;

    return negative
      ? -value
      : value;
  }

  function updateVoiceUi(
    message = null
  ) {
    const supported =
      Boolean(
        getSpeechRecognitionClass()
      );

    if (!supported) {
      voiceBtn.disabled = true;
      voiceBtn.textContent =
        "🎤 音声回答 非対応";

      voiceStatus.textContent =
        "このブラウザでは音声回答を利用できません。";

      voiceStatus.classList.remove(
        "listening"
      );

      return;
    }

    voiceBtn.disabled = false;

    voiceBtn.classList.toggle(
      "on",
      voiceAnswerEnabled
    );

    voiceBtn.textContent =
      voiceAnswerEnabled
        ? "🎤 音声回答 ON"
        : "🎤 音声回答 OFF";

    voiceStatus.textContent =
      message ||
      (
        voiceAnswerEnabled
          ? "音声回答：数字を話してください"
          : "音声回答：OFF"
      );

    voiceStatus.classList.toggle(
      "listening",
      voiceAnswerEnabled &&
      voiceRecognitionRunning &&
      !voicePauseForFeedback
    );
  }

  function clearVoiceRestartTimer() {
    if (!voiceRestartTimer) {
      return;
    }

    clearTimeout(
      voiceRestartTimer
    );

    voiceRestartTimer = null;
  }

  function stopVoiceRecognition() {
    clearVoiceRestartTimer();

    if (!voiceRecognition) {
      voiceRecognitionRunning = false;
      refreshBgmVolume();
      return;
    }

    if (voiceRecognitionRunning) {
      try {
        voiceRecognition.stop();
      } catch (error) {}
    }
  }

  function scheduleVoiceRestart(
    delay = 280
  ) {
    if (
      !voiceAnswerEnabled ||
      voicePauseForFeedback ||
      locked ||
      !workspace.classList.contains("show") ||
      results.classList.contains("show")
    ) {
      return;
    }

    clearVoiceRestartTimer();

    voiceRestartTimer =
      setTimeout(() => {
        startVoiceRecognition();
      }, delay);
  }

  function handleRecognizedSpeech(
    event
  ) {
    if (
      locked ||
      !voiceAnswerEnabled ||
      voicePauseForFeedback ||
      voiceCalloutRunning
    ) {
      return;
    }

    const result =
      event.results?.[0];

    if (!result) {
      return;
    }

    const alternatives = [];

    for (
      let i = 0;
      i < result.length;
      i += 1
    ) {
      alternatives.push(
        result[i].transcript
      );
    }

    let parsed = null;
    let recognizedText = "";

    for (
      const transcript
      of alternatives
    ) {
      const value =
        japaneseIntegerToNumber(
          transcript
        );

      if (
        value !== null &&
        Number.isInteger(value) &&
        value >= 0
      ) {
        parsed = value;
        recognizedText =
          transcript;
        break;
      }
    }

    if (parsed === null) {
      updateVoiceUi(
        `音声回答：「${alternatives[0] || ""}」を数字として認識できませんでした`
      );
      return;
    }

    answerInput.value =
      String(parsed);

    updateVoiceUi(
      `音声回答：「${recognizedText}」→ ${parsed}`
    );

    stopVoiceRecognition();

    setTimeout(() => {
      if (!locked) {
        submitAnswer();
      }
    }, 160);
  }

  function createVoiceRecognition() {
    const Recognition =
      getSpeechRecognitionClass();

    if (!Recognition) {
      return null;
    }

    const recognition =
      new Recognition();

    recognition.lang = "ja-JP";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 5;

    recognition.onstart = () => {
      voiceRecognitionRunning = true;

      refreshBgmVolume();
      bgmEngine.ensureRunning();
      startBgmKeepAlive();

      updateVoiceUi(
        "音声回答：聞き取り中"
      );

      // ① ゴワサン終了
      // ② マイクの onstart を確認
      // ③ ここで初めて問題を生成・表示する
      renderQuestion(true);

      updateVoiceUi(
        "音声回答：数字を話してください"
      );
    };

    recognition.onresult =
      handleRecognizedSpeech;

    recognition.onend = () => {
      voiceRecognitionRunning = false;

      refreshBgmVolume();
      bgmEngine.ensureRunning();

      if (
        voiceAnswerEnabled &&
        !voicePauseForFeedback &&
        !voiceCalloutRunning &&
        !locked &&
        workspace.classList.contains("show") &&
        !results.classList.contains("show")
      ) {
        // 無音や認識失敗で終了した場合も、
        // 次回は必ず「ゴワサン！」から再開する。
        scheduleVoiceRestart(350);
      } else {
        updateVoiceUi();
      }
    };

    recognition.onerror = (
      event
    ) => {
      voiceRecognitionRunning = false;

      refreshBgmVolume();
      bgmEngine.ensureRunning();

      if (
        event.error ===
        "not-allowed"
      ) {
        voiceAnswerEnabled = false;
        voiceCalloutRunning = false;
        stopBgmKeepAlive();

        updateVoiceUi(
          "マイクが許可されていません。ブラウザでマイクを許可してください。"
        );
        return;
      }

      if (
        event.error === "no-speech" ||
        event.error === "aborted"
      ) {
        if (
          voiceAnswerEnabled &&
          !voicePauseForFeedback &&
          !voiceCalloutRunning &&
          !locked
        ) {
          scheduleVoiceRestart(
            380
          );
        }
        return;
      }

      updateVoiceUi(
        `音声回答：${event.error}`
      );

      if (
        voiceAnswerEnabled &&
        !voicePauseForFeedback &&
        !voiceCalloutRunning &&
        !locked
      ) {
        scheduleVoiceRestart(500);
      }
    };

    return recognition;
  }

  function startMicrophoneRecognition() {
    if (
      !voiceAnswerEnabled ||
      voicePauseForFeedback ||
      voiceCalloutRunning ||
      locked ||
      voiceRecognitionRunning ||
      results.classList.contains("show") ||
      !workspace.classList.contains("show")
    ) {
      return;
    }

    if (!voiceRecognition) {
      voiceRecognition =
        createVoiceRecognition();
    }

    if (!voiceRecognition) {
      updateVoiceUi();
      return;
    }

    bgmEngine.ensureContext();
    bgmEngine.ensureRunning();

    if (
      bgmOn &&
      currentBgm &&
      !bgmEngine.hasActiveSource()
    ) {
      bgmEngine.play(
        currentBgm,
        true
      );
    }

    refreshBgmVolume();

    try {
      voiceRecognition.start();
    } catch (error) {
      scheduleVoiceRestart(500);
    }
  }

  function hideQuestionForVoiceCallout() {
    questionCard.classList.add(
      "voice-waiting"
    );
  }

  function revealQuestionAfterVoiceCallout() {
    questionCard.classList.remove(
      "voice-waiting"
    );

    // 表示された瞬間にレイアウトを確定。
    void questionCard.offsetWidth;
  }

  function speakGowasanThenListen() {
    if (
      !voiceAnswerEnabled ||
      voicePauseForFeedback ||
      voiceCalloutRunning ||
      locked ||
      voiceRecognitionRunning ||
      results.classList.contains("show") ||
      !workspace.classList.contains("show")
    ) {
      return;
    }

    voiceCalloutRunning = true;

    // 音声回答ON中は「ゴワサン！」が終わるまで問題を隠す。
    hideQuestionForVoiceCallout();

    // ① まず「ゴワサン！」を読み上げる。
    // この間、音声認識はまだ開始しない。
    updateVoiceUi(
      "音声回答：ゴワサン！"
    );

    voicePauseForFeedback = true;
    refreshBgmVolume();
    bgmEngine.ensureRunning();

    const beginListening = () => {
      voiceCalloutRunning = false;
      voicePauseForFeedback = false;

      // ゴワサン終了時点では、まだ問題は作らず表示もしない。
      // 次にマイクを開始し、recognition.onstart が発火してから
      // 初めて問題を生成・表示する。
      refreshBgmVolume();

      if (
        !voiceAnswerEnabled ||
        locked ||
        results.classList.contains("show")
      ) {
        return;
      }

      setTimeout(() => {
        startMicrophoneRecognition();
      }, 220);
    };

    if (
      !("speechSynthesis" in window) ||
      typeof SpeechSynthesisUtterance ===
        "undefined"
    ) {
      beginListening();
      return;
    }

    window.speechSynthesis.cancel();

    const utterance =
      new SpeechSynthesisUtterance(
        "ゴワサン！"
      );

    utterance.lang = "ja-JP";
    utterance.rate = 1.18;
    utterance.pitch = 1.35;
    utterance.volume = 0.95;

    const voice =
      getJapaneseVoice();

    if (voice) {
      utterance.voice = voice;
    }

    let finished = false;

    const done = () => {
      if (finished) {
        return;
      }

      finished = true;
      beginListening();
    };

    utterance.onend = done;
    utterance.onerror = done;

    window.speechSynthesis.speak(
      utterance
    );
  }

  function startVoiceRecognition() {
    // 音声入力を開始するたびに必ず
    // 「ゴワサン！」→マイク開始の順序にする。
    speakGowasanThenListen();
  }

  function setVoiceAnswerEnabled(
    enabled
  ) {
    voiceAnswerEnabled =
      Boolean(enabled);

    if (voiceAnswerEnabled) {
      bgmEngine.ensureContext();
      bgmEngine.ensureRunning();

      if (
        bgmOn &&
        currentBgm &&
        !bgmEngine.hasActiveSource()
      ) {
        bgmEngine.play(
          currentBgm,
          true
        );
      }

      startBgmKeepAlive();

      updateVoiceUi(
        "音声回答：開始します…"
      );

      // ボタンをONにした直後から問題を隠す。
      hideQuestionForVoiceCallout();

      startVoiceRecognition();
      return;
    }

    voiceCalloutRunning = false;
    voicePauseForFeedback = false;

    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }

    stopVoiceRecognition();
    stopBgmKeepAlive();

    refreshBgmVolume();

    // 音声モードをOFFにした場合は、
    // まだ作っていない現在の問題を通常モードとしてここで生成・表示。
    renderQuestion(true);

    updateVoiceUi(
      "音声回答：OFF"
    );
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

  function speakAnswerFeedback(
    ok,
    streak
  ) {
    // 判定音声中はマイクだけ一時停止。
    // BGM再生ノードは止めず、4%へGainを下げる。
    voicePauseForFeedback = true;

    stopVoiceRecognition();
    refreshBgmVolume();

    bgmEngine.ensureRunning();

    if (
      !("speechSynthesis" in window) ||
      typeof SpeechSynthesisUtterance ===
        "undefined"
    ) {
      voicePauseForFeedback = false;
      refreshBgmVolume();

      if (voiceAnswerEnabled) {
        scheduleVoiceRestart(280);
      }

      return;
    }

    window.speechSynthesis.cancel();

    const message =
      !ok
        ? "残念！"
        : streak >= 2
          ? `お見事！${streak}問連続正解！`
          : "お見事！";

    const utterance =
      new SpeechSynthesisUtterance(
        message
      );

    utterance.lang = "ja-JP";
    utterance.rate = 1.30;
    utterance.pitch = 1.48;
    utterance.volume = 0.95;

    const voice =
      getJapaneseVoice();

    if (voice) {
      utterance.voice = voice;
    }

    let resumed = false;

    const resumeAfterFeedback = () => {
      if (resumed) {
        return;
      }

      resumed = true;
      voicePauseForFeedback = false;

      // BGMはここでも再スタートしない。
      // 同じWebAudioノードのGainだけ戻す。
      refreshBgmVolume();
      bgmEngine.ensureRunning();

      if (voiceAnswerEnabled) {
        scheduleVoiceRestart(280);
      }
    };

    utterance.onend =
      resumeAfterFeedback;

    utterance.onerror =
      resumeAfterFeedback;

    window.speechSynthesis.speak(
      utterance
    );
  }

  function setRainbowForStreak(streak) {
    const vars = [
      "--rb1", "--rb2", "--rb3", "--rb4",
      "--rb5", "--rb6", "--rb7", "--rb8"
    ];

    if (streak < 6) {
      vars.forEach((name) =>
        questionCard.style.removeProperty(name)
      );
      return;
    }

    // 6問連続正解以降は、正解するたび少しずつ配色を変える。
    const baseHue =
      ((streak - 6) * 47) % 360;

    const offsets = [
      0, 46, 92, 138,
      184, 230, 276, 322
    ];

    offsets.forEach(
      (offset, index) => {
        const hue =
          (baseHue + offset) % 360;

        questionCard.style.setProperty(
          `--rb${index + 1}`,
          `hsl(${hue} 92% 58%)`
        );
      }
    );
  }

  function updateStreakFrame(streak) {
    questionCard.classList.remove(
      "streak5",
      "streak6",
      "streak10",
      "question-flash"
    );

    questionCard.style.borderColor = "";
    questionCard.style.borderWidth = "";
    questionCard.style.boxShadow = "";

    setRainbowForStreak(streak);

    if (streak >= 10) {
      questionCard.classList.add(
        "streak10"
      );
      return;
    }

    if (streak >= 6) {
      questionCard.classList.add(
        "streak6"
      );
    }
  }

  function flashQuestionFrameIfNeeded() {
    questionCard.classList.remove(
      "question-flash"
    );

    if (correctStreak < 10) {
      return;
    }

    // reflowして、毎問きちんと発光アニメーションを再生。
    void questionCard.offsetWidth;

    questionCard.classList.add(
      "question-flash"
    );

    setTimeout(() => {
      questionCard.classList.remove(
        "question-flash"
      );
    }, 1200);
  }

  function loadTutorialProgress() {
    try {
      const raw =
        localStorage.getItem(
          LEARNING_PROGRESS_STORAGE_KEY
        );

      if (!raw) {
        return {
          cleared: {}
        };
      }

      const parsed =
        JSON.parse(raw);

      if (
        !parsed ||
        typeof parsed !== "object"
      ) {
        return {
          cleared: {}
        };
      }

      if (
        !parsed.cleared ||
        typeof parsed.cleared !== "object"
      ) {
        parsed.cleared = {};
      }

      return parsed;
    } catch (error) {
      return {
        cleared: {}
      };
    }
  }

  function saveTutorialProgress() {
    try {
      localStorage.setItem(
        LEARNING_PROGRESS_STORAGE_KEY,
        JSON.stringify(
          learningProgress
        )
      );
    } catch (error) {}
  }

  function allTutorialLessons() {
    return Object.values(
      learningCategories
    ).flatMap(
      (category) =>
        category.lessons
    );
  }

  function isTutorialLessonCleared(
    lessonId
  ) {
    return Boolean(
      learningProgress
        .cleared[lessonId]
    );
  }

  function tutorialCategoryStats(
    categoryKey
  ) {
    const lessons =
      learningCategories[
        categoryKey
      ].lessons;

    const cleared =
      lessons.filter(
        (lesson) =>
          isTutorialLessonCleared(
            lesson.id
          )
      ).length;

    return {
      cleared,
      total: lessons.length
    };
  }

  function tutorialLessonUnlocked(
    categoryKey,
    index
  ) {
    if (index === 0) {
      return true;
    }

    const lessons =
      learningCategories[
        categoryKey
      ].lessons;

    return isTutorialLessonCleared(
      lessons[index - 1].id
    );
  }

  function updateTutorialOverallProgress() {
    const all =
      allTutorialLessons();

    const cleared =
      all.filter(
        (lesson) =>
          isTutorialLessonCleared(
            lesson.id
          )
      ).length;

    const total =
      all.length;

    learningOverallText.textContent =
      `全体 ${cleared} / ${total} STEP クリア`;

    learningOverallBar.style.width =
      `${total ? (cleared / total) * 100 : 0}%`;
  }

  function showHome() {
    stopTimer();
    stopBgm();
    hideSorobanHint();
    stopLearningAnimation();
    setVoiceAnswerEnabled(false);

    workspace.classList.remove(
      "show"
    );
    results.classList.remove(
      "show"
    );
    menuView.classList.add(
      "hidden"
    );
    learningView.classList.remove(
      "show"
    );
    homeView.classList.remove(
      "hidden"
    );

    currentMode = null;
  }

  function showChallengeMenu() {
    stopLearningAnimation();

    homeView.classList.add(
      "hidden"
    );
    learningView.classList.remove(
      "show"
    );
    workspace.classList.remove(
      "show"
    );
    results.classList.remove(
      "show"
    );
    menuView.classList.remove(
      "hidden"
    );
  }

  function showLearningHome() {
    stopTimer();
    stopBgm();
    hideSorobanHint();
    setVoiceAnswerEnabled(false);

    homeView.classList.add(
      "hidden"
    );
    menuView.classList.add(
      "hidden"
    );
    workspace.classList.remove(
      "show"
    );
    results.classList.remove(
      "show"
    );

    learningView.classList.add(
      "show"
    );

    learningCategoryView.classList.remove(
      "hidden"
    );
    learningStageView.classList.add(
      "hidden"
    );
    learningLessonView.classList.add(
      "hidden"
    );

    learningCurrentCategory = null;
    stopLearningAnimation();
    renderLearningCategories();
  }

  function renderLearningCategories() {
    learningCategoryGrid.innerHTML =
      "";

    updateTutorialOverallProgress();

    Object.entries(
      learningCategories
    ).forEach(
      ([key, category]) => {
        const stats =
          tutorialCategoryStats(
            key
          );

        const card =
          document.createElement(
            "article"
          );

        card.className =
          "learning-category-card";

        const starsFilled =
          "★".repeat(
            stats.cleared
          );

        const starsEmpty =
          "☆".repeat(
            stats.total -
            stats.cleared
          );

        card.innerHTML = `
          <div class="learning-category-symbol">${category.symbol}</div>
          <div class="learning-category-title">${category.title}</div>
          <div class="learning-category-desc">${category.desc}</div>
          <div class="learning-stars">${starsFilled}${starsEmpty} ${stats.cleared}/${stats.total}</div>
        `;

        const button =
          document.createElement(
            "button"
          );

        button.type =
          "button";

        button.className =
          "primary";

        button.textContent =
          stats.cleared === 0
            ? "STEP 1から学ぶ"
            : stats.cleared === stats.total
              ? "復習する"
              : "続きから学ぶ";

        button.addEventListener(
          "click",
          () => {
            showLearningStages(
              key
            );
          }
        );

        card.appendChild(button);
        learningCategoryGrid.appendChild(
          card
        );
      }
    );
  }

  function showLearningStages(
    categoryKey
  ) {
    learningCurrentCategory =
      categoryKey;

    stopLearningAnimation();

    learningCategoryView.classList.add(
      "hidden"
    );

    learningLessonView.classList.add(
      "hidden"
    );

    learningStageView.classList.remove(
      "hidden"
    );

    const category =
      learningCategories[
        categoryKey
      ];

    learningStageKicker.textContent =
      `${category.symbol} ${category.title}`;

    learningStageHeading.textContent =
      "少しずつSTEP UP";

    learningStageGrid.innerHTML =
      "";

    category.lessons.forEach(
      (lesson, index) => {
        const unlocked =
          tutorialLessonUnlocked(
            categoryKey,
            index
          );

        const cleared =
          isTutorialLessonCleared(
            lesson.id
          );

        const card =
          document.createElement(
            "article"
          );

        card.className =
          "learning-stage-card";

        if (!unlocked) {
          card.classList.add(
            "locked"
          );
        }

        if (cleared) {
          card.classList.add(
            "cleared"
          );
        }

        card.innerHTML = `
          <div class="learning-stage-no">STEP ${index + 1}</div>
          <div class="learning-stage-title">${lesson.title}</div>
          <div class="learning-stage-desc">${lesson.desc}</div>
          <div class="learning-stage-status">${
            cleared
              ? "★ クリア"
              : unlocked
                ? "○ 学習できます"
                : "🔒 1つ前のSTEPをクリアすると開きます"
          }</div>
        `;

        const button =
          document.createElement(
            "button"
          );

        button.type =
          "button";

        button.disabled =
          !unlocked;

        button.textContent =
          cleared
            ? "もう一度見る"
            : unlocked
              ? "学習スタート"
              : "ロック中";

        if (unlocked) {
          button.className =
            "primary";

          button.addEventListener(
            "click",
            () => {
              openLearningLesson(
                categoryKey,
                index
              );
            }
          );
        }

        card.appendChild(
          button
        );

        learningStageGrid.appendChild(
          card
        );
      }
    );
  }

  function buildLearningBoard(
    digitCount
  ) {
    learningRods = [];
    learningSorobanBoard.innerHTML =
      "";

    const safeCount =
      Math.max(
        1,
        digitCount
      );

    for (
      let i = 0;
      i < safeCount;
      i += 1
    ) {
      const place =
        10 ** (
          safeCount -
          1 -
          i
        );

      const rod =
        document.createElement(
          "div"
        );

      rod.className =
        "soroban-rod";

      rod.dataset.place =
        String(place);

      const line =
        document.createElement(
          "div"
        );

      line.className =
        "rod-line";

      rod.appendChild(
        line
      );

      const upper =
        document.createElement(
          "div"
        );

      upper.className =
        "soroban-bead upper-bead";

      rod.appendChild(
        upper
      );

      const lowers = [];

      for (
        let j = 0;
        j < 4;
        j += 1
      ) {
        const bead =
          document.createElement(
            "div"
          );

        bead.className =
          "soroban-bead lower-bead";

        bead.style.top =
          `${112 + j * 18}px`;

        rod.appendChild(
          bead
        );

        lowers.push(
          bead
        );
      }

      const label =
        document.createElement(
          "div"
        );

      label.className =
        "rod-place";

      label.textContent =
        shortPlaceName(
          place
        );

      rod.appendChild(
        label
      );

      learningSorobanBoard.appendChild(
        rod
      );

      learningRods.push({
        rod,
        place,
        upper,
        lowers
      });
    }
  }

  function showLearningNumber(
    value,
    activePlace = null
  ) {
    const safeValue =
      Math.max(
        0,
        Math.floor(
          Math.abs(
            Number(value) || 0
          )
        )
      );

    const digits =
      String(safeValue)
        .padStart(
          learningRods.length,
          "0"
        )
        .slice(
          -learningRods.length
        )
        .split("")
        .map(Number);

    learningRods.forEach(
      (rodInfo, index) => {
        setRodDigit(
          rodInfo,
          digits[index]
        );

        rodInfo.rod
          .classList.toggle(
            "active",
            activePlace !== null &&
            rodInfo.place ===
              activePlace
          );
      }
    );
  }

  function currentLearningLesson() {
    if (!learningCurrentCategory) {
      return null;
    }

    return learningCategories[
      learningCurrentCategory
    ].lessons[
      learningCurrentLessonIndex
    ] || null;
  }

  function stopLearningAnimation() {
    learningAnimationToken += 1;
    learningAnimationPaused = false;
  }

  function renderLearningFrame(
    frameIndex
  ) {
    const lesson =
      currentLearningLesson();

    if (!lesson) {
      return;
    }

    const safeIndex =
      Math.max(
        0,
        Math.min(
          lesson.frames.length - 1,
          frameIndex
        )
      );

    const frame =
      lesson.frames[
        safeIndex
      ];

    learningCurrentFrame =
      safeIndex;

    learningStepText.textContent =
      frame.text;

    learningFrameCounter.textContent =
      `${safeIndex + 1} / ${lesson.frames.length}`;

    showLearningNumber(
      frame.value,
      frame.place
    );
  }

  function runLearningAnimation(
    restart = true
  ) {
    const lesson =
      currentLearningLesson();

    if (!lesson) {
      return;
    }

    if (restart) {
      stopLearningAnimation();
      learningCurrentFrame = 0;
    }

    const token =
      learningAnimationToken;

    learningAnimationPaused =
      false;

    learningPauseBtn.textContent =
      "Ⅱ 一時停止";

    const showNext = () => {
      if (
        token !==
        learningAnimationToken
      ) {
        return;
      }

      if (
        learningAnimationPaused
      ) {
        setTimeout(
          showNext,
          180
        );
        return;
      }

      renderLearningFrame(
        learningCurrentFrame
      );

      learningCurrentFrame += 1;

      if (
        learningCurrentFrame >=
        lesson.frames.length
      ) {
        learningCurrentFrame = 0;

        // 1周終わったら少し間を空けて自動で繰り返す。
        setTimeout(
          showNext,
          1500
        );
        return;
      }

      setTimeout(
        showNext,
        1150
      );
    };

    showNext();
  }

  function renderLearningQuiz(
    lesson
  ) {
    learningQuizQuestion.textContent =
      lesson.quiz.q;

    learningQuizOptions.innerHTML =
      "";

    learningQuizFeedback.textContent =
      "";

    learningClearActions.classList.remove(
      "show"
    );

    lesson.quiz.options.forEach(
      (option) => {
        const button =
          document.createElement(
            "button"
          );

        button.type =
          "button";

        button.className =
          "learning-quiz-option";

        button.textContent =
          option;

        button.addEventListener(
          "click",
          () => {
            const correct =
              option ===
              lesson.quiz.answer;

            learningQuizOptions
              .querySelectorAll(
                "button"
              )
              .forEach(
                (item) => {
                  item.disabled =
                    true;

                  if (
                    item.textContent ===
                    lesson.quiz.answer
                  ) {
                    item.classList.add(
                      "correct-choice"
                    );
                  }
                }
              );

            if (correct) {
              learningProgress
                .cleared[
                  lesson.id
                ] = true;

              saveTutorialProgress();

              learningQuizFeedback
                .textContent =
                "★ クリア！ 次のSTEPが開きました。";

              learningQuizFeedback
                .style.color =
                "#2f6a43";

              learningClearActions
                .classList.add(
                  "show"
                );

              renderLearningCategories();
            } else {
              button.classList.add(
                "wrong-choice"
              );

              learningQuizFeedback
                .textContent =
                `もう一度動画を見てみよう。正解は「${lesson.quiz.answer}」。`;

              learningQuizFeedback
                .style.color =
                "#a14428";

              learningClearActions
                .classList.add(
                  "show"
                );
            }
          }
        );

        learningQuizOptions
          .appendChild(
            button
          );
      }
    );
  }

  function openLearningLesson(
    categoryKey,
    lessonIndex
  ) {
    learningCurrentCategory =
      categoryKey;

    learningCurrentLessonIndex =
      lessonIndex;

    const category =
      learningCategories[
        categoryKey
      ];

    const lesson =
      category.lessons[
        lessonIndex
      ];

    learningCategoryView
      .classList.add(
        "hidden"
      );

    learningStageView
      .classList.add(
        "hidden"
      );

    learningLessonView
      .classList.remove(
        "hidden"
      );

    learningLessonKicker.textContent =
      `${category.symbol} ${category.title} / STEP ${lessonIndex + 1}`;

    learningLessonTitle.textContent =
      lesson.title;

    learningBasicText.textContent =
      lesson.basic;

    learningTroubleText.textContent =
      lesson.trouble;

    learningRuleBox.textContent =
      lesson.rule;

    const maxValue =
      Math.max(
        0,
        ...lesson.frames.map(
          (frame) =>
            Math.abs(
              Number(
                frame.value
              ) || 0
            )
        )
      );

    const digitCount =
      Math.max(
        1,
        String(
          Math.floor(
            maxValue
          )
        ).length
      );

    buildLearningBoard(
      digitCount
    );

    renderLearningQuiz(
      lesson
    );

    renderLearningFrame(
      0
    );

    runLearningAnimation(
      true
    );

    const nextExists =
      Boolean(
        category.lessons[
          lessonIndex + 1
        ]
      );

    learningNextBtn.textContent =
      nextExists
        ? "次のSTEPへ"
        : "STEP一覧へ";
  }

  function goNextLearningLesson() {
    const category =
      learningCategories[
        learningCurrentCategory
      ];

    const nextIndex =
      learningCurrentLessonIndex +
      1;

    if (
      category &&
      category.lessons[
        nextIndex
      ] &&
      tutorialLessonUnlocked(
        learningCurrentCategory,
        nextIndex
      )
    ) {
      openLearningLesson(
        learningCurrentCategory,
        nextIndex
      );
      return;
    }

    showLearningStages(
      learningCurrentCategory
    );
  }

  const TIME_LIMIT_STORAGE_KEY =
    "soroban_time_limit_enabled_v1";

  function loadTimeLimitSetting() {
    try {
      const raw =
        localStorage.getItem(
          TIME_LIMIT_STORAGE_KEY
        );

      if (raw === "false") {
        return false;
      }
    } catch (error) {}

    return true;
  }

  function saveTimeLimitSetting() {
    try {
      localStorage.setItem(
        TIME_LIMIT_STORAGE_KEY,
        String(timeLimitEnabled)
      );
    } catch (error) {}
  }

  function updateTimeLimitUi() {
    root.classList.toggle(
      "untimed-mode",
      !timeLimitEnabled
    );

    timeLimitBtn.textContent =
      timeLimitEnabled
        ? "5分"
        : "OFF";

    timeLimitBtn.classList.toggle(
      "off",
      !timeLimitEnabled
    );

    modeTimeBadge.textContent =
      timeLimitEnabled
        ? "12問 / 5分"
        : "12問 / 時間制限なし";

    root
      .querySelectorAll(
        ".time-chip"
      )
      .forEach((chip) => {
        chip.textContent =
          timeLimitEnabled
            ? "5分"
            : "時間制限なし";
      });

    statusSub.textContent =
      timeLimitEnabled
        ? "12問・制限時間5分"
        : "12問・時間制限なし・得点なし";

    if (!workspace.classList.contains("show")) {
      return;
    }

    updateTimer();
  }

  function toggleTimeLimit() {
    timeLimitEnabled =
      !timeLimitEnabled;

    saveTimeLimitSetting();
    updateTimeLimitUi();
  }

  function startMode(mode) {
    scoreAnimationToken += 1;

    // 「はじめる」のクリック中にWebAudioを先に起動。
    // 以後、マイク開始時も同じBGMノードを使い続ける。
    bgmEngine.ensureContext();
    bgmEngine.ensureRunning();

    currentMode = mode;
    questions = [];

    index = 0;
    score = 0;
    answers = [];
    seconds = 300;
    locked = false;
    correctStreak = 0;
    maxCorrectStreak = 0;
    currentBgm = null;
    currentBgmGroupKey = null;

    sessionWeakAsked = 0;
    sessionWeakCorrect = 0;
    promotedMode = null;
    sessionRankingSaved = false;
    sessionChallengeRecorded = false;
    closeRankingModal();

    $("#retryBtn").textContent = "同じモードをもう一度";

    homeView.classList.add("hidden");
    learningView.classList.remove("show");
    menuView.classList.add("hidden");
    workspace.classList.add("show");
    questionCard.classList.remove(
      "hidden",
      "voice-waiting"
    );
    results.classList.remove("show");

    $("#statusTitle").textContent = modeInfo[mode].title;
    $("#streak").textContent = "連続正解 0";

    feedback.textContent = "";
    feedback.className = "feedback";

    updateStreakFrame(0);

    stopTimer();
    updateTimeLimitUi();
    updateTimer();

    if (timeLimitEnabled) {
      timerHandle = setInterval(() => {
        seconds -= 1;
        updateTimer();

        if (seconds <= 0) {
          finish(true);
        }
      }, 1000);
    }

    playBgmForStreak(0, true);
    renderQuestion();
  }

  function renderQuestion(voiceReady = false) {
    hideSorobanHint();

    // 音声モードでは、
    // 「ゴワサン！」→マイクonstart の前に問題を作らない。
    if (
      voiceAnswerEnabled &&
      !voiceReady
    ) {
      hideQuestionForVoiceCallout();

      // 前の問題が一瞬見えないように表示内容も消しておく。
      equation.textContent = "";
      answerInput.value = "";
      feedback.textContent = "";
      feedback.className = "feedback";

      $("#qCount").textContent =
        `${index + 1} / ${TOTAL_QUESTIONS}`;
      $("#score").textContent =
        `正解 ${score}`;

      $("#weakBadge").classList.remove(
        "show"
      );

      bar.style.width =
        `${(index / TOTAL_QUESTIONS) * 100}%`;

      // 前問の判定後は locked=true なので、
      // 次のゴワサン→マイク開始へ進めるようここで解除する。
      locked = false;

      if (!voicePauseForFeedback) {
        scheduleVoiceRestart(350);
      }

      return;
    }

    // 非音声モード、またはマイクonstart確認後だけ
    // ここで問題を生成する。
    if (!questions[index]) {
      questions[index] =
        makeQuestionForIndex(
          index,
          currentMode
        );
    }

    const q = questions[index];

    if (!isValidQuestion(q)) {
      throw new Error(
        `表示禁止問題を検出: ${q.a} ${q.op} ${q.b}`
      );
    }

    $("#qCount").textContent =
      `${index + 1} / ${TOTAL_QUESTIONS}`;

    $("#score").textContent =
      `正解 ${score}`;

    $("#weakBadge").classList.toggle(
      "show",
      Boolean(q.isWeakness)
    );

    bar.style.width =
      `${(index / TOTAL_QUESTIONS) * 100}%`;

    equation.textContent =
      `${q.a} ${q.op} ${q.b} ＝ ?`;

    answerInput.value = "";
    feedback.textContent = "";
    feedback.className = "feedback";
    locked = false;

    // ここへ voiceReady=true で来た時点では、
    // マイクはすでに聞き取り状態。
    revealQuestionAfterVoiceCallout();

    // 10問連続正解以上では、
    // 問題が実際に表示された瞬間だけ発光。
    flashQuestionFrameIfNeeded();
  }


  function submitAnswer() {
    if (locked || index >= TOTAL_QUESTIONS) return;

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

    recordAnswer(currentMode, q, ok);

    if (q.isWeakness && ok) {
      sessionWeakCorrect += 1;
    }

    if (ok) {
      score += 1;
      correctStreak += 1;
      maxCorrectStreak = Math.max(
        maxCorrectStreak,
        correctStreak
      );
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

    feedback.textContent = ok ? "お見事！" : `残念！ 答えは ${q.answer}`;
    feedback.className = `feedback ${ok ? "good" : "bad"}`;

    setTimeout(() => {
      index += 1;

      if (index >= TOTAL_QUESTIONS) {
        finish(false);
      } else {
        renderQuestion();
      }
    }, 850);
  }

  function updateTimer() {
    if (!timeLimitEnabled) {
      timerEl.textContent =
        "制限なし";

      timerEl.classList.remove(
        "warn"
      );

      return;
    }

    const safe = Math.max(0, seconds);
    const min = Math.floor(safe / 60);
    const sec = safe % 60;

    timerEl.textContent =
      `${String(min).padStart(2, "0")}:` +
      `${String(sec).padStart(2, "0")}`;

    timerEl.classList.toggle(
      "warn",
      seconds <= 60
    );
  }

  function stopTimer() {
    if (timerHandle) {
      clearInterval(timerHandle);
      timerHandle = null;
    }
  }

  function calculateChallengeScore() {
    const wrongCount = answers.filter(
      (entry) =>
        entry.user !== null &&
        !entry.ok
    ).length;

    // 得点計算では残り時間を秒まで反映する。
    // 例：6分48秒 = 408秒 = 6.8分として計算。
    const remainingSeconds =
      Math.max(0, seconds);

    const remainingMinutes =
      remainingSeconds / 60;

    const rawScore =
      score *
      maxCorrectStreak *
      remainingMinutes /
      (wrongCount + 1);

    return {
      correctCount: score,
      maxStreak: maxCorrectStreak,
      remainingSeconds,
      remainingMinutes,
      wrongCount,
      rawScore,
      finalScore: Math.max(
        0,
        Math.round(rawScore)
      )
    };
  }

  function playBabaanSound() {
    try {
      const AudioContextClass =
        window.AudioContext ||
        window.webkitAudioContext;

      if (!AudioContextClass) {
        return;
      }

      const ctx = new AudioContextClass();
      const now = ctx.currentTime;

      const master = ctx.createGain();
      master.gain.setValueAtTime(0.0001, now);
      master.gain.exponentialRampToValueAtTime(
        0.72,
        now + 0.025
      );
      master.gain.exponentialRampToValueAtTime(
        0.0001,
        now + 1.05
      );
      master.connect(ctx.destination);

      const notes = [
        { freq: 196.00, start: 0.00, dur: .78 },
        { freq: 261.63, start: 0.07, dur: .82 },
        { freq: 329.63, start: 0.14, dur: .90 },
        { freq: 523.25, start: 0.25, dur: .74 }
      ];

      notes.forEach((note, index) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type =
          index === notes.length - 1
            ? "triangle"
            : "sawtooth";

        osc.frequency.setValueAtTime(
          note.freq,
          now + note.start
        );

        gain.gain.setValueAtTime(
          0.0001,
          now + note.start
        );
        gain.gain.exponentialRampToValueAtTime(
          index === notes.length - 1 ? .28 : .16,
          now + note.start + .025
        );
        gain.gain.exponentialRampToValueAtTime(
          0.0001,
          now + note.start + note.dur
        );

        osc.connect(gain);
        gain.connect(master);

        osc.start(now + note.start);
        osc.stop(now + note.start + note.dur + .04);
      });

      const drum = ctx.createOscillator();
      const drumGain = ctx.createGain();

      drum.type = "sine";
      drum.frequency.setValueAtTime(120, now);
      drum.frequency.exponentialRampToValueAtTime(
        46,
        now + .42
      );

      drumGain.gain.setValueAtTime(.36, now);
      drumGain.gain.exponentialRampToValueAtTime(
        .0001,
        now + .48
      );

      drum.connect(drumGain);
      drumGain.connect(master);

      drum.start(now);
      drum.stop(now + .5);

      setTimeout(() => {
        ctx.close().catch(() => {});
      }, 1400);
    } catch (error) {
      // 効果音に失敗しても得点表示は続行する。
    }
  }

  function launchConfetti() {
    scoreStage
      .querySelectorAll(".confetti-piece")
      .forEach((node) => node.remove());

    const hues = [
      8, 32, 52, 105, 175, 210, 260, 315
    ];

    for (let i = 0; i < 42; i += 1) {
      const piece = document.createElement("span");
      piece.className = "confetti-piece";

      piece.style.left =
        `${Math.random() * 100}%`;

      piece.style.background =
        `hsl(${hues[i % hues.length]} 90% 58%)`;

      piece.style.setProperty(
        "--drift",
        `${-90 + Math.random() * 180}px`
      );

      piece.style.setProperty(
        "--spin",
        `${360 + Math.floor(Math.random() * 720)}deg`
      );

      piece.style.animationDelay =
        `${Math.random() * .16}s`;

      scoreStage.appendChild(piece);
    }

    setTimeout(() => {
      scoreStage
        .querySelectorAll(".confetti-piece")
        .forEach((node) => node.remove());
    }, 2200);
  }

  function speakFinalScore(scoreInfo) {
    if (
      !("speechSynthesis" in window) ||
      typeof SpeechSynthesisUtterance === "undefined"
    ) {
      return;
    }

    window.speechSynthesis.cancel();

    const points =
      scoreInfo.finalScore;

    const challengeCount =
      Math.max(
        0,
        Number(
          scoreInfo.challengeCount
        ) || 0
      );

    const challengeMessage =
      (
        challengeCount > 0 &&
        challengeCount % 5 === 0
      )
        ? `今回で${modeVoiceName(scoreInfo.mode)}モードは${challengeCount}回目のチャレンジでした。がんばってますね。`
        : null;

    let openingMessage = null;

    if (
      scoreInfo.correctCount === TOTAL_QUESTIONS &&
      scoreInfo.wrongCount === 0
    ) {
      openingMessage =
        "お見事！パーフェクト！";
    } else if (
      scoreInfo.correctCount === TOTAL_QUESTIONS - 1 &&
      scoreInfo.wrongCount === 1
    ) {
      openingMessage =
        "惜しい！もう少しでパーフェクト！";
    }

    const makeUtterance = (
      message,
      rate = 1.18,
      pitch = 1.52
    ) => {
      const utterance =
        new SpeechSynthesisUtterance(
          message
        );

      utterance.lang = "ja-JP";
      utterance.rate = rate;
      utterance.pitch = pitch;
      utterance.volume = 1.0;

      const voice =
        getJapaneseVoice();

      if (voice) {
        utterance.voice = voice;
      }

      return utterance;
    };

    const speakChallengeMessage = () => {
      if (!challengeMessage) {
        return;
      }

      const challengeUtterance =
        makeUtterance(
          challengeMessage,
          1.08,
          1.42
        );

      window.speechSynthesis.speak(
        challengeUtterance
      );
    };

    const speakPoints = () => {
      const scoreUtterance =
        makeUtterance(
          `得点は、${points}点！`,
          1.22,
          1.62
        );

      if (challengeMessage) {
        let continued = false;

        const continueToChallenge = () => {
          if (continued) {
            return;
          }

          continued = true;

          setTimeout(() => {
            speakChallengeMessage();
          }, 260);
        };

        scoreUtterance.onend =
          continueToChallenge;

        scoreUtterance.onerror =
          continueToChallenge;
      }

      window.speechSynthesis.speak(
        scoreUtterance
      );
    };

    if (openingMessage) {
      const openingUtterance =
        makeUtterance(
          openingMessage,
          1.18,
          1.55
        );

      let continued = false;

      const continueToScore = () => {
        if (continued) {
          return;
        }

        continued = true;

        setTimeout(() => {
          speakPoints();
        }, 220);
      };

      openingUtterance.onend =
        continueToScore;

      openingUtterance.onerror =
        continueToScore;

      window.speechSynthesis.speak(
        openingUtterance
      );

      return;
    }

    speakPoints();
  }

  function speakUntimedFinish(scoreInfo) {
    if (
      !("speechSynthesis" in window) ||
      typeof SpeechSynthesisUtterance === "undefined"
    ) {
      return;
    }

    const messages = [];

    if (
      scoreInfo.correctCount === TOTAL_QUESTIONS &&
      scoreInfo.wrongCount === 0
    ) {
      messages.push(
        "お見事！パーフェクト！"
      );
    } else if (
      scoreInfo.correctCount === TOTAL_QUESTIONS - 1 &&
      scoreInfo.wrongCount === 1
    ) {
      messages.push(
        "惜しい！もう少しでパーフェクト！"
      );
    }

    if (
      scoreInfo.challengeCount > 0 &&
      scoreInfo.challengeCount % 5 === 0
    ) {
      messages.push(
        `今回で${modeVoiceName(scoreInfo.mode)}モードは${scoreInfo.challengeCount}回目のチャレンジでした。がんばってますね。`
      );
    }

    if (messages.length === 0) {
      return;
    }

    window.speechSynthesis.cancel();

    const speakAt = (index) => {
      if (index >= messages.length) {
        return;
      }

      const utterance =
        new SpeechSynthesisUtterance(
          messages[index]
        );

      utterance.lang = "ja-JP";
      utterance.rate = 1.14;
      utterance.pitch = 1.5;
      utterance.volume = 1.0;

      const voice =
        getJapaneseVoice();

      if (voice) {
        utterance.voice = voice;
      }

      utterance.onend = () => {
        setTimeout(() => {
          speakAt(index + 1);
        }, 220);
      };

      utterance.onerror =
        utterance.onend;

      window.speechSynthesis.speak(
        utterance
      );
    };

    speakAt(0);
  }

  function runScoreRoulette(scoreInfo) {
    scoreAnimationToken += 1;
    const token = scoreAnimationToken;

    const finalPoints = scoreInfo.finalScore;

    scoreStage.classList.remove(
      "babaan",
      "score-rainbow"
    );

    if (finalPoints > 1000) {
      scoreStage.classList.add(
        "score-rainbow"
      );
    }
    resultScore.classList.remove("reveal");
    resultScore.classList.add("roulette");

    const remainMin =
      Math.floor(
        scoreInfo.remainingSeconds / 60
      );

    const remainSec =
      scoreInfo.remainingSeconds % 60;

    scoreFormula.textContent =
      `${scoreInfo.correctCount}正解 × ` +
      `最高${scoreInfo.maxStreak}問連続 × ` +
      `残り${remainMin}分${remainSec}秒 ÷ ` +
      `（${scoreInfo.wrongCount}回ミス＋1）`;

    let tick = 0;

    const rouletteTimer = setInterval(() => {
      if (token !== scoreAnimationToken) {
        clearInterval(rouletteTimer);
        return;
      }

      const spread = Math.max(
        finalPoints * 1.9,
        180
      );

      const randomValue = Math.max(
        0,
        Math.floor(Math.random() * spread)
      );

      resultScore.textContent =
        `${randomValue.toLocaleString()} 点`;

      tick += 1;
    }, 72);

    setTimeout(() => {
      if (token !== scoreAnimationToken) {
        clearInterval(rouletteTimer);
        return;
      }

      clearInterval(rouletteTimer);

      resultScore.classList.remove("roulette");
      resultScore.textContent =
        `${finalPoints.toLocaleString()} 点`;

      // 再アニメーションのためreflow
      void resultScore.offsetWidth;

      resultScore.classList.add("reveal");
      scoreStage.classList.add("babaan");

      playBabaanSound();
      launchConfetti();

      setTimeout(() => {
        if (token === scoreAnimationToken) {
          speakFinalScore(scoreInfo);
        }
      }, 380);

      setTimeout(() => {
        scoreStage.classList.remove("babaan", "score-rainbow");
      }, 900);
    }, 2700);
  }

  function finish(timeup) {
    stopTimer();
    stopBgm();
    hideSorobanHint();
    stopVoiceRecognition();

    if (
      timeup &&
      "speechSynthesis" in window
    ) {
      window.speechSynthesis.cancel();
    }

    locked = true;

    if (timeup) {
      for (
        let i = index;
        i < TOTAL_QUESTIONS;
        i += 1
      ) {
        if (!questions[i]) {
          questions[i] =
            makeQuestionForIndex(
              i,
              currentMode
            );
        }

        answers.push({
          q: questions[i],
          user: null,
          ok: false
        });
      }
    }

    questionCard.classList.remove(
      "voice-waiting"
    );

    questionCard.classList.add(
      "hidden"
    );

    results.classList.add("show");

    const challengeScore =
      calculateChallengeScore();

    if (!sessionChallengeRecorded) {
      challengeScore.challengeCount =
        incrementChallengeCount(
          currentMode
        );

      challengeScore.mode =
        currentMode;

      sessionChallengeRecorded = true;
    } else {
      challengeScore.challengeCount =
        getChallengeCount(
          currentMode
        );

      challengeScore.mode =
        currentMode;
    }

    const timedResult =
      timeLimitEnabled;

    scoreStage.classList.toggle(
      "hidden",
      !timedResult
    );

    resultRankingPanel.classList.toggle(
      "hidden",
      !timedResult
    );

    if (timedResult) {
      resultScore.textContent = "---";

      resultScore.classList.remove(
        "roulette",
        "reveal"
      );

      scoreStage.classList.remove(
        "babaan"
      );

      if (!sessionRankingSaved) {
        addScoreRanking(
          currentMode,
          challengeScore,
          timeup
        );

        sessionRankingSaved = true;
      }

      renderResultRanking(
        currentMode
      );
    }

    const weakSummary =
      sessionWeakAsked > 0
        ? `苦手克服 ${sessionWeakCorrect}/${sessionWeakAsked}問。`
        : "今回は苦手克服問題なし。";

    const canPromote =
      !timeup &&
      Boolean(
        NEXT_MODE[currentMode]
      ) &&
      shouldLevelUp(
        currentMode,
        score
      );

    promotedMode =
      canPromote
        ? NEXT_MODE[currentMode]
        : null;

    let resultMessage;

    if (timeup) {
      resultMessage =
        `5分になりました。正解は${score}問です。${weakSummary}`;
    } else if (timeLimitEnabled) {
      resultMessage =
        `12問終了。残り時間は${timerEl.textContent}、正解は${score}問です。${weakSummary}`;
    } else {
      resultMessage =
        `12問終了。正解は${score}問です。${weakSummary}`;
    }

    resultMessage +=
      ` 総チャレンジ回数は${challengeScore.challengeCount}回です。`;

    if (promotedMode) {
      resultMessage +=
        ` 苦手を克服できたので、次は「${modeInfo[promotedMode].title}」へレベルアップします。`;

      $("#retryBtn").textContent =
        "レベルアップして次へ";
    } else if (
      !timeup &&
      sessionWeakAsked > 0
    ) {
      resultMessage +=
        " 苦手は次回も優先して出題します。";
    }

    $("#resultNote").textContent =
      resultMessage;

    const review = $("#review");
    review.innerHTML = "";

    answers.forEach(
      (entry, i) => {
        const div =
          document.createElement(
            "div"
          );

        div.className =
          `review-item ${entry.ok ? "correct" : "wrong"}`;

        const weakMark =
          entry.q.isWeakness
            ? "【苦手克服】"
            : "";

        div.textContent =
          `${i + 1}. ${weakMark}${entry.q.a} ${entry.q.op} ${entry.q.b}` +
          ` ＝ ${entry.q.answer}｜` +
          (
            entry.user === null
              ? "未回答"
              : `回答 ${entry.user}`
          );

        review.appendChild(div);
      }
    );

    if (timedResult) {
      // 5分モードだけ得点を表示・読み上げる。
      setTimeout(() => {
        runScoreRoulette(
          challengeScore
        );
      }, 450);
    } else {
      // 時間制限OFFでは得点は表示・読み上げない。
      setTimeout(() => {
        speakUntimedFinish(
          challengeScore
        );
      }, 450);
    }
  }

  function challengeIsOnTop() {
    return (
      !workspace.classList.contains("show") &&
      !rankingModal.classList.contains("show")
    );
  }

  function pushInAppBackGuard() {
    try {
      window.history.pushState(
        {
          sorobanInApp: true,
          guard: Date.now()
        },
        "",
        window.location.href
      );
    } catch (error) {}
  }

  function installInAppBackGuard() {
    if (inAppBackGuardReady) {
      return;
    }

    inAppBackGuardReady = true;

    // 最初に1つアプリ内履歴を作っておく。
    pushInAppBackGuard();

    window.addEventListener(
      "popstate",
      () => {
        if (handlingBrowserBack) {
          return;
        }

        handlingBrowserBack = true;

        try {
          if (
            rankingModal.classList.contains("show")
          ) {
            closeRankingModal();
          } else if (
            workspace.classList.contains("show") ||
            results.classList.contains("show")
          ) {
            // チャレンジ中／結果画面 → チャレンジのモード選択。
            goMenu();
          } else if (
            !learningLessonView.classList.contains("hidden")
          ) {
            // 学習STEP詳細 → STEP一覧。
            showLearningStages(
              learningCurrentCategory
            );
          } else if (
            learningView.classList.contains("show") &&
            !learningStageView.classList.contains("hidden")
          ) {
            // STEP一覧 → 足し算・引き算などの種類選択。
            showLearningHome();
          } else if (
            learningView.classList.contains("show")
          ) {
            // 学習モードの種類選択 → アプリTOP。
            showHome();
          } else if (
            !menuView.classList.contains("hidden")
          ) {
            // チャレンジのモード選択 → アプリTOP。
            showHome();
          } else {
            // アプリTOPでは外へ抜けず、そのまま維持。
            showHome();
          }
        } finally {
          // 次回のBackもアプリ内で処理できるようガードを戻す。
          setTimeout(() => {
            pushInAppBackGuard();
            handlingBrowserBack = false;
          }, 30);
        }
      }
    );
  }

  function goMenu() {
    scoreAnimationToken += 1;
    closeRankingModal();
    stopTimer();
    stopBgm();
    hideSorobanHint();
    setVoiceAnswerEnabled(false);

    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }

    workspace.classList.remove("show");
    homeView.classList.add("hidden");
    learningView.classList.remove("show");
    menuView.classList.remove("hidden");
    results.classList.remove("show");
    questionCard.classList.remove("hidden");

    currentMode = null;
    correctStreak = 0;
    updateStreakFrame(0);
  }

  $("#homeChallengeBtn").addEventListener(
    "click",
    showChallengeMenu
  );

  $("#homeLearningBtn").addEventListener(
    "click",
    showLearningHome
  );

  $("#challengeTopBtn").addEventListener(
    "click",
    showHome
  );

  $("#learningTopBtn").addEventListener(
    "click",
    showHome
  );

  $("#learningStageBackBtn").addEventListener(
    "click",
    showLearningHome
  );

  $("#learningLessonBackBtn").addEventListener(
    "click",
    () => {
      showLearningStages(
        learningCurrentCategory
      );
    }
  );

  $("#learningReplayBtn").addEventListener(
    "click",
    () => {
      runLearningAnimation(
        true
      );
    }
  );

  learningPauseBtn.addEventListener(
    "click",
    () => {
      learningAnimationPaused =
        !learningAnimationPaused;

      learningPauseBtn.textContent =
        learningAnimationPaused
          ? "▶ 再開"
          : "Ⅱ 一時停止";
    }
  );

  $("#learningAgainBtn").addEventListener(
    "click",
    () => {
      const lesson =
        currentLearningLesson();

      if (lesson) {
        renderLearningQuiz(
          lesson
        );
      }

      runLearningAnimation(
        true
      );
    }
  );

  learningNextBtn.addEventListener(
    "click",
    goNextLearningLesson
  );

  voiceBtn.addEventListener("click", () => {
    setVoiceAnswerEnabled(!voiceAnswerEnabled);
  });

  hintBtn.addEventListener("click", () => {
    runSorobanHint();
  });

  $("#hintReplayBtn").addEventListener("click", () => {
    runSorobanHint();
  });

  $("#hintCloseBtn").addEventListener("click", () => {
    hideSorobanHint();
  });

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

  setupModeChallengeCountLabels();
  setupModeRankingButtons();

  root.querySelectorAll(".start-mode").forEach((button) => {
    button.addEventListener("click", () => {
      startMode(button.dataset.mode);
    });
  });

  $("#rankingModalClose").addEventListener(
    "click",
    closeRankingModal
  );

  rankingModal.addEventListener(
    "click",
    (event) => {
      if (event.target === rankingModal) {
        closeRankingModal();
      }
    }
  );

  $("#answerForm").addEventListener("submit", (event) => {
    event.preventDefault();
    submitAnswer();
  });

  timeLimitBtn.addEventListener(
    "click",
    toggleTimeLimit
  );

  bgmBtn.addEventListener("click", toggleBgm);
  $("#quitBtn").addEventListener("click", goMenu);
  $("#menuBtn").addEventListener("click", goMenu);

  $("#retryBtn").addEventListener("click", () => {
    if (promotedMode) {
      startMode(promotedMode);
      return;
    }

    if (currentMode) {
      startMode(currentMode);
    }
  });

  timeLimitEnabled =
    loadTimeLimitSetting();

  homeView.classList.remove("hidden");
  menuView.classList.add("hidden");
  learningView.classList.remove("show");
  workspace.classList.remove("show");

  updateTimeLimitUi();
  renderLearningCategories();
  installInAppBackGuard();
  updateBgmButton();
  updateVoiceUi();
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
