import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.translations import translate

# 전역 설정 변수
TARGET_DEFECT_RATE = 0.2  # 목표 불량률 (%)
TARGET_ACHIEVEMENT_RATE = 90  # 목표 달성률 (%)

def calculate_production_rate(records):
    """생산목표 달성률 계산"""
    total_target = sum(r.get('목표수량', 0) for r in records)
    total_production = sum(r.get('생산수량', 0) for r in records)
    
    if total_target == 0:
        return 0
    
    # 달성률은 최대 100%로 제한
    return min((total_production / total_target) * 100, 100)

def calculate_defect_rate(records):
    """불량률 계산"""
    total_production = sum(r.get('생산수량', 0) for r in records)
    total_defects = sum(r.get('불량수량', 0) for r in records)
    
    if total_production == 0:
        return 0
    
    return (total_defects / total_production) * 100

def calculate_achievement_rate(records):
    """작업효율 계산"""
    total_target = sum(r.get('목표수량', 0) for r in records)
    total_production = sum(r.get('생산수량', 0) for r in records)
    total_defects = sum(r.get('불량수량', 0) for r in records)
    
    if total_target == 0:
        return 0
    
    # 작업효율은 최대 100%로 제한
    return min(((total_production - total_defects) / total_target) * 100, 100)

def show_worker_performance(records):
    """작업자별 실적 표시"""
    if not records:
        return
    
    # 데이터프레임 변환
    df = pd.DataFrame(records)
    
    # 작업자별 집계
    worker_stats = df.groupby('작업자').agg({
        '목표수량': 'sum',
        '생산수량': 'sum',
        '불량수량': 'sum'
    }).reset_index()
    
    # KPI 계산 - 최대 100%로 제한
    worker_stats['달성률'] = (worker_stats['생산수량'] / worker_stats['목표수량'] * 100).round(1)
    worker_stats['달성률'] = worker_stats['달성률'].apply(lambda x: min(x, 100))
    worker_stats['불량률'] = (worker_stats['불량수량'] / worker_stats['생산수량'] * 100).round(1)
    worker_stats['작업효율'] = (((worker_stats['생산수량'] - worker_stats['불량수량']) / worker_stats['목표수량']) * 100).round(1)
    worker_stats['작업효율'] = worker_stats['작업효율'].apply(lambda x: min(x, 100))
    
    # 테이블 표시
    st.subheader(translate("작업자별 실적"))
    
    # 테이블 컬럼 번역을 위한 복사본 생성
    display_stats = worker_stats.copy()
    display_stats.columns = [translate(col) for col in display_stats.columns]
    
    st.dataframe(
        display_stats,
        use_container_width=True,
        hide_index=True
    )
    
    # 그래프 표시
    st.subheader(translate("작업자별 생산량"))
    fig = px.bar(
        worker_stats,
        x='작업자',
        y=['생산수량', '불량수량'],
        barmode='group',
        labels={'value': translate('수량'), 'variable': translate('구분')},
        color_discrete_sequence=['#1f77b4', '#ff7f0e']
    )
    
    # Plotly 그래프의 범례 항목 번역
    new_names = {col: translate(col) for col in ['생산수량', '불량수량']}
    fig.for_each_trace(lambda t: t.update(name = new_names[t.name]))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # KPI 그래프
    st.subheader(translate("작업자별 KPI"))
    
    fig = px.bar(
        worker_stats,
        x='작업자',
        y=['달성률', '작업효율'],
        barmode='group',
        labels={'value': translate('비율 (%)'), 'variable': translate('지표')},
        color_discrete_sequence=['#2ca02c', '#d62728']
    )
    
    # Plotly 그래프의 범례 항목 번역
    new_names = {col: translate(col) for col in ['달성률', '작업효율']}
    fig.for_each_trace(lambda t: t.update(name = new_names[t.name]))
    
    fig.add_hline(y=95, line_dash="dash", line_color="green", annotation_text=translate("목표 달성률 95%"))
    fig.add_hline(y=90, line_dash="dash", line_color="red", annotation_text=translate("목표 작업효율 90%"))
    
    st.plotly_chart(fig, use_container_width=True)

def show_dashboard():
    st.title(translate("📈 ALMUS TECH CNC 생산 종합 대시보드"))
    
    # CSS 스타일 추가
    st.markdown("""
        <style>
        .kpi-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 10px;
        }
        .kpi-title {
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 5px;
        }
        .kpi-value {
            font-size: 24px;
            font-weight: bold;
            color: #343a40;
        }
        .kpi-change {
            font-size: 12px;
            margin-top: 5px;
        }
        .kpi-change-positive {
            color: #28a745;
        }
        .kpi-change-negative {
            color: #dc3545;
        }
        .section-title {
            font-size: 18px;
            font-weight: bold;
            margin: 20px 0 10px 0;
            padding-bottom: 5px;
            border-bottom: 1px solid #dee2e6;
        }
        .alert-card {
            background-color: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 10px 15px;
            margin-bottom: 10px;
            border-radius: 5px;
        }
        .warning-card {
            background-color: #f8d7da;
            border-left: 5px solid #dc3545;
            padding: 10px 15px;
            margin-bottom: 10px;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 필터링 옵션 (사이드바)
    with st.sidebar:
        st.subheader(translate("대시보드 필터"))
        
        # 기간 선택
        period_options = [translate("일간"), translate("주간"), translate("월간"), translate("연간")]
        selected_period = st.selectbox(translate("기간 선택"), period_options, index=2)  # 기본값: 월간
        
        # 날짜 범위 계산
        today = datetime.now().date()
        
        if selected_period == translate("일간"):
            # 일간 선택 시 날짜 선택 가능
            selected_date = st.date_input(translate("조회할 날짜"), today)
            start_date = selected_date
            end_date = selected_date
            date_title = translate(selected_date.strftime("%Y년 %m월 %d일"))
        elif selected_period == translate("주간"):
            # 주간 선택 시 시작 날짜 선택 가능
            # 선택한 날짜가 속한 주의 월요일 계산
            default_monday = today - timedelta(days=today.weekday())
            selected_start_date = st.date_input(translate("조회할 주의 시작일(월요일)"), default_monday)
            # 선택한 날짜의 요일을 확인하고 해당 주의 월요일로 조정
            adjusted_start = selected_start_date - timedelta(days=selected_start_date.weekday())
            start_date = adjusted_start
            end_date = start_date + timedelta(days=6)
            date_title = translate(f"{start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}")
        elif selected_period == translate("월간"):
            # 월간 선택 시 년월 선택
            selected_month = st.date_input(translate("조회할 월"), today.replace(day=1))
            start_date = selected_month.replace(day=1)
            # 다음 달의 1일 - 1일 = 해당 월의 마지막 날
            if selected_month.month == 12:
                next_month = selected_month.replace(year=selected_month.year+1, month=1, day=1)
            else:
                next_month = selected_month.replace(month=selected_month.month+1, day=1)
            end_date = next_month - timedelta(days=1)
            date_title = translate(selected_month.strftime("%Y년 %m월"))
        else:  # 연간
            # 연간 선택 시 년도 선택
            year_options = list(range(datetime.now().year, datetime.now().year - 5, -1))
            selected_year = st.selectbox(translate("조회할 연도"), year_options)
            start_date = datetime(selected_year, 1, 1).date()
            end_date = datetime(selected_year, 12, 31).date()
            date_title = translate(f"{selected_year}년")
        
        # 라인 선택
        line_options = [translate("전체"), "B-01", "B-02", "B-03", "B-04", "B-05", "B-06"]
        selected_line = st.selectbox(translate("라인 선택"), line_options)
        
        # 데이터 새로고침 버튼
        if st.button(translate("데이터 새로고침"), use_container_width=True):
            st.rerun()
    
    # 데이터 로드
    records = st.session_state.db.get_production_records(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    if not records:
        st.info(translate(f"{date_title} 기간의 생산 실적이 없습니다."))
        return
    
    # 데이터프레임 변환
    df = pd.DataFrame(records)
    
    # 라인 필터링
    if selected_line != translate("전체"):
        df = df[df['라인번호'] == selected_line]
        if df.empty:
            st.info(translate(f"{date_title} 기간의 {selected_line} 라인 생산 실적이 없습니다."))
            return
    
    # 1. 주요 KPI 요약 섹션
    st.markdown(f"<div class='section-title'>{date_title} {translate('주요 KPI 요약')}</div>", unsafe_allow_html=True)
    
    # KPI 계산
    total_target = df['목표수량'].sum()
    total_production = df['생산수량'].sum()
    total_defects = df['불량수량'].sum()
    
    # 달성률은 최대 100%로 제한
    production_rate = min(round((total_production / total_target) * 100, 1), 100) if total_target > 0 else 0
    defect_rate = round((total_defects / total_production) * 100, 1) if total_production > 0 else 0
    # 작업효율은 최대 100%로 제한
    efficiency_rate = min(round(((total_production - total_defects) / total_target) * 100, 1), 100) if total_target > 0 else 0
    
    # KPI 카드 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">{translate('계획수량')}</div>
                <div class="kpi-value">{total_target:,}{translate('개')}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">{translate('생산수량')}</div>
                <div class="kpi-value">{total_production:,}{translate('개')}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">{translate('불량수량')}</div>
                <div class="kpi-value">{total_defects:,}{translate('개')}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">{translate('목표달성률')}</div>
                <div class="kpi-value">{production_rate}%</div>
            </div>
        """, unsafe_allow_html=True)
        
    # 2. 성과 게이지 차트
    st.markdown(f"<div class='section-title'>{translate('생산목표 달성률')}</div>", unsafe_allow_html=True)
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = production_rate,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': translate("생산목표 달성률")},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "royalblue"},
            'steps': [
                {'range': [0, 70], 'color': "lightgray"},
                {'range': [70, 90], 'color': "lightblue"},
                {'range': [90, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': TARGET_ACHIEVEMENT_RATE
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    # 라인별/작업자별 실적
    if selected_line == translate("전체"):
        # 라인별 실적 데이터
        line_stats = df.groupby('라인번호').agg({
            '목표수량': 'sum',
            '생산수량': 'sum',
            '불량수량': 'sum'
        }).reset_index()
        
        # KPI 계산
        line_stats['달성률'] = (line_stats['생산수량'] / line_stats['목표수량'] * 100).round(1)
        line_stats['달성률'] = line_stats['달성률'].apply(lambda x: min(x, 100))
        line_stats['불량률'] = (line_stats['불량수량'] / line_stats['생산수량'] * 100).round(1)
        line_stats['작업효율'] = (((line_stats['생산수량'] - line_stats['불량수량']) / line_stats['목표수량']) * 100).round(1)
        line_stats['작업효율'] = line_stats['작업효율'].apply(lambda x: min(x, 100))
        
        # 라인별 실적 표시
        st.markdown(f"<div class='section-title'>{translate('라인별 실적')}</div>", unsafe_allow_html=True)
        
        # 테이블 컬럼 번역을 위한 복사본 생성
        display_line_stats = line_stats.copy()
        display_line_stats.columns = [translate(col) for col in display_line_stats.columns]
        
        st.dataframe(
            display_line_stats,
            use_container_width=True,
            hide_index=True
        )
        
        # 라인별 생산량 그래프
        st.subheader(translate("라인별 생산량"))
        fig = px.bar(
            line_stats,
            x='라인번호',
            y=['생산수량', '불량수량'],
            barmode='group',
            labels={'value': translate('수량'), 'variable': translate('구분')},
            color_discrete_sequence=['#1f77b4', '#ff7f0e']
        )
        
        # Plotly 그래프의 범례 항목 번역
        new_names = {col: translate(col) for col in ['생산수량', '불량수량']}
        fig.for_each_trace(lambda t: t.update(name = new_names[t.name]))
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 라인별 KPI 그래프
        st.subheader(translate("라인별 KPI"))
        fig = px.bar(
            line_stats,
            x='라인번호',
            y=['달성률', '작업효율'],
            barmode='group',
            labels={'value': translate('비율 (%)'), 'variable': translate('지표')},
            color_discrete_sequence=['#2ca02c', '#d62728']
        )
        
        # Plotly 그래프의 범례 항목 번역
        new_names = {col: translate(col) for col in ['달성률', '작업효율']}
        fig.for_each_trace(lambda t: t.update(name = new_names[t.name]))
        
        fig.add_hline(y=95, line_dash="dash", line_color="green", annotation_text=translate("목표 달성률 95%"))
        fig.add_hline(y=90, line_dash="dash", line_color="red", annotation_text=translate("목표 작업효율 90%"))
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 특정 라인이 선택된 경우 작업자별 실적 표시
    else:
        show_worker_performance(df.to_dict('records'))
    
    # 불량률 경고 확인
    if defect_rate > TARGET_DEFECT_RATE:
        st.markdown(f"""
            <div class="warning-card">
                <h4>{translate('⚠️ 불량률 경고')}</h4>
                <p>{translate('현재 불량률')} {defect_rate}%{translate('는 목표 불량률')} {TARGET_DEFECT_RATE}%{translate('를 초과했습니다. 품질 관리가 필요합니다.')}</p>
            </div>
        """, unsafe_allow_html=True)
    
    # 달성률 경고 확인
    if production_rate < TARGET_ACHIEVEMENT_RATE:
        st.markdown(f"""
            <div class="alert-card">
                <h4>{translate('⚠️ 생산목표 미달')}</h4>
                <p>{translate('현재 달성률')} {production_rate}%{translate('는 목표 달성률')} {TARGET_ACHIEVEMENT_RATE}%{translate('에 미치지 못했습니다. 생산성 향상이 필요합니다.')}</p>
            </div>
        """, unsafe_allow_html=True) 