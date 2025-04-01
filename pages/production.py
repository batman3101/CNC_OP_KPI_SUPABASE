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

# 프로젝트 루트 디렉토리를 path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

def save_production_data(data):
    try:
        # Supabase에 데이터 저장
        db = SupabaseDB()
        success = db.add_production_record(
            date=data["날짜"] if "날짜" in data else data.get("생산일자", ""),
            worker=data["작업자"],
            line_number=data["라인번호"] if "라인번호" in data else data.get("라인", ""),
            model=data["모델차수"] if "모델차수" in data else data.get("모델명", ""),
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
        import traceback
        print(f"[ERROR] 상세 오류: {traceback.format_exc()}")
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
    
    # 필터 UI를 컬럼으로 구성하여 더 깔끔하게 표시
    st.markdown("### 🔍 데이터 검색")
    with st.form("필터 조건", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("시작일", datetime.now().date() - timedelta(days=7))
        with col2:
            end_date = st.date_input("종료일", datetime.now().date())
        with col3:
            search_worker = st.text_input("작업자 검색")
        
        col4, col5 = st.columns([2, 1])
        with col4:
            st.markdown("") # 간격 조정용
        with col5:
            filter_submitted = st.form_submit_button("🔍 검색", use_container_width=True)
    
    # 필터 적용 여부 확인
    if filter_submitted or 'filtered_key' in st.session_state:
        try:
            # 필터링된 데이터 준비
            filtered_records = []
            
            if filter_submitted:
                str_start_date = start_date.strftime("%Y-%m-%d")
                str_end_date = end_date.strftime("%Y-%m-%d")
                
                # 캐시 키 생성
                filter_key = f"{str_start_date}_{str_end_date}_{search_worker}"
                st.session_state['filtered_key'] = filter_key
                
                # 데이터 필터링
                records = st.session_state.production_data
                for record in records:
                    record_date = str(record.get('날짜', ''))
                    if str_start_date <= record_date <= str_end_date:
                        if not search_worker or search_worker.lower() in str(record.get('작업자', '')).lower():
                            filtered_records.append(record)
                
                st.session_state['filtered_records'] = filtered_records
            else:
                if 'filtered_records' in st.session_state:
                    filtered_records = st.session_state['filtered_records']
            
            # 필터링 결과 표시
            if not filtered_records:
                st.warning("조건에 맞는 데이터가 없습니다.")
                return
            
            st.markdown("---")
            st.markdown("### 📝 데이터 수정/삭제")
            st.info(f"총 {len(filtered_records)}개의 데이터가 검색되었습니다. 수정할 데이터를 선택하세요.")
            
            # DataFrame 생성 및 AgGrid 표시
            df = pd.DataFrame(filtered_records)
            
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=10)
            gb.configure_default_column(
                value=True, 
                editable=False, 
                sortable=True, 
                resizable=True, 
                filterable=True
            )
            gb.configure_selection(selection_mode='single')
            grid_options = gb.build()
            
            grid_response = AgGrid(
                df,
                gridOptions=grid_options,
                enable_enterprise_modules=False,
                update_mode=GridUpdateMode.MODEL_CHANGED,
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                fit_columns_on_grid_load=True,
                height=300
            )
            
            # 선택된 행 처리
            selected_rows = grid_response['selected_rows']
            if selected_rows:
                selected_row = selected_rows[0]
                
                st.markdown("---")
                st.markdown("### ✏️ 선택된 데이터 수정")
                
                # 수정 폼
                with st.form("실적_수정_폼"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_date = st.date_input(
                            "생산일자",
                            datetime.strptime(selected_row.get('날짜', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
                        )
                        
                        # 작업자 선택
                        workers = st.session_state.workers if 'workers' in st.session_state else []
                        worker_names = [w.get('이름', '') for w in workers if '이름' in w]
                        current_worker = selected_row.get('작업자', '')
                        worker_idx = worker_names.index(current_worker) if current_worker in worker_names else 0
                        edit_worker = st.selectbox("작업자", worker_names, index=worker_idx)
                        
                        # 라인 선택
                        line_numbers = list(set([w.get('라인번호', '') for w in workers if '라인번호' in w]))
                        current_line = selected_row.get('라인번호', '')
                        line_idx = line_numbers.index(current_line) if current_line in line_numbers else 0
                        edit_line = st.selectbox("라인", line_numbers, index=line_idx)
                        
                        # 모델 선택
                        models = st.session_state.models if 'models' in st.session_state else []
                        model_names = list(set([m.get('모델명', '') for m in models if '모델명' in m]))
                        current_model = selected_row.get('모델차수', '')
                        model_idx = model_names.index(current_model) if current_model in model_names else 0
                        edit_model = st.selectbox("모델", model_names, index=model_idx)
                    
                    with col2:
                        edit_target = st.number_input("목표수량", min_value=0, value=int(selected_row.get('목표수량', 0)))
                        edit_production = st.number_input("생산수량", min_value=0, value=int(selected_row.get('생산수량', 0)))
                        edit_defect = st.number_input("불량수량", min_value=0, value=int(selected_row.get('불량수량', 0)))
                    
                    col3, col4 = st.columns([3, 1])
                    with col3:
                        st.markdown("") # 간격 조정용
                    with col4:
                        submit_edit = st.form_submit_button("💾 수정 적용", use_container_width=True)
                
                if submit_edit:
                    try:
                        record_id = selected_row.get('id')
                        if not record_id:
                            st.error("레코드 ID를 찾을 수 없습니다.")
                        else:
                            # 수정할 데이터 준비
                            updated_data = {
                                'id': record_id,
                                '날짜': edit_date.strftime("%Y-%m-%d"),
                                '작업자': edit_worker,
                                '라인번호': edit_line,
                                '모델차수': edit_model,
                                '목표수량': edit_target,
                                '생산수량': edit_production,
                                '불량수량': edit_defect
                            }
                            
                            # 데이터베이스 업데이트
                            if 'db' not in st.session_state:
                                st.session_state.db = SupabaseDB()
                            
                            success = st.session_state.db.update_production_record(record_id, updated_data)
                            
                            if success:
                                st.success("✅ 데이터가 성공적으로 수정되었습니다.")
                                # 세션 상태 초기화 및 데이터 리로드
                                st.session_state.pop('production_data', None)
                                st.session_state.production_data = load_production_data()
                                st.experimental_rerun()
                            else:
                                st.error("데이터 저장 중 오류가 발생했습니다.")
                    except Exception as e:
                        st.error(f"데이터 수정 중 오류: {str(e)}")
                
                # 삭제 기능
                st.markdown("---")
                st.markdown("### ❌ 데이터 삭제")
                
                col5, col6 = st.columns([3, 1])
                with col5:
                    delete_confirm = st.checkbox("이 데이터를 삭제하시겠습니까?")
                with col6:
                    if delete_confirm and st.button("🗑️ 삭제", use_container_width=True):
                        try:
                            record_id = selected_row.get('id')
                            if not record_id:
                                st.error("레코드 ID를 찾을 수 없습니다.")
                            else:
                                if 'db' not in st.session_state:
                                    st.session_state.db = SupabaseDB()
                                
                                success = st.session_state.db.delete_production_record(record_id)
                                
                                if success:
                                    st.success("✅ 데이터가 성공적으로 삭제되었습니다.")
                                    # 세션 상태 초기화 및 데이터 리로드
                                    st.session_state.pop('production_data', None)
                                    st.session_state.production_data = load_production_data()
                                    st.experimental_rerun()
                                else:
                                    st.error("데이터 삭제 중 오류가 발생했습니다.")
                        except Exception as e:
                            st.error(f"데이터 삭제 중 오류: {str(e)}")
        
        except Exception as e:
            st.error(f"데이터 처리 중 오류가 발생했습니다: {str(e)}")
            import traceback
            print(f"[ERROR] 상세 오류: {traceback.format_exc()}")

def add_production_data():
    st.subheader("생산 실적 등록")
    
    # 입력 폼
    with st.form("production_input_form"):
        # 날짜 선택
        date = st.date_input(
            "생산일자",
            value=datetime.now()
        )
        
        # 작업자 정보 입력 (드롭다운으로 변경)
        col1, col2 = st.columns(2)
        with col1:
            # 작업자 목록 가져오기
            workers = st.session_state.workers if 'workers' in st.session_state else []
            worker_names = [worker.get('이름', '') for worker in workers if '이름' in worker]
            worker = st.selectbox("작업자", options=worker_names)
        with col2:
            # 라인 목록 가져오기
            workers = st.session_state.workers if 'workers' in st.session_state else []
            line_numbers = list(set([worker.get('라인번호', '') for worker in workers if '라인번호' in worker and worker.get('라인번호', '')]))
            line = st.selectbox("라인", options=line_numbers)
        
        # 모델 정보 입력 (드롭다운으로 변경)
        models = st.session_state.models if 'models' in st.session_state else []
        model_names = list(set([model.get('모델명', '') for model in models if '모델명' in model and model.get('모델명', '')]))
        model = st.selectbox("모델명", options=model_names)
        
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
            st.error("작업자를 선택해주세요.")
        elif not line:
            st.error("라인을 선택해주세요.")
        elif not model:
            st.error("모델명을 선택해주세요.")
        else:
            try:
                # 새 레코드 생성
                record = {
                    "id": str(uuid.uuid4()),
                    "날짜": date.strftime("%Y-%m-%d"),
                    "작업자": worker,
                    "라인번호": line,
                    "모델차수": model,
                    "목표수량": int(target),
                    "생산수량": int(prod),
                    "불량수량": int(defect),
                    "등록시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # 데이터 저장
                save_production_data(record)
                
                st.success("생산 실적이 저장되었습니다.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"생산 실적 저장 중 오류가 발생했습니다: {str(e)}")

def view_production_data():
    st.subheader("실적 조회")
    
    # 데이터 로드 - 항상 최신 데이터 사용
    st.session_state.production_data = load_production_data()
    
    # 조회 필터
    with st.form("조회 필터", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("시작일", datetime.now().date() - timedelta(days=7))
        with col2:
            end_date = st.date_input("종료일", datetime.now().date())
        with col3:
            search_term = st.text_input("검색어(작업자/모델/라인)", "")
        
        filter_submitted = st.form_submit_button("조회")
    
    # 필터 적용 전체를 try-except로 보호
    try:
        # 필터 적용 여부 확인
        if filter_submitted or 'view_filtered_key' in st.session_state:
            # 필터링된 데이터 준비
            filtered_records = []
            
            # 필터 제출 시 새로 필터링
            if filter_submitted:
                str_start_date = start_date.strftime("%Y-%m-%d")
                str_end_date = end_date.strftime("%Y-%m-%d")
                
                # 캐시 키 생성
                filter_key = f"{str_start_date}_{str_end_date}_{search_term}"
                st.session_state['view_filtered_key'] = filter_key
                
                # 필드명 자동 감지
                records = st.session_state.production_data
                if not records or len(records) == 0:
                    st.warning("데이터가 없습니다.")
                    return
                
                sample_record = records[0]
                fields = list(sample_record.keys())
                
                # 필드명 자동 감지
                date_field = None
                worker_field = None
                model_field = None
                line_field = None
                
                for field in fields:
                    if '날짜' in field or 'date' in field.lower():
                        date_field = field
                    if '작업자' in field or 'worker' in field.lower():
                        worker_field = field
                    if '모델' in field or 'model' in field.lower():
                        model_field = field
                    if '라인' in field or 'line' in field.lower():
                        line_field = field
                
                # 기본값 설정
                if not date_field:
                    date_field = '날짜' if '날짜' in sample_record else 'date'
                if not worker_field:
                    worker_field = '작업자' if '작업자' in sample_record else 'worker'
                if not model_field:
                    model_field = '모델차수' if '모델차수' in sample_record else 'model'
                if not line_field:
                    line_field = '라인번호' if '라인번호' in sample_record else 'line_number'
                
                # 필터링 실행
                for record in records:
                    if date_field not in record:
                        continue
                        
                    record_date = str(record.get(date_field, ''))
                    
                    # 날짜 필터링 (범위 내)
                    if str_start_date <= record_date <= str_end_date:
                        # 검색어 필터링
                        if not search_term:
                            filtered_records.append(record)
                        else:
                            search_term_lower = search_term.lower()
                            if (worker_field in record and search_term_lower in str(record.get(worker_field, '')).lower()) or \
                            (model_field in record and search_term_lower in str(record.get(model_field, '')).lower()) or \
                            (line_field in record and search_term_lower in str(record.get(line_field, '')).lower()):
                                filtered_records.append(record)
                
                # 필터링 결과 저장
                st.session_state['view_filtered_records'] = filtered_records
            else:
                # 기존 필터링 결과 사용
                if 'view_filtered_records' in st.session_state:
                    filtered_records = st.session_state['view_filtered_records']
            
            # 결과 수 확인
            if len(filtered_records) == 0:
                st.warning("조건에 맞는 데이터가 없습니다.")
                return
            
            # 결과 정보 표시
            st.info(f"총 {len(filtered_records)}개의 데이터가 검색되었습니다.")
            
            # DataFrame 생성
            try:
                # 안전하게 DataFrame 생성
                filtered_df = pd.DataFrame(filtered_records)
                
                # 필드명 매핑 준비
                column_mapping = {}
                
                # 실제 컬럼이 있는 경우만 매핑
                cols = filtered_df.columns.tolist()
                
                # 날짜 필드 매핑
                date_cols = [col for col in cols if '날짜' in col or 'date' in col.lower()]
                if date_cols and date_cols[0] != '생산일자':
                    column_mapping[date_cols[0]] = '생산일자'
                
                # 작업자 필드 매핑
                worker_cols = [col for col in cols if '작업자' in col or 'worker' in col.lower()]
                if worker_cols and worker_cols[0] != '작업자':
                    column_mapping[worker_cols[0]] = '작업자'
                
                # 모델 필드 매핑
                model_cols = [col for col in cols if '모델' in col or 'model' in col.lower()]
                if model_cols and model_cols[0] != '모델명':
                    column_mapping[model_cols[0]] = '모델명'
                
                # 라인 필드 매핑
                line_cols = [col for col in cols if '라인' in col or 'line' in col.lower()]
                if line_cols and line_cols[0] != '라인':
                    column_mapping[line_cols[0]] = '라인'
                
                # 필드명 변경
                if column_mapping:
                    filtered_df = filtered_df.rename(columns=column_mapping)
                
                # 통계 정보 표시
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if '목표수량' in filtered_df.columns:
                        total_target = filtered_df['목표수량'].sum()
                        st.metric("총 목표수량", f"{total_target:,}")
                
                with col2:
                    if '생산수량' in filtered_df.columns:
                        total_production = filtered_df['생산수량'].sum()
                        st.metric("총 생산수량", f"{total_production:,}")
                
                with col3:
                    if '불량수량' in filtered_df.columns:
                        total_defect = filtered_df['불량수량'].sum()
                        st.metric("총 불량수량", f"{total_defect:,}")
                
                # 작업효율 계산
                if '목표수량' in filtered_df.columns and '생산수량' in filtered_df.columns:
                    total_target = filtered_df['목표수량'].sum()
                    if total_target > 0:  # 0으로 나누기 방지
                        total_production = filtered_df['생산수량'].sum()
                        efficiency = (total_production / total_target) * 100
                        st.metric("평균 작업효율", f"{efficiency:.1f}%")
                
                # AgGrid 설정
                gb = GridOptionsBuilder.from_dataframe(filtered_df)
                gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=50)
                
                # 기본 컬럼 설정 - Community 버전 호환
                gb.configure_default_column(
                    value=True, 
                    editable=False, 
                    sortable=True, 
                    resizable=True, 
                    filterable=True
                )
                
                # 단순 선택 모드 설정
                gb.configure_selection(selection_mode='single')
                
                grid_options = gb.build()
                
                # 그리드 출력 - Community 버전 설정
                AgGrid(
                    filtered_df,
                    gridOptions=grid_options,
                    enable_enterprise_modules=False,
                    update_mode=GridUpdateMode.MODEL_CHANGED,
                    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                    fit_columns_on_grid_load=True,
                    height=500,
                    allow_unsafe_jscode=False
                )
            except Exception as e:
                st.error(f"데이터 표시 중 오류가 발생했습니다: {str(e)}")
                import traceback
                print(f"[ERROR] 데이터 표시 상세 오류: {traceback.format_exc()}")
                print(f"[DEBUG] DataFrame 정보: 크기={len(filtered_records)}개 레코드")
                if len(filtered_records) > 0:
                    print(f"[DEBUG] 샘플 레코드 키: {list(filtered_records[0].keys())}")
    except Exception as e:
        st.error(f"데이터 처리 중 오류가 발생했습니다: {str(e)}")
        import traceback
        print(f"[ERROR] 상세 오류: {traceback.format_exc()}")

if __name__ == "__main__":
    show_production_management() 