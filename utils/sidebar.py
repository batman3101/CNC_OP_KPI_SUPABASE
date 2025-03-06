import streamlit as st

def show_sidebar():
    with st.sidebar:
        # 관리자 메뉴
        st.subheader("👥 관리자 메뉴")
        with st.container():
            if st.button("관리자 및 사용자 관리", use_container_width=True):
                st.session_state.current_page = "admin"
            if st.button("작업자 등록 및 관리", use_container_width=True):
                st.session_state.current_page = "worker"
            if st.button("생산 모델 관리", use_container_width=True):
                st.session_state.current_page = "model"
            if st.button("생산 실적 관리", use_container_width=True):
                st.session_state.current_page = "production"
        
        # 리포트 메뉴
        st.subheader("📊 리포트 메뉴")
        with st.container():
            if st.button("종합 대시보드", use_container_width=True):
                st.session_state.current_page = "dashboard"
            if st.button("일간 리포트", use_container_width=True):
                st.session_state.current_page = "daily"
            if st.button("주간 리포트", use_container_width=True):
                st.session_state.current_page = "weekly"
            if st.button("월간 리포트", use_container_width=True):
                st.session_state.current_page = "monthly"
            if st.button("연간 리포트", use_container_width=True):
                st.session_state.current_page = "yearly"

        # CNC KPI Management
        st.subheader("CNC KPI Management")
        with st.container():
            if st.button("로그아웃", use_container_width=True):
                st.session_state.current_page = "logout" 