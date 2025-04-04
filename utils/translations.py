import streamlit as st
import json
import os
import re

def load_translations():
    """
    번역 파일을 로드합니다. 번역 파일이 없으면 빈 딕셔너리를 반환합니다.
    """
    try:
        with open('translations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"번역 파일을 로드하는 중 오류가 발생했습니다: {e}")
        return {"ko": {}, "vi": {}}

def translate(text):
    """
    주어진 텍스트를 현재 선택된 언어로 번역합니다.
    번역이 없으면 원본 텍스트를 반환합니다.
    동적으로 생성된 문자열(예: "2023년 4월" 등)의 경우에도 부분적으로 번역을 적용합니다.
    """
    if text is None:
        return ""
        
    text = str(text)
    
    if 'translations' not in st.session_state:
        st.session_state.translations = load_translations()
        
    translations = st.session_state.translations
    current_lang = st.session_state.language if 'language' in st.session_state else 'ko'
    
    # 현재 언어가 한국어면 원문 반환
    if current_lang == 'ko':
        return text
        
    # 전체 텍스트가 번역 사전에 있으면 해당 번역 반환
    if text in translations['ko']:
        translated = translations[current_lang].get(text)
        if translated and translated.strip():
            return translated
            
    # 한국어 원문에 해당하는 번역 찾기
    for ko_text, vi_text in translations[current_lang].items():
        if ko_text == text:
            return vi_text
    
    # 동적 텍스트에 부분 번역 적용 (예: "2023년 4월" -> "Tháng 4 năm 2023")
    # 날짜 형식 패턴 검색
    date_patterns = [
        (r'(\d+)년\s*(\d+)월\s*(\d+)일', r'%s ngày \2 tháng \1 năm \3'),  # YYYY년 MM월 DD일
        (r'(\d+)년\s*(\d+)월', r'Tháng \2 năm \1'),  # YYYY년 MM월
        (r'(\d+)년', r'Năm \1')  # YYYY년
    ]
    
    for pattern, replacement_format in date_patterns:
        if re.search(pattern, text):
            return re.sub(pattern, replacement_format, text)
    
    # 특수 단어나 구문 찾아서 부분 번역
    for ko_word, vi_word in translations[current_lang].items():
        if ko_word in text:
            text = text.replace(ko_word, vi_word)
    
    # 번역을 찾지 못한 경우 원문 반환
    return text

def change_language(lang):
    """
    언어를 변경합니다.
    """
    if lang in ['ko', 'vi']:
        st.session_state.language = lang
        
def get_current_language():
    """
    현재 선택된 언어를 반환합니다.
    """
    return st.session_state.language if 'language' in st.session_state else 'ko' 