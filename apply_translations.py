#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
번역을 앱에 적용하는 방법 안내 문서

이 파일은 실제로 번역을 적용하는 코드를 구현하지 않고, 
번역 작업 완료 후에 어떻게 앱에 적용할 수 있는지 안내하는 가이드입니다.
"""

print("""
=========================================================
번역 적용 가이드
=========================================================

번역 작업이 완료된 후 앱에 적용하는 방법입니다.
아래 방법 중 하나를 선택하여 구현할 수 있습니다.

1. Streamlit 세션 상태 활용 방법
-------------------------------

app.py에 다음과 같은 코드를 추가합니다:

```python
import json
import streamlit as st

# 번역 파일 로드
def load_translations():
    try:
        with open('translations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"번역 파일을 로드하는 중 오류가 발생했습니다: {e}")
        return {"ko": {}, "vi": {}}

# 초기화
if 'translations' not in st.session_state:
    st.session_state.translations = load_translations()
    
if 'language' not in st.session_state:
    st.session_state.language = 'ko'  # 기본 언어: 한국어

# 언어 전환 함수
def change_language(lang):
    st.session_state.language = lang
    st.rerun()

# 번역 함수 (앱 전체에서 사용)
def translate(text):
    translations = st.session_state.translations
    current_lang = st.session_state.language
    
    # 현재 언어가 한국어면 원문 반환
    if current_lang == 'ko':
        return text
        
    # 한국어 원문에 해당하는 키 찾기
    for key, value in translations['ko'].items():
        if value == text:
            # 해당 키의 번역문 반환
            translated = translations[current_lang].get(key)
            if translated:
                return translated
    
    # 번역을 찾지 못한 경우 원문 반환
    return text

# 사이드바에 언어 선택 추가
with st.sidebar:
    st.write("언어 / Ngôn ngữ")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("한국어"):
            change_language('ko')
    with col2:
        if st.button("Tiếng Việt"):
            change_language('vi')
```

2. 번역 텍스트 사용 방법
---------------------

앱 코드에서 원래 한국어 텍스트 대신 translate() 함수를 사용합니다:

```python
# 변경 전:
st.title("생산 모델 관리")

# 변경 후:
st.title(translate("생산 모델 관리"))
```

3. 주의 사항
---------

- 번역 적용 후에는 앱을 다시 시작해야 합니다.
- 번역 파일(translations.json)이 앱 실행 디렉토리에 있어야 합니다.
- 새로운 텍스트가 추가되면 extract_translations.py를 다시 실행해야 합니다.
- 컴포넌트 라이브러리에 있는 텍스트는 별도로 처리해야 할 수 있습니다.

감사합니다.
=========================================================
""") 