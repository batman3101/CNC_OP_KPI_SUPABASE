import streamlit as st
import pandas as pd
from datetime import datetime
from utils.user_data import load_user_data, save_user_data
from utils.supabase_db import SupabaseDB

def show_admin_management():
    st.title("🔑 관리자 및 사용자 관리")
    
    # admin_accounts 세션 상태 변수 확인 및 초기화
    if 'admin_accounts' not in st.session_state:
        st.session_state.admin_accounts = []
        # DB 연결이 있으면 관리자 계정 목록 로드
        if 'db' in st.session_state:
            try:
                admin_users = [user.get('이메일', '') for user in st.session_state.db.get_all_users() if user.get('권한', '') == '관리자']
                st.session_state.admin_accounts = admin_users
            except Exception as e:
                st.error(f"관리자 계정 로드 중 오류 발생: {e}")
    
    # 관리자 권한 체크
    is_admin = False
    if not st.session_state.authenticated:
        st.error("로그인이 필요합니다.")
        return
    
    # 사용자 역할로 관리자 권한 확인
    if st.session_state.user_role == '관리자':
        is_admin = True
    
    # 관리자 계정 목록으로 확인
    elif st.session_state.username in st.session_state.admin_accounts:
        is_admin = True
    
    if not is_admin:
        st.error("관리자 권한이 필요합니다.")
        st.write(f"현재 사용자: {st.session_state.username}")
        st.write(f"현재 권한: {st.session_state.user_role}")
        st.write(f"관리자 계정 목록: {st.session_state.admin_accounts}")
        return
    
    # 사용자 데이터 로드
    if 'user_accounts' not in st.session_state:
        st.session_state.user_accounts = load_user_data()
    
    # 탭 생성
    admin_tab, user_tab = st.tabs(["관리자 관리", "사용자 관리"])
    
    with admin_tab:
        show_admin_section()
    
    with user_tab:
        show_user_section()

def show_admin_section():
    # 현재 관리자 계정 목록 표시
    st.subheader("관리자 계정 목록")
    
    # Supabase에서 관리자 계정 로드
    db = SupabaseDB()
    admin_users = [user for user in db.get_all_users() if user.get('권한', '') == '관리자']
    
    # 관리자 계정을 데이터프레임으로 변환
    admin_data = [
        {"아이디": user.get('이메일', ''), "이름": user.get('이름', ''), "권한": user.get('권한', '')} 
        for user in admin_users
    ]
    
    if admin_data:
        admin_df = pd.DataFrame(admin_data)
        st.dataframe(admin_df, hide_index=True)
    else:
        st.info("등록된 관리자가 없습니다.")
    
    # 새 관리자 추가
    st.subheader("새 관리자 추가")
    with st.form("add_admin_form"):
        new_admin_id = st.text_input("아이디(이메일)", key="new_admin_id")
        new_admin_pw = st.text_input("비밀번호", type="password", key="new_admin_pw")
        new_admin_name = st.text_input("이름", key="new_admin_name")
        new_admin_pw_confirm = st.text_input("비밀번호 확인", type="password", key="new_admin_pw_confirm")
        
        submit_button = st.form_submit_button("추가")
        if submit_button:
            if not new_admin_id or not new_admin_pw or not new_admin_name:
                st.error("아이디, 이름, 비밀번호를 모두 입력해주세요.")
            elif new_admin_pw != new_admin_pw_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                # 이미 존재하는 이메일인지 확인
                existing_user = db.get_user(new_admin_id)
                if existing_user:
                    st.error("이미 존재하는 아이디입니다.")
                else:
                    # 새 관리자 추가
                    success = db.add_user(
                        email=new_admin_id,
                        password=new_admin_pw,
                        name=new_admin_name,
                        role='관리자'
                    )
                    
                    if success:
                        # 관리자 계정 목록 업데이트
                        if new_admin_id not in st.session_state.admin_accounts:
                            st.session_state.admin_accounts.append(new_admin_id)
                        
                        st.success("관리자가 추가되었습니다.")
                        st.rerun()
                    else:
                        st.error("관리자 추가 중 오류가 발생했습니다.")
    
    # 관리자 삭제
    st.subheader("관리자 삭제")
    admin_to_delete = st.selectbox(
        "삭제할 관리자 선택",
        options=[user.get('이메일', '') for user in admin_users]
    )
    
    if st.button("삭제"):
        if admin_to_delete == st.session_state.username:
            st.error("현재 로그인된 계정은 삭제할 수 없습니다.")
        else:
            success = db.delete_user(admin_to_delete)
            if success:
                # 관리자 계정 목록에서 제거
                if admin_to_delete in st.session_state.admin_accounts:
                    st.session_state.admin_accounts.remove(admin_to_delete)
                
                st.success("관리자가 삭제되었습니다.")
                st.rerun()
            else:
                st.error("관리자 삭제 중 오류가 발생했습니다.")

def show_user_section():
    # 사용자 관리는 관리자만 접근 가능
    is_admin = False
    
    # admin_accounts 세션 상태 변수 확인
    if 'admin_accounts' not in st.session_state:
        st.session_state.admin_accounts = []
    
    # 로그인 확인
    if not st.session_state.authenticated:
        st.error("로그인이 필요합니다.")
        return
    
    # 사용자 역할로 관리자 권한 확인
    if st.session_state.user_role == '관리자':
        is_admin = True
    
    # 관리자 계정 목록으로 확인
    elif st.session_state.username in st.session_state.admin_accounts:
        is_admin = True
    
    if not is_admin:
        st.error("사용자 관리는 관리자만 접근할 수 있습니다.")
        return
    
    # Supabase에서 사용자 계정 로드
    db = SupabaseDB()
    regular_users = [user for user in db.get_all_users() if user.get('권한', '') != '관리자']
        
    # 사용자 목록 표시
    st.subheader("사용자 계정 목록")
    user_data = [
        {
            "아이디": user.get('이메일', ''),
            "이름": user.get('이름', ''),
            "부서": user.get('권한', '')
        }
        for user in regular_users
    ]
    
    if user_data:
        user_df = pd.DataFrame(user_data)
        st.dataframe(user_df, hide_index=True)
    else:
        st.info("등록된 사용자가 없습니다.")
    
    # 새 사용자 추가
    st.subheader("새 사용자 추가")
    with st.form("add_user_form"):
        new_user_id = st.text_input("아이디(이메일)", key="new_user_id")
        new_user_pw = st.text_input("비밀번호", type="password", key="new_user_pw")
        new_user_name = st.text_input("이름", key="new_user_name")
        new_user_dept = st.text_input("부서", key="new_user_dept")
        
        submit_button = st.form_submit_button("추가")
        if submit_button:
            if not all([new_user_id, new_user_pw, new_user_name, new_user_dept]):
                st.error("모든 필드를 입력해주세요.")
            else:
                # 이미 존재하는 이메일인지 확인
                existing_user = db.get_user(new_user_id)
                if existing_user:
                    st.error("이미 존재하는 아이디입니다.")
                else:
                    # 새 사용자 추가
                    success = db.add_user(
                        email=new_user_id,
                        password=new_user_pw,
                        name=new_user_name,
                        role=new_user_dept
                    )
                    
                    if success:
                        st.success("사용자가 추가되었습니다.")
                        st.rerun()
                    else:
                        st.error("사용자 추가 중 오류가 발생했습니다.")
    
    # 사용자 삭제
    st.subheader("사용자 삭제")
    user_to_delete = st.selectbox(
        "삭제할 사용자 선택",
        options=[user.get('이메일', '') for user in regular_users],
        key="user_delete_select"
    )
    
    if st.button("삭제", key="delete_user_button"):
        if user_to_delete:
            success = db.delete_user(user_to_delete)
            if success:
                st.success("사용자가 삭제되었습니다.")
                st.rerun()
            else:
                st.error("사용자 삭제 중 오류가 발생했습니다.") 