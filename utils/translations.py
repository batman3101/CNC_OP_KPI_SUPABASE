import streamlit as st
import json
import os

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
    """
    if 'translations' not in st.session_state:
        st.session_state.translations = load_translations()
        
    translations = st.session_state.translations
    current_lang = st.session_state.language if 'language' in st.session_state else 'ko'
    
    # 현재 언어가 한국어면 원문 반환
    if current_lang == 'ko':
        return text
        
    # 한국어 원문이 있으면 해당 번역 반환
    if text in translations['ko']:
        translated = translations[current_lang].get(text)
        if translated and translated.strip():
            return translated
    
    # 한국어 원문에 해당하는 번역 찾기
    for ko_text, vi_text in translations[current_lang].items():
        if ko_text == text:
            return vi_text
            
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