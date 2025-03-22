import streamlit as st
import bcrypt
from typing import Optional

def login() -> Optional[dict]:
    """
    사용자 로그인 처리 함수
    
    Returns:
        Optional[dict]: 로그인 성공 시 사용자 정보, 실패 시 None
    """
    st.title("로그인")
    
    with st.form(key="login_form"):
        email = st.text_input("이메일", key="login_email_input")
        password = st.text_input("비밀번호", type="password", key="login_password_input")
        submitted = st.form_submit_button("로그인")
        
        if submitted:
            if 'db' in st.session_state:
                # Supabase에서 사용자 정보 조회
                user = st.session_state.db.get_user(email)
                
                if user and verify_password(password, user['비밀번호']):
                    # 사용자 정보 세션에 저장
                    st.session_state.authenticated = True
                    st.session_state.username = user['이름']
                    st.session_state.user_email = email.strip().lower()
                    st.session_state.user_role = user['권한']
                    
                    # 관리자 계정 목록 다시 로드 (최신 상태 유지)
                    try:
                        all_users = st.session_state.db.get_all_users()
                        admin_emails = [u.get('이메일', '').strip().lower() for u in all_users if u.get('권한', '') == '관리자']
                        st.session_state.admin_accounts = admin_emails
                        
                        # 관리자 권한 설정 (이메일로 확인)
                        if st.session_state.user_email in st.session_state.admin_accounts:
                            st.session_state.user_role = '관리자'
                    except Exception as e:
                        st.error(f"관리자 계정 목록 업데이트 중 오류 발생: {e}")
                    
                    st.success(f"{user['이름']}님, 로그인 성공!")
                    return user
                else:
                    st.error("이메일 또는 비밀번호가 올바르지 않습니다.")
            else:
                st.error("데이터베이스 연결이 설정되어 있지 않습니다.")
    
    return None

def logout():
    """
    사용자 로그아웃 처리 함수
    """
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_email = None
    st.session_state.user_role = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증 함수
    
    Args:
        plain_password: 일반 텍스트 비밀번호
        hashed_password: 해시된 비밀번호
        
    Returns:
        bool: 비밀번호 일치 여부
    """
    try:
        # 해시된 비밀번호가 bcrypt 형식인지 확인
        if hashed_password.startswith('$2'):
            # bcrypt 해시 검증
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        else:
            # 일반 텍스트 비밀번호 비교 (개발 환경용)
            return plain_password == hashed_password
    except Exception as e:
        print(f"비밀번호 검증 중 오류 발생: {e}")
        return False 