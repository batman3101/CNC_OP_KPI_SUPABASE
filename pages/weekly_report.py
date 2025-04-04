import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import plotly.graph_objects as go
from utils.supabase_db import SupabaseDB
from utils.translations import translate

def show_weekly_report():
    st.title(translate("📆 주간 리포트"))
    
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
        .percentage-value {  /* 새로운 클래스 추가 */
            font-size: 2.0em;
            font-weight: bold;
            color: #000;
        }
        </style>
    """, unsafe_allow_html=True)

    # 날짜 선택 레이블 변경
    selected_date = st.date_input(
        translate("조회할 주간 시작일"),
        datetime.now().date()
    )
    
    # 주간 날짜 계산
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    st.write(f"{translate('조회 기간')}: {start_of_week.strftime('%Y-%m-%d')} ~ {end_of_week.strftime('%Y-%m-%d')}")
    
    # 데이터 조회
    try:
        # 세션 상태에 db가 없으면 새로 생성
        if 'db' not in st.session_state:
            st.session_state.db = SupabaseDB()
            st.write(translate("새로운 SupabaseDB 인스턴스를 생성했습니다."))
        
        st.write(translate("데이터베이스에서 생산 실적을 조회합니다..."))
        records = st.session_state.db.get_production_records(
            start_date=start_of_week.strftime('%Y-%m-%d'),
            end_date=end_of_week.strftime('%Y-%m-%d')
        )
        
        st.write(f"{translate('조회된 레코드 수')}: {len(records)}")
        
        # 디버깅용: 조회된 레코드 출력
        if len(records) == 0:
            st.warning(translate("해당 기간에 조회된 데이터가 없습니다."))
            
            # 다른 기간 데이터 확인 (2월 데이터)
            st.write(translate("2월 데이터 확인 중..."))
            feb_start = datetime(2024, 2, 1).date()
            feb_end = datetime(2024, 2, 29).date()
            feb_records = st.session_state.db.get_production_records(
                start_date=feb_start.strftime('%Y-%m-%d'),
                end_date=feb_end.strftime('%Y-%m-%d')
            )
            st.write(f"{translate('2월 데이터 레코드 수')}: {len(feb_records)}")
            
            if len(feb_records) > 0:
                st.write(translate("2월 첫 번째 레코드 샘플:"))
                st.write(feb_records[0])
            else:
                st.error(translate("2월 데이터도 조회되지 않습니다. 데이터베이스 연결 또는 테이블 구조를 확인하세요."))
                
                # 테이블 구조 확인
                st.write(translate("Production 테이블 구조 확인 중..."))
                try:
                    # 모든 데이터 조회 시도
                    all_records = st.session_state.db.client.table('Production').select('*').execute()
                    st.write(f"{translate('Production 테이블 전체 레코드 수')}: {len(all_records.data)}")
                    if len(all_records.data) > 0:
                        st.write(translate("첫 번째 레코드 샘플:"))
                        st.write(all_records.data[0])
                except Exception as e:
                    st.error(f"{translate('테이블 구조 확인 중 오류 발생')}: {e}")
    except Exception as e:
        st.error(f"{translate('데이터 조회 중 오류 발생')}: {e}")
        import traceback
        st.code(traceback.format_exc())

    if records:
        df = pd.DataFrame(records)
        worker_stats = calculate_worker_stats(df)  # 작업자별 통계 계산

        # KPI 및 최고 성과자 계산
        best_performers = calculate_best_performers(worker_stats)
        weekly_averages = calculate_weekly_averages(worker_stats)

        # 주간 평균 KPI 표시
        st.subheader(translate("주간 평균 KPI"))
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">🎯 {translate('생산 목표 달성률')}</div>
                    <div style="font-size: 24px; font-weight: bold;">{weekly_averages['production_rate']:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">⚠️ {translate('불량률')}</div>
                    <div style="font-size: 24px; font-weight: bold;">{weekly_averages['defect_rate']:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
                <div class="highlight-box">
                    <div class="metric-label">⚡ {translate('작업효율')}</div>
                    <div style="font-size: 24px; font-weight: bold;">{weekly_averages['efficiency_rate']:.1f}%</div>
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
        
        # 그래프 표시
        st.plotly_chart(fig, use_container_width=True)
        
        # 작업자별 주간 실적 테이블
        st.subheader(translate("작업자별 주간 실적"))
        
        # 작업효율에 % 추가
        worker_stats['작업효율'] = worker_stats['작업효율'].astype(str) + '%'
        
        # 테이블 표시
        display_columns = ['작업자', '목표수량', '생산수량', '불량수량', '작업효율']
        st.dataframe(
            worker_stats[display_columns],
            use_container_width=True,
            hide_index=True
        )
        
    else:
        st.info(f"{start_of_week.strftime('%Y-%m-%d')} ~ {end_of_week.strftime('%Y-%m-%d')} {translate('기간의 생산 실적이 없습니다.')}")

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

def calculate_weekly_averages(worker_stats):
    # 주간 평균 KPI 계산
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
    best_performers = {}
    
    # 생산률이 가장 높은 작업자
    best_production_idx = worker_stats['생산수량'].idxmax()
    best_performers['production_worker'] = worker_stats.loc[best_production_idx, '작업자']
    
    # 작업자의 생산률 계산
    best_production_rate = round(
        (worker_stats.loc[best_production_idx, '생산수량'] / worker_stats.loc[best_production_idx, '목표수량']) * 100,
        1
    )
    best_performers['production_rate'] = best_production_rate
    
    # 불량률이 가장 낮은 작업자
    # 생산량이 0이 아닌 작업자 중에서 불량률이 가장 낮은 작업자 선택
    valid_workers = worker_stats[worker_stats['생산수량'] > 0].copy()
    if len(valid_workers) > 0:
        valid_workers['불량률'] = (valid_workers['불량수량'] / valid_workers['생산수량']) * 100
        best_defect_idx = valid_workers['불량률'].idxmin()
        best_performers['defect_worker'] = valid_workers.loc[best_defect_idx, '작업자']
        best_performers['defect_rate'] = round(valid_workers.loc[best_defect_idx, '불량률'], 1)
    else:
        best_performers['defect_worker'] = translate("데이터 없음")
        best_performers['defect_rate'] = 0.0
    
    # 작업효율이 가장 높은 작업자
    best_efficiency_idx = worker_stats['작업효율'].idxmax()
    best_performers['efficiency_worker'] = worker_stats.loc[best_efficiency_idx, '작업자']
    best_performers['efficiency_rate'] = worker_stats.loc[best_efficiency_idx, '작업효율']
    
    return best_performers 