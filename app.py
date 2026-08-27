# VERSION: CLEAN-V39-INAPP-BACK-NAV-2026-08-28

import hashlib
import io
import json
import random
import re

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
from supabase import create_client


st.set_page_config(
    page_title="そろばん計算トレーナー",
    page_icon="🧮",
    layout="wide",
)

APP_VERSION = "CLEAN-V39-INAPP-BACK-NAV"
BUCKET_NAME = "music"
SIGNED_URL_EXPIRES_IN = 3600

BGM_FILES = [
    "1.mp3", "2.mp3", "3.mp3",
    "4.mp3", "5.mp3", "6.mp3",
    "7.mp3", "8.mp3", "9.mp3",
    "10-1.mp3", "10-2.mp3", "10-3.mp3",
]



PRACTICE_TOTAL_QUESTIONS = 12

PRACTICE_MODES = {
    "ba1": "初級・足し算1｜1桁の足し算",
    "ba2": "初級・足し算2｜2桁の足し算",
    "ba3": "初級・足し算3｜3桁の足し算",
    "bs1": "初級・引き算1｜1桁の引き算",
    "bs2": "初級・引き算2｜2桁の引き算",
    "bs3": "初級・引き算3｜3桁の引き算",
    "mm1": "中級・掛け算1｜1桁×1桁",
    "mm2": "中級・掛け算2｜2桁×1桁",
    "mm3": "中級・掛け算3｜2桁×2桁",
    "md1": "中級・割り算1｜1〜81÷1桁",
    "md2": "中級・割り算2｜3桁÷1桁",
    "md3": "中級・割り算3｜3桁÷2桁",
    "a1": "上級1｜4桁の足し算・引き算",
    "a2": "上級2｜3桁×2桁 / 4桁÷2桁",
    "a3": "上級3｜3桁×3桁 / 5桁÷3桁",
}


@st.cache_resource(show_spinner=False)
def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "Streamlit Secrets に OPENAI_API_KEY を設定してください。"
        )
    return OpenAI(api_key=api_key)


def _practice_question(a, op, b):
    if op == "＋":
        answer = a + b
    elif op == "－":
        answer = a - b
    elif op == "×":
        answer = a * b
    elif op == "÷":
        answer = a // b
    else:
        raise ValueError(f"未対応の演算子です: {op}")

    return {
        "a": int(a),
        "op": op,
        "b": int(b),
        "answer": int(answer),
    }


def _practice_add(final_min, final_max):
    return _practice_question(
        random.randint(final_min, final_max),
        "＋",
        random.randint(final_min, final_max),
    )


def _practice_sub(final_min, final_max):
    a = random.randint(final_min, final_max)
    b = random.randint(final_min, a)
    return _practice_question(a, "－", b)


def _practice_mul(a_min, a_max, b_min, b_max):
    return _practice_question(
        random.randint(a_min, a_max),
        "×",
        random.randint(b_min, b_max),
    )


def _practice_div(numerator_min, numerator_max, divisor_min, divisor_max):
    for _ in range(1000):
        divisor = random.randint(max(1, divisor_min), divisor_max)
        q_min = max(1, (numerator_min + divisor - 1) // divisor)
        q_max = numerator_max // divisor

        if q_min <= q_max:
            quotient = random.randint(q_min, q_max)
            return _practice_question(
                divisor * quotient,
                "÷",
                divisor,
            )

    raise RuntimeError("整数になる割り算を生成できませんでした。")


def make_practice_question(mode):
    if mode == "ba1":
        return _practice_add(1, 9)
    if mode == "ba2":
        return _practice_add(10, 99)
    if mode == "ba3":
        return _practice_add(100, 999)

    if mode == "bs1":
        return _practice_sub(1, 9)
    if mode == "bs2":
        return _practice_sub(10, 99)
    if mode == "bs3":
        return _practice_sub(100, 999)

    if mode == "mm1":
        return _practice_mul(1, 9, 1, 9)
    if mode == "mm2":
        return _practice_mul(10, 99, 1, 9)
    if mode == "mm3":
        return _practice_mul(10, 99, 10, 99)

    if mode == "md1":
        return _practice_div(1, 81, 1, 9)
    if mode == "md2":
        return _practice_div(100, 999, 1, 9)
    if mode == "md3":
        return _practice_div(100, 999, 10, 99)

    if mode == "a1":
        if random.choice([True, False]):
            return _practice_add(1000, 9999)
        return _practice_sub(1000, 9999)

    if mode == "a2":
        if random.choice([True, False]):
            return _practice_mul(100, 999, 10, 99)
        return _practice_div(1000, 9999, 10, 99)

    if mode == "a3":
        if random.choice([True, False]):
            return _practice_mul(100, 999, 100, 999)
        return _practice_div(10000, 99999, 100, 999)

    raise ValueError(f"不明な練習モードです: {mode}")


def audio_digest(uploaded_audio):
    if uploaded_audio is None:
        return None

    try:
        return hashlib.sha256(
            uploaded_audio.getvalue()
        ).hexdigest()
    except Exception:
        return None


def transcribe_practice_answer(uploaded_audio, question):
    audio_file = io.BytesIO(
        uploaded_audio.getvalue()
    )
    audio_file.name = "soroban_answer.wav"

    context = (
        f"そろばんの計算問題 "
        f"{question['a']} {question['op']} {question['b']} "
        "の答えを、5〜6歳の子どもが日本語で短く話しています。"
        "聞こえた数値を、できるだけ半角数字だけで文字起こししてください。"
        "説明や単位は付けないでください。"
    )

    result = (
        get_openai_client()
        .audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio_file,
            language="ja",
            prompt=context,
        )
    )

    return str(result.text or "").strip()


def parse_transcribed_integer(value):
    value = str(value or "").strip()

    value = value.translate(
        str.maketrans(
            "０１２３４５６７８９",
            "0123456789",
        )
    )

    direct = re.search(r"-?\d+", value.replace(",", ""))
    if direct:
        try:
            return int(direct.group(0))
        except ValueError:
            pass

    kanji = (
        value.replace("答えは", "")
        .replace("答え", "")
        .replace("です", "")
        .replace("。", "")
        .replace("、", "")
        .strip()
    )

    digit_map = {
        "〇": 0, "零": 0,
        "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9,
    }

    if kanji and all(ch in digit_map for ch in kanji):
        return int("".join(str(digit_map[ch]) for ch in kanji))

    if not kanji or not all(
        ch in "〇零一二三四五六七八九十百千万"
        for ch in kanji
    ):
        return None

    total = 0
    section = 0
    number = 0

    for ch in kanji:
        if ch in digit_map:
            number = digit_map[ch]
        elif ch == "十":
            section += (number or 1) * 10
            number = 0
        elif ch == "百":
            section += (number or 1) * 100
            number = 0
        elif ch == "千":
            section += (number or 1) * 1000
            number = 0
        elif ch == "万":
            total += (section + number or 1) * 10000
            section = 0
            number = 0

    return total + section + number


def reset_practice_session(mode):
    st.session_state.practice_active_mode = mode
    st.session_state.practice_screen = "game"
    st.session_state.practice_index = 0
    st.session_state.practice_question = make_practice_question(mode)
    st.session_state.practice_feedback = None
    st.session_state.practice_transcript = ""
    st.session_state.practice_manual_buffer = ""
    st.session_state.practice_answer_serial = (
        st.session_state.get("practice_answer_serial", 0) + 1
    )
    st.session_state.practice_finished = False


def next_practice_question():
    mode = st.session_state.practice_active_mode
    next_index = st.session_state.practice_index + 1

    if next_index >= PRACTICE_TOTAL_QUESTIONS:
        st.session_state.practice_finished = True
        st.session_state.practice_feedback = None
        st.session_state.practice_transcript = ""
        st.session_state.practice_manual_buffer = ""
        return

    st.session_state.practice_index = next_index
    st.session_state.practice_question = make_practice_question(mode)
    st.session_state.practice_feedback = None
    st.session_state.practice_transcript = ""
    st.session_state.practice_manual_buffer = ""
    st.session_state.practice_answer_serial += 1


def retry_practice_voice():
    st.session_state.practice_feedback = None
    st.session_state.practice_transcript = ""
    st.session_state.practice_manual_buffer = ""
    st.session_state.practice_answer_serial += 1


def practice_go_menu():
    st.session_state.practice_screen = "menu"
    st.session_state.practice_feedback = None
    st.session_state.practice_transcript = ""
    st.session_state.practice_manual_buffer = ""


def practice_submit_manual(question):
    raw = st.session_state.get(
        "practice_manual_buffer",
        "",
    )

    parsed = parse_transcribed_integer(raw)

    if parsed is None:
        st.session_state.practice_feedback = {
            "kind": "retry",
            "message": "数字を入力してください。",
        }
        return

    if parsed == question["answer"]:
        st.session_state.practice_feedback = {
            "kind": "correct",
            "message": "お見事！",
        }
    else:
        st.session_state.practice_feedback = {
            "kind": "wrong",
            "message": (
                f"残念！ 答えは {question['answer']} です。"
            ),
        }


def practice_keypad_press(value):
    current = str(
        st.session_state.get(
            "practice_manual_buffer",
            "",
        )
    )

    if value == "clear":
        st.session_state.practice_manual_buffer = ""
        return

    if value == "backspace":
        st.session_state.practice_manual_buffer = current[:-1]
        return

    if len(current) >= 10:
        return

    digit = str(value)
    st.session_state.practice_manual_buffer = (
        digit
        if current == "0"
        else current + digit
    )


def render_practice_mode():
    # ブラウザの「戻る」でもアプリ内の画面遷移になるよう、
    # 練習モードの画面状態をURLにも同期する。
    query_view = str(
        st.query_params.get(
            "practice_view",
            "menu",
        )
    )
    query_mode = str(
        st.query_params.get(
            "practice_mode",
            "",
        )
    )

    if query_view == "game" and query_mode in PRACTICE_MODES:
        if (
            st.session_state.get("practice_screen") != "game"
            or st.session_state.get("practice_active_mode") != query_mode
        ):
            reset_practice_session(query_mode)
    elif st.session_state.get("practice_screen") == "game":
        # ブラウザBackで game のURLから戻った場合は練習TOPへ。
        st.session_state.practice_screen = "menu"
        st.session_state.practice_feedback = None
        st.session_state.practice_transcript = ""
        st.session_state.practice_manual_buffer = ""

    st.markdown(
        """
        <style>
        /* 練習モードをチャレンジモードと近い外観にする */
        [data-testid="stAppViewContainer"] {
            background: #f7f5ef;
            color: #24231f;
        }

        [data-testid="stHeader"] {
            background: rgba(247,245,239,.94);
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1180px;
            padding-top: 1rem;
        }

        .practice-head {
            display:flex;
            justify-content:space-between;
            align-items:flex-end;
            gap:16px;
            margin:4px 0 18px;
        }

        .practice-lead {
            max-width:820px;
            color:#66635d;
            font-size:14px;
            line-height:1.7;
        }

        .practice-badge {
            white-space:nowrap;
            border:1px solid #d8d2c6;
            border-radius:999px;
            padding:8px 12px;
            color:#24231f;
            font-size:13px;
            font-weight:850;
        }

        .practice-level-title {
            margin:22px 0 8px;
            color:#24231f;
            font-size:20px;
            font-weight:900;
        }

        /* モードカード */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.practice-mode-card-marker) {
            min-height:196px;
            padding:2px;
            border:1px solid #ddd7ca !important;
            border-radius:18px !important;
            background:#fff !important;
            box-shadow:none !important;
        }

        .practice-mode-no {
            color:#817b70;
            font-size:11px;
            font-weight:900;
            letter-spacing:.08em;
        }

        .practice-mode-name {
            margin:5px 0 6px;
            color:#24231f;
            font-size:18px;
            font-weight:900;
        }

        .practice-mode-desc {
            min-height:42px;
            color:#66635d;
            font-size:12px;
            line-height:1.55;
        }

        .practice-chip {
            display:inline-block;
            margin:8px 4px 7px 0;
            padding:5px 8px;
            border-radius:999px;
            background:#f2eee5;
            color:#4e4942;
            font-size:11px;
            font-weight:800;
        }

        /* Streamlit buttonをチャレンジモード風に */
        .stButton > button,
        .stFormSubmitButton > button {
            min-height:46px;
            border-radius:12px;
            border:0;
            font-weight:800;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.practice-mode-card-marker)
        .stButton > button {
            width:100%;
            background:#315f86;
            color:#fff;
        }

        /* ステータスバー */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.practice-status-marker) {
            padding:2px;
            border:1px solid #ddd7ca !important;
            border-radius:18px !important;
            background:#fff !important;
        }

        .practice-status-title {
            color:#24231f;
            font-size:16px;
            font-weight:900;
        }

        .practice-status-sub {
            margin-top:3px;
            color:#706c64;
            font-size:12px;
        }

        .practice-status-pill {
            display:inline-block;
            padding:8px 11px;
            border-radius:999px;
            background:#f2eee5;
            color:#4e4942;
            font-size:12px;
            font-weight:850;
        }

        /* 問題カード */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.practice-question-marker) {
            margin-top:14px;
            padding:8px 10px 12px;
            border:2px solid #ddd7ca !important;
            border-radius:22px !important;
            background:#fff !important;
            box-shadow:none !important;
        }

        .practice-qtop {
            display:flex;
            justify-content:space-between;
            gap:12px;
            color:#706c64;
            font-size:13px;
            font-weight:850;
        }

        .practice-equation {
            margin:28px 0 20px;
            text-align:center;
            color:#24231f;
            font-size:clamp(42px,7vw,68px);
            font-weight:950;
            letter-spacing:.03em;
        }

        .practice-voice-label {
            margin:4px 0 4px;
            text-align:center;
            color:#706c64;
            font-size:12px;
            font-weight:800;
        }

        [data-testid="stAudioInput"] {
            max-width:430px;
            margin:0 auto;
        }

        .practice-answer-display {
            width:min(280px,100%);
            min-height:62px;
            margin:12px auto 8px;
            padding:10px 12px;
            border:2px solid #c8c1b4;
            border-radius:14px;
            background:#fff;
            color:#24231f;
            text-align:center;
            font-size:30px;
            font-weight:900;
        }

        .practice-keypad-label {
            margin:8px 0 6px;
            text-align:center;
            color:#706c64;
            font-size:13px;
            font-weight:850;
        }

        /* 問題カード内の数字ボタンをテンキー風に */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.practice-question-marker)
        .stButton > button {
            width:100%;
            min-height:58px;
            border:1px solid #d4cec1;
            background:#f3efe7;
            color:#24231f;
            font-size:22px;
            font-weight:900;
        }

        .practice-feedback {
            min-height:36px;
            margin:12px 0 4px;
            text-align:center;
            font-size:20px;
            font-weight:900;
        }

        .practice-feedback.correct { color:#2f6a43; }
        .practice-feedback.wrong { color:#a14428; }
        .practice-feedback.retry { color:#846b20; }

        .practice-finish {
            padding:26px 18px;
            border:2px solid #ddd7ca;
            border-radius:22px;
            background:#fff;
            text-align:center;
        }

        .practice-finish-title {
            color:#24231f;
            font-size:28px;
            font-weight:950;
        }

        .practice-finish-sub {
            margin-top:8px;
            color:#706c64;
            font-size:13px;
        }

        @media (max-width: 700px) {
            .practice-head {
                align-items:flex-start;
                flex-direction:column;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.practice-mode-card-marker) {
                min-height:0;
            }

            .practice-equation {
                margin-top:22px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "practice_screen" not in st.session_state:
        st.session_state.practice_screen = "menu"

    # -------------------------------
    # モード選択画面
    # -------------------------------
    if st.session_state.practice_screen != "game":
        st.markdown(
            """
            <div class="practice-head">
              <div class="practice-lead">
                時間制限なし・得点なしの練習モードです。
                ランキングや総チャレンジ回数には加算しません。
              </div>
              <div class="practice-badge">12問 / 時間制限なし</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        mode_groups = [
            (
                "初級モード｜足し算のみ",
                [
                    ("ba1", "BEGINNER ADD 1", "1桁の足し算", "1〜9の足し算のみ"),
                    ("ba2", "BEGINNER ADD 2", "2桁の足し算", "10〜99の足し算のみ"),
                    ("ba3", "BEGINNER ADD 3", "3桁の足し算", "100〜999の足し算のみ"),
                ],
            ),
            (
                "初級モード｜引き算のみ",
                [
                    ("bs1", "BEGINNER SUB 1", "1桁の引き算", "1〜9の引き算のみ"),
                    ("bs2", "BEGINNER SUB 2", "2桁の引き算", "10〜99の引き算のみ"),
                    ("bs3", "BEGINNER SUB 3", "3桁の引き算", "100〜999の引き算のみ"),
                ],
            ),
            (
                "中級モード｜掛け算のみ",
                [
                    ("mm1", "INTERMEDIATE MUL 1", "1桁×1桁", "1〜9同士の掛け算"),
                    ("mm2", "INTERMEDIATE MUL 2", "2桁×1桁", "2桁×1桁の掛け算"),
                    ("mm3", "INTERMEDIATE MUL 3", "2桁×2桁", "2桁同士の掛け算"),
                ],
            ),
            (
                "中級モード｜割り算のみ",
                [
                    ("md1", "INTERMEDIATE DIV 1", "1〜81÷1桁", "整数になる割り算"),
                    ("md2", "INTERMEDIATE DIV 2", "3桁÷1桁", "整数になる割り算"),
                    ("md3", "INTERMEDIATE DIV 3", "3桁÷2桁", "整数になる割り算"),
                ],
            ),
            (
                "上級モード",
                [
                    ("a1", "ADVANCED 1", "4桁の足し算・引き算", "4桁の加減算"),
                    ("a2", "ADVANCED 2", "3桁×2桁 / 4桁÷2桁", "掛け算・整数の割り算"),
                    ("a3", "ADVANCED 3", "3桁×3桁 / 5桁÷3桁", "掛け算・整数の割り算"),
                ],
            ),
        ]

        for group_title, modes in mode_groups:
            st.markdown(
                f'<div class="practice-level-title">{group_title}</div>',
                unsafe_allow_html=True,
            )

            cols = st.columns(3)

            for col, (mode, no, name, desc) in zip(cols, modes):
                with col:
                    with st.container(border=True):
                        st.markdown(
                            '<div class="practice-mode-card-marker"></div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"""
                            <div class="practice-mode-no">{no}</div>
                            <div class="practice-mode-name">{name}</div>
                            <div class="practice-mode-desc">{desc}</div>
                            <span class="practice-chip">12問</span>
                            <span class="practice-chip">時間制限なし</span>
                            """,
                            unsafe_allow_html=True,
                        )

                        if st.button(
                            "はじめる",
                            key=f"practice_start_{mode}",
                            use_container_width=True,
                        ):
                            reset_practice_session(mode)
                            st.query_params["practice_view"] = "game"
                            st.query_params["practice_mode"] = mode
                            st.rerun()

        return

    # -------------------------------
    # ゲーム画面
    # -------------------------------
    selected_mode = st.session_state.get(
        "practice_active_mode",
        "ba1",
    )

    if selected_mode not in PRACTICE_MODES:
        selected_mode = "ba1"
        reset_practice_session(selected_mode)

    # 終了画面
    if st.session_state.get("practice_finished", False):
        st.markdown(
            """
            <div class="practice-finish">
              <div class="practice-finish-title">12問の練習が終わりました</div>
              <div class="practice-finish-sub">
                練習モードなので、得点・ランキング・総チャレンジ回数には反映しません。
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "同じモードをもう12問",
                type="primary",
                use_container_width=True,
            ):
                reset_practice_session(selected_mode)
                st.query_params["practice_view"] = "game"
                st.query_params["practice_mode"] = selected_mode
                st.rerun()

        with col2:
            if st.button(
                "モード選択へ",
                use_container_width=True,
            ):
                practice_go_menu()
                st.query_params["practice_view"] = "menu"
                st.query_params.pop("practice_mode", None)
                st.rerun()

        return

    question = st.session_state.practice_question
    index = st.session_state.practice_index

    # Status bar
    with st.container(border=True):
        st.markdown(
            '<div class="practice-status-marker"></div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(
            [3.8, 1.25, 1.15],
            vertical_alignment="center",
        )

        with c1:
            st.markdown(
                f"""
                <div class="practice-status-title">
                  {PRACTICE_MODES[selected_mode]}
                </div>
                <div class="practice-status-sub">
                  12問・時間制限なし・得点なし
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                '<div class="practice-status-pill">時間制限なし</div>',
                unsafe_allow_html=True,
            )

        with c3:
            if st.button(
                "終了",
                key="practice_quit",
                use_container_width=True,
            ):
                practice_go_menu()
                st.query_params["practice_view"] = "menu"
                st.query_params.pop("practice_mode", None)
                st.rerun()

    # Question card
    with st.container(border=True):
        st.markdown(
            '<div class="practice-question-marker"></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="practice-qtop">
              <span>問題 {index + 1} / {PRACTICE_TOTAL_QUESTIONS}</span>
              <span>練習モード</span>
            </div>
            <div class="practice-equation">
              {question['a']} {question['op']} {question['b']} ＝ ?
            </div>
            """,
            unsafe_allow_html=True,
        )

        voice_available = bool(
            st.secrets.get("OPENAI_API_KEY", "")
        )

        st.markdown(
            '<div class="practice-voice-label">音声で答える</div>',
            unsafe_allow_html=True,
        )

        if not voice_available:
            st.warning(
                "音声入力を使うには Streamlit Secrets に "
                "OPENAI_API_KEY を追加してください。"
            )

        answer_audio = st.audio_input(
            "マイクを押して答えてください",
            sample_rate=16000,
            key=(
                f"practice_voice_{selected_mode}_"
                f"{index}_{st.session_state.practice_answer_serial}"
            ),
            disabled=not voice_available,
            label_visibility="collapsed",
        )

        if answer_audio is not None and voice_available:
            digest = audio_digest(answer_audio)
            digest_key = (
                f"practice_digest_{selected_mode}_{index}_"
                f"{st.session_state.practice_answer_serial}"
            )

            if (
                digest
                and st.session_state.get(digest_key)
                != digest
            ):
                st.session_state[digest_key] = digest

                try:
                    with st.spinner("声を聞いています…"):
                        transcript = transcribe_practice_answer(
                            answer_audio,
                            question,
                        )

                    parsed = parse_transcribed_integer(
                        transcript
                    )

                    st.session_state.practice_transcript = transcript

                    if parsed is None:
                        st.session_state.practice_feedback = {
                            "kind": "retry",
                            "message": (
                                f"「{transcript}」と聞こえました。"
                                "数字として認識できませんでした。"
                            ),
                        }
                    elif parsed == question["answer"]:
                        st.session_state.practice_feedback = {
                            "kind": "correct",
                            "message": "お見事！",
                        }
                    else:
                        st.session_state.practice_feedback = {
                            "kind": "wrong",
                            "message": (
                                f"残念！ 「{transcript}」→ {parsed}。"
                                f" 答えは {question['answer']} です。"
                            ),
                        }

                    st.rerun()

                except Exception:
                    st.session_state.practice_feedback = {
                        "kind": "retry",
                        "message": (
                            "音声を認識できませんでした。"
                            "もう一度お試しください。"
                        ),
                    }
                    st.rerun()

        # Manual answer display and keypad
        manual_value = str(
            st.session_state.get(
                "practice_manual_buffer",
                "",
            )
        )

        st.markdown(
            f"""
            <div class="practice-answer-display">
              {manual_value if manual_value else "&nbsp;"}
            </div>
            <div class="practice-keypad-label">
              画面の数字でも答えられます
            </div>
            """,
            unsafe_allow_html=True,
        )

        keypad_rows = [
            ["7", "8", "9"],
            ["4", "5", "6"],
            ["1", "2", "3"],
        ]

        for row_i, row in enumerate(keypad_rows):
            cols = st.columns(3)
            for col, digit in zip(cols, row):
                with col:
                    if st.button(
                        digit,
                        key=f"practice_key_{index}_{row_i}_{digit}",
                        use_container_width=True,
                    ):
                        practice_keypad_press(digit)
                        st.rerun()

        cols = st.columns(3)

        with cols[0]:
            if st.button(
                "クリア",
                key=f"practice_clear_{index}",
                use_container_width=True,
            ):
                practice_keypad_press("clear")
                st.rerun()

        with cols[1]:
            if st.button(
                "0",
                key=f"practice_key_{index}_0",
                use_container_width=True,
            ):
                practice_keypad_press("0")
                st.rerun()

        with cols[2]:
            if st.button(
                "← 1つ消す",
                key=f"practice_back_{index}",
                use_container_width=True,
            ):
                practice_keypad_press("backspace")
                st.rerun()

        if st.button(
            "答える",
            type="primary",
            key=f"practice_submit_{index}",
            use_container_width=True,
        ):
            practice_submit_manual(question)
            st.rerun()

        feedback = st.session_state.get(
            "practice_feedback"
        )

        if feedback:
            kind = feedback.get("kind", "retry")
            message = feedback.get("message", "")

            st.markdown(
                f'<div class="practice-feedback {kind}">{message}</div>',
                unsafe_allow_html=True,
            )

            if kind == "correct":
                if st.button(
                    "次の問題",
                    type="primary",
                    key=f"practice_next_{index}",
                    use_container_width=True,
                ):
                    next_practice_question()
                    st.rerun()
            else:
                c1, c2 = st.columns(2)

                with c1:
                    if st.button(
                        "もう一度",
                        key=f"practice_retry_{index}",
                        use_container_width=True,
                    ):
                        retry_practice_voice()
                        st.rerun()

                with c2:
                    if st.button(
                        "次の問題へ",
                        key=f"practice_skip_{index}",
                        use_container_width=True,
                    ):
                        next_practice_question()
                        st.rerun()




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

play_style = st.radio(
    "プレイ方法",
    [
        "チャレンジモード",
        "練習モード（時間制限なし・得点なし）",
    ],
    horizontal=True,
    label_visibility="collapsed",
    key="play_style",
)

if play_style == "練習モード（時間制限なし・得点なし）":
    render_practice_mode()
    st.stop()

# チャレンジモードへ切り替えた場合は練習画面のURL状態を解除。
if "practice_view" in st.query_params:
    st.query_params.pop("practice_view", None)
if "practice_mode" in st.query_params:
    st.query_params.pop("practice_mode", None)


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

<div id="menuView">
  <div class="intro">
    <div class="lead">
      各モード12問・制限時間5分です。
      割り算以外は、計算式を確定する直前に左右の数へ必ず+1します。
      そのため表示される数に0は出ません。
    </div>
    <div class="badge">12問 / 5分</div>
  </div>

  <div class="level-title">初級モード｜足し算のみ</div>
  <div class="mode-grid">
    <article class="mode-card">
      <div class="mode-no">BEGINNER ADD 1</div>
      <div class="mode-name">1桁の足し算</div>
      <div class="mode-desc">最終表示は1〜9の数だけ。足し算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="ba1">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">BEGINNER ADD 2</div>
      <div class="mode-name">2桁の足し算</div>
      <div class="mode-desc">最終表示は10〜99。足し算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="ba2">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">BEGINNER ADD 3</div>
      <div class="mode-name">3桁の足し算</div>
      <div class="mode-desc">最終表示は100〜999。足し算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="ba3">はじめる</button>
    </article>
  </div>

  <div class="level-title">初級モード｜引き算のみ</div>
  <div class="mode-grid">
    <article class="mode-card">
      <div class="mode-no">BEGINNER SUB 1</div>
      <div class="mode-name">1桁の引き算</div>
      <div class="mode-desc">最終表示は1〜9。引き算のみ12問。答えは必ず0以上です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="bs1">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">BEGINNER SUB 2</div>
      <div class="mode-name">2桁の引き算</div>
      <div class="mode-desc">最終表示は10〜99。引き算のみ12問。答えは必ず0以上です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="bs2">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">BEGINNER SUB 3</div>
      <div class="mode-name">3桁の引き算</div>
      <div class="mode-desc">最終表示は100〜999。引き算のみ12問。答えは必ず0以上です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="bs3">はじめる</button>
    </article>
  </div>

  <div class="level-title">中級モード｜掛け算のみ</div>
  <div class="mode-grid">
    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE MUL 1</div>
      <div class="mode-name">1桁×1桁</div>
      <div class="mode-desc">1〜9同士の掛け算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="mm1">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE MUL 2</div>
      <div class="mode-name">2桁×1桁</div>
      <div class="mode-desc">2桁×1桁の掛け算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="mm2">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE MUL 3</div>
      <div class="mode-name">2桁×2桁</div>
      <div class="mode-desc">2桁同士の掛け算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="mm3">はじめる</button>
    </article>
  </div>

  <div class="level-title">中級モード｜割り算のみ</div>
  <div class="mode-grid">
    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE DIV 1</div>
      <div class="mode-name">1〜81 ÷ 1桁</div>
      <div class="mode-desc">1〜81を1桁で割り、答えが整数になる割り算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="md1">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE DIV 2</div>
      <div class="mode-name">3桁÷1桁</div>
      <div class="mode-desc">100〜999を1桁で割り、答えが整数になる割り算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="md2">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">INTERMEDIATE DIV 3</div>
      <div class="mode-name">3桁÷2桁</div>
      <div class="mode-desc">100〜999を2桁で割り、答えが整数になる割り算のみ12問です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="md3">はじめる</button>
    </article>
  </div>

  <div class="level-title">上級モード</div>
  <div class="mode-grid">
    <article class="mode-card">
      <div class="mode-no">ADVANCED 1</div>
      <div class="mode-name">4桁の足し算・引き算</div>
      <div class="mode-desc">最終表示は1000〜9999。引き算の答えは0以上です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="a1">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">ADVANCED 2</div>
      <div class="mode-name">3桁×2桁 / 4桁÷2桁</div>
      <div class="mode-desc">3桁×2桁の掛け算と、4桁÷2桁の整数解です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
      <button type="button" class="primary start-mode" data-mode="a2">はじめる</button>
    </article>

    <article class="mode-card">
      <div class="mode-no">ADVANCED 3</div>
      <div class="mode-name">3桁×3桁 / 5桁÷3桁</div>
      <div class="mode-desc">3桁同士の掛け算と、5桁÷3桁の整数解です。</div>
      <div class="chips"><span class="chip">12問</span><span class="chip">5分</span></div>
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

<section id="workspace" class="workspace">
  <div class="statusbar">
    <div>
      <div id="statusTitle" class="status-title"></div>
      <div class="status-sub">12問・制限時間5分</div>
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

  const menuView = $("#menuView");
  const workspace = $("#workspace");
  const questionCard = $("#questionCard");
  const results = $("#results");
  const equation = $("#equation");
  const answerInput = $("#answerInput");
  const feedback = $("#feedback");
  const timerEl = $("#timer");
  const bar = $("#bar");
  const scoreStage = $("#scoreStage");
  const resultScore = $("#resultScore");
  const scoreFormula = $("#scoreFormula");
  const resultRankingList = $("#resultRankingList");
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

  const BGM_VOLUME_FIXED = 0.04;

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
      this.targetVolume = BGM_VOLUME_FIXED;
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
          "過去の得点ランキング";

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
    // BGMは常に4%固定。
    // 音声モード、ゴワサン、音声認識、判定読み上げ中でも変えない。
    return BGM_VOLUME_FIXED;
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
    updateTimer();

    timerHandle = setInterval(() => {
      seconds -= 1;
      updateTimer();

      if (seconds <= 0) finish(true);
    }, 1000);

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

    if (timeup && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }

    locked = true;

    if (timeup) {
      for (let i = index; i < TOTAL_QUESTIONS; i += 1) {
        if (!questions[i]) {
          questions[i] = makeQuestionForIndex(i, currentMode);
        }

        answers.push({
          q: questions[i],
          user: null,
          ok: false
        });
      }
    }

    questionCard.classList.remove("voice-waiting");
    questionCard.classList.add("hidden");
    results.classList.add("show");

    resultScore.textContent = "---";
    resultScore.classList.remove(
      "roulette",
      "reveal"
    );
    scoreStage.classList.remove("babaan");

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

    const weakSummary =
      sessionWeakAsked > 0
        ? `苦手克服 ${sessionWeakCorrect}/${sessionWeakAsked}問。`
        : "今回は苦手克服問題なし。";

    const canPromote =
      !timeup &&
      Boolean(NEXT_MODE[currentMode]) &&
      shouldLevelUp(currentMode, score);

    promotedMode = canPromote
      ? NEXT_MODE[currentMode]
      : null;

    let resultMessage = timeup
      ? `5分になりました。正解は${score}問です。${weakSummary}`
      : `12問終了。残り時間は${timerEl.textContent}、正解は${score}問です。${weakSummary}`;

    resultMessage +=
      ` 総チャレンジ回数は${challengeScore.challengeCount}回です。`;

    if (promotedMode) {
      resultMessage +=
        ` 苦手を克服できたので、次は「${modeInfo[promotedMode].title}」へレベルアップします。`;

      $("#retryBtn").textContent =
        "レベルアップして次へ";
    } else if (!timeup && sessionWeakAsked > 0) {
      resultMessage +=
        " 苦手は次回も優先して出題します。";
    }

    $("#resultNote").textContent = resultMessage;

    const review = $("#review");
    review.innerHTML = "";

    answers.forEach((entry, i) => {
      const div = document.createElement("div");
      div.className = `review-item ${entry.ok ? "correct" : "wrong"}`;
      const weakMark = entry.q.isWeakness
        ? "【苦手克服】"
        : "";

      div.textContent =
        `${i + 1}. ${weakMark}${entry.q.a} ${entry.q.op} ${entry.q.b}` +
        ` ＝ ${entry.q.answer}｜` +
        (entry.user === null ? "未回答" : `回答 ${entry.user}`);
      review.appendChild(div);
    });

    // 最後の正誤読み上げと少し重ならないよう、
    // 結果画面表示後に得点ルーレットを開始する。
    setTimeout(() => {
      runScoreRoulette(challengeScore);
    }, 450);
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
            // ゲーム中／結果画面ならTOP（モード選択）へ。
            goMenu();
          } else {
            // すでにTOPなら外へ出ず、そのままTOPを維持。
            menuView.classList.remove("hidden");
            workspace.classList.remove("show");
            results.classList.remove("show");
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
    menuView.classList.remove("hidden");
    results.classList.remove("show");
    questionCard.classList.remove("hidden");

    currentMode = null;
    correctStreak = 0;
    updateStreakFrame(0);
  }

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
