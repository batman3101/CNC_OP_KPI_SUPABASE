import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.supabase_db import SupabaseDB
from datetime import datetime, timedelta

def show_yearly_report():
    st.title("🗓️ 연간 리포트")
    
    # CSS 스타일 추가
    st.markdown("""
        <style>
        .metric-box {
            background-color: #E8F4F9;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #2C3E50;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 현재 연도 가져오기
    current_year = datetime.now().year
    
    # 연도 선택 (현재 연도부터 2년 전까지)
    year_options = list(range(current_year, current_year - 3, -1))
    year = st.selectbox(
        "년도",
        options=year_options,
        index=0
    )
    
    # 데이터 조회
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    records = st.session_state.db.get_production_records(
        start_date=start_date,
        end_date=end_date
    )
    
    if records:
        df = pd.DataFrame(records)
        
        # 연간 종합 현황 계산
        total_target = df['목표수량'].sum()
        total_production = df['생산수량'].sum()
        total_defects = df['불량수량'].sum()
        
        # 연간 KPI 계산
        production_rate = round((total_production / total_target) * 100, 1)
        defect_rate = round((total_defects / total_production) * 100, 1)
        efficiency_rate = round(((total_production - total_defects) / total_target) * 100, 1)
        
        # 연간 종합 현황 표시
        st.subheader("연간 종합 현황")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">연간 목표량</div>
                    <div class="metric-value">{total_target:,}개</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">연간 생산량</div>
                    <div class="metric-value">{total_production:,}개</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">연간 불량수량</div>
                    <div class="metric-value">{total_defects:,}개</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">연간 달성률</div>
                    <div class="metric-value">{production_rate}%</div>
                </div>
            """, unsafe_allow_html=True)
        
        # 월별 현황
        st.subheader("월별 현황")
        monthly_stats = df.groupby(pd.to_datetime(df['날짜']).dt.month).agg({
            '목표수량': 'sum',
            '생산수량': 'sum',
            '불량수량': 'sum'
        }).reset_index()
        monthly_stats = monthly_stats.rename(columns={'날짜': '월'})
        
        # 테이블 표시
        st.dataframe(
            monthly_stats[['월', '목표수량', '생산수량', '불량수량']],
            use_container_width=True,
            hide_index=True
        )
        
        # 라인별 연간 현황
        st.subheader("라인별 연간 현황")
        line_stats = df.groupby('라인번호').agg({
            '목표수량': 'sum',
            '생산수량': 'sum',
            '불량수량': 'sum'
        }).reset_index()
        
        # 라인별 KPI 계산
        line_stats['생산목표달성률'] = round((line_stats['생산수량'] / line_stats['목표수량']) * 100, 1)
        line_stats['불량률'] = round((line_stats['불량수량'] / line_stats['생산수량']) * 100, 1)
        line_stats['작업효율'] = round(((line_stats['생산수량'] - line_stats['불량수량']) / line_stats['목표수량']) * 100, 1)
        
        # 테이블 표시
        st.dataframe(
            line_stats[['라인번호', '목표수량', '생산수량', '불량수량', '생산목표달성률', '불량률', '작업효율']],
            use_container_width=True,
            hide_index=True
        )
        
        # 하단 KPI 표시
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">연간 생산목표 달성률</div>
                    <div class="metric-value">{production_rate}%</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">연간 평균 불량률</div>
                    <div class="metric-value">{defect_rate}%</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">연간 평균 작업효율</div>
                    <div class="metric-value">{efficiency_rate}%</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-label">연간 총 생산량</div>
                    <div class="metric-value">{total_production:,}개</div>
                </div>
            """, unsafe_allow_html=True)
            
    else:
        st.info(f"{year}년의 생산 실적이 없습니다.") 