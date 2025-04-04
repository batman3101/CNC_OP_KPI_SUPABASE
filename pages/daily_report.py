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
from utils.translations import translate

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
    st.title(translate("📊 일일 실적 보고서"))
    
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
    target_date = st.date_input(translate("조회할 일자"), value=datetime.now().date())
    
    # 선택된 날짜의 데이터 필터링
    target_date_str = target_date.strftime("%Y-%m-%d")
    
    try:
        # 데이터 존재 여부 확인
        if st.session_state.production_data is None or len(st.session_state.production_data) == 0:
            st.warning(translate("생산 데이터가 없습니다."))
            return
        
        # 해당 날짜의 데이터만 필터링
        filtered_records = []
        for record in st.session_state.production_data:
            if record.get('날짜', '') == target_date_str:
                filtered_records.append(record)
        
        if not filtered_records:
            st.warning(f"{target_date_str} " + translate("날짜에 해당하는 생산 데이터가 없습니다."))
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
        st.subheader(translate("일간 평균 KPI"))
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">🎯 {translate('생산 목표 달성률')}</div>
                    <div style="font-size: 24px; font-weight: bold;">{daily_averages['production_rate']:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">⚠️ {translate('불량률')}</div>
                    <div style="font-size: 24px; font-weight: bold;">{daily_averages['defect_rate']:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">⚡ {translate('작업효율')}</div>
                    <div style="font-size: 24px; font-weight: bold;">{daily_averages['efficiency_rate']:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)

        # 최고 성과자 KPI 표시
        st.subheader(translate("최고 성과자"))
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">🎯 {translate('생산 목표 달성률')}</div>
                    <div style="font-size: 24px; font-weight: bold;">{best_performers['production_rate']:.1f}%</div>
                    <div class="performer">{best_performers['production_worker']}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">⚠️ {translate('불량률')}</div>
                    <div style="font-size: 24px; font-weight: bold;">{best_performers['defect_rate']:.1f}%</div>
                    <div class="performer">{best_performers['defect_worker']}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">⚡ {translate('작업효율')}</div>
                    <div style="font-size: 24px; font-weight: bold;">{best_performers['efficiency_rate']:.1f}%</div>
                    <div class="performer">{best_performers['efficiency_worker']}</div>
                </div>
            """, unsafe_allow_html=True)

        # 작업자별 생산량 그래프
        st.subheader(translate("작업자별 생산량"))
        
        # 그래프 데이터 준비
        fig = go.Figure()
        
        # 목표수량 막대 그래프 (하늘색)
        fig.add_trace(go.Bar(
            name=translate('목표수량'),
            x=worker_stats['작업자'],
            y=worker_stats['목표수량'],
            marker_color='rgba(173, 216, 230, 0.7)'  # 하늘색
        ))
        
        # 생산수량 꺾은선 그래프 (파란색)
        fig.add_trace(go.Scatter(
            name=translate('생산수량'),
            x=worker_stats['작업자'],
            y=worker_stats['생산수량'],
            line=dict(color='royalblue', width=2),
            mode='lines+markers'
        ))
        
        # 불량수량 꺾은선 그래프 (빨간색)
        fig.add_trace(go.Scatter(
            name=translate('불량수량'),
            x=worker_stats['작업자'],
            y=worker_stats['불량수량'],
            line=dict(color='red', width=2),
            mode='lines+markers'
        ))
        
        # 그래프 레이아웃 설정
        fig.update_layout(
            title=translate('작업자별 생산 실적'),
            xaxis_title=translate('작업자'),
            yaxis_title=translate('수량'),
            legend_title=translate('항목'),
            barmode='group',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 작업자별 목표 달성률 및 불량률 그래프
        st.subheader(translate("작업자별 목표달성률 및 불량률"))
        
        # 그래프 데이터 준비
        fig2 = go.Figure()
        
        # 목표달성률 (파란색)
        fig2.add_trace(go.Bar(
            name=translate('목표달성률 (%)'),
            x=worker_stats['작업자'],
            y=worker_stats['생산률'],
            marker_color='rgba(65, 105, 225, 0.7)'  # 로얄블루
        ))
        
        # 불량률 (빨간색)
        fig2.add_trace(go.Bar(
            name=translate('불량률 (%)'),
            x=worker_stats['작업자'],
            y=worker_stats['불량률'],
            marker_color='rgba(255, 99, 71, 0.7)'  # 토마토 색상
        ))
        
        # 그래프 레이아웃 설정
        fig2.update_layout(
            title=translate('작업자별 생산성 지표'),
            xaxis_title=translate('작업자'),
            yaxis_title=translate('비율 (%)'),
            legend_title=translate('지표'),
            barmode='group',
            height=500
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # 상세 데이터 표시
        with st.expander(translate("상세 데이터"), expanded=False):
            st.subheader(translate("원본 데이터"))
            st.dataframe(df)
            
            st.subheader(translate("작업자별 통계"))
            st.dataframe(worker_stats)
        
    except Exception as e:
        st.error(f"{translate('데이터 처리 중 오류가 발생했습니다')}: {str(e)}")
        import traceback
        print(f"[ERROR] 상세 오류: {traceback.format_exc()}")

def calculate_worker_stats(df):
    # 작업자별 통계 계산
    worker_stats = df.groupby('작업자').agg({
        '목표수량': 'sum',
        '생산수량': 'sum',
        '불량수량': 'sum'
    }).reset_index()
    
    # 생산률, A등급률 등 계산
    worker_stats['생산률'] = (worker_stats['생산수량'] / worker_stats['목표수량'] * 100).round(1)
    worker_stats['불량률'] = (worker_stats['불량수량'] / worker_stats['생산수량'] * 100).round(1).fillna(0)
    worker_stats['효율성'] = ((worker_stats['생산수량'] - worker_stats['불량수량']) / worker_stats['목표수량'] * 100).round(1)
    
    return worker_stats

def calculate_daily_averages(worker_stats):
    # 일간 평균 KPI 계산
    daily_averages = {
        'production_rate': worker_stats['생산률'].mean(),
        'defect_rate': worker_stats['불량률'].mean(),
        'efficiency_rate': worker_stats['효율성'].mean()
    }
    
    return daily_averages

def calculate_best_performers(worker_stats):
    # 최고 성과자 및 해당 KPI 값 계산
    best_performers = {}
    
    # 생산 목표 달성률이 가장 높은 작업자
    best_production_idx = worker_stats['생산률'].idxmax()
    best_performers['production_worker'] = worker_stats.loc[best_production_idx, '작업자']
    best_performers['production_rate'] = worker_stats.loc[best_production_idx, '생산률']
    
    # 불량률이 가장 낮은 작업자 (불량품이 0개인 작업자가 여러 명이면 생산량이 더 많은 작업자)
    valid_defect = worker_stats[worker_stats['생산수량'] > 0]  # 생산량이 0인 경우 제외
    if len(valid_defect) > 0:
        # 불량률이 있는 경우
        best_defect_idx = valid_defect['불량률'].idxmin()
        best_performers['defect_worker'] = worker_stats.loc[best_defect_idx, '작업자']
        best_performers['defect_rate'] = worker_stats.loc[best_defect_idx, '불량률']
    else:
        # 불량률 데이터가 없는 경우
        best_performers['defect_worker'] = translate("데이터 없음")
        best_performers['defect_rate'] = 0.0
    
    # 작업 효율성이 가장 높은 작업자
    best_efficiency_idx = worker_stats['효율성'].idxmax()
    best_performers['efficiency_worker'] = worker_stats.loc[best_efficiency_idx, '작업자']
    best_performers['efficiency_rate'] = worker_stats.loc[best_efficiency_idx, '효율성']
    
    return best_performers

def show_daily_report():
    """
    app.py에서 호출하기 위한 함수입니다.
    내부적으로 show() 함수를 호출합니다.
    """
    show()

if __name__ == "__main__":
    show() 