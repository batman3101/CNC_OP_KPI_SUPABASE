import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from utils.supabase_db import SupabaseDB
from utils.translations import translate

def load_model_data():
    try:
        # Supabase에서 모델 데이터 로드
        if 'db' not in st.session_state:
            st.session_state.db = SupabaseDB()
        
        db = st.session_state.db
        
        # 캐시 무효화 먼저 수행
        db._invalidate_cache('models')
        
        models = db.get_all_models()
        print(f"[DEBUG] 로드된 모델 데이터: {len(models)}개")
        return models
    except Exception as e:
        st.error(f"{translate('모델 데이터 로드 실패')}: {str(e)}")
        import traceback
        print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
        return []

def save_model_data(model_data):
    try:
        # Supabase에 모델 데이터 저장
        db = SupabaseDB()
        success = db.add_model(
            model_name=model_data["모델명"],
            process=model_data["공정"]
        )
        
        if success:
            st.success(translate("모델이 등록되었습니다."))
        else:
            st.error(translate("모델 등록 중 오류가 발생했습니다."))
        
        return success
    except Exception as e:
        st.error(f"{translate('모델 데이터 저장 실패')}: {str(e)}")
        import traceback
        print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
        return False

def show_model_management():
    st.title(translate("📦 생산 모델 관리"))
    
    # 모델 데이터 항상 최신으로 로드
    st.session_state.models = load_model_data()
    
    # 탭 생성
    tab1, tab2 = st.tabs([translate("모델 목록"), translate("모델 등록/삭제")])
    
    # 모델 목록 탭
    with tab1:
        st.subheader(translate("등록된 생산 모델"))
        if st.session_state.models:
            df = pd.DataFrame(st.session_state.models)
            st.dataframe(df, hide_index=True)
        else:
            st.info(translate("등록된 생산 모델이 없습니다."))
    
    # 모델 등록/삭제 탭
    with tab2:
        col1, col2 = st.columns(2)
        
        # 새 모델 등록
        with col1:
            st.subheader(translate("신규 모델 등록"))
            with st.form("add_model_form"):
                new_model = st.text_input(translate("모델명"))
                new_process = st.text_input(translate("공정"))
                
                if st.form_submit_button(translate("등록")):
                    if not all([new_model, new_process]):
                        st.error(translate("모든 필드를 입력해주세요."))
                    else:
                        model_data = {
                            "모델명": new_model,
                            "공정": new_process
                        }
                        
                        if save_model_data(model_data):
                            # 데이터 다시 로드
                            st.session_state.models = load_model_data()
                            st.rerun()
        
        # 모델 삭제
        with col2:
            st.subheader(translate("모델 삭제"))
            if st.session_state.models:
                model_options = {f"{m.get('모델명', '')} - {m.get('공정', '')}": m.get('id', '') for i, m in enumerate(st.session_state.models)}
                selected_model = st.selectbox(
                    translate("삭제할 모델 선택"),
                    options=list(model_options.keys())
                )
                
                if st.button(translate("삭제")):
                    model_id = model_options[selected_model]
                    db = SupabaseDB()
                    if db.delete_model(model_id):
                        st.success(translate("모델이 삭제되었습니다."))
                        # 데이터 다시 로드
                        st.session_state.models = load_model_data()
                        st.rerun()
                    else:
                        st.error(translate("모델 삭제 중 오류가 발생했습니다."))
            else:
                st.info(translate("삭제할 모델이 없습니다.")) 