import streamlit as st
import bcrypt
from utils.translation import translate

def verify_password(stored_hash, provided_password):
    """저장된 해시와 제공된 비밀번호를 비교하여 일치하는지 확인"""
    try:
        # 저장된 해시가 문자열이라면 바이트로 변환
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        
        # 제공된 비밀번호가 문자열이라면 바이트로 변환
        if isinstance(provided_password, str):
            provided_password = provided_password.encode('utf-8')
            
        return bcrypt.checkpw(provided_password, stored_hash)
    except Exception as e:
        print(f"비밀번호 검증 중 오류 발생: {e}")
        return False
    
def login():
    """로그인 페이지를 표시하고 로그인 처리"""
    
    # 이미 로그인되어 있으면 처리 중단
    if st.session_state.get('authenticated', False):
        return {'username': st.session_state.username, 'email': st.session_state.user_email}
    
    # 로그인 폼
    st.title(translate("생산관리 시스템"))
    
    with st.form("login_form"):
        email = st.text_input(translate("이메일"))
        password = st.text_input(translate("비밀번호"), type="password")
        submit_button = st.form_submit_button(translate("로그인"))
    
    # 로그인 버튼 클릭 처리
    if submit_button:
        # 로그인 처리 로직
        if 'db' in st.session_state:
            try:
                users = st.session_state.db.get_all_users()
                
                # 일치하는 사용자 찾기
                for user in users:
                    if (user.get('이메일', '').strip().lower() == email.strip().lower() and 
                        verify_password(user.get('비밀번호', '').encode('utf-8'), password)):
                        
                        # 로그인 성공 - 세션 상태 업데이트
                        st.session_state.authenticated = True
                        st.session_state.username = user.get('이름')
                        st.session_state.user_email = email.strip().lower()
                        st.session_state.user_role = user.get('권한', '')
                        
                        return {
                            'username': user.get('이름'),
                            'email': email.strip().lower()
                        }
                
                # 로그인 실패 처리
                st.error(translate("사용자 이름 또는 비밀번호가 잘못되었습니다."))
                return None
                
            except Exception as e:
                st.error(f"로그인 처리 중 오류 발생: {e}")
                return None
        else:
            # Supabase 연결이 없는 경우
            st.warning(translate("관리자 계정이 없습니다. 먼저 관리자 계정을 생성해주세요."))
            return None
    
    return None

def logout():
    """로그아웃 처리 - 세션 상태에서 인증 정보 제거"""
    if 'authenticated' in st.session_state:
        st.session_state.authenticated = False
    if 'username' in st.session_state:
        st.session_state.username = None
    if 'user_email' in st.session_state:
        st.session_state.user_email = None
    if 'user_role' in st.session_state:
        st.session_state.user_role = None 