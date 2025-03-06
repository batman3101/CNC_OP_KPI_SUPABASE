import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    st.subheader("작업자별 실적")
    st.dataframe(
        worker_stats[['작업자', '목표수량', '생산수량', '불량수량', '달성률', '불량률', '작업효율']],
        use_container_width=True,
        hide_index=True
    )
    
    # 그래프 표시
    st.subheader("작업자별 생산량")
    fig = px.bar(
        worker_stats,
        x='작업자',
        y=['생산수량', '불량수량'],
        barmode='group',
        labels={'value': '수량', 'variable': '구분'},
        color_discrete_sequence=['#1f77b4', '#ff7f0e']
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # KPI 그래프
    st.subheader("작업자별 KPI")
    
    fig = px.bar(
        worker_stats,
        x='작업자',
        y=['달성률', '작업효율'],
        barmode='group',
        labels={'value': '비율 (%)', 'variable': '지표'},
        color_discrete_sequence=['#2ca02c', '#d62728']
    )
    
    fig.add_hline(y=95, line_dash="dash", line_color="green", annotation_text="목표 달성률 95%")
    fig.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="목표 작업효율 90%")
    
    st.plotly_chart(fig, use_container_width=True)

def show_dashboard():
    st.title("CNC 생산 종합 대시보드")
    
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
        st.subheader("대시보드 필터")
        
        # 기간 선택
        period_options = ["일간", "주간", "월간", "연간"]
        selected_period = st.selectbox("기간 선택", period_options, index=2)  # 기본값: 월간
        
        # 날짜 범위 계산
        today = datetime.now().date()
        if selected_period == "일간":
            start_date = today
            end_date = today
            date_title = today.strftime("%Y년 %m월 %d일")
        elif selected_period == "주간":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
            date_title = f"{start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}"
        elif selected_period == "월간":
            start_date = today.replace(day=1)
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = next_month.replace(day=1) - timedelta(days=1)
            date_title = today.strftime("%Y년 %m월")
        else:  # 연간
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
            date_title = today.strftime("%Y년")
        
        # 라인 선택
        line_options = ["전체", "B-01", "B-02", "B-03", "B-04", "B-05", "B-06"]
        selected_line = st.selectbox("라인 선택", line_options)
        
        # 데이터 새로고침 버튼
        if st.button("데이터 새로고침", use_container_width=True):
            st.rerun()
    
    # 데이터 로드
    records = st.session_state.db.get_production_records(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    if not records:
        st.info(f"{date_title} 기간의 생산 실적이 없습니다.")
        return
    
    # 데이터프레임 변환
    df = pd.DataFrame(records)
    
    # 라인 필터링
    if selected_line != "전체":
        df = df[df['라인번호'] == selected_line]
        if df.empty:
            st.info(f"{date_title} 기간의 {selected_line} 라인 생산 실적이 없습니다.")
            return
    
    # 1. 주요 KPI 요약 섹션
    st.markdown(f"<div class='section-title'>{date_title} 주요 KPI 요약</div>", unsafe_allow_html=True)
    
    # KPI 계산
    total_target = df['목표수량'].sum()
    total_production = df['생산수량'].sum()
    total_defects = df['불량수량'].sum()
    
    # 달성률은 최대 100%로 제한
    production_rate = min(round((total_production / total_target) * 100, 1), 100) if total_target > 0 else 0
    defect_rate = round((total_defects / total_production) * 100, 1) if total_production > 0 else 0
    # 작업효율은 최대 100%로 제한
    efficiency_rate = min(round(((total_production - total_defects) / total_target) * 100, 1), 100) if total_target > 0 else 0
    
    # 전년 대비 증감률 (임의 데이터)
    production_change = 5.2  # 예시 데이터
    defect_change = -2.1     # 예시 데이터
    efficiency_change = 3.7  # 예시 데이터
    
    # KPI 카드 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">계획 생산수량</div>
                <div class="kpi-value">{total_target:,}개</div>
                <div class="kpi-change kpi-change-positive">↑ 전년 대비 3.5%</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">실제 생산수량</div>
                <div class="kpi-value">{total_production:,}개</div>
                <div class="kpi-change {'kpi-change-positive' if production_change >= 0 else 'kpi-change-negative'}">
                    {'↑' if production_change >= 0 else '↓'} 전년 대비 {abs(production_change)}%
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">불량수량</div>
                <div class="kpi-value">{total_defects:,}개</div>
                <div class="kpi-change {'kpi-change-positive' if defect_change <= 0 else 'kpi-change-negative'}">
                    {'↓' if defect_change <= 0 else '↑'} 전년 대비 {abs(defect_change)}%
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">KPI 달성률</div>
                <div class="kpi-value">{efficiency_rate}%</div>
                <div class="kpi-change {'kpi-change-positive' if efficiency_change >= 0 else 'kpi-change-negative'}">
                    {'↑' if efficiency_change >= 0 else '↓'} 전년 대비 {abs(efficiency_change)}%
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # 목표 달성률 게이지 차트
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=production_rate,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "생산목표 달성률"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "royalblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 70], 'color': 'red'},
                {'range': [70, 90], 'color': 'orange'},
                {'range': [90, 100], 'color': 'green'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 95
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 날짜별 집계 (예측 및 목표 섹션에서 사용)
    df['날짜'] = pd.to_datetime(df['날짜'])
    daily_stats = df.groupby('날짜').agg({
        '목표수량': 'sum',
        '생산수량': 'sum',
        '불량수량': 'sum'
    }).reset_index()
    
    # KPI 계산 - 최대 100%로 제한
    daily_stats['달성률'] = (daily_stats['생산수량'] / daily_stats['목표수량'] * 100).round(1)
    daily_stats['달성률'] = daily_stats['달성률'].apply(lambda x: min(x, 100))
    daily_stats['불량률'] = (daily_stats['불량수량'] / daily_stats['생산수량'] * 100).round(1)
    
    # 주간, 월간, 연간 선택 시 불량률 트렌드 그래프 추가
    if selected_period in ["주간", "월간", "연간"]:
        st.markdown("<div class='section-title'>불량률 트렌드</div>", unsafe_allow_html=True)
        
        # 불량률 영역 차트
        fig = px.area(
            daily_stats,
            x='날짜',
            y='불량률',
            labels={'불량률': '불량률 (%)', '날짜': '날짜'},
            title=f'{selected_period} 불량률 추이',
            color_discrete_sequence=['#d62728']
        )
        
        fig.add_hline(y=5, line_dash="dash", line_color="red", annotation_text="목표 불량률 5%")
        
        fig.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 3. 라인별 성능 비교 섹션
    st.markdown("<div class='section-title'>라인별 성능 비교</div>", unsafe_allow_html=True)
    
    # 라인별 집계
    line_stats = df.groupby('라인번호').agg({
        '목표수량': 'sum',
        '생산수량': 'sum',
        '불량수량': 'sum'
    }).reset_index()
    
    # KPI 계산 - 최대 100%로 제한
    line_stats['달성률'] = (line_stats['생산수량'] / line_stats['목표수량'] * 100).round(1)
    line_stats['달성률'] = line_stats['달성률'].apply(lambda x: min(x, 100))
    line_stats['불량률'] = (line_stats['불량수량'] / line_stats['생산수량'] * 100).round(1)
    line_stats['작업효율'] = (((line_stats['생산수량'] - line_stats['불량수량']) / line_stats['목표수량']) * 100).round(1)
    line_stats['작업효율'] = line_stats['작업효율'].apply(lambda x: min(x, 100))
    
    # 라인별 KPI 달성률 수평 바 차트
    fig = px.bar(
        line_stats,
        y='라인번호',
        x='달성률',
        orientation='h',
        labels={'달성률': '생산목표 달성률 (%)', '라인번호': '라인'},
        title='라인별 생산목표 달성률',
        color='달성률',
        color_continuous_scale=px.colors.sequential.Blues,
        range_color=[70, 100]
    )
    
    fig.add_vline(x=95, line_dash="dash", line_color="green", annotation_text="목표 95%")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 라인별 불량률 도넛 차트
    fig = px.pie(
        line_stats,
        names='라인번호',
        values='불량률',
        title='라인별 불량률 비교',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textinfo='label+percent')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 라인별 작업효율 레이더 차트
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=line_stats['작업효율'].tolist(),
        theta=line_stats['라인번호'].tolist(),
        fill='toself',
        name='작업효율'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title='라인별 작업효율 비교',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 4. 알림 및 예외 관리 섹션
    st.markdown("<div class='section-title'>알림 및 예외 관리</div>", unsafe_allow_html=True)
    
    # 문제 있는 라인 식별
    low_performance_lines = line_stats[line_stats['달성률'] < 90]
    high_defect_lines = line_stats[line_stats['불량률'] > 5]
    
    # 알림 표시
    if not low_performance_lines.empty:
        for _, line in low_performance_lines.iterrows():
            st.markdown(f"""
                <div class="alert-card">
                    <strong>⚠️ 주의:</strong> {line['라인번호']} 라인의 생산목표 달성률이 {line['달성률']}%로 목표(90%) 미달입니다.
                </div>
            """, unsafe_allow_html=True)
    
    if not high_defect_lines.empty:
        for _, line in high_defect_lines.iterrows():
            st.markdown(f"""
                <div class="warning-card">
                    <strong>🚨 경고:</strong> {line['라인번호']} 라인의 불량률이 {line['불량률']}%로 임계치(5%)를 초과했습니다.
                </div>
            """, unsafe_allow_html=True)
    
    # 5. 세부 데이터 테이블
    st.markdown("<div class='section-title'>세부 데이터</div>", unsafe_allow_html=True)
    
    # 라인별 성능 테이블
    st.subheader("라인별 성능 지표")
    st.dataframe(
        line_stats[['라인번호', '목표수량', '생산수량', '불량수량', '달성률', '불량률', '작업효율']],
        use_container_width=True,
        hide_index=True,
        column_config={
            '달성률': st.column_config.NumberColumn(
                '생산목표 달성률 (%)',
                format="%.1f%%"
            ),
            '불량률': st.column_config.NumberColumn(
                '불량률 (%)',
                format="%.1f%%"
            ),
            '작업효율': st.column_config.NumberColumn(
                '작업효율 (%)',
                format="%.1f%%"
            )
        }
    )
    
    # 작업자별 성능 테이블
    st.subheader("작업자별 성능 지표")
    
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
    
    st.dataframe(
        worker_stats[['작업자', '목표수량', '생산수량', '불량수량', '달성률', '불량률', '작업효율']],
        use_container_width=True,
        hide_index=True,
        column_config={
            '달성률': st.column_config.NumberColumn(
                '생산목표 달성률 (%)',
                format="%.1f%%"
            ),
            '불량률': st.column_config.NumberColumn(
                '불량률 (%)',
                format="%.1f%%"
            ),
            '작업효율': st.column_config.NumberColumn(
                '작업효율 (%)',
                format="%.1f%%"
            )
        }
    )
    
    # 6. 예측 및 목표 섹션
    if selected_period in ["월간", "연간"]:
        st.markdown("<div class='section-title'>예측 및 목표</div>", unsafe_allow_html=True)
        
        # 현재 진행률 계산 (월 또는 연 기준)
        if selected_period == "월간":
            days_in_month = (end_date - start_date).days + 1
            days_passed = (min(today, end_date) - start_date).days + 1
            progress_pct = days_passed / days_in_month
        else:  # 연간
            days_in_year = 365
            days_passed = (today - start_date).days + 1
            progress_pct = days_passed / days_in_year
        
        # 예상 연말/월말 달성률
        projected_production = total_production / progress_pct if progress_pct > 0 else 0
        # 예상 달성률은 최대 100%로 제한
        projected_rate = min(round((projected_production / total_target) * 100, 1), 100) if total_target > 0 else 0
        
        # 목표 달성을 위한 필요 생산량
        target_goal = 95  # 목표 달성률 95%
        required_production = (target_goal / 100) * total_target
        remaining_production = max(0, required_production - total_production)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">예상 {selected_period} 말 달성률</div>
                    <div class="kpi-value">{projected_rate}%</div>
                    <div class="kpi-change {'kpi-change-positive' if projected_rate >= 95 else 'kpi-change-negative'}">
                        {'✓ 목표 달성 예상' if projected_rate >= 95 else '✗ 목표 미달 예상'}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">목표 달성을 위한 추가 생산 필요량</div>
                    <div class="kpi-value">{int(remaining_production):,}개</div>
                    <div class="kpi-change">
                        목표 달성률 95%
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        # 예측 차트
        fig = go.Figure()
        
        # 현재까지의 실제 데이터
        fig.add_trace(go.Scatter(
            x=daily_stats['날짜'],
            y=daily_stats['달성률'],
            mode='lines+markers',
            name='실제 달성률',
            line=dict(color='blue')
        ))
        
        # 예측 데이터 (단순 선형 예측)
        if len(daily_stats) > 1:
            last_date = daily_stats['날짜'].max()
            future_dates = pd.date_range(start=last_date + timedelta(days=1), end=end_date)
            
            # 간단한 선형 예측 (실제로는 더 복잡한 예측 모델 사용 가능)
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=[projected_rate] * len(future_dates),
                mode='lines',
                name='예상 달성률',
                line=dict(color='blue', dash='dash')
            ))
        
        fig.add_hline(y=95, line_dash="dash", line_color="green", annotation_text="목표 달성률 95%")
        
        fig.update_layout(
            title=f"{selected_period} 생산목표 달성률 예측",
            xaxis_title="날짜",
            yaxis_title="달성률 (%)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True) 