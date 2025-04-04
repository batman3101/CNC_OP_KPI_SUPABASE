import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.supabase_db import SupabaseDB
from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from utils.translations import translate

def show_monthly_report():
    st.title(translate("📊 월간 리포트"))
    
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
        .highlight-box {
            background-color: #E8F4F9;
            border-radius: 10px;
            padding: 10px;
            margin: 5px 0;
            line-height: 1.3;    
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
    
    # 현재 월
    today = datetime.now()
    current_year = today.year
    current_month = today.month
    
    # 월 선택 옵션 생성
    month_options = []
    for i in range(12):
        # 현재 월부터 거꾸로 이전 12개월
        year = current_year
        month = current_month - i
        
        # 월이 0 이하면 이전 년도로 조정
        if month <= 0:
            month += 12
            year -= 1
        
        # 날짜 객체 생성
        d = date(year, month, 1)
        # 월 이름 형식 (예: "2023년 4월")
        month_label = translate(d.strftime("%Y년 %m월"))
        month_options.append((month_label, year, month))
    
    # 월 선택 드롭다운
    selected_month = st.selectbox(
        translate("월 선택"),
        options=[option[0] for option in month_options],
        index=0
    )
    
    # 선택된 월의 년도와 월 가져오기
    selected_idx = [option[0] for option in month_options].index(selected_month)
    year = month_options[selected_idx][1]
    month = month_options[selected_idx][2]
    
    # 해당 월의 첫날과 마지막 날 계산
    first_day = date(year, month, 1)
    # 해당 월의 마지막 날짜 계산
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    
    # 데이터 조회
    records = st.session_state.db.get_production_records(
        start_date=first_day.strftime('%Y-%m-%d'),
        end_date=last_day.strftime('%Y-%m-%d')
    )
    
    if not records:
        st.info(translate(f"{translate(first_day.strftime('%Y년 %m월'))} 기간의 생산 데이터가 없습니다."))
        return
        
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
    st.subheader(translate("월간 평균 KPI"))
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">
                    <span class="metric-icon production-icon">🎯</span>
                    {translate('생산 목표 달성률')}
                </div>
                <div class="metric-value">{production_rate}%</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">
                    <span class="metric-icon defect-icon">⚠️</span>
                    {translate('불량률')}
                </div>
                <div class="metric-value">{defect_rate}%</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">
                    <span class="metric-icon efficiency-icon">⚡</span>
                    {translate('작업효율')}
                </div>
                <div class="metric-value">{efficiency_rate}%</div>
            </div>
        """, unsafe_allow_html=True)
    
    # 최고 성과자 표시
    st.subheader(translate("최고 성과자"))
    col1, col2, col3 = st.columns(3)
    
    with col1:
        best_prod_rate = round((best_production['생산수량'] / best_production['목표수량']) * 100, 1)
        st.markdown(f"""
            <div class="highlight-box">
                <div class="metric-label">
                    <span class="metric-icon production-icon">🎯</span>
                    {translate('생산 목표 달성률')}
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
                    {translate('불량률')}
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
                    {translate('작업효율')}
                </div>
                <div class="metric-value">{best_efficiency['작업효율']}%</div>
                <div class="performer">{best_efficiency['작업자']}</div>
            </div>
        """, unsafe_allow_html=True)

def display_monthly_charts(worker_stats):
    st.subheader(translate("작업자별 생산량"))
    
    # 그래프 생성
    fig = go.Figure()
    
    # 목표수량 막대 그래프 (하늘색)
    fig.add_trace(go.Bar(
        name=translate('목표수량'),
        x=worker_stats['작업자'],
        y=worker_stats['목표수량'],
        marker_color='rgba(173, 216, 230, 0.7)'
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
            title=translate('수량'),
            gridcolor='lightgray',
            gridwidth=0.5,
            zeroline=False
        ),
        plot_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_monthly_stats_table(worker_stats):
    st.subheader(translate("작업자별 월간 실적"))
    
    # 진행 중인 작업 현황
    worker_stats['생산목표달성률'] = round((worker_stats['생산수량'] / worker_stats['목표수량']) * 100, 1)
    worker_stats['불량률'] = round((worker_stats['불량수량'] / worker_stats['생산수량']) * 100, 1)
    
    # 소수점 첫째 자리까지 포맷팅하고 % 기호 추가
    worker_stats['생산목표달성률'] = worker_stats['생산목표달성률'].apply(lambda x: f'{x}%')
    worker_stats['불량률'] = worker_stats['불량률'].apply(lambda x: f'{x}%')
    worker_stats['작업효율'] = worker_stats['작업효율'].apply(lambda x: f'{x}%')
    
    # 테이블 컬럼 번역을 위한 복사본 생성
    display_stats = worker_stats.copy()
    display_stats.columns = [translate(col) for col in display_stats.columns]
    
    # 데이터프레임 출력
    st.dataframe(
        display_stats,
        use_container_width=True,
        hide_index=True
    ) 