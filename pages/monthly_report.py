import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.supabase_db import SupabaseDB
from datetime import datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta

def show_monthly_report():
    st.title("🗓️ 월간 리포트")
    
    # CSS 스타일 추가
    st.markdown("""
        <style>
        .metric-box {
            background-color: #E8F4F9;
            border-radius: 10px;
            padding: 10px;
            margin: 5px 0;
            line-height: 1.3;   
        }
        .highlight-box {
            background-color: #E8F4F9;
            border-radius: 10px;
            padding: 10px;
            margin: 5px 0;
            line-height: 1.3;    
        }
        .metric-label {
            color: #666;
            font-size: 1.0em;
            font-weight: bold;
            margin-bottom: 5px;
            line-height: 1.3;    
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #2C3E50;
            line-height: 1.3;    
        }
        .metric-icon {
            font-size: 1.2em;
            margin-right: 5px;
        }
        .production-icon { color: #0066CC; }
        .defect-icon { color: #FFA500; }
        .efficiency-icon { color: #00CC66; }
        .performer {
            margin-top: 5px;
            font-size: 2.0em;
            font-weight: bold;
            color: #2C3E50;
            line-height: 1.3;    
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 날짜 선택
    selected_date = st.date_input(
        "조회할 월",
        datetime.now().date()
    )
    
    # 선택된 월의 시작일과 종료일 계산
    start_of_month = selected_date.replace(day=1)
    end_of_month = (start_of_month + relativedelta(months=1, days=-1))
    
    # 데이터 조회
    records = st.session_state.db.get_production_records(
        start_date=start_of_month.strftime('%Y-%m-%d'),
        end_date=end_of_month.strftime('%Y-%m-%d')
    )
    
    if records:
        df = pd.DataFrame(records)
        
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
        
        # KPI 계산 및 표시
        display_monthly_kpi(worker_stats)
        
        # 그래프 표시
        display_monthly_charts(worker_stats)
        
        # 작업자별 월간 실적 테이블 표시
        display_monthly_stats_table(worker_stats)
        
    else:
        st.info(f"{selected_date.strftime('%Y-%m')} 월의 생산 실적이 없습니다.")

def display_monthly_kpi(worker_stats):
    # 월간 평균 KPI 계산
    total_target = worker_stats['목표수량'].sum()
    total_production = worker_stats['생산수량'].sum()
    total_defects = worker_stats['불량수량'].sum()
    
    # KPI 값 계산
    production_rate = round((total_production / total_target) * 100, 1) if total_target > 0 else 0
    defect_rate = round((total_defects / total_production) * 100, 1) if total_production > 0 else 0
    efficiency_rate = round(((total_production - total_defects) / total_target) * 100, 1) if total_target > 0 else 0
    
    # 최고 성과자 찾기
    best_production = worker_stats.loc[worker_stats['생산수량'].idxmax()]
    best_defect = worker_stats.loc[worker_stats['불량수량'].idxmin()]
    best_efficiency = worker_stats.loc[worker_stats['작업효율'].idxmax()]
    
    # 월간 평균 KPI 표시
    st.subheader("월간 평균 KPI")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">
                    <span class="metric-icon production-icon">🎯</span>
                    생산 목표 달성률
                </div>
                <div class="metric-value">{production_rate}%</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">
                    <span class="metric-icon defect-icon">⚠️</span>
                    불량률
                </div>
                <div class="metric-value">{defect_rate}%</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">
                    <span class="metric-icon efficiency-icon">⚡</span>
                    작업효율
                </div>
                <div class="metric-value">{efficiency_rate}%</div>
            </div>
        """, unsafe_allow_html=True)
    
    # 최고 성과자 표시
    st.subheader("최고 성과자")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        best_prod_rate = round((best_production['생산수량'] / best_production['목표수량']) * 100, 1)
        st.markdown(f"""
            <div class="highlight-box">
                <div class="metric-label">
                    <span class="metric-icon production-icon">🎯</span>
                    생산 목표 달성률
                </div>
                <div class="metric-value">{best_prod_rate}%</div>
                <div class="performer">{best_production['작업자']}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        best_defect_rate = round((best_defect['불량수량'] / best_defect['생산수량']) * 100, 1) if best_defect['생산수량'] > 0 else 0
        st.markdown(f"""
            <div class="highlight-box">
                <div class="metric-label">
                    <span class="metric-icon defect-icon">⚠️</span>
                    불량률
                </div>
                <div class="metric-value">{best_defect_rate}%</div>
                <div class="performer">{best_defect['작업자']}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="highlight-box">
                <div class="metric-label">
                    <span class="metric-icon efficiency-icon">⚡</span>
                    작업효율
                </div>
                <div class="metric-value">{best_efficiency['작업효율']}%</div>
                <div class="performer">{best_efficiency['작업자']}</div>
            </div>
        """, unsafe_allow_html=True)

def display_monthly_charts(worker_stats):
    st.subheader("작업자별 생산량")
    
    # 그래프 생성
    fig = go.Figure()
    
    # 목표수량 막대 그래프 (하늘색)
    fig.add_trace(go.Bar(
        name='목표수량',
        x=worker_stats['작업자'],
        y=worker_stats['목표수량'],
        marker_color='rgba(173, 216, 230, 0.7)'
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
    
    st.plotly_chart(fig, use_container_width=True)

def display_monthly_stats_table(worker_stats):
    st.subheader("작업자별 월간 실적")
    
    # 작업효율에 % 추가
    worker_stats['작업효율'] = worker_stats['작업효율'].astype(str) + '%'
    
    # 테이블 표시
    display_columns = ['작업자', '목표수량', '생산수량', '불량수량', '작업효율']
    st.dataframe(
        worker_stats[display_columns],
        use_container_width=True,
        hide_index=True
    ) 