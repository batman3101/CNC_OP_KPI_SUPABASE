import streamlit as st
from datetime import datetime
from utils.supabase_db import SupabaseDB  # SupabaseDB 클래스를 import
import os
from dotenv import load_dotenv
import bcrypt
from utils.auth import initialize_admin
from utils.sidebar import show_sidebar
from utils.login import login, logout, verify_password

# 캐시 초기화 - 앱 시작 시 데이터 갱신을 보장
st.cache_data.clear()
st.cache_resource.clear()

# 환경 변수 로드
load_dotenv()

# 관리자 계정 초기화
initialize_admin()

# 영어 메뉴 항목 숨기기
st.set_page_config(
    page_title="생산관리 시스템",
    page_icon="🏭",
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# 페이지 숨기기 CSS
hide_pages = """
<style>
[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
    display: none;
}
</style>
"""
st.markdown(hide_pages, unsafe_allow_html=True)

# 사이드바 스타일 설정
st.markdown("""
<style>
    .sidebar-group {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .sidebar-title {
        font-weight: bold;
        margin-bottom: 10px;
        color: #1f77b4;
    }
    .stButton>button {
        width: 100%;
        margin: 2px 0;
    }
</style>
""", unsafe_allow_html=True)

# 사이드바 구성
with st.sidebar:
    # 관리자 메뉴 그룹
    st.markdown('<div class="sidebar-group">', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-title">👥 관리자 메뉴</p>', unsafe_allow_html=True)
    if st.button("🔑 관리자 및 사용자 관리", key="admin_user_btn"):
        st.session_state.current_page = "admin_user"
    if st.button("👨‍🏭 작업자 등록 및 관리", key="worker_btn"):
        st.session_state.current_page = "worker"
    if st.button("📦 생산 모델 관리", key="model_btn"):
        st.session_state.current_page = "model"
    if st.button("📋 생산 실적 관리", key="production_btn"):
        st.session_state.current_page = "production"
    if st.button("💾 데이터 관리", key="data_sync_btn"):
        st.session_state.current_page = "data_sync"
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 리포트 메뉴 그룹
    st.markdown('<div class="sidebar-group">', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-title">📊 리포트 메뉴</p>', unsafe_allow_html=True)
    if st.button("📈 종합 대시보드", key="dashboard_btn"):
        st.session_state.current_page = "dashboard"
    if st.button("📅 일간 리포트", key="daily_btn"):
        st.session_state.current_page = "daily"
    if st.button("📆 주간 리포트", key="weekly_btn"):
        st.session_state.current_page = "weekly"
    if st.button("📊 월간 리포트", key="monthly_btn"):
        st.session_state.current_page = "monthly"
    if st.button("📅 연간 리포트", key="yearly_btn"):
        st.session_state.current_page = "yearly"
    st.markdown('</div>', unsafe_allow_html=True)

# 로그인 화면에 관리자 계정 목록이 표시되지 않도록 CSS 추가
hide_admin_list = """
<style>
[data-testid="stText"] {
    display: none;
}
</style>
"""
st.markdown(hide_admin_list, unsafe_allow_html=True)

# 로그인 상태 초기화
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None    
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'admin_accounts' not in st.session_state:
    st.session_state.admin_accounts = []

if 'current_page' not in st.session_state:
    st.session_state.current_page = "dashboard"

# 세션 상태 초기화
if 'db' not in st.session_state:
    # Supabase 연결 정보 확인
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        st.error("Supabase 연결 정보가 설정되어 있지 않습니다. '데이터 관리' 메뉴에서 설정해주세요.")
    else:
        st.session_state.db = SupabaseDB()  # SupabaseDB 클래스의 인스턴스 생성
        # 관리자 계정 목록 로드
        try:
            admin_users = st.session_state.db.get_all_users()
            admin_emails = [user.get('이메일', '').strip().lower() for user in admin_users if user.get('권한', '') == '관리자']
            st.session_state.admin_accounts = admin_emails
        except Exception as e:
            st.error(f"관리자 계정 로드 중 오류 발생: {e}")

# 데이터 자동 동기화 함수
def auto_sync_data():
    """앱 시작 시 자동으로 데이터 동기화 수행"""
    if 'db' in st.session_state:
        try:
            # 작업자 데이터 동기화
            if 'workers' not in st.session_state or not st.session_state.workers:
                from pages.worker_management import load_worker_data
                st.session_state.workers = load_worker_data()
                print(f"[AUTO-SYNC] 작업자 데이터 {len(st.session_state.workers)}개 로드 완료")
            
            # 생산 실적 데이터 동기화
            if 'production_data' not in st.session_state:
                from pages.production import load_production_data
                st.session_state.production_data = load_production_data()
                print(f"[AUTO-SYNC] 생산 실적 데이터 {len(st.session_state.production_data)}개 로드 완료")
            
            # 모델 데이터 동기화
            if 'models' not in st.session_state:
                from pages.model_management import load_model_data
                st.session_state.models = load_model_data()
                print(f"[AUTO-SYNC] 모델 데이터 {len(st.session_state.models)}개 로드 완료")
                
            print("[AUTO-SYNC] 데이터 자동 동기화 완료")
        except Exception as e:
            print(f"[ERROR] 자동 데이터 동기화 중 오류 발생: {e}")

# 로그인 상태가 아니면 로그인 페이지 표시
if not st.session_state.authenticated:
    user = login()
    if user:
        # 로그인 성공 시 자동 데이터 동기화 실행
        auto_sync_data()
        st.rerun()
else:
    # 로그인 상태이면 메인 페이지 표시
    st.sidebar.title(f"안녕하세요, {st.session_state.username}님")
    
    # 관리자 권한 확인 및 업데이트 (페이지 접근 시마다 확인)
    if 'db' in st.session_state and hasattr(st.session_state, 'user_email'):
        try:
            all_users = st.session_state.db.get_all_users()
            admin_emails = [user.get('이메일', '').strip().lower() for user in all_users if user.get('권한', '') == '관리자']
            st.session_state.admin_accounts = admin_emails
            
            if st.session_state.user_email in st.session_state.admin_accounts:
                st.session_state.user_role = '관리자'
        except Exception as e:
            pass
    
    # 로그아웃 버튼
    if st.sidebar.button("로그아웃", key="logout_btn"):
        logout()
        st.rerun()

    # 페이지 라우팅
    if st.session_state.current_page == "admin_user":
        from pages.admin_management import show_admin_management
        show_admin_management()
    elif st.session_state.current_page == "worker":
        from pages.worker_management import show_worker_management
        show_worker_management()
    elif st.session_state.current_page == "dashboard":
        from pages.dashboard import show_dashboard
        show_dashboard()
    elif st.session_state.current_page == "production":
        from pages.production import show_production_management
        show_production_management()
    elif st.session_state.current_page == "daily":
        from pages.daily_report import show_daily_report
        show_daily_report()
    elif st.session_state.current_page == "weekly":
        from pages.weekly_report import show_weekly_report
        show_weekly_report()
    elif st.session_state.current_page == "monthly":
        from pages.monthly_report import show_monthly_report
        show_monthly_report()
    elif st.session_state.current_page == "yearly":
        from pages.yearly_report import show_yearly_report
        show_yearly_report()
    elif st.session_state.current_page == "model":
        from pages.model_management import show_model_management
        show_model_management()
    elif st.session_state.current_page == "data_sync":
        from pages.data_sync import show_data_sync
        show_data_sync()

# 앱 실행
if __name__ == "__main__":
    pass  # 메인 로직은 위에서 이미 실행됨 
