# 다국어 지원 가이드

## 개요

이 문서는 생산관리 시스템의 다국어 지원 기능에 대한 설명입니다. 현재 시스템은 한국어(기본)와 베트남어를 지원합니다.

## 주요 기능

1. **언어 선택**: 사이드바 상단에 언어 선택 버튼이 추가되어 한국어와 베트남어 중 선택할 수 있습니다.
2. **번역 관리**: 모든 UI 텍스트는 중앙 번역 파일(`translations.json`)에서 관리됩니다.
3. **확장 가능**: 추가 언어를 손쉽게 확장할 수 있는 구조로 설계되었습니다.

## 파일 구조

- `translations.json`: 모든 UI 텍스트의 번역을 담고 있는 JSON 파일
- `utils/translation.py`: 번역 기능을 위한 유틸리티 함수들이 포함된 모듈

## 번역 사용법

1. **앱에서 사용하기**:
   ```python
   from utils.translation import translate
   
   # 텍스트 번역하기
   translated_text = translate("원본 한국어 텍스트")
   
   # Streamlit UI에 번역 적용하기
   st.title(translate("제목"))
   st.button(translate("버튼 텍스트"))
   ```

2. **언어 선택 UI 추가하기**:
   ```python
   from utils.translation import add_language_selector
   
   # 사이드바에 언어 선택기 추가
   add_language_selector(location="sidebar")
   
   # 메인 페이지에 언어 선택기 추가
   add_language_selector(location="main")
   ```

## 번역 추가하기

새로운 텍스트를 추가하거나 번역하려면 `translations.json` 파일을 수정하세요:

```json
{
  "ko": {
    "새로운_텍스트": "새로운 한국어 텍스트"
  },
  "vi": {
    "새로운_텍스트": "새로운 베트남어 텍스트"
  }
}
```

## 새로운 언어 추가하기

새로운 언어를 추가하려면:

1. `translations.json` 파일에 새 언어 코드와 번역 추가:
   ```json
   {
     "ko": { ... },
     "vi": { ... },
     "en": {
       "생산관리 시스템": "Production Management System",
       ...
     }
   }
   ```

2. `app.py`의 언어 선택 UI에 새 언어 버튼 추가:
   ```python
   # 언어 선택 메뉴
   col1, col2, col3 = st.columns(3)
   with col1:
       if st.button(translate("한국어"), key="ko_lang"):
           change_language('ko')
   with col2:
       if st.button(translate("베트남어"), key="vi_lang"):
           change_language('vi')
   with col3:
       if st.button("English", key="en_lang"):
           change_language('en')
   ```

## 참고 사항

- 번역되지 않은 텍스트는 기본적으로 한국어로 표시됩니다.
- 새로운 UI 요소를 추가할 때는 항상 `translate()` 함수를 사용하여 다국어 지원을 준비하세요.
- 앱의 성능을 위해 번역 데이터는 세션 상태에 캐시됩니다. 