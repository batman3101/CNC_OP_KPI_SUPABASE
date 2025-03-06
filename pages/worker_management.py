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

def update_worker(worker_id, data):
    try:
        # Supabase에 작업자 데이터 업데이트
        db = SupabaseDB()
        success = db.update_worker(worker_id, data)
        
        if success:
            st.success("작업자 데이터가 업데이트되었습니다.")
        else:
            st.error("작업자 데이터 업데이트 중 오류가 발생했습니다.")
        
        return success
    except Exception as e:
        st.error(f"데이터 업데이트 중 오류 발생: {str(e)}")
        return False

def delete_worker(worker_id):
    try:
        # Supabase에서 작업자 데이터 삭제
        db = SupabaseDB()
        success = db.delete_worker(worker_id)
        
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
    st.session_state.workers = load_worker_data()
    
    tab1, tab2, tab3 = st.tabs(["작업자 목록", "신규 등록", "수정/삭제"])
    
    # 작업자 목록 탭
    with tab1:
        st.subheader("등록된 작업자 명단")
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
            new_dept = st.text_input("부서")
            new_line = st.text_input("라인번호")
            
            submit_button = st.form_submit_button("등록")
            
            if submit_button:
                if not new_id or not new_name or not new_dept or not new_line:
                    st.error("모든 필드를 입력해주세요.")
                else:
                    # 사번 중복 체크
                    if any(w["사번"] == new_id for w in st.session_state.workers):
                        st.error("이미 등록된 사번입니다.")
                    else:
                        new_worker = {
                            "사번": new_id,
                            "이름": new_name,
                            "부서": new_dept,
                            "라인번호": new_line,
                            "등록일": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        st.session_state.workers.append(new_worker)
                        if save_worker_data(new_worker):
                            st.success("작업자가 등록되었습니다.")
                            st.rerun()
    
    # 수정/삭제 탭
    with tab3:
        st.subheader("작업자 정보 수정/삭제")
        if st.session_state.workers:
            # 작업자 선택
            worker_options = {f"{w['사번']} - {w['이름']}": i for i, w in enumerate(st.session_state.workers)}
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
                        edit_id = st.text_input("사번", value=worker["사번"])
                        edit_name = st.text_input("이름", value=worker["이름"])
                        edit_dept = st.text_input("부서", value=worker["부서"])
                        edit_line = st.text_input("라인번호", value=worker["라인번호"])
                        
                        edit_button = st.form_submit_button("수정")
                        
                        if edit_button:
                            st.session_state.workers[idx].update({
                                "사번": edit_id,
                                "이름": edit_name,
                                "부서": edit_dept,
                                "라인번호": edit_line,
                                "수정일": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            
                            # 업데이트할 데이터 준비
                            update_data = {
                                "사번": edit_id,
                                "이름": edit_name,
                                "부서": edit_dept,
                                "라인번호": edit_line
                            }
                            
                            # 원래 사번을 저장
                            original_id = worker["사번"]
                            
                            # 사번이 변경된 경우 새로운 작업자로 추가하고 기존 작업자 삭제
                            if original_id != edit_id:
                                print(f"[DEBUG] 사번 변경 감지: {original_id} -> {edit_id}")
                                
                                # 새 작업자 추가
                                db = SupabaseDB()
                                if db.add_worker(
                                    employee_id=edit_id,
                                    name=edit_name,
                                    department=edit_dept,
                                    line_number=edit_line
                                ):
                                    # 기존 작업자 삭제
                                    if db.delete_worker(original_id):
                                        st.success("작업자 정보가 수정되었습니다.")
                                        # 세션 스테이트 갱신
                                        st.session_state.workers = load_worker_data()
                                        st.rerun()
                                    else:
                                        st.error("기존 작업자 삭제 중 오류가 발생했습니다.")
                                else:
                                    st.error("새 작업자 추가 중 오류가 발생했습니다.")
                            else:
                                # 사번이 변경되지 않은 경우 일반 업데이트
                                if update_worker(worker["사번"], update_data):
                                    st.success("작업자 정보가 수정되었습니다.")
                                    st.rerun()
                
                # 삭제 버튼
                with col2:
                    if st.button("삭제", key="delete_worker"):
                        st.session_state.workers.pop(idx)
                        if delete_worker(worker["사번"]):
                            st.success("작업자가 삭제되었습니다.")
                            st.rerun()
        else:
            st.info("수정/삭제할 작업자가 없습니다.")

def show_worker_history():
    st.info("작업자 이력 관리 기능은 준비 중입니다.")

if __name__ == "__main__":
    show_worker_management() 