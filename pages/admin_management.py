import streamlit as st
import pandas as pd
from datetime import datetime
from utils.user_data import load_user_data, save_user_data
from utils.supabase_db import SupabaseDB
import bcrypt
from utils.translation import translate

# config_local.py가 있으면 관리자 계정 정보 로드, 없으면 기본값 사용
try:
    from config_local import ADMIN_EMAIL
except ImportError:
    ADMIN_EMAIL = "admin@example.com"  # 기본값

def show_admin_management():
    st.title(translate("🔑 관리자 및 사용자 관리"))
    
    # admin_accounts 세션 상태 변수 확인 및 초기화
    if 'admin_accounts' not in st.session_state:
        st.session_state.admin_accounts = []
        # DB 연결이 있으면 관리자 계정 목록 로드
        if 'db' in st.session_state:
            try:
                admin_users = [user.get('이메일', '').strip().lower() for user in st.session_state.db.get_all_users() if user.get('권한', '') == '관리자']
                st.session_state.admin_accounts = admin_users
                print(f"[DEBUG] 관리자 계정 목록: {admin_users}")
            except Exception as e:
                st.error(translate(f"관리자 계정 로드 중 오류 발생: {e}"))
                print(f"[ERROR] 관리자 계정 로드 중 오류: {e}")
    
    # 로그인 확인
    if not st.session_state.authenticated:
        st.error(translate("로그인이 필요합니다."))
        return
    
    # 관리자 권한 확인을 위한 로그
    print(f"[DEBUG] 관리자 페이지 접근 시도: 사용자={st.session_state.get('username', '없음')}, 이메일={st.session_state.get('user_email', '없음')}, 권한={st.session_state.get('user_role', '없음')}")
    print(f"[DEBUG] 지정된 admin 이메일: {ADMIN_EMAIL}")
    
    # 관리자 권한 확인 (지정된 admin 계정은 항상 접근 허용)
    user_email = st.session_state.get('user_email', '').strip().lower()
    admin_email = ADMIN_EMAIL.strip().lower()
    is_admin = (st.session_state.user_role == '관리자' or user_email == admin_email)
    
    # 디버깅 정보 출력
    print(f"[DEBUG] 사용자 이메일: {user_email}")
    print(f"[DEBUG] 관리자 이메일: {admin_email}")
    print(f"[DEBUG] 관리자 권한 확인 결과: {is_admin}")
    
    if not is_admin:
        st.error(translate("관리자 권한이 필요합니다."))
        st.write(translate(f"현재 로그인 계정: {st.session_state.username} ({st.session_state.user_email})"))
        st.write(translate(f"현재 권한: {st.session_state.user_role}"))
        return
    
    # 권한 확인 완료 로그
    print(f"[INFO] 관리자 권한 확인 완료: 접근 허용")
    
    # 사용자 데이터 로드
    if 'user_accounts' not in st.session_state:
        st.session_state.user_accounts = load_user_data()
    
    # 탭 생성
    admin_tab, user_tab = st.tabs([translate("관리자 관리"), translate("사용자 관리")])
    
    with admin_tab:
        show_admin_section()
    
    with user_tab:
        show_user_section()

def show_admin_section():
    # 현재 관리자 계정 목록 표시
    st.subheader(translate("관리자 계정 목록"))
    
    # Supabase에서 관리자 계정 로드
    db = SupabaseDB()
    admin_users = [user for user in db.get_all_users() if user.get('권한', '') == '관리자']
    
    # 관리자 계정을 데이터프레임으로 변환
    admin_data = [
        {
            translate("아이디"): user.get('이메일', ''), 
            translate("이름"): user.get('이름', ''), 
            translate("권한"): user.get('권한', '')
        } 
        for user in admin_users
    ]
    
    if admin_data:
        admin_df = pd.DataFrame(admin_data)
        st.dataframe(admin_df, hide_index=True)
    else:
        st.info(translate("등록된 관리자가 없습니다."))
    
    # 새 관리자 추가
    st.subheader(translate("새 관리자 추가"))
    with st.form("add_admin_form"):
        new_admin_id = st.text_input(translate("아이디(이메일)"), key="new_admin_id")
        new_admin_pw = st.text_input(translate("비밀번호"), type="password", key="new_admin_pw")
        new_admin_name = st.text_input(translate("이름"), key="new_admin_name")
        new_admin_pw_confirm = st.text_input(translate("비밀번호 확인"), type="password", key="new_admin_pw_confirm")
        
        submit_button = st.form_submit_button(translate("추가"))
        if submit_button:
            if not new_admin_id or not new_admin_pw or not new_admin_name:
                st.error(translate("아이디, 이름, 비밀번호를 모두 입력해주세요."))
            elif new_admin_pw != new_admin_pw_confirm:
                st.error(translate("비밀번호가 일치하지 않습니다."))
            else:
                # 이미 존재하는 이메일인지 확인
                existing_user = db.get_user(new_admin_id)
                if existing_user:
                    st.error(translate("이미 존재하는 아이디입니다."))
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
                        
                        st.success(translate("관리자가 추가되었습니다."))
                        st.rerun()
                    else:
                        st.error(translate("관리자 추가 중 오류가 발생했습니다."))
    
    # 관리자 삭제
    st.subheader(translate("관리자 삭제"))
    admin_to_delete = st.selectbox(
        translate("삭제할 관리자 선택"),
        options=[user.get('이메일', '') for user in admin_users]
    )
    
    if st.button(translate("삭제")):
        if admin_to_delete == st.session_state.username:
            st.error(translate("현재 로그인된 계정은 삭제할 수 없습니다."))
        else:
            success = db.delete_user(admin_to_delete)
            if success:
                # 관리자 계정 목록에서 제거
                if admin_to_delete in st.session_state.admin_accounts:
                    st.session_state.admin_accounts.remove(admin_to_delete)
                
                st.success(translate("관리자가 삭제되었습니다."))
                st.rerun()
            else:
                st.error(translate("관리자 삭제 중 오류가 발생했습니다."))

def show_user_section():
    # 사용자 관리는 관리자만 접근 가능
    is_admin = False
    
    # admin_accounts 세션 상태 변수 확인
    if 'admin_accounts' not in st.session_state:
        st.session_state.admin_accounts = []
    
    # 로그인 확인
    if not st.session_state.authenticated:
        st.error(translate("로그인이 필요합니다."))
        return
    
    # 관리자 권한 확인을 위한 로그
    print(f"[DEBUG] 사용자 관리 탭 접근: 사용자={st.session_state.get('username', '없음')}, 이메일={st.session_state.get('user_email', '없음')}, 권한={st.session_state.get('user_role', '없음')}")
    
    # 사용자 역할로 관리자 권한 확인 (지정된 admin 계정은 항상 관리자 권한 부여)
    user_email = st.session_state.get('user_email', '').strip().lower()
    admin_email = ADMIN_EMAIL.strip().lower()
    is_admin = (st.session_state.user_role == '관리자' or user_email == admin_email)
    
    if not is_admin:
        st.error(translate("사용자 관리는 관리자만 접근할 수 있습니다."))
        return
    
    # Supabase에서 사용자 계정 로드
    db = SupabaseDB()
    regular_users = [user for user in db.get_all_users() if user.get('권한', '') != '관리자']
        
    # 사용자 목록 표시
    st.subheader(translate("사용자 계정 목록"))
    user_data = [
        {
            translate("아이디"): user.get('이메일', ''),
            translate("이름"): user.get('이름', ''),
            translate("부서"): user.get('권한', '')
        }
        for user in regular_users
    ]
    
    if user_data:
        user_df = pd.DataFrame(user_data)
        st.dataframe(user_df, hide_index=True)
    else:
        st.info(translate("등록된 사용자가 없습니다."))
    
    # 새 사용자 추가
    st.subheader(translate("새 사용자 추가"))
    with st.form("add_user_form"):
        new_user_id = st.text_input(translate("아이디(이메일)"), key="new_user_id")
        new_user_pw = st.text_input(translate("비밀번호"), type="password", key="new_user_pw")
        new_user_name = st.text_input(translate("이름"), key="new_user_name")
        new_user_dept = st.text_input(translate("부서"), key="new_user_dept")
        
        submit_button = st.form_submit_button(translate("추가"))
        if submit_button:
            if not all([new_user_id, new_user_pw, new_user_name, new_user_dept]):
                st.error(translate("모든 필드를 입력해주세요."))
            else:
                # 이미 존재하는 이메일인지 확인
                existing_user = db.get_user(new_user_id)
                if existing_user:
                    st.error(translate("이미 존재하는 아이디입니다."))
                else:
                    # 새 사용자 추가
                    success = db.add_user(
                        email=new_user_id,
                        password=new_user_pw,
                        name=new_user_name,
                        role=new_user_dept
                    )
                    
                    if success:
                        st.success(translate("사용자가 추가되었습니다."))
                        st.rerun()
                    else:
                        st.error(translate("사용자 추가 중 오류가 발생했습니다."))
    
    # 사용자 삭제
    st.subheader(translate("사용자 삭제"))
    user_to_delete = st.selectbox(
        translate("삭제할 사용자 선택"),
        options=[user.get('이메일', '') for user in regular_users],
        key="user_delete_select"
    )
    
    if st.button(translate("삭제"), key="delete_user_button"):
        if user_to_delete:
            success = db.delete_user(user_to_delete)
            if success:
                st.success(translate("사용자가 삭제되었습니다."))
                st.rerun()
            else:
                st.error(translate("사용자 삭제 중 오류가 발생했습니다.")) 