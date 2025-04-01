import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import sys
import uuid
from utils.supabase_db import SupabaseDB
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid import GridUpdateMode, DataReturnMode
from utils.local_storage import LocalStorage
import utils.common as common

def save_production_data(data):
    try:
        # Supabase에 데이터 저장
        db = SupabaseDB()
        success = db.add_production_record(
            date=data["날짜"],
            worker=data["작업자"],
            line_number=data["라인번호"],
            model=data["모델차수"],
            target_quantity=data["목표수량"],
            production_quantity=data["생산수량"],
            defect_quantity=data["불량수량"],
            note=data.get("특이사항", "")
        )
        
        if success:
            st.success("생산 데이터가 저장되었습니다.")
        else:
            st.error("생산 데이터 저장 중 오류가 발생했습니다.")
        
        return success
    except Exception as e:
        st.error(f"데이터 저장 중 오류 발생: {str(e)}")
        return False

def load_production_data():
    try:
        # Supabase에서 데이터 로드
        if 'db' not in st.session_state:
            st.session_state.db = SupabaseDB()
        
        db = st.session_state.db
        
        # 캐시 무효화 먼저 수행
        db._invalidate_cache()
        
        # 전체 기간의 데이터를 로드하도록 수정
        # 시작일을 충분히 과거로, 종료일을 충분히 미래로 설정
        start_date = "2020-01-01"
        end_date = "2030-12-31"
        
        print(f"[DEBUG] 생산 데이터 로드 시도: {start_date} ~ {end_date}")
        records = db.get_production_records(start_date=start_date, end_date=end_date)
        record_count = len(records)
        print(f"[DEBUG] 로드된 생산 데이터: {record_count}개")
        
        # record_count를 10000으로 제한하지 않도록 수정
        if record_count >= 10000:
            print(f"[INFO] 최대 10000개 레코드 제한이 적용되었습니다. 실제 레코드 수: {record_count}")
        
        return records
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {str(e)}")
        import traceback
        print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
        return []

def show_production_management():
    st.title("📋 생산 실적 관리")
    
    # 데이터 로드
    if 'workers' not in st.session_state:
        from pages.worker_management import load_worker_data
        st.session_state.workers = load_worker_data()
    
    if 'models' not in st.session_state:
        from pages.model_management import load_model_data
        st.session_state.models = load_model_data()
    
    # 항상 최신 데이터를 로드하도록 수정
    st.session_state.production_data = load_production_data()
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["실적 등록", "실적 수정", "실적 조회"])
    
    with tab1:
        add_production_data()
    
    with tab2:
        edit_production_data()
        
    with tab3:
        view_production_data()

def edit_production_data():
    st.subheader("실적 수정")
    storage = LocalStorage()
    
    with st.form("필터 조건", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("시작일", datetime.now().date() - timedelta(days=7))
        with col2:
            end_date = st.date_input("종료일", datetime.now().date())
        with col3:
            search_worker = st.text_input("작업자 검색", "")
        
        filter_submitted = st.form_submit_button("필터 적용")
    
    if filter_submitted or 'production_filtered_df' in st.session_state:
        records = storage.load_production_records()
        
        # 날짜 변환
        str_start_date = start_date.strftime("%Y-%m-%d")
        str_end_date = end_date.strftime("%Y-%m-%d")
        
        filtered_records = []
        for record in records:
            record_date = record.get('생산일자', '')
            if str_start_date <= record_date <= str_end_date:
                if not search_worker or search_worker.lower() in record.get('작업자', '').lower():
                    filtered_records.append(record)
        
        if not filtered_records:
            st.warning("조건에 맞는 데이터가 없습니다.")
            return
        
        # 필터링된 DataFrame 생성
        filtered_df = pd.DataFrame(filtered_records)
        st.session_state['production_filtered_df'] = filtered_df
        st.session_state['production_filtered_records'] = filtered_records
        
        st.info(f"총 {len(filtered_records)}개의 데이터가 검색되었습니다.")
        
        # AgGrid 설정
        gb = GridOptionsBuilder.from_dataframe(filtered_df)
        gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=50)
        gb.configure_side_bar()
        gb.configure_default_column(
            groupable=True, 
            value=True, 
            enableRowGroup=True, 
            editable=False, 
            sortable=True, 
            resizable=True, 
            filterable=True
        )
        gb.configure_selection(selection_mode='single', use_checkbox=True)
        grid_options = gb.build()
        
        # 그리드 출력
        grid_response = AgGrid(
            filtered_df,
            gridOptions=grid_options,
            enable_enterprise_modules=False,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=True
        )
        
        # 선택된 행 처리
        selected_rows = grid_response['selected_rows']
        
        if selected_rows:
            selected_row = selected_rows[0]
            st.session_state['selected_production_record'] = selected_row
            
            st.subheader("선택된 실적 데이터 수정")
            
            with st.form("실적 수정 폼"):
                col1, col2 = st.columns(2)
                with col1:
                    edit_date = st.date_input("생산일자", datetime.strptime(selected_row['생산일자'], "%Y-%m-%d"))
                    edit_worker = st.text_input("작업자", selected_row.get('작업자', ''))
                    edit_model = st.text_input("모델명", selected_row.get('모델명', ''))
                    edit_line = st.text_input("라인", selected_row.get('라인', ''))
                
                with col2:
                    edit_target = st.number_input("목표수량", min_value=0, value=int(selected_row.get('목표수량', 0)))
                    edit_production = st.number_input("생산수량", min_value=0, value=int(selected_row.get('생산수량', 0)))
                    edit_defect = st.number_input("불량수량", min_value=0, value=int(selected_row.get('불량수량', 0)))
                    
                submit_edit = st.form_submit_button("수정 적용")
                
                if submit_edit:
                    # 선택된 레코드의 ID
                    record_id = selected_row.get('id')
                    
                    # 변경된 데이터 준비
                    updated_record = {
                        'id': record_id,
                        '생산일자': edit_date.strftime("%Y-%m-%d"),
                        '작업자': edit_worker,
                        '모델명': edit_model,
                        '라인': edit_line,
                        '목표수량': edit_target,
                        '생산수량': edit_production,
                        '불량수량': edit_defect
                    }
                    
                    # 데이터 업데이트
                    for i, record in enumerate(st.session_state['production_filtered_records']):
                        if record.get('id') == record_id:
                            st.session_state['production_filtered_records'][i] = updated_record
                    
                    # 모든 레코드 업데이트
                    all_records = storage.load_production_records()
                    for i, record in enumerate(all_records):
                        if record.get('id') == record_id:
                            all_records[i] = updated_record
                    
                    # 데이터 저장
                    storage.save_production_records(all_records)
                    st.success("실적 데이터가 성공적으로 수정되었습니다.")
                    
                    # 세션 상태 업데이트
                    st.session_state['production_filtered_df'] = pd.DataFrame(st.session_state['production_filtered_records'])
                    st.experimental_rerun()
            
            # 삭제 버튼
            if st.button("선택한 데이터 삭제"):
                if st.session_state.get('delete_confirmation', False):
                    # 선택된 레코드의 ID
                    record_id = selected_row.get('id')
                    
                    # 데이터 삭제
                    all_records = storage.load_production_records()
                    updated_records = [r for r in all_records if r.get('id') != record_id]
                    
                    # 데이터 저장
                    storage.save_production_records(updated_records)
                    st.success("실적 데이터가 성공적으로 삭제되었습니다.")
                    
                    # 세션 상태 초기화
                    st.session_state.pop('production_filtered_df', None)
                    st.session_state.pop('production_filtered_records', None)
                    st.session_state.pop('selected_production_record', None)
                    st.session_state.pop('delete_confirmation', None)
                    st.experimental_rerun()
                else:
                    st.session_state['delete_confirmation'] = True
                    st.warning("정말로 이 데이터를 삭제하시겠습니까? 삭제를 진행하려면 다시 한번 '선택한 데이터 삭제' 버튼을 클릭하세요.")

def add_production_data():
    st.subheader("생산 실적 등록")
    
    # 입력 폼
    with st.form("production_input_form"):
        # 날짜 선택
        date = st.date_input(
            "생산일자",
            value=datetime.now()
        )
        
        # 작업자 정보 입력
        col1, col2 = st.columns(2)
        with col1:
            worker = st.text_input("작업자", "")
        with col2:
            line = st.text_input("라인", "")
        
        # 모델 정보 입력
        model = st.text_input("모델명", "")
        
        # 수량 입력
        col1, col2, col3 = st.columns(3)
        with col1:
            target = st.number_input("목표수량", min_value=0, value=0)
        with col2:
            prod = st.number_input("생산수량", min_value=0, value=0)
        with col3:
            defect = st.number_input("불량수량", min_value=0, value=0)
        
        # 저장 버튼
        submitted = st.form_submit_button("실적 저장")
    
    # 폼 제출 처리
    if submitted:
        if not worker:
            st.error("작업자를 입력해주세요.")
        elif not line:
            st.error("라인을 입력해주세요.")
        elif not model:
            st.error("모델명을 입력해주세요.")
        else:
            # 새 레코드 생성
            record = {
                "id": str(uuid.uuid4()),
                "생산일자": date.strftime("%Y-%m-%d"),
                "작업자": worker,
                "라인": line,
                "모델명": model,
                "목표수량": int(target),
                "생산수량": int(prod),
                "불량수량": int(defect),
                "등록시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 데이터 저장
            storage = LocalStorage()
            records = storage.load_production_records()
            records.append(record)
            storage.save_production_records(records)
            
            st.success("생산 실적이 저장되었습니다.")
            st.experimental_rerun()

def view_production_data():
    st.subheader("실적 조회")
    storage = LocalStorage()
    
    with st.form("조회 필터", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("시작일", datetime.now().date() - timedelta(days=7))
        with col2:
            end_date = st.date_input("종료일", datetime.now().date())
        with col3:
            search_term = st.text_input("검색어(작업자/모델/라인)", "")
        
        filter_submitted = st.form_submit_button("조회")
    
    if filter_submitted or 'view_filtered_df' in st.session_state:
        records = storage.load_production_records()
        
        # 날짜 변환
        str_start_date = start_date.strftime("%Y-%m-%d")
        str_end_date = end_date.strftime("%Y-%m-%d")
        
        filtered_records = []
        for record in records:
            record_date = record.get('생산일자', '')
            if str_start_date <= record_date <= str_end_date:
                # 검색어 필터링
                if not search_term:
                    filtered_records.append(record)
                else:
                    search_term_lower = search_term.lower()
                    if (search_term_lower in record.get('작업자', '').lower() or
                        search_term_lower in record.get('모델명', '').lower() or
                        search_term_lower in record.get('라인', '').lower()):
                        filtered_records.append(record)
        
        if not filtered_records:
            st.warning("조건에 맞는 데이터가 없습니다.")
            return
        
        # 필터링된 DataFrame 생성
        filtered_df = pd.DataFrame(filtered_records)
        st.session_state['view_filtered_df'] = filtered_df
        
        st.info(f"총 {len(filtered_records)}개의 데이터가 검색되었습니다.")
        
        # 통계 정보 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            total_target = filtered_df['목표수량'].sum()
            st.metric("총 목표수량", f"{total_target:,}")
        with col2:
            total_production = filtered_df['생산수량'].sum()
            st.metric("총 생산수량", f"{total_production:,}")
        with col3:
            total_defect = filtered_df['불량수량'].sum()
            st.metric("총 불량수량", f"{total_defect:,}")
        
        # 작업효율 계산 (목표수량이 0이 아닌 경우만)
        if total_target > 0:
            efficiency = (total_production / total_target) * 100
            st.metric("평균 작업효율", f"{efficiency:.1f}%")
        
        # AgGrid 설정
        gb = GridOptionsBuilder.from_dataframe(filtered_df)
        gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=50)
        gb.configure_side_bar()
        gb.configure_default_column(
            groupable=True, 
            value=True, 
            enableRowGroup=True, 
            editable=False, 
            sortable=True, 
            resizable=True, 
            filterable=True
        )
        
        # 날짜, 작업자, 라인별 그룹핑 설정
        gb.configure_column("생산일자", rowGroup=True, hide=False)
        gb.configure_column("작업자", rowGroup=True, hide=False)
        gb.configure_column("라인", rowGroup=True, hide=False)
        
        # 집계 함수 설정
        gb.configure_column("목표수량", aggFunc="sum", type=["numericColumn", "numberColumnFilter"])
        gb.configure_column("생산수량", aggFunc="sum", type=["numericColumn", "numberColumnFilter"])
        gb.configure_column("불량수량", aggFunc="sum", type=["numericColumn", "numberColumnFilter"])
        
        grid_options = gb.build()
        
        # 그리드 출력
        AgGrid(
            filtered_df,
            gridOptions=grid_options,
            enable_enterprise_modules=False,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=True,
            height=500
        )

if __name__ == "__main__":
    show_production_management() 