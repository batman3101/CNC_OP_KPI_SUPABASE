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
        
        # 전체 캐시 무효화 후 데이터 로드
        st.session_state.db._invalidate_cache()
        workers = st.session_state.db.get_workers()
        print(f"[INFO] 작업자 데이터 {len(workers)}개 로드 완료")
        
        # 작업자 데이터 출력 (디버깅용)
        for i, worker in enumerate(workers):
            print(f"[DEBUG] 작업자 {i+1}: {worker}")
            
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
        
        # 캐시 파일 존재 여부 확인 및 삭제
        try:
            import os
            if os.path.exists('cache/supabase_cache.json'):
                os.remove('cache/supabase_cache.json')
                print("[INFO] 캐시 파일 삭제 성공")
        except Exception as e:
            print(f"[ERROR] 캐시 파일 삭제 실패: {e}")
            
        # 작업자 정보 업데이트 시도
        success = st.session_state.db.update_worker(old_name, new_name, new_id, new_line)
        
        if success:
            print(f"[INFO] 작업자 '{old_name}'의 정보가 성공적으로 업데이트되었습니다")
            st.success(f"작업자 '{old_name}'의 정보가 업데이트되었습니다.")
            
            # 전체 캐시 무효화
            st.session_state.db._invalidate_cache()
            
            # 작업자 데이터 즉시 새로고침
            workers = load_worker_data()
            if workers:
                st.session_state.workers = workers
                print(f"[INFO] 작업자 데이터 새로고침 완료: {len(workers)}개")
            else:
                print("[WARNING] 작업자 데이터 새로고침 실패: 빈 목록")
                
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
        
        # 캐시 파일 존재 여부 확인 및 삭제
        try:
            import os
            if os.path.exists('cache/supabase_cache.json'):
                os.remove('cache/supabase_cache.json')
                print("[INFO] 캐시 파일 삭제 성공")
        except Exception as e:
            print(f"[ERROR] 캐시 파일 삭제 실패: {e}")
        
        # 작업자 삭제 시도
        success = st.session_state.db.delete_worker(worker_name)
        
        if success:
            print(f"[INFO] 작업자 '{worker_name}'이(가) 성공적으로 삭제되었습니다")
            st.success(f"작업자 '{worker_name}'이(가) 삭제되었습니다.")
            
            # 전체 캐시 무효화
            st.session_state.db._invalidate_cache()
            
            # 작업자 데이터 즉시 새로고침
            workers = load_worker_data()
            if workers is not None:
                st.session_state.workers = workers
                print(f"[INFO] 작업자 데이터 새로고침 완료: {len(workers)}개")
            else:
                print("[WARNING] 작업자 데이터 새로고침 실패: 빈 목록")
                
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
    
    # 세션 상태 초기화
    if 'delete_mode' not in st.session_state:
        st.session_state.delete_mode = False
        st.session_state.delete_worker_name = ""
    
    # Supabase 연결 초기화
    if 'db' not in st.session_state:
        print("[INFO] SupabaseDB 인스턴스 생성")
        st.session_state.db = SupabaseDB()
    
    # 작업자 데이터 로드 버튼
    if st.button("🔄 데이터 새로고침", key="refresh_all", use_container_width=True):
        print("[INFO] 전체 데이터 새로고침 요청")
        # 캐시 파일 삭제
        try:
            import os
            if os.path.exists('cache/supabase_cache.json'):
                os.remove('cache/supabase_cache.json')
                print("[INFO] 캐시 파일 삭제 성공")
        except Exception as e:
            print(f"[ERROR] 캐시 파일 삭제 실패: {e}")
        
        # 캐시 무효화
        st.session_state.db._invalidate_cache()
        
        # 데이터 새로고침
        st.session_state.workers = load_worker_data()
        st.success("작업자 데이터를 새로고침했습니다.")
        st.rerun()  # 페이지 리로드
    
    # 작업자 데이터 항상 최신으로 로드
    if 'workers' not in st.session_state:
        print("[INFO] 초기 작업자 데이터 로드")
        with st.spinner("작업자 데이터 로드 중..."):
            st.session_state.workers = load_worker_data()
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["작업자 목록", "신규 등록", "수정/삭제"])
    
    # 작업자 목록 탭
    with tab1:
        st.subheader("등록된 작업자 명단")
        # 데이터 새로고침 버튼
        if st.button("새로고침", key="refresh_workers"):
            with st.spinner("작업자 데이터 로드 중..."):
                st.session_state.workers = load_worker_data()
                st.success("작업자 목록을 새로고침했습니다.")
                st.rerun()
            
        if st.session_state.workers:
            df = pd.DataFrame(st.session_state.workers)
            # 필요한 열만 선택
            display_columns = ['사번', '이름', '부서', '라인번호']
            if all(col in df.columns for col in display_columns):
                df = df[display_columns]
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.info("등록된 작업자가 없습니다. '신규 등록' 탭에서 작업자를 추가해주세요.")
    
    # 신규 등록 탭
    with tab2:
        st.subheader("신규 작업자 등록")
        with st.form("worker_registration_form"):
            new_id = st.text_input("사번", placeholder="예: 21020147")
            new_name = st.text_input("이름", placeholder="예: DƯƠNG THỊ BỒNG")
            new_dept = st.text_input("부서", value="CNC")
            new_line = st.text_input("라인번호", placeholder="예: B-200")
            
            submit_button = st.form_submit_button("등록", use_container_width=True)
            
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
                        
                        with st.spinner("작업자 등록 중..."):
                            if save_worker_data(new_worker):
                                # 작업자 목록 즉시 새로고침
                                st.session_state.workers = load_worker_data()
                                st.success(f"작업자 '{new_name}'이(가) 등록되었습니다.")
                                st.rerun()
    
    # 수정/삭제 탭
    with tab3:
        st.subheader("작업자 정보 수정/삭제")
        
        if not st.session_state.workers or len(st.session_state.workers) == 0:
            st.info("수정/삭제할 작업자가 없습니다. '신규 등록' 탭에서 작업자를 추가해주세요.")
            return
        
        # 작업자 목록 다시 로드하는 버튼 추가
        if st.button("작업자 목록 새로고침", key="reload_worker_list"):
            with st.spinner("작업자 데이터 로드 중..."):
                # 캐시 무효화 먼저 수행
                st.session_state.db._invalidate_cache()
                
                # 캐시 파일 삭제
                try:
                    import os
                    if os.path.exists('cache/supabase_cache.json'):
                        os.remove('cache/supabase_cache.json')
                        print("[INFO] 캐시 파일 삭제 성공")
                except Exception as e:
                    print(f"[ERROR] 캐시 파일 삭제 실패: {e}")
                
                # 데이터 다시 로드
                st.session_state.workers = load_worker_data()
                st.success("작업자 목록을 새로고침했습니다.")
                st.rerun()
        
        # 현재 목록 출력 - 디버깅 및 확인용
        st.write("### 현재 작업자 목록")
        if st.session_state.workers:
            df = pd.DataFrame(st.session_state.workers)
            # 필요한 열만 선택
            display_columns = ['사번', '이름', '부서', '라인번호']
            if all(col in df.columns for col in display_columns):
                df = df[display_columns]
            st.dataframe(df, hide_index=True, use_container_width=True)
            
            # 작업자 선택
            worker_options = {f"{w.get('사번', '')} - {w.get('이름', '')}": i for i, w in enumerate(st.session_state.workers)}
            
            if len(worker_options) > 0:
                selected_worker = st.selectbox(
                    "수정/삭제할 작업자 선택",
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
                    
                    # 수정 폼
                    st.write("#### 작업자 정보 수정")
                    
                    with st.form(key="edit_worker_form"):
                        # 입력 필드 정의
                        edit_id = st.text_input("사번", value=worker.get("사번", ""), key="edit_id")
                        edit_name = st.text_input("이름", value=worker.get("이름", ""), key="edit_name")
                        edit_dept = "CNC"  # 부서는 항상 CNC로 고정
                        edit_line = st.text_input("라인번호", value=worker.get("라인번호", ""), key="edit_line")
                        
                        # 저장 버튼
                        save_button = st.form_submit_button("저장", use_container_width=True)
                        
                        if save_button:
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
                                    with st.spinner(f"작업자 '{original_name}' 정보 업데이트 중..."):
                                        if update_worker_data(original_name, edit_name, edit_id, edit_line):
                                            st.success(f"작업자 '{original_name}'의 정보가 업데이트되었습니다.")
                    
                    # 삭제 영역 - 폼 외부에 배치
                    st.write("#### 작업자 삭제")
                    if st.button("작업자 삭제", key="delete_worker_btn", type="primary"):
                        # 세션 상태에 삭제 모드 저장
                        st.session_state.delete_mode = True
                        st.session_state.delete_worker_name = worker.get("이름", "")
                        st.rerun()  # 페이지 새로고침
                    
                    # 삭제 확인 UI
                    if st.session_state.get("delete_mode", False):
                        st.warning(f"작업자 **{st.session_state.delete_worker_name}**을(를) 정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
                        
                        # 삭제 확인 폼
                        with st.form(key="confirm_delete_form"):
                            # 확인을 위한 작업자 이름 입력
                            confirm_name = st.text_input("삭제를 확인하려면 작업자 이름을 입력하세요:", key="confirm_delete")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                confirm_button = st.form_submit_button("확인 삭제", type="primary")
                            with col2:
                                cancel_button = st.form_submit_button("취소")
                            
                            if confirm_button:
                                if confirm_name == st.session_state.delete_worker_name:
                                    # 작업자 삭제
                                    with st.spinner(f"작업자 '{st.session_state.delete_worker_name}' 삭제 중..."):
                                        if delete_worker_data(st.session_state.delete_worker_name):
                                            st.success(f"작업자 '{st.session_state.delete_worker_name}'이(가) 삭제되었습니다.")
                                            # 삭제 모드 해제
                                            st.session_state.delete_mode = False
                                            st.session_state.delete_worker_name = ""
                                            # 작업자 목록 새로고침
                                            st.session_state.workers = load_worker_data()
                                            st.rerun()
                                else:
                                    st.error("입력한 이름이 일치하지 않습니다.")
                                    
                            if cancel_button:
                                # 삭제 모드 해제
                                st.session_state.delete_mode = False
                                st.session_state.delete_worker_name = ""
                                st.rerun()
            else:
                st.info("수정/삭제할 작업자가 없습니다. '신규 등록' 탭에서 작업자를 추가해주세요.")

def show_worker_history():
    st.info("작업자 이력 관리 기능은 준비 중입니다.")

if __name__ == "__main__":
    show_worker_management() 