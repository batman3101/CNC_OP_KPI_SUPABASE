import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
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
            
            # AgGrid를 사용하여 데이터 표시
            display_data_grid(df[display_columns])
        
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

# AgGrid를 사용하여 데이터 표시
def display_data_grid(df, title="데이터 테이블"):
    try:
        if df is None or len(df) == 0:
            st.info("표시할 데이터가 없습니다.")
            return
        
        st.subheader(title)
        
        # 가장 기본적인 설정만 사용하여 AgGrid 설정
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationPageSize=10)
        gb.configure_default_column(sortable=True)
        gb.configure_selection(selection_mode='single')
        grid_options = gb.build()
        
        # 최소한의 옵션으로 그리드 표시
        AgGrid(
            df,
            gridOptions=grid_options,
            enable_enterprise_modules=False,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            fit_columns_on_grid_load=True,
            height=400
        )
    except Exception as e:
        st.error(f"데이터 그리드 표시 중 오류가 발생했습니다: {str(e)}")

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
    
    # 데이터 로드
    if 'daily_report_data' not in st.session_state:
        st.session_state.daily_report_data = None
    
    if 'production_data' not in st.session_state or st.session_state.production_data is None:
        from pages.production import load_production_data
        st.session_state.production_data = load_production_data()
    
    # 날짜 선택
    with st.form(key="일일보고서_날짜선택"):
        col1, col2 = st.columns(2)
        with col1:
            target_date = st.date_input("보고서 날짜", value=datetime.now().date())
        with col2:
            generate_button = st.form_submit_button("보고서 생성", use_container_width=True)
    
    if generate_button or st.session_state.daily_report_data is not None:
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
            
            # 여러 탭으로 데이터 표시
            tab1, tab2, tab3 = st.tabs(["요약", "상세 데이터", "효율성 분석"])
            
            with tab1:
                display_summary(df, target_date_str)
            
            with tab2:
                display_detailed_data(df)
            
            with tab3:
                display_efficiency_analysis(df)
            
        except Exception as e:
            st.error(f"데이터 처리 중 오류가 발생했습니다: {str(e)}")
            import traceback
            print(f"[ERROR] 상세 오류: {traceback.format_exc()}")

def display_summary(df, date_str):
    try:
        st.header(f"{date_str} 일일 생산 요약")
        
        st.markdown("### 📈 생산 실적 요약")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_target = df['목표수량'].sum()
            st.metric("총 목표 수량", f"{total_target:,}")
        
        with col2:
            total_production = df['생산수량'].sum()
            st.metric("총 생산 수량", f"{total_production:,}")
        
        with col3:
            total_defect = df['불량수량'].sum()
            st.metric("총 불량 수량", f"{total_defect:,}")
        
        with col4:
            if total_target > 0:
                achievement_rate = (total_production / total_target) * 100
                st.metric("목표 달성률", f"{achievement_rate:.1f}%")
        
        # 작업자별 생산량
        st.markdown("### 👥 작업자별 생산량")
        worker_production = df.groupby('작업자')['생산수량'].sum().reset_index()
        worker_production = worker_production.sort_values('생산수량', ascending=False)
        
        # 간단한 차트
        st.bar_chart(worker_production.set_index('작업자'))
        
        # 라인별 생산량
        st.markdown("### 🏭 라인별 생산량")
        line_production = df.groupby('라인번호')['생산수량'].sum().reset_index()
        line_production = line_production.sort_values('생산수량', ascending=False)
        
        # 간단한 차트
        st.bar_chart(line_production.set_index('라인번호'))
        
        # 모델별 생산량
        st.markdown("### 📊 모델별 생산량")
        model_production = df.groupby('모델차수')['생산수량'].sum().reset_index()
        model_production = model_production.sort_values('생산수량', ascending=False)
        
        # 간단한 차트
        st.bar_chart(model_production.set_index('모델차수'))
        
    except Exception as e:
        st.error(f"요약 데이터 처리 중 오류가 발생했습니다: {str(e)}")

def display_detailed_data(df):
    st.header("상세 생산 데이터")
    
    try:
        if df.empty:
            st.warning("표시할 데이터가 없습니다.")
            return
        
        # 페이지네이션 설정
        if 'detailed_page_number' not in st.session_state:
            st.session_state.detailed_page_number = 1
        page_size = 10
        
        # 페이지네이션된 데이터프레임 가져오기
        paginated_df, total_pages = paginate_dataframe(df, page_size, st.session_state.detailed_page_number)
        
        # 테이블 표시
        st.dataframe(paginated_df, use_container_width=True)
        
        # 페이지네이션 UI
        col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
        with col1:
            if st.button("◀️ 이전", key="detailed_prev", disabled=st.session_state.detailed_page_number <= 1):
                st.session_state.detailed_page_number -= 1
                st.rerun()
        with col2:
            if st.button("다음 ▶️", key="detailed_next", disabled=st.session_state.detailed_page_number >= total_pages):
                st.session_state.detailed_page_number += 1
                st.rerun()
        with col3:
            st.write(f"페이지: {st.session_state.detailed_page_number}/{total_pages}")
        with col4:
            new_page = st.number_input("페이지 이동", min_value=1, max_value=total_pages, value=st.session_state.detailed_page_number, step=1, key="detailed_page_input")
            if new_page != st.session_state.detailed_page_number:
                st.session_state.detailed_page_number = new_page
                st.rerun()
        
        # 상세 레코드 선택 기능
        st.markdown("### 🔍 레코드 선택")
        selected_index = st.selectbox(
            "상세 정보를 볼 레코드를 선택하세요",
            options=paginated_df.index.tolist(),
            format_func=lambda x: f"{paginated_df.loc[x, '작업자']} - {paginated_df.loc[x, '라인번호']} - {paginated_df.loc[x, '모델차수']} (목표: {paginated_df.loc[x, '목표수량']}, 생산: {paginated_df.loc[x, '생산수량']})"
        )
        
        if selected_index is not None:
            with st.expander("📄 선택한 레코드 상세 정보", expanded=True):
                st.json(df.loc[selected_index].to_dict())
    
    except Exception as e:
        st.error(f"상세 데이터 처리 중 오류가 발생했습니다: {str(e)}")

def display_efficiency_analysis(df):
    st.header("생산 효율성 분석")
    
    try:
        if df.empty:
            st.warning("분석할 데이터가 없습니다.")
            return
        
        # 작업자별 효율성 계산
        worker_efficiency = pd.DataFrame()
        worker_efficiency['작업자'] = df['작업자']
        worker_efficiency['목표수량'] = df['목표수량']
        worker_efficiency['생산수량'] = df['생산수량']
        worker_efficiency['불량수량'] = df['불량수량']
        worker_efficiency['달성률'] = (worker_efficiency['생산수량'] / worker_efficiency['목표수량'] * 100).fillna(0).round(1)
        worker_efficiency['불량률'] = (worker_efficiency['불량수량'] / worker_efficiency['생산수량'] * 100).fillna(0).round(1)
        
        # 작업자별 효율성 집계
        worker_summary = worker_efficiency.groupby('작업자').agg({
            '목표수량': 'sum',
            '생산수량': 'sum',
            '불량수량': 'sum'
        }).reset_index()
        
        worker_summary['달성률'] = (worker_summary['생산수량'] / worker_summary['목표수량'] * 100).fillna(0).round(1)
        worker_summary['불량률'] = (worker_summary['불량수량'] / worker_summary['생산수량'] * 100).fillna(0).round(1)
        
        # 효율성 표시
        st.markdown("### 👥 작업자별 생산 효율성")
        
        # 페이지네이션 설정
        if 'efficiency_page_number' not in st.session_state:
            st.session_state.efficiency_page_number = 1
        page_size = 5
        
        # 페이지네이션된 데이터프레임 가져오기
        paginated_ws, total_pages = paginate_dataframe(worker_summary, page_size, st.session_state.efficiency_page_number)
        
        # 테이블 표시
        st.dataframe(paginated_ws, use_container_width=True)
        
        # 페이지네이션 UI
        col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
        with col1:
            if st.button("◀️ 이전", key="efficiency_prev", disabled=st.session_state.efficiency_page_number <= 1):
                st.session_state.efficiency_page_number -= 1
                st.rerun()
        with col2:
            if st.button("다음 ▶️", key="efficiency_next", disabled=st.session_state.efficiency_page_number >= total_pages):
                st.session_state.efficiency_page_number += 1
                st.rerun()
        with col3:
            st.write(f"페이지: {st.session_state.efficiency_page_number}/{total_pages}")
        with col4:
            new_page = st.number_input("페이지 이동", min_value=1, max_value=total_pages, value=st.session_state.efficiency_page_number, step=1, key="efficiency_page_input")
            if new_page != st.session_state.efficiency_page_number:
                st.session_state.efficiency_page_number = new_page
                st.rerun()
        
        # 달성률 및 불량률 시각화
        st.markdown("### 📊 작업자별 달성률 및 불량률")
        col1, col2 = st.columns(2)
        
        with col1:
            achievement_chart = pd.DataFrame({
                '작업자': worker_summary['작업자'],
                '달성률': worker_summary['달성률']
            }).set_index('작업자')
            st.subheader("달성률 (%)")
            st.bar_chart(achievement_chart)
        
        with col2:
            defect_chart = pd.DataFrame({
                '작업자': worker_summary['작업자'],
                '불량률': worker_summary['불량률']
            }).set_index('작업자')
            st.subheader("불량률 (%)")
            st.bar_chart(defect_chart)
        
        # 라인별 효율성 분석
        st.markdown("### 🏭 라인별 생산 효율성")
        line_efficiency = df.groupby('라인번호').agg({
            '목표수량': 'sum',
            '생산수량': 'sum',
            '불량수량': 'sum'
        }).reset_index()
        
        line_efficiency['달성률'] = (line_efficiency['생산수량'] / line_efficiency['목표수량'] * 100).fillna(0).round(1)
        line_efficiency['불량률'] = (line_efficiency['불량수량'] / line_efficiency['생산수량'] * 100).fillna(0).round(1)
        
        st.dataframe(line_efficiency, use_container_width=True)
        
        # 모델별 효율성 분석
        st.markdown("### 📝 모델별 생산 효율성")
        model_efficiency = df.groupby('모델차수').agg({
            '목표수량': 'sum',
            '생산수량': 'sum',
            '불량수량': 'sum'
        }).reset_index()
        
        model_efficiency['달성률'] = (model_efficiency['생산수량'] / model_efficiency['목표수량'] * 100).fillna(0).round(1)
        model_efficiency['불량률'] = (model_efficiency['불량수량'] / model_efficiency['생산수량'] * 100).fillna(0).round(1)
        
        st.dataframe(model_efficiency, use_container_width=True)
    
    except Exception as e:
        st.error(f"효율성 분석 중 오류가 발생했습니다: {str(e)}")
        import traceback
        print(f"[ERROR] 상세 오류: {traceback.format_exc()}")

if __name__ == "__main__":
    show() 