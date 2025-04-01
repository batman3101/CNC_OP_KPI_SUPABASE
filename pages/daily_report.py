import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder

def calculate_change_rate(current, previous):
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def show_daily_report():
    st.title("📅 일간 리포트")
    
    # 세션 상태 초기화
    if 'db' not in st.session_state:
        st.error("데이터베이스 연결이 초기화되지 않았습니다.")
        return  # 초기화되지 않으면 함수 종료
    
    # 날짜 선택
    selected_date = st.date_input(
        "조회할 날짜",
        datetime.now().date()
    )
    
    # 전일 날짜 계산
    previous_date = selected_date - timedelta(days=1)
    
    # 데이터 조회
    current_records = st.session_state.db.get_production_records(
        start_date=selected_date.strftime('%Y-%m-%d'),
        end_date=selected_date.strftime('%Y-%m-%d')
    )
    
    previous_records = st.session_state.db.get_production_records(
        start_date=previous_date.strftime('%Y-%m-%d'),
        end_date=previous_date.strftime('%Y-%m-%d')
    )
    
    if current_records:
        # DataFrame 생성
        df = pd.DataFrame(current_records)
        df_prev = pd.DataFrame(previous_records) if previous_records else pd.DataFrame()
        
        # 총 데이터 수 표시
        st.info(f"해당 날짜({selected_date.strftime('%Y-%m-%d')})의 총 데이터: {len(df)}개")
        
        # 작업 효율 계산: ((생산수량-불량수량)/목표수량) × 100
        df['작업효율'] = round(((df['생산수량'] - df['불량수량']) / df['목표수량']) * 100, 1)
        # 작업효율에 % 기호 추가
        df['작업효율'] = df['작업효율'].astype(str) + '%'
        
        # 데이터 표시
        st.subheader("생산 실적 데이터")
        if not df.empty:
            # 표시할 컬럼 순서 정의
            display_columns = [
                '날짜', '작업자', '라인번호', '모델차수', 
                '목표수량', '생산수량', '불량수량', '작업효율'
            ]
            
            # 데이터프레임 표시
            # AgGrid 설정
            gb = GridOptionsBuilder.from_dataframe(df[display_columns])
            gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=50)
            gb.configure_side_bar()
            gb.configure_default_column(
                groupable=True, 
                value=True, 
                enableRowGroup=True, 
                aggFunc='sum',
                editable=False,
                sorteable=True,
                resizable=True,
                filterable=True
            )
            grid_options = gb.build()
            
            AgGrid(
                df[display_columns],
                gridOptions=grid_options,
                height=500,
                width='100%',
                data_return_mode='AS_INPUT',
                update_mode='MODEL_CHANGED',
                fit_columns_on_grid_load=False,
                allow_unsafe_jscode=True
            )
            
            st.write(f"총 {len(df)}개 데이터 표시 중")
        
        # 통계 계산 시에도 특이사항 제외
        if not df.empty:
            total_target = df['목표수량'].sum()
            total_production = df['생산수량'].sum()
            total_defect = df['불량수량'].sum()
            
            # KPI 지표 계산
            current_achievement = (total_production / total_target * 100)
            current_defect = (total_defect / total_production * 100)
            current_efficiency = ((total_production - total_defect) / total_target * 100)
            
            # 전일 KPI 계산
            prev_achievement = (df_prev['생산수량'].sum() / df_prev['목표수량'].sum() * 100) if not df_prev.empty else 0
            prev_defect = (df_prev['불량수량'].sum() / df_prev['생산수량'].sum() * 100) if not df_prev.empty else 0
            prev_efficiency = ((df_prev['생산수량'].sum() - df_prev['불량수량'].sum()) / df_prev['목표수량'].sum() * 100) if not df_prev.empty else 0
            
            # 변화율 계산
            achievement_change = calculate_change_rate(current_achievement, prev_achievement)
            defect_change = calculate_change_rate(current_defect, prev_defect)
            efficiency_change = calculate_change_rate(current_efficiency, prev_efficiency)
            
            # 최고 성과자 찾기
            best_achievement = df.loc[df['생산수량'] / df['목표수량'] == (df['생산수량'] / df['목표수량']).max(), '작업자'].iloc[0]
            best_defect = df.loc[df['불량수량'] / df['생산수량'] == (df['불량수량'] / df['생산수량']).min(), '작업자'].iloc[0]
            best_efficiency = df.loc[(df['생산수량'] - df['불량수량']) / df['목표수량'] == ((df['생산수량'] - df['불량수량']) / df['목표수량']).max(), '작업자'].iloc[0]
            
            # KPI 표시
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "🎯 생산목표 달성률",
                    f"{current_achievement:.1f}%",
                    f"{achievement_change:+.1f}% {'↑' if achievement_change > 0 else '↓'}",
                    delta_color="normal" if achievement_change > 0 else "inverse"
                )
                st.markdown(f"<p style='font-size: 24px; font-weight: bold;'>최고 성과자: {best_achievement}</p>", unsafe_allow_html=True)
            
            with col2:
                st.metric(
                    "⚠️ 불량률",
                    f"{current_defect:.1f}%",
                    f"{defect_change:+.1f}% {'↑' if defect_change > 0 else '↓'}",
                    delta_color="inverse" if defect_change > 0 else "normal"
                )
                st.markdown(f"<p style='font-size: 24px; font-weight: bold;'>최고 성과자: {best_defect}</p>", unsafe_allow_html=True)
            
            with col3:
                st.metric(
                    "⚡ 작업효율",
                    f"{current_efficiency:.1f}%",
                    f"{efficiency_change:+.1f}% {'↑' if efficiency_change > 0 else '↓'}",
                    delta_color="normal" if efficiency_change > 0 else "inverse"
                )
                st.markdown(f"<p style='font-size: 24px; font-weight: bold;'>최고 성과자: {best_efficiency}</p>", unsafe_allow_html=True)
        
        # 작업자별 생산량 그래프
        st.subheader("작업자별 생산량")
        
        # 그래프 표시 시에도 특이사항 제외
        # 작업자별로 데이터 그룹화하여 집계
        worker_data = df.groupby('작업자').agg({
            '목표수량': 'sum',
            '생산수량': 'sum',
            '불량수량': 'sum'
        }).reset_index()
        
        workers = worker_data['작업자'].tolist()
        
        # Plotly 그래프 생성
        fig = go.Figure()
        
        # 목표수량 막대 (하늘색) - 맨 뒤에 배치
        fig.add_trace(go.Bar(
            name='목표수량',
            x=workers,
            y=worker_data['목표수량'],
            marker_color='lightblue',
            width=0.5,
            opacity=0.7  # 약간 투명하게 설정
        ))
        
        # 생산수량 꺾은선 (파란색) - 두 번째로 배치
        fig.add_trace(go.Scatter(
            name='생산수량',
            x=workers,
            y=worker_data['생산수량'],
            mode='lines+markers',
            line=dict(
                color='blue',
                width=3,
                shape='linear'
            ),
            marker=dict(
                size=8,
                color='blue',
                symbol='circle'
            )
        ))
        
        # 불량수량 꺾은선 (빨간색) - 맨 앞에 배치
        fig.add_trace(go.Scatter(
            name='불량수량',
            x=workers,
            y=worker_data['불량수량'],
            mode='lines+markers',
            line=dict(
                color='red',
                width=3,
                shape='linear'
            ),
            marker=dict(
                size=8,
                color='red',
                symbol='circle'
            )
        ))
        
        # 그래프 레이아웃 설정
        fig.update_layout(
            yaxis_title="수량",
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            yaxis=dict(
                rangemode='tozero',
                gridcolor='lightgray',
                gridwidth=0.5,
                zeroline=True,
                zerolinecolor='lightgray',
                zerolinewidth=1
            ),
            xaxis=dict(
                tickangle=-45,
                categoryorder='array',
                categoryarray=workers  # 정렬된 작업자 리스트 사용
            ),
            margin=dict(t=50, b=100),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # 그래프 표시
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"{selected_date} 날짜의 생산 실적이 없습니다.") 