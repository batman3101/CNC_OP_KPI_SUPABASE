import streamlit as st
from datetime import datetime
from utils.supabase_db import SupabaseDB  # SupabaseDB 클래스를 import
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

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
    if st.button("관리자 및 사용자 관리"):
        st.session_state.current_page = "admin_user"
    if st.button("작업자 등록 및 관리"):
        st.session_state.current_page = "worker"
    if st.button("생산 모델 관리"):
        st.session_state.current_page = "model"
    if st.button("생산 실적 관리"):
        st.session_state.current_page = "production"        
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 리포트 메뉴 그룹
    st.markdown('<div class="sidebar-group">', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-title">📊 리포트 메뉴</p>', unsafe_allow_html=True)
    if st.button("종합 대시보드"):
        st.session_state.current_page = "dashboard"
    if st.button("일간 리포트"):
        st.session_state.current_page = "daily"
    if st.button("주간 리포트"):
        st.session_state.current_page = "weekly"
    if st.button("월간 리포트"):
        st.session_state.current_page = "monthly"
    if st.button("연간 리포트"):
        st.session_state.current_page = "yearly"
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 데이터 관리 메뉴 그룹
    st.markdown('<div class="sidebar-group">', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-title">🔄 데이터 관리</p>', unsafe_allow_html=True)
    if st.button("데이터 수정"):
        st.session_state.current_page = "data_edit"
    if st.button("데이터 동기화"):
        st.session_state.current_page = "data_sync"    
    st.markdown('</div>', unsafe_allow_html=True)

# 로그인 상태 초기화
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'admin_accounts' not in st.session_state:
    st.session_state.admin_accounts = {
        'zetooo1972@gmail.com': 'admin7472'
    }
if 'current_page' not in st.session_state:
    st.session_state.current_page = "dashboard"

# 세션 상태 초기화
if 'db' not in st.session_state:
    # Supabase 연결 정보 확인
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        st.error("Supabase 연결 정보가 설정되어 있지 않습니다. '데이터 동기화' 메뉴에서 설정해주세요.")
    else:
        st.session_state.db = SupabaseDB()  # SupabaseDB 클래스의 인스턴스 생성

def show_login():
    st.title("로그인")
    
    with st.form("login_form"):
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인")
        
        if submitted:
            if (username in st.session_state.admin_accounts and 
                st.session_state.admin_accounts[username] == password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

# 로그인 상태가 아니면 로그인 페이지 표시
if not st.session_state.authenticated:
    show_login()
else:
    # 로그인 상태이면 메인 페이지 표시
    st.sidebar.title("CNC KPI Management")
    
    # 로그아웃 버튼
    if st.sidebar.button("로그아웃"):
        st.session_state.authenticated = False
        st.session_state.username = None
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
    elif st.session_state.current_page == "data_edit":
        from pages.data_edit import show_data_edit
        show_data_edit()
    elif st.session_state.current_page == "data_sync":
        from pages.data_sync import show_data_sync
        show_data_sync()
    elif st.session_state.current_page == "model":
        from pages.model_management import show_model_management
        show_model_management()

def main():
    st.title("CNC KPI Management")
    # ... 나머지 코드 ...

if __name__ == "__main__":
    main() 
