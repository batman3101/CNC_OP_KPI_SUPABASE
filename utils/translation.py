import streamlit as st
import json
import os

def load_translations():
    """번역 파일을 로드하는 함수"""
    try:
        with open('translations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"번역 파일을 로드하는 중 오류가 발생했습니다: {e}")
        return {"ko": {}, "vi": {}}

def translate(text):
    """텍스트를 현재 선택된 언어로 번역하는 함수"""
    # 세션 상태에 번역 데이터가 없으면 로드
    if 'translations' not in st.session_state:
        st.session_state.translations = load_translations()
    
    # 언어가 설정되지 않았으면 기본값 설정
    if 'language' not in st.session_state:
        st.session_state.language = 'ko'
    
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
            if translated and translated.strip():
                return translated
    
    # 번역을 찾지 못한 경우 원문 반환
    return text

def change_language(lang):
    """언어 변경 함수"""
    st.session_state.language = lang
    st.rerun()

def get_current_language():
    """현재 선택된 언어 코드 반환"""
    if 'language' not in st.session_state:
        st.session_state.language = 'ko'
    return st.session_state.language

def add_language_selector(location="sidebar"):
    """언어 선택기를 추가하는 함수
    
    Args:
        location (str): 'sidebar' 또는 'main' - 선택기를 배치할 위치
    """
    container = st.sidebar if location == "sidebar" else st
    
    container.markdown('<div class="language-selector">', unsafe_allow_html=True)
    container.markdown(f"<p style='font-weight: bold; color: #0066cc;'>{translate('언어')}</p>", unsafe_allow_html=True)
    col1, col2 = container.columns(2)
    with col1:
        if container.button(translate("한국어"), key=f"ko_lang_{location}"):
            change_language('ko')
    with col2:
        if container.button(translate("베트남어"), key=f"vi_lang_{location}"):
            change_language('vi')
    container.markdown('</div>', unsafe_allow_html=True) 