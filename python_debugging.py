from datetime import datetime
import os
import random

import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv(".chatgptkey.env")

st.set_page_config(page_title="실습 통합 앱", page_icon="🧪", layout="wide")

st.markdown(
    """
    <style>
    .lotto-wrap {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 16px 0 8px;
    }
    .lotto-ball {
        width: 54px;
        height: 54px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 22px;
        font-weight: 800;
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.18);
    }
    .ball-yellow { background: #f2b705; }
    .ball-blue { background: #2f80ed; }
    .ball-red { background: #eb5757; }
    .ball-gray { background: #828282; }
    .ball-green { background: #27ae60; }
    .history-item {
        padding: 12px 0;
        border-bottom: 1px solid rgba(128, 128, 128, 0.25);
    }
    div[role="tablist"] button p {
        font-size: 2.5rem;
        font-weight: 800;
        line-height: 1.2;
    }
    div[role="tablist"] button {
        min-height: 72px;
        padding: 12px 22px;
    }
    .page-title {
        display: flex;
        align-items: center;
        gap: 14px;
        margin: 8px 0 28px;
    }
    .page-logo {
        width: 56px;
        height: 56px;
        border-radius: 14px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        color: white;
        background: white;
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.18);
    }
    .page-logo img {
        max-width: 88%;
        max-height: 88%;
        object-fit: contain;
    }
    .wide-logo {
        width: 118px;
    }
    .page-title h1 {
        margin: 0;
        padding: 0;
    }
    .title-spacer {
        height: 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    try:
        return st.secrets.get("OPENAI_API_KEY")
    except Exception:
        return None


def make_legacy_prompt(code, goal, error_message):
    return f"""
당신은 비전공자를 돕는 친절한 파이썬 코드 리뷰어이자 디버깅 튜터입니다.
사용자가 이해하기 쉬운 말로 설명하고, 어려운 용어는 짧게 풀어서 설명하세요.

[사용자의 목표]
{goal or "목표 설명 없음"}

[에러 메시지 또는 현재 문제]
{error_message or "에러 메시지 없음"}

[검토할 파이썬 코드]
```python
{code}
```

아래 형식으로 답하세요.

1. 문제 요약
- 비전공자도 이해할 수 있게 핵심 문제를 3줄 이내로 설명하세요.

2. Legacy code editing 방식
- 기존 코드를 직접 고친 최종 코드를 제시하세요.
- 바뀐 부분과 이유를 짧게 설명하세요.
- 사용자가 바로 복사해서 실행할 수 있게 전체 코드를 보여주세요.

3. 다음 확인 단계
- 사용자가 실행 후 확인해야 할 체크리스트를 3개 이내로 제시하세요.
"""


def make_vibe_prompt(code, goal, error_message):
    return f"""
당신은 비전공자를 돕는 바이브코딩 프롬프트 코치입니다.
아래 코드와 문제를 바탕으로, 사용자가 AI에게 다시 요청하면 좋은 프롬프트를 만들어 주세요.

[사용자의 목표]
{goal or "목표 설명 없음"}

[에러 메시지 또는 현재 문제]
{error_message or "에러 메시지 없음"}

[검토할 파이썬 코드]
```python
{code}
```

아래 형식으로 답하세요.

1. 추천 프롬프트
- 사용자가 그대로 복사해서 AI에게 붙여넣을 수 있는 프롬프트를 작성하세요.
- 목표, 에러, 원하는 수정 방향, 출력 형식이 포함되어야 합니다.

2. 프롬프트 사용 팁
- 왜 이 프롬프트가 좋은지 비전공자도 이해할 수 있게 설명하세요.

3. 추가로 물어보면 좋은 질문
- AI에게 이어서 물어볼 질문 3개를 제안하세요.
"""


def get_ball_class(number):
    if number <= 10:
        return "ball-yellow"
    if number <= 20:
        return "ball-blue"
    if number <= 30:
        return "ball-red"
    if number <= 40:
        return "ball-gray"
    return "ball-green"


def render_lotto_numbers(numbers):
    balls = "".join(
        f'<span class="lotto-ball {get_ball_class(number)}">{number}</span>'
        for number in numbers
    )
    st.markdown(f'<div class="lotto-wrap">{balls}</div>', unsafe_allow_html=True)


def render_lotto_tab():
    if "lotto_history" not in st.session_state:
        st.session_state.lotto_history = []

    st.markdown(
        """
        <div class="page-title">
            <div class="page-logo wide-logo">
                <img src="https://www.dhlottery.co.kr/resources/img/images/img-draw-hLogo01.svg" alt="로또6/45 로고">
            </div>
            <h1>로또 6/45 생성기</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("버튼을 누르면 1부터 45까지의 숫자 중 6개를 무작위로 뽑아 저장합니다.")
    st.markdown('<div class="title-spacer"></div>', unsafe_allow_html=True)

    if st.button("로또 번호 생성", type="primary"):
        numbers = sorted(random.sample(range(1, 46), 6))
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.lotto_history.insert(
            0,
            {
                "numbers": numbers,
                "created_at": created_at,
            },
        )

    if st.session_state.lotto_history:
        latest = st.session_state.lotto_history[0]
        st.subheader("이번 생성 번호")
        render_lotto_numbers(latest["numbers"])
        st.write(f"생성 시간: {latest['created_at']}")

        st.subheader("생성된 로또 리스트")
        for index, item in enumerate(st.session_state.lotto_history, start=1):
            st.markdown(f'<div class="history-item">#{index}</div>', unsafe_allow_html=True)
            render_lotto_numbers(item["numbers"])
            st.caption(item["created_at"])
    else:
        st.info("아직 생성된 로또 번호가 없습니다.")


def render_debugging_tab():
    st.markdown(
        """
        <div class="page-title">
            <div class="page-logo wide-logo">
                <img src="https://www.python.org/static/community_logos/python-logo.png" alt="Python 로고">
            </div>
            <h1>비전공자를 위한 파이썬 코드 리뷰어 및 디버깅 툴</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    goal = st.text_input(
        "이 코드로 무엇을 하고 싶나요?",
        placeholder="예: CSV 파일을 읽어서 그래프로 보여주고 싶어요.",
    )
    error_message = st.text_area("에러 메시지나 이상한 동작을 붙여넣어 주세요.", height=140)
    code = st.text_area("검토할 파이썬 코드를 붙여넣어 주세요.", height=320)

    if st.button("코드 리뷰 및 디버깅 시작", type="primary"):
        api_key = get_openai_api_key()

        if not api_key:
            st.error("OpenAI API 키가 설정되어 있지 않습니다.")
        elif not code.strip():
            st.warning("검토할 파이썬 코드를 입력해 주세요.")
        else:
            with st.spinner("코드를 분석하고 있습니다..."):
                llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini", temperature=0.2)
                legacy_response = llm.invoke(make_legacy_prompt(code, goal, error_message))
                vibe_response = llm.invoke(make_vibe_prompt(code, goal, error_message))

            st.subheader("분석 결과")

            legacy_tab, vibe_tab = st.tabs(["Legacy code editing", "바이브코딩 프롬프트"])

            with legacy_tab:
                st.markdown("기존 코드를 직접 수정하는 방식입니다.")
                st.markdown(legacy_response.content)

            with vibe_tab:
                st.markdown("AI에게 더 잘 요청하기 위한 프롬프트 방식입니다.")
                st.markdown(vibe_response.content)


lotto_tab, debugging_tab = st.tabs(["로또 생성기", "파이썬 디버깅"])

with lotto_tab:
    render_lotto_tab()

with debugging_tab:
    render_debugging_tab()
