import os

import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv(".chatgptkey.env")

st.set_page_config(page_title="파이썬 코드 리뷰어", page_icon="🛠️", layout="wide")


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


st.title("비전공자를 위한 파이썬 코드 리뷰어 및 디버깅 툴")

goal = st.text_input("이 코드로 무엇을 하고 싶나요?", placeholder="예: CSV 파일을 읽어서 그래프로 보여주고 싶어요.")
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
