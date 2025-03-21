import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from utils.supabase_db import SupabaseDB

def load_worker_data():
    try:
        # Supabase에서 작업자 데이터 로드
        db = SupabaseDB()
        workers = db.get_workers()
        return workers
    except Exception as e:
        st.error(f"작업자 데이터 로드 중 오류 발생: {str(e)}")
        return []

def save_worker_data(worker):
    try:
        # Supabase에 작업자 데이터 저장
        db = SupabaseDB()
        success = db.add_worker(
            employee_id=worker["사번"],
            name=worker["이름"],
            department=worker["부서"],
            line_number=worker["라인번호"]
        )
        
        if success:
            st.success("작업자 데이터가 저장되었습니다.")
        else:
            st.error("작업자 데이터 저장 중 오류가 발생했습니다.")
        
        return success
    except Exception as e:
        st.error(f"데이터 저장 중 오류 발생: {str(e)}")
        return False

def update_worker_data(old_name, new_name, new_id, new_line):
    try:
        # Supabase에 작업자 데이터 업데이트
        db = SupabaseDB()
        success = db.update_worker(old_name, new_name, new_id, new_line)
        
        if success:
            st.success("작업자 데이터가 업데이트되었습니다.")
        else:
            st.error("작업자 데이터 업데이트 중 오류가 발생했습니다.")
        
        return success
    except Exception as e:
        st.error(f"데이터 업데이트 중 오류 발생: {str(e)}")
        return False

def delete_worker_data(worker_name):
    try:
        # Supabase에서 작업자 데이터 삭제
        db = SupabaseDB()
        success = db.delete_worker(worker_name)
        
        if success:
            st.success("작업자가 삭제되었습니다.")
        else:
            st.error("작업자 삭제 중 오류가 발생했습니다.")
        
        return success
    except Exception as e:
        st.error(f"작업자 삭제 중 오류 발생: {str(e)}")
        return False

def show_worker_management():
    st.title("👨‍🏭 작업자 관리")
    
    # 작업자 데이터 항상 최신으로 로드
    if 'workers' not in st.session_state or st.session_state.get('reload_workers', False):
        st.session_state.workers = load_worker_data()
        st.session_state.reload_workers = False
    
    tab1, tab2, tab3 = st.tabs(["작업자 목록", "신규 등록", "수정/삭제"])
    
    # 작업자 목록 탭
    with tab1:
        st.subheader("등록된 작업자 명단")
        # 데이터 새로고침 버튼
        if st.button("새로고침", key="refresh_workers"):
            st.session_state.workers = load_worker_data()
            st.success("작업자 목록을 새로고침했습니다.")
            
        if st.session_state.workers:
            df = pd.DataFrame(st.session_state.workers)
            st.dataframe(df, hide_index=True)
        else:
            st.info("등록된 작업자가 없습니다.")
    
    # 신규 등록 탭
    with tab2:
        st.subheader("신규 작업자 등록")
        with st.form("worker_registration_form"):
            new_id = st.text_input("사번")
            new_name = st.text_input("이름")
            new_dept = st.text_input("부서", value="CNC")
            new_line = st.text_input("라인번호")
            
            submit_button = st.form_submit_button("등록")
            
            if submit_button:
                if not new_id or not new_name or not new_dept or not new_line:
                    st.error("모든 필드를 입력해주세요.")
                else:
                    # 사번 중복 체크
                    if any(w.get("사번") == new_id for w in st.session_state.workers):
                        st.error("이미 등록된 사번입니다.")
                    else:
                        new_worker = {
                            "사번": new_id,
                            "이름": new_name,
                            "부서": new_dept,
                            "라인번호": new_line
                        }
                        
                        if save_worker_data(new_worker):
                            st.session_state.reload_workers = True
                            st.rerun()
    
    # 수정/삭제 탭
    with tab3:
        st.subheader("작업자 정보 수정/삭제")
        if st.session_state.workers:
            # 작업자 선택
            worker_options = {f"{w.get('사번', '')} - {w.get('이름', '')}": i for i, w in enumerate(st.session_state.workers)}
            selected_worker = st.selectbox(
                "작업자 선택",
                options=list(worker_options.keys())
            )
            
            if selected_worker:
                idx = worker_options[selected_worker]
                worker = st.session_state.workers[idx]
                
                col1, col2 = st.columns(2)
                
                # 수정 폼
                with col1:
                    with st.form("worker_edit_form"):
                        edit_id = st.text_input("사번", value=worker.get("사번", ""))
                        edit_name = st.text_input("이름", value=worker.get("이름", ""))
                        edit_dept = st.text_input("부서", value=worker.get("부서", "CNC"))
                        edit_line = st.text_input("라인번호", value=worker.get("라인번호", ""))
                        
                        edit_button = st.form_submit_button("수정")
                        
                        if edit_button:
                            # 원래 이름을 저장
                            original_name = worker.get("이름", "")
                            
                            # 작업자 정보 업데이트
                            if update_worker_data(original_name, edit_name, edit_id, edit_line):
                                st.session_state.reload_workers = True
                                st.rerun()
                
                # 삭제 기능
                with col2:
                    with st.form("worker_delete_form"):
                        st.write(f"작업자 **{worker.get('이름')}** 삭제")
                        st.warning("이 작업은 되돌릴 수 없습니다.")
                        delete_button = st.form_submit_button("삭제")
                        
                        if delete_button:
                            # 작업자 삭제
                            if delete_worker_data(worker.get("이름", "")):
                                st.session_state.reload_workers = True
                                st.rerun()
        else:
            st.info("수정/삭제할 작업자가 없습니다.")

def show_worker_history():
    st.info("작업자 이력 관리 기능은 준비 중입니다.")

if __name__ == "__main__":
    show_worker_management() 