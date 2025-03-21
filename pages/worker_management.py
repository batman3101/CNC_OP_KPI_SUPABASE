import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from utils.supabase_db import SupabaseDB

def load_worker_data():
    try:
        print("[DEBUG] 작업자 데이터 로드 시작")
        
        # 데이터베이스 객체 가져오기
        if 'db' not in st.session_state:
            st.session_state.db = SupabaseDB()
            print("[DEBUG] 새 SupabaseDB 인스턴스 생성")
        
        # 캐시 무효화 후 데이터 로드
        st.session_state.db._invalidate_cache('workers')
        workers = st.session_state.db.get_workers()
        print(f"[INFO] 작업자 데이터 {len(workers)}개 로드 완료")
        return workers
    except Exception as e:
        print(f"[ERROR] 작업자 데이터 로드 중 예외 발생: {e}")
        st.error(f"작업자 데이터 로드 중 오류 발생: {str(e)}")
        import traceback
        print(f"[ERROR] 작업자 데이터 로드 중 상세 오류: {traceback.format_exc()}")
        return []

def save_worker_data(worker):
    try:
        # Supabase에 작업자 데이터 저장
        if 'db' not in st.session_state:
            st.session_state.db = SupabaseDB()
        
        success = st.session_state.db.add_worker(
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
        print(f"[DEBUG] 작업자 정보 업데이트 시도: {old_name} → {new_name}, 사번: {new_id}, 라인: {new_line}")
        
        # 데이터베이스 객체 가져오기
        if 'db' not in st.session_state:
            st.session_state.db = SupabaseDB()
            print("[DEBUG] 새 SupabaseDB 인스턴스 생성")
        
        # DB 연결 확인
        if not st.session_state.db.client:
            print("[ERROR] Supabase 클라이언트 연결이 설정되지 않았습니다")
            st.error("데이터베이스 연결 오류. 관리자에게 문의하세요.")
            return False
        
        # 작업자 정보 업데이트 시도
        success = st.session_state.db.update_worker(old_name, new_name, new_id, new_line)
        
        if success:
            print(f"[INFO] 작업자 '{old_name}'의 정보가 성공적으로 업데이트되었습니다")
            st.success(f"작업자 '{old_name}'의 정보가 업데이트되었습니다.")
            
            # 작업자 데이터 즉시 새로고침
            st.session_state.workers = load_worker_data()
            return True
        else:
            print(f"[ERROR] 작업자 '{old_name}' 데이터 업데이트에 실패했습니다")
            st.error(f"작업자 '{old_name}' 데이터 업데이트에 실패했습니다.")
            return False
            
    except Exception as e:
        print(f"[ERROR] 작업자 업데이트 중 예외 발생: {e}")
        st.error(f"작업자 정보 업데이트 중 오류가 발생했습니다: {str(e)}")
        import traceback
        print(f"[DEBUG] 작업자 업데이트 중 상세 오류: {traceback.format_exc()}")
        return False

def delete_worker_data(worker_name):
    try:
        print(f"[DEBUG] 작업자 삭제 시도: {worker_name}")
        
        # 데이터베이스 객체 가져오기
        if 'db' not in st.session_state:
            st.session_state.db = SupabaseDB()
            print("[DEBUG] 새 SupabaseDB 인스턴스 생성")
        
        # DB 연결 확인
        if not st.session_state.db.client:
            print("[ERROR] Supabase 클라이언트 연결이 설정되지 않았습니다")
            st.error("데이터베이스 연결 오류. 관리자에게 문의하세요.")
            return False
        
        # 작업자 삭제 시도
        success = st.session_state.db.delete_worker(worker_name)
        
        if success:
            print(f"[INFO] 작업자 '{worker_name}'이(가) 성공적으로 삭제되었습니다")
            st.success(f"작업자 '{worker_name}'이(가) 삭제되었습니다.")
            
            # 작업자 데이터 즉시 새로고침
            st.session_state.workers = load_worker_data()
            return True
        else:
            print(f"[ERROR] 작업자 '{worker_name}' 삭제에 실패했습니다")
            st.error(f"작업자 '{worker_name}' 삭제에 실패했습니다.")
            return False
            
    except Exception as e:
        print(f"[ERROR] 작업자 삭제 중 예외 발생: {e}")
        st.error(f"작업자 삭제 중 오류가 발생했습니다: {str(e)}")
        import traceback
        print(f"[DEBUG] 작업자 삭제 중 상세 오류: {traceback.format_exc()}")
        return False

def show_worker_management():
    st.title("👨‍🏭 작업자 관리")
    
    # Supabase 연결 초기화
    if 'db' not in st.session_state:
        st.session_state.db = SupabaseDB()
        print("[INFO] 새로운 SupabaseDB 인스턴스를 생성했습니다.")
    
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
        
        # 작업자 목록 다시 로드하는 버튼 추가
        if st.button("작업자 목록 새로고침", key="reload_worker_list"):
            st.session_state.workers = load_worker_data()
            st.success("작업자 목록을 새로고침했습니다.")
            st.rerun()
        
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
                
                # 현재 작업자 정보 표시
                st.write("#### 현재 작업자 정보")
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.write(f"**사번**: {worker.get('사번', '')}")
                    st.write(f"**이름**: {worker.get('이름', '')}")
                with info_col2:
                    st.write(f"**부서**: {worker.get('부서', 'CNC')}")
                    st.write(f"**라인번호**: {worker.get('라인번호', '')}")
                
                st.write("---")
                
                # 수정 폼 (st.form 없이 직접 UI 구성)
                st.write("#### 작업자 정보 수정")
                
                # 입력 필드 정의
                edit_id = st.text_input("사번", value=worker.get("사번", ""), key="edit_id")
                edit_name = st.text_input("이름", value=worker.get("이름", ""), key="edit_name")
                edit_dept = st.text_input("부서", value=worker.get("부서", "CNC"), disabled=True, 
                                        help="부서는 자동으로 유지됩니다.", key="edit_dept")
                edit_line = st.text_input("라인번호", value=worker.get("라인번호", ""), key="edit_line")
                
                col1, col2 = st.columns([3, 1])
                
                # 저장 버튼
                with col1:
                    if st.button("저장", key="save_worker", use_container_width=True):
                        # 변경 사항 확인
                        if (edit_id == worker.get("사번", "") and 
                            edit_name == worker.get("이름", "") and 
                            edit_line == worker.get("라인번호", "")):
                            st.warning("변경된 내용이 없습니다.")
                        else:
                            # 필수 입력 확인
                            if not edit_id or not edit_name or not edit_line:
                                st.error("모든 필드를 입력해주세요.")
                            else:
                                # 원래 이름을 저장
                                original_name = worker.get("이름", "")
                                
                                # 작업자 정보 업데이트
                                if update_worker_data(original_name, edit_name, edit_id, edit_line):
                                    st.rerun()
                
                # 삭제 버튼 및 기능
                with col2:
                    if st.button("삭제", key="delete_worker", type="primary", use_container_width=True):
                        # 세션 상태에 삭제 모드 저장
                        st.session_state.delete_mode = True
                        st.session_state.delete_worker_name = worker.get("이름", "")
                
                # 삭제 확인 UI
                if st.session_state.get("delete_mode", False):
                    st.warning(f"작업자 **{st.session_state.delete_worker_name}**을(를) 정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
                    
                    # 확인을 위한 작업자 이름 입력
                    confirm_name = st.text_input("삭제를 확인하려면 작업자 이름을 입력하세요:", key="confirm_delete")
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("확인 삭제", key="confirm_delete_btn", type="primary"):
                            if confirm_name == st.session_state.delete_worker_name:
                                # 작업자 삭제
                                if delete_worker_data(st.session_state.delete_worker_name):
                                    # 삭제 모드 해제
                                    st.session_state.delete_mode = False
                                    st.session_state.delete_worker_name = ""
                                    st.rerun()
                            else:
                                st.error("입력한 이름이 일치하지 않습니다.")
                    
                    with col2:
                        if st.button("취소", key="cancel_delete"):
                            # 삭제 모드 해제
                            st.session_state.delete_mode = False
                            st.session_state.delete_worker_name = ""
                            st.rerun()
                
        else:
            st.info("수정/삭제할 작업자가 없습니다.")

def show_worker_history():
    st.info("작업자 이력 관리 기능은 준비 중입니다.")

if __name__ == "__main__":
    show_worker_management() 