import streamlit as st
import bcrypt
from utils.translation import translate

def verify_password(stored_hash, provided_password):
    """저장된 해시와 제공된 비밀번호를 비교하여 일치하는지 확인"""
    try:
        # 디버그 출력
        print(f"[DEBUG] 비밀번호 검증 시도 - 저장된 해시: {stored_hash[:20] if stored_hash else 'None'}, 입력된 비밀번호: {'*' * len(provided_password)}")
        
        # 저장된 해시가 문자열이라면 바이트로 변환
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        
        # 제공된 비밀번호가 문자열이라면 바이트로 변환
        if isinstance(provided_password, str):
            provided_password = provided_password.encode('utf-8')
        
        # 예외 처리 - 해시가 bcrypt 형식인지 확인
        if stored_hash.startswith(b'$2'):
            # bcrypt 형식이면 정상 검증
            return bcrypt.checkpw(provided_password, stored_hash)
        else:
            # 일반 텍스트 비교 (개발용)
            print(f"[WARNING] 해시가 bcrypt 형식이 아닙니다. 일반 텍스트 비교 시도")
            return provided_password.decode('utf-8') == stored_hash.decode('utf-8')
    except Exception as e:
        print(f"[ERROR] 비밀번호 검증 중 오류 발생: {e}")
        import traceback
        print(f"[ERROR] 상세 오류: {traceback.format_exc()}")
        
        # 최후의 수단으로 plain text 비교 (개발용)
        try:
            if stored_hash and provided_password:
                if isinstance(stored_hash, bytes):
                    stored_hash = stored_hash.decode('utf-8')
                if isinstance(provided_password, bytes):
                    provided_password = provided_password.decode('utf-8')
                return stored_hash == provided_password
        except Exception as inner_e:
            print(f"[ERROR] plain text 비교 중 오류 발생: {inner_e}")
        
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
                print(f"[DEBUG] 총 {len(users)}명의 사용자가 있습니다.")
                
                # 일치하는 사용자 찾기
                for user in users:
                    print(f"[DEBUG] 사용자 확인: {user.get('이름')}, 이메일: {user.get('이메일')}")
                    if (user.get('이메일', '').strip().lower() == email.strip().lower()):
                        print(f"[DEBUG] 이메일 일치: {email}")
                        
                        # 비밀번호 검증
                        stored_password = user.get('비밀번호', '')
                        if verify_password(stored_password, password):
                            # 로그인 성공 - 세션 상태 업데이트
                            st.session_state.authenticated = True
                            st.session_state.username = user.get('이름')
                            st.session_state.user_email = email.strip().lower()
                            st.session_state.user_role = user.get('권한', '')
                            
                            print(f"[INFO] 로그인 성공: {user.get('이름')}")
                            return {
                                'username': user.get('이름'),
                                'email': email.strip().lower()
                            }
                        else:
                            print(f"[DEBUG] 비밀번호 불일치: {email}")
                
                # 로그인 실패 처리
                st.error(translate("사용자 이름 또는 비밀번호가 잘못되었습니다."))
                return None
                
            except Exception as e:
                print(f"[ERROR] 로그인 처리 중 오류 발생: {e}")
                import traceback
                print(f"[ERROR] 상세 오류: {traceback.format_exc()}")
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