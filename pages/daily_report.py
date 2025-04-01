import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os
import numpy as np
import json
from utils.supabase_db import SupabaseDB

# 프로젝트 루트 디렉토리를 path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.local_storage import LocalStorage
import utils.common as common

# 페이지네이션 기능 구현
def paginate_dataframe(dataframe, page_size, page_num):
    """
    dataframe을 페이지네이션하여 반환합니다.
    """
    total_pages = len(dataframe) // page_size + (1 if len(dataframe) % page_size > 0 else 0)
    
    # 페이지 번호 유효성 검사
    if page_num < 1:
        page_num = 1
    elif page_num > total_pages:
        page_num = total_pages
    
    # 페이지 범위 계산
    start_idx = (page_num - 1) * page_size
    end_idx = min(start_idx + page_size, len(dataframe))
    
    return dataframe.iloc[start_idx:end_idx], total_pages

def show():
    st.title("📊 일일 실적 보고서")
    
    # 데이터 로드
    if 'daily_report_data' not in st.session_state:
        st.session_state.daily_report_data = None
    
    if 'production_data' not in st.session_state or st.session_state.production_data is None:
        from pages.production import load_production_data
        st.session_state.production_data = load_production_data()
    
    # 날짜 선택
    with st.form(key="일일보고서_날짜선택"):
        col1, col2 = st.columns(2)
        with col1:
            target_date = st.date_input("보고서 날짜", value=datetime.now().date())
        with col2:
            generate_button = st.form_submit_button("보고서 생성", use_container_width=True)
    
    if generate_button or st.session_state.daily_report_data is not None:
        # 선택된 날짜의 데이터 필터링
        target_date_str = target_date.strftime("%Y-%m-%d")
        
        try:
            # 데이터 존재 여부 확인
            if st.session_state.production_data is None or len(st.session_state.production_data) == 0:
                st.warning("생산 데이터가 없습니다.")
                return
            
            # 해당 날짜의 데이터만 필터링
            filtered_records = []
            for record in st.session_state.production_data:
                if record.get('날짜', '') == target_date_str:
                    filtered_records.append(record)
            
            if not filtered_records:
                st.warning(f"{target_date_str} 날짜에 해당하는 생산 데이터가 없습니다.")
                return
            
            # 데이터프레임 생성
            df = pd.DataFrame(filtered_records)
            
            # 세션에 저장
            st.session_state.daily_report_data = df
            
            # 여러 탭으로 데이터 표시
            tab1, tab2, tab3 = st.tabs(["요약", "상세 데이터", "효율성 분석"])
            
            with tab1:
                display_summary(df, target_date_str)
            
            with tab2:
                display_detailed_data(df)
            
            with tab3:
                display_efficiency_analysis(df)
            
        except Exception as e:
            st.error(f"데이터 처리 중 오류가 발생했습니다: {str(e)}")
            import traceback
            print(f"[ERROR] 상세 오류: {traceback.format_exc()}")

def display_summary(df, date_str):
    try:
        st.header(f"{date_str} 일일 생산 요약")
        
        st.markdown("### 📈 생산 실적 요약")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_target = df['목표수량'].sum()
            st.metric("총 목표 수량", f"{total_target:,}")
        
        with col2:
            total_production = df['생산수량'].sum()
            st.metric("총 생산 수량", f"{total_production:,}")
        
        with col3:
            total_defect = df['불량수량'].sum()
            st.metric("총 불량 수량", f"{total_defect:,}")
        
        with col4:
            if total_target > 0:
                achievement_rate = (total_production / total_target) * 100
                st.metric("목표 달성률", f"{achievement_rate:.1f}%")
        
        # 작업자별 생산량
        st.markdown("### 👥 작업자별 생산량")
        worker_production = df.groupby('작업자')['생산수량'].sum().reset_index()
        worker_production = worker_production.sort_values('생산수량', ascending=False)
        
        # 간단한 차트
        st.bar_chart(worker_production.set_index('작업자'))
        
        # 라인별 생산량
        st.markdown("### 🏭 라인별 생산량")
        line_production = df.groupby('라인번호')['생산수량'].sum().reset_index()
        line_production = line_production.sort_values('생산수량', ascending=False)
        
        # 간단한 차트
        st.bar_chart(line_production.set_index('라인번호'))
        
        # 모델별 생산량
        st.markdown("### 📊 모델별 생산량")
        model_production = df.groupby('모델차수')['생산수량'].sum().reset_index()
        model_production = model_production.sort_values('생산수량', ascending=False)
        
        # 간단한 차트
        st.bar_chart(model_production.set_index('모델차수'))
        
    except Exception as e:
        st.error(f"요약 데이터 처리 중 오류가 발생했습니다: {str(e)}")

def display_detailed_data(df):
    st.header("상세 생산 데이터")
    
    try:
        if df.empty:
            st.warning("표시할 데이터가 없습니다.")
            return
        
        # 페이지네이션 설정
        if 'detailed_page_number' not in st.session_state:
            st.session_state.detailed_page_number = 1
        page_size = 10
        
        # 페이지네이션된 데이터프레임 가져오기
        paginated_df, total_pages = paginate_dataframe(df, page_size, st.session_state.detailed_page_number)
        
        # 테이블 표시
        st.dataframe(paginated_df, use_container_width=True)
        
        # 페이지네이션 UI
        col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
        with col1:
            if st.button("◀️ 이전", key="detailed_prev", disabled=st.session_state.detailed_page_number <= 1):
                st.session_state.detailed_page_number -= 1
                st.rerun()
        with col2:
            if st.button("다음 ▶️", key="detailed_next", disabled=st.session_state.detailed_page_number >= total_pages):
                st.session_state.detailed_page_number += 1
                st.rerun()
        with col3:
            st.write(f"페이지: {st.session_state.detailed_page_number}/{total_pages}")
        with col4:
            new_page = st.number_input("페이지 이동", min_value=1, max_value=total_pages, value=st.session_state.detailed_page_number, step=1, key="detailed_page_input")
            if new_page != st.session_state.detailed_page_number:
                st.session_state.detailed_page_number = new_page
                st.rerun()
        
        # 상세 레코드 선택 기능
        st.markdown("### 🔍 레코드 선택")
        selected_index = st.selectbox(
            "상세 정보를 볼 레코드를 선택하세요",
            options=paginated_df.index.tolist(),
            format_func=lambda x: f"{paginated_df.loc[x, '작업자']} - {paginated_df.loc[x, '라인번호']} - {paginated_df.loc[x, '모델차수']} (목표: {paginated_df.loc[x, '목표수량']}, 생산: {paginated_df.loc[x, '생산수량']})"
        )
        
        if selected_index is not None:
            with st.expander("📄 선택한 레코드 상세 정보", expanded=True):
                st.json(df.loc[selected_index].to_dict())
    
    except Exception as e:
        st.error(f"상세 데이터 처리 중 오류가 발생했습니다: {str(e)}")

def display_efficiency_analysis(df):
    st.header("생산 효율성 분석")
    
    try:
        if df.empty:
            st.warning("분석할 데이터가 없습니다.")
            return
        
        # 작업자별 효율성 계산
        worker_efficiency = pd.DataFrame()
        worker_efficiency['작업자'] = df['작업자']
        worker_efficiency['목표수량'] = df['목표수량']
        worker_efficiency['생산수량'] = df['생산수량']
        worker_efficiency['불량수량'] = df['불량수량']
        worker_efficiency['달성률'] = (worker_efficiency['생산수량'] / worker_efficiency['목표수량'] * 100).fillna(0).round(1)
        worker_efficiency['불량률'] = (worker_efficiency['불량수량'] / worker_efficiency['생산수량'] * 100).fillna(0).round(1)
        
        # 작업자별 효율성 집계
        worker_summary = worker_efficiency.groupby('작업자').agg({
            '목표수량': 'sum',
            '생산수량': 'sum',
            '불량수량': 'sum'
        }).reset_index()
        
        worker_summary['달성률'] = (worker_summary['생산수량'] / worker_summary['목표수량'] * 100).fillna(0).round(1)
        worker_summary['불량률'] = (worker_summary['불량수량'] / worker_summary['생산수량'] * 100).fillna(0).round(1)
        
        # 효율성 표시
        st.markdown("### 👥 작업자별 생산 효율성")
        
        # 페이지네이션 설정
        if 'efficiency_page_number' not in st.session_state:
            st.session_state.efficiency_page_number = 1
        page_size = 5
        
        # 페이지네이션된 데이터프레임 가져오기
        paginated_ws, total_pages = paginate_dataframe(worker_summary, page_size, st.session_state.efficiency_page_number)
        
        # 테이블 표시
        st.dataframe(paginated_ws, use_container_width=True)
        
        # 페이지네이션 UI
        col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
        with col1:
            if st.button("◀️ 이전", key="efficiency_prev", disabled=st.session_state.efficiency_page_number <= 1):
                st.session_state.efficiency_page_number -= 1
                st.rerun()
        with col2:
            if st.button("다음 ▶️", key="efficiency_next", disabled=st.session_state.efficiency_page_number >= total_pages):
                st.session_state.efficiency_page_number += 1
                st.rerun()
        with col3:
            st.write(f"페이지: {st.session_state.efficiency_page_number}/{total_pages}")
        with col4:
            new_page = st.number_input("페이지 이동", min_value=1, max_value=total_pages, value=st.session_state.efficiency_page_number, step=1, key="efficiency_page_input")
            if new_page != st.session_state.efficiency_page_number:
                st.session_state.efficiency_page_number = new_page
                st.rerun()
        
        # 달성률 및 불량률 시각화
        st.markdown("### 📊 작업자별 달성률 및 불량률")
        col1, col2 = st.columns(2)
        
        with col1:
            achievement_chart = pd.DataFrame({
                '작업자': worker_summary['작업자'],
                '달성률': worker_summary['달성률']
            }).set_index('작업자')
            st.subheader("달성률 (%)")
            st.bar_chart(achievement_chart)
        
        with col2:
            defect_chart = pd.DataFrame({
                '작업자': worker_summary['작업자'],
                '불량률': worker_summary['불량률']
            }).set_index('작업자')
            st.subheader("불량률 (%)")
            st.bar_chart(defect_chart)
        
        # 라인별 효율성 분석
        st.markdown("### 🏭 라인별 생산 효율성")
        line_efficiency = df.groupby('라인번호').agg({
            '목표수량': 'sum',
            '생산수량': 'sum',
            '불량수량': 'sum'
        }).reset_index()
        
        line_efficiency['달성률'] = (line_efficiency['생산수량'] / line_efficiency['목표수량'] * 100).fillna(0).round(1)
        line_efficiency['불량률'] = (line_efficiency['불량수량'] / line_efficiency['생산수량'] * 100).fillna(0).round(1)
        
        st.dataframe(line_efficiency, use_container_width=True)
        
        # 모델별 효율성 분석
        st.markdown("### 📝 모델별 생산 효율성")
        model_efficiency = df.groupby('모델차수').agg({
            '목표수량': 'sum',
            '생산수량': 'sum',
            '불량수량': 'sum'
        }).reset_index()
        
        model_efficiency['달성률'] = (model_efficiency['생산수량'] / model_efficiency['목표수량'] * 100).fillna(0).round(1)
        model_efficiency['불량률'] = (model_efficiency['불량수량'] / model_efficiency['생산수량'] * 100).fillna(0).round(1)
        
        st.dataframe(model_efficiency, use_container_width=True)
    
    except Exception as e:
        st.error(f"효율성 분석 중 오류가 발생했습니다: {str(e)}")
        import traceback
        print(f"[ERROR] 상세 오류: {traceback.format_exc()}")

def show_daily_report():
    """
    app.py에서 호출하기 위한 함수입니다.
    내부적으로 show() 함수를 호출합니다.
    """
    show()

if __name__ == "__main__":
    show() 