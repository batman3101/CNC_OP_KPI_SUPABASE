import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import sys
import os
import numpy as np

# 프로젝트 루트 디렉토리를 path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.local_storage import LocalStorage
import utils.common as common

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
    
    # 직접 Supabase에서 데이터 조회
    print(f"[DEBUG] 선택한 날짜: {selected_date.strftime('%Y-%m-%d')}")
    
    # 세션 상태에 데이터가 있는지 확인
    if 'production_data' not in st.session_state or st.session_state.production_data is None:
        print("[DEBUG] 세션에 production_data 없음, 새로 로드합니다")
        
        # 캐시 무효화 후 직접 데이터 로드
        st.session_state.db._invalidate_cache()
        
        # 직접 Supabase에서 페이지네이션으로 데이터 로드
        try:
            page_size = 1000
            offset = 0
            all_records = []
            
            while True:
                response = st.session_state.db.client.table('Production').select('*').limit(page_size).offset(offset).execute()
                records = response.data
                
                if not records:
                    break
                    
                all_records.extend(records)
                
                if len(records) < page_size:
                    break
                    
                offset += page_size
            
            # 수동으로 필드 형식 변환
            formatted_records = []
            for record in all_records:
                formatted_record = {}
                for key, value in record.items():
                    # id 필드 처리
                    if key == 'id':
                        formatted_record['STT'] = value
                    # 날짜 필드 처리
                    elif key == 'date' or key == '날짜':
                        formatted_record['날짜'] = value
                    # 작업자 필드 처리
                    elif key == 'worker' or key == '작업자' or '작업자' in key:
                        formatted_record['작업자'] = value
                    # 라인번호 필드 처리
                    elif key == 'line_number' or key == '라인번호' or '라인' in key:
                        formatted_record['라인번호'] = value
                    # 모델차수 필드 처리
                    elif key == 'model' or key == '모델차수' or '모델' in key:
                        formatted_record['모델차수'] = value
                    # 목표수량 필드 처리
                    elif key == 'target_quantity' or key == '목표수량' or '목표' in key:
                        formatted_record['목표수량'] = int(value) if value else 0
                    # 생산수량 필드 처리
                    elif key == 'production_quantity' or key == '생산수량' or '생산' in key:
                        formatted_record['생산수량'] = int(value) if value else 0
                    # 불량수량 필드 처리
                    elif key == 'defect_quantity' or key == '불량수량' or '불량' in key:
                        formatted_record['불량수량'] = int(value) if value else 0
                    # 특이사항 필드 처리
                    elif key == 'note' or key == '특이사항' or '특이' in key:
                        formatted_record['특이사항'] = value
                    else:
                        formatted_record[key] = value
                
                # 필수 필드 채우기
                for field in ['날짜', '작업자', '라인번호', '모델차수', '목표수량', '생산수량', '불량수량']:
                    if field not in formatted_record:
                        if field in ['목표수량', '생산수량', '불량수량']:
                            formatted_record[field] = 0
                        else:
                            formatted_record[field] = ''
                
                formatted_records.append(formatted_record)
            
            st.session_state.production_data = formatted_records
            
        except Exception as e:
            st.error(f"데이터 로드 중 오류: {str(e)}")
            import traceback
            print(f"[ERROR] 상세 오류: {traceback.format_exc()}")
            
            # 오류 발생 시 기존 방식으로 시도
            from pages.production import load_production_data
            st.session_state.production_data = load_production_data()
    
    total_records = len(st.session_state.production_data) if st.session_state.production_data else 0
    print(f"[DEBUG] 전체 데이터 수: {total_records}개")
    
    # 날짜 형식을 문자열로 변환
    selected_date_str = selected_date.strftime('%Y-%m-%d')
    
    # 전체 데이터에서 해당 날짜 데이터 필터링
    if st.session_state.production_data:
        all_df = pd.DataFrame(st.session_state.production_data)
        
        # 데이터 형식 확인
        if '날짜' in all_df.columns:
            sample_date = all_df['날짜'].iloc[0] if not all_df.empty else ""
            print(f"[DEBUG] 데이터 날짜 형식 샘플: {sample_date}, 타입: {type(sample_date)}")
        
        # 날짜 필터링 개선
        df = all_df[all_df['날짜'].astype(str).str.contains(selected_date_str)].copy()
        df_prev = all_df[all_df['날짜'].astype(str).str.contains(previous_date.strftime('%Y-%m-%d'))].copy()
        
        print(f"[DEBUG] 필터링된 {selected_date_str} 날짜 데이터: {len(df)}개")
        print(f"[DEBUG] 필터링된 {previous_date.strftime('%Y-%m-%d')} 날짜 데이터: {len(df_prev)}개")
    else:
        df = pd.DataFrame()
        df_prev = pd.DataFrame()
    
    if not df.empty:
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
            
            # AgGrid 설정
            gb = GridOptionsBuilder.from_dataframe(df[display_columns])
            gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=100)
            gb.configure_side_bar()
            gb.configure_default_column(
                groupable=False,  # Enterprise 기능 비활성화
                value=True,
                enableRowGroup=False,  # Enterprise 기능 비활성화
                aggFunc=None,  # Enterprise 기능 제거
                editable=False,
                sorteable=True,
                resizable=True,
                filterable=True
            )
            grid_options = gb.build()
            
            # AgGrid 표시
            AgGrid(
                df[display_columns],
                gridOptions=grid_options,
                height=500,
                width='100%',
                data_return_mode='AS_INPUT',
                update_mode='VALUE_CHANGED',
                fit_columns_on_grid_load=False,
                allow_unsafe_jscode=True,
                enable_enterprise_modules=False  # Enterprise 모듈 비활성화
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