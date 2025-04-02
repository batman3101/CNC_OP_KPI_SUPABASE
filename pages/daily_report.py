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
    
    # CSS 스타일 추가
    st.markdown("""
        <style>
        .highlight-box {
            background-color: #E8F4F9;
            border-radius: 10px;
            padding: 10px;
            margin: 5px 0;
        }
        .metric-label {
            font-size: 1.0em;
            font-weight: bold;
            color: #666;
        }
        .performer {
            font-size: 2.0em;
            font-weight: bold;
            color: #2C3E50;
        }
        .percentage-value {
            font-size: 2.0em;
            font-weight: bold;
            color: #000;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 데이터 로드
    if 'daily_report_data' not in st.session_state:
        st.session_state.daily_report_data = None
    
    if 'production_data' not in st.session_state or st.session_state.production_data is None:
        from pages.production import load_production_data
        st.session_state.production_data = load_production_data()
    
    # 날짜 선택
    target_date = st.date_input("조회할 일자", value=datetime.now().date())
    
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
        
        # 작업자별 통계 계산
        worker_stats = calculate_worker_stats(df)  
        
        # KPI 및 최고 성과자 계산
        best_performers = calculate_best_performers(worker_stats)
        daily_averages = calculate_daily_averages(worker_stats)

        # 일간 평균 KPI 표시
        st.subheader("일간 평균 KPI")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">🎯 생산 목표 달성률</div>
                    <div style="font-size: 24px; font-weight: bold;">{daily_averages['production_rate']:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">⚠️ 불량률</div>
                    <div style="font-size: 24px; font-weight: bold;">{daily_averages['defect_rate']:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">⚡ 작업효율</div>
                    <div style="font-size: 24px; font-weight: bold;">{daily_averages['efficiency_rate']:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)

        # 최고 성과자 KPI 표시
        st.subheader("최고 성과자")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">🎯 생산 목표 달성률</div>
                    <div style="font-size: 24px; font-weight: bold;">{best_performers['production_rate']:.1f}%</div>
                    <div class="performer">{best_performers['production_worker']}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">⚠️ 불량률</div>
                    <div style="font-size: 24px; font-weight: bold;">{best_performers['defect_rate']:.1f}%</div>
                    <div class="performer">{best_performers['defect_worker']}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">⚡ 작업효율</div>
                    <div style="font-size: 24px; font-weight: bold;">{best_performers['efficiency_rate']:.1f}%</div>
                    <div class="performer">{best_performers['efficiency_worker']}</div>
                </div>
            """, unsafe_allow_html=True)

        # 작업자별 생산량 그래프
        st.subheader("작업자별 생산량")
        
        # 그래프 데이터 준비
        fig = go.Figure()
        
        # 목표수량 막대 그래프 (하늘색)
        fig.add_trace(go.Bar(
            name='목표수량',
            x=worker_stats['작업자'],
            y=worker_stats['목표수량'],
            marker_color='rgba(173, 216, 230, 0.7)'  # 하늘색
        ))
        
        # 생산수량 꺾은선 그래프 (파란색)
        fig.add_trace(go.Scatter(
            name='생산수량',
            x=worker_stats['작업자'],
            y=worker_stats['생산수량'],
            line=dict(color='royalblue', width=2),
            mode='lines+markers'
        ))
        
        # 불량수량 꺾은선 그래프 (빨간색)
        fig.add_trace(go.Scatter(
            name='불량수량',
            x=worker_stats['작업자'],
            y=worker_stats['불량수량'],
            line=dict(color='red', width=2),
            mode='lines+markers'
        ))
        
        # 그래프 레이아웃 설정
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            yaxis=dict(
                title='수량',
                gridcolor='lightgray',
                gridwidth=0.5,
                zeroline=False
            ),
            plot_bgcolor='white'
        )
        
        # 그래프 표시
        st.plotly_chart(fig, use_container_width=True)
        
        # 작업자별 일간 실적 테이블
        st.subheader("작업자별 일간 실적")
        
        # 작업효율에 % 추가
        worker_stats['작업효율'] = worker_stats['작업효율'].astype(str) + '%'
        
        # 테이블 표시
        display_columns = ['작업자', '목표수량', '생산수량', '불량수량', '작업효율']
        st.dataframe(
            worker_stats[display_columns],
            use_container_width=True,
            hide_index=True
        )
        
    except Exception as e:
        st.error(f"데이터 처리 중 오류가 발생했습니다: {str(e)}")
        import traceback
        print(f"[ERROR] 상세 오류: {traceback.format_exc()}")

def calculate_worker_stats(df):
    # 작업자별 통계 계산
    worker_stats = df.groupby('작업자').agg({
        '목표수량': 'sum',
        '생산수량': 'sum',
        '불량수량': 'sum'
    }).reset_index()
    
    # 작업효율 계산
    worker_stats['작업효율'] = round(
        ((worker_stats['생산수량'] - worker_stats['불량수량']) / worker_stats['목표수량']) * 100,
        1
    )
    return worker_stats

def calculate_daily_averages(worker_stats):
    # 일간 평균 KPI 계산
    total_target = worker_stats['목표수량'].sum()
    total_production = worker_stats['생산수량'].sum()
    total_defects = worker_stats['불량수량'].sum()
    
    return {
        'production_rate': (total_production / total_target) * 100,
        'defect_rate': (total_defects / total_production) * 100 if total_production > 0 else 0,
        'efficiency_rate': ((total_production - total_defects) / total_target) * 100
    }

def calculate_best_performers(worker_stats):
    # 최고 성과자 및 해당 KPI 값 계산
    if len(worker_stats) == 0:
        return {
            'production_worker': '-',
            'production_rate': 0,
            'defect_worker': '-',
            'defect_rate': 0,
            'efficiency_worker': '-',
            'efficiency_rate': 0
        }
    
    best_production = worker_stats.loc[worker_stats['생산수량'].idxmax()]
    best_defect = worker_stats.loc[worker_stats['불량수량'].idxmin()]
    best_efficiency = worker_stats.loc[worker_stats['작업효율'].idxmax()]
    
    return {
        'production_worker': best_production['작업자'],
        'production_rate': (best_production['생산수량'] / best_production['목표수량']) * 100,
        'defect_worker': best_defect['작업자'],
        'defect_rate': (best_defect['불량수량'] / best_defect['생산수량']) * 100 if best_defect['생산수량'] > 0 else 0,
        'efficiency_worker': best_efficiency['작업자'],
        'efficiency_rate': best_efficiency['작업효율']
    }

def show_daily_report():
    """
    app.py에서 호출하기 위한 함수입니다.
    내부적으로 show() 함수를 호출합니다.
    """
    show()

if __name__ == "__main__":
    show() 