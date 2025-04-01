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
    
    # LocalStorage 대신 Supabase DB 데이터 사용
    if 'production_data' not in st.session_state or st.session_state.production_data is None:
        st.session_state.production_data = load_production_data()
    
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
        try:
            # records = storage.load_production_records()  # 이전 코드
            records = st.session_state.production_data  # Supabase에서 가져온 데이터 사용
            
            # 로그 추가 - 콘솔에만 출력하도록 변경
            print(f"[DEBUG] 전체 레코드 수: {len(records)}개")
            if len(records) > 0:
                print(f"[DEBUG] 데이터 샘플: {records[0]}")
                print(f"[DEBUG] 필드명: {list(records[0].keys())}")
            
            # 날짜 변환
            str_start_date = start_date.strftime("%Y-%m-%d")
            str_end_date = end_date.strftime("%Y-%m-%d")
            
            # 필터링 로직 개선 - 다양한 필드명에 대응
            filtered_records = []
            date_field = None
            worker_field = None
            
            # 필드명 자동 감지
            if len(records) > 0:
                fields = list(records[0].keys())
                for field in fields:
                    if '날짜' in field or 'date' in field.lower():
                        date_field = field
                    if '작업자' in field or 'worker' in field.lower():
                        worker_field = field
            
            if not date_field and len(records) > 0:
                date_field = 'date' if 'date' in records[0] else '날짜'
            if not worker_field and len(records) > 0:
                worker_field = 'worker' if 'worker' in records[0] else '작업자'
            
            # 로그 추가 - 콘솔에만 출력하도록 변경
            print(f"[DEBUG] 사용할 날짜 필드: {date_field}")
            print(f"[DEBUG] 사용할 작업자 필드: {worker_field}")
            
            for record in records:
                # 날짜 필드가 있는지 확인
                if date_field not in record:
                    continue
                    
                record_date = str(record.get(date_field, ''))
                
                # 날짜 필터링 - 포함 관계로 변경 (contains)
                if str_start_date in record_date or str_end_date in record_date or (
                    str_start_date <= record_date <= str_end_date):
                    
                    # 작업자 필터링
                    if not search_worker:
                        filtered_records.append(record)
                    elif worker_field in record and search_worker.lower() in str(record.get(worker_field, '')).lower():
                        filtered_records.append(record)
            
            print(f"[DEBUG] 필터링된 레코드 수: {len(filtered_records)}개")
            
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
            # 단일 항목 선택으로 설정
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
            
            # 선택된 행이 있는지 확인
            if selected_rows and len(selected_rows) > 0:
                # 선택된 첫 번째 행 가져오기
                selected_row = selected_rows[0]
                st.session_state['selected_production_record'] = selected_row
                
                st.subheader("선택된 실적 데이터 수정")
                
                try:
                    # 작업자 목록 가져오기
                    workers = st.session_state.workers if 'workers' in st.session_state else []
                    worker_names = [worker.get('이름', '') for worker in workers if '이름' in worker]
                    
                    # 라인 목록 가져오기
                    line_numbers = list(set([worker.get('라인번호', '') for worker in workers if '라인번호' in worker and worker.get('라인번호', '')]))
                    
                    # 모델 목록 가져오기
                    models = st.session_state.models if 'models' in st.session_state else []
                    model_names = list(set([model.get('모델명', '') for model in models if '모델명' in model and model.get('모델명', '')]))
                    
                    # 필드명 확인
                    date_field = '날짜'
                    model_field = '모델차수'
                    line_field = '라인번호'
                    
                    # 필드명 자동 감지
                    fields = list(selected_row.keys())
                    for field in fields:
                        if '날짜' in field or 'date' in field.lower():
                            date_field = field
                        if '모델' in field:
                            model_field = field
                        if '라인' in field:
                            line_field = field
                    
                    # 디버깅 로그
                    print(f"[DEBUG] 선택된 행 필드명: {fields}")
                    print(f"[DEBUG] 감지된 날짜 필드: {date_field}")
                    print(f"[DEBUG] 감지된 모델 필드: {model_field}")
                    print(f"[DEBUG] 감지된 라인 필드: {line_field}")
                    
                    with st.form("실적 수정 폼"):
                        col1, col2 = st.columns(2)
                        with col1:
                            # 날짜 필드 처리
                            try:
                                default_date = datetime.now()
                                if date_field in selected_row and selected_row.get(date_field):
                                    try:
                                        default_date = datetime.strptime(selected_row.get(date_field, ''), "%Y-%m-%d")
                                    except:
                                        pass
                                edit_date = st.date_input("생산일자", default_date)
                            except Exception as e:
                                print(f"[ERROR] 날짜 처리 오류: {str(e)}")
                                edit_date = st.date_input("생산일자", datetime.now())
                            
                            # 작업자 필드
                            default_worker_index = 0
                            if worker_names and '작업자' in selected_row and selected_row.get('작업자', '') in worker_names:
                                default_worker_index = worker_names.index(selected_row.get('작업자', ''))
                            edit_worker = st.selectbox("작업자", options=worker_names, index=default_worker_index)
                            
                            # 모델 필드
                            default_model_index = 0
                            if model_names and model_field in selected_row and selected_row.get(model_field, '') in model_names:
                                default_model_index = model_names.index(selected_row.get(model_field, ''))
                            edit_model = st.selectbox("모델명", options=model_names, index=default_model_index)
                            
                            # 라인 필드
                            default_line_index = 0
                            if line_numbers and line_field in selected_row and selected_row.get(line_field, '') in line_numbers:
                                default_line_index = line_numbers.index(selected_row.get(line_field, ''))
                            edit_line = st.selectbox("라인", options=line_numbers, index=default_line_index)
                        
                        with col2:
                            # 수량 필드(목표, 생산, 불량)에 대한 안전한 기본값 설정
                            try:
                                default_target = int(selected_row.get('목표수량', 0))
                            except:
                                default_target = 0
                                
                            try:
                                default_production = int(selected_row.get('생산수량', 0))
                            except:
                                default_production = 0
                                
                            try:
                                default_defect = int(selected_row.get('불량수량', 0))
                            except:
                                default_defect = 0
                                
                            edit_target = st.number_input("목표수량", min_value=0, value=default_target)
                            edit_production = st.number_input("생산수량", min_value=0, value=default_production)
                            edit_defect = st.number_input("불량수량", min_value=0, value=default_defect)
                            
                        submit_edit = st.form_submit_button("수정 적용")
                        
                        if submit_edit:
                            try:
                                # 선택된 레코드의 ID
                                record_id = selected_row.get('id')
                                
                                if not record_id:
                                    st.error("선택된 레코드의 ID를 찾을 수 없습니다.")
                                    return
                                
                                # 변경된 데이터 준비
                                updated_record = selected_row.copy()  # 기존 데이터 복사
                                
                                # 수정할 필드 업데이트
                                updated_record[date_field] = edit_date.strftime("%Y-%m-%d")
                                updated_record['작업자'] = edit_worker
                                updated_record[model_field] = edit_model
                                updated_record[line_field] = edit_line
                                updated_record['목표수량'] = int(edit_target)
                                updated_record['생산수량'] = int(edit_production)
                                updated_record['불량수량'] = int(edit_defect)
                                
                                # 데이터 업데이트 - 필터링된 레코드
                                for i, record in enumerate(st.session_state['production_filtered_records']):
                                    if record.get('id') == record_id:
                                        st.session_state['production_filtered_records'][i] = updated_record
                                
                                # 모든 레코드 업데이트
                                all_records = st.session_state.production_data
                                for i, record in enumerate(all_records):
                                    if record.get('id') == record_id:
                                        all_records[i] = updated_record
                                
                                # 데이터 저장
                                if save_production_data(updated_record):
                                    st.success("실적 데이터가 성공적으로 수정되었습니다.")
                                else:
                                    st.error("실적 데이터 수정 중 오류가 발생했습니다.")
                                    
                                # 세션 상태 업데이트
                                if len(st.session_state['production_filtered_records']) > 0:
                                    st.session_state['production_filtered_df'] = pd.DataFrame(st.session_state['production_filtered_records'])
                                else:
                                    st.session_state.pop('production_filtered_df', None)
                                    st.session_state.pop('production_filtered_records', None)
                                
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"데이터 수정 중 오류가 발생했습니다: {str(e)}")
                                import traceback
                                print(f"[ERROR] 상세 오류: {traceback.format_exc()}")
                    
                    # 선택한 데이터 삭제 기능 추가
                    if st.button("선택한 데이터 삭제"):
                        if 'delete_confirmation' not in st.session_state or not st.session_state.get('delete_confirmation', False):
                            st.session_state['delete_confirmation'] = True
                            st.warning("정말로 이 데이터를 삭제하시겠습니까? 삭제를 진행하려면 다시 한번 '선택한 데이터 삭제' 버튼을 클릭하세요.")
                        else:
                            try:
                                # 선택된 레코드의 ID
                                record_id = selected_row.get('id')
                                
                                if not record_id:
                                    st.error("선택된 레코드의 ID를 찾을 수 없습니다.")
                                    return
                                
                                # Supabase에서 데이터 삭제
                                if 'db' not in st.session_state:
                                    st.session_state.db = SupabaseDB()
                                
                                success = st.session_state.db.delete_production_record(record_id)
                                
                                if success:
                                    # 필터링된 레코드에서 삭제
                                    st.session_state['production_filtered_records'] = [
                                        r for r in st.session_state['production_filtered_records'] 
                                        if r.get('id') != record_id
                                    ]
                                    
                                    # 모든 레코드에서 삭제
                                    st.session_state.production_data = [
                                        r for r in st.session_state.production_data 
                                        if r.get('id') != record_id
                                    ]
                                    
                                    st.success("실적 데이터가 성공적으로 삭제되었습니다.")
                                    
                                    # 세션 상태 초기화
                                    st.session_state.pop('delete_confirmation', None)
                                    st.session_state.pop('selected_production_record', None)
                                    
                                    # DataFrame 업데이트
                                    if len(st.session_state['production_filtered_records']) > 0:
                                        st.session_state['production_filtered_df'] = pd.DataFrame(st.session_state['production_filtered_records'])
                                    else:
                                        st.session_state.pop('production_filtered_df', None)
                                        st.session_state.pop('production_filtered_records', None)
                                    
                                    st.experimental_rerun()
                                else:
                                    st.error("데이터 삭제 중 오류가 발생했습니다.")
                            except Exception as e:
                                st.error(f"데이터 삭제 중 오류가 발생했습니다: {str(e)}")
                                import traceback
                                print(f"[ERROR] 상세 오류: {traceback.format_exc()}")
                except Exception as e:
                    st.error(f"데이터 표시 중 오류가 발생했습니다: {str(e)}")
                    import traceback
                    print(f"[ERROR] 상세 오류: {traceback.format_exc()}")
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
    
    # LocalStorage 대신 Supabase DB 데이터 사용
    if 'production_data' not in st.session_state or st.session_state.production_data is None:
        st.session_state.production_data = load_production_data()
    
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
        # records = storage.load_production_records()  # 이전 코드
        records = st.session_state.production_data  # Supabase에서 가져온 데이터 사용
        
        # 로그 추가 - 콘솔에만 출력하도록 변경
        print(f"[DEBUG] 전체 레코드 수: {len(records)}개")
        if len(records) > 0:
            print(f"[DEBUG] 데이터 샘플: {records[0]}")
            print(f"[DEBUG] 필드명: {list(records[0].keys())}")
        
        # 날짜 변환
        str_start_date = start_date.strftime("%Y-%m-%d")
        str_end_date = end_date.strftime("%Y-%m-%d")
        
        # 필터링 로직 개선 - 다양한 필드명에 대응
        filtered_records = []
        date_field = None
        worker_field = None
        model_field = None
        line_field = None
        
        # 필드명 자동 감지
        if len(records) > 0:
            fields = list(records[0].keys())
            for field in fields:
                if '날짜' in field or 'date' in field.lower():
                    date_field = field
                if '작업자' in field or 'worker' in field.lower():
                    worker_field = field
                if '모델' in field or 'model' in field.lower():
                    model_field = field
                if '라인' in field or 'line' in field.lower():
                    line_field = field
        
        if not date_field:
            date_field = 'date' if 'date' in records[0] else '날짜'
        if not worker_field:
            worker_field = 'worker' if 'worker' in records[0] else '작업자'
        if not model_field:
            model_field = 'model' if 'model' in records[0] else '모델차수'
        if not line_field:
            line_field = 'line_number' if 'line_number' in records[0] else '라인번호'
        
        # 로그 추가 - 콘솔에만 출력하도록 변경
        print(f"[DEBUG] 사용할 날짜 필드: {date_field}")
        print(f"[DEBUG] 사용할 작업자 필드: {worker_field}")
        print(f"[DEBUG] 사용할 모델 필드: {model_field}")
        print(f"[DEBUG] 사용할 라인 필드: {line_field}")
        
        for record in records:
            # 날짜 필드가 있는지 확인
            if date_field not in record:
                continue
                
            record_date = str(record.get(date_field, ''))
            
            # 날짜 필터링 - 포함 관계로 변경 (contains)
            if str_start_date in record_date or str_end_date in record_date or (
                str_start_date <= record_date <= str_end_date):
                
                # 검색어 필터링
                if not search_term:
                    filtered_records.append(record)
                else:
                    search_term_lower = search_term.lower()
                    if (worker_field in record and search_term_lower in str(record.get(worker_field, '')).lower()) or \
                       (model_field in record and search_term_lower in str(record.get(model_field, '')).lower()) or \
                       (line_field in record and search_term_lower in str(record.get(line_field, '')).lower()):
                        filtered_records.append(record)
        
        print(f"[DEBUG] 필터링된 레코드 수: {len(filtered_records)}개")
        
        if not filtered_records:
            st.warning("조건에 맞는 데이터가 없습니다.")
            return
        
        # 필터링된 DataFrame 생성 - 필드명 수정
        filtered_df = pd.DataFrame(filtered_records)
        
        # 필드명 맵핑 (필요한 경우)
        column_mapping = {}
        if date_field != '생산일자':
            column_mapping[date_field] = '생산일자'
        if worker_field != '작업자':
            column_mapping[worker_field] = '작업자'
        if model_field != '모델명':
            column_mapping[model_field] = '모델명'
        if line_field != '라인':
            column_mapping[line_field] = '라인'
        
        # 필드명 변경
        if column_mapping:
            filtered_df = filtered_df.rename(columns=column_mapping)
        
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
        
        # 날짜, 작업자, 라인별 그룹핑 설정 - 필드명 확인 먼저 수행
        if '생산일자' in filtered_df.columns:
            gb.configure_column("생산일자", rowGroup=True, hide=False)
        if '작업자' in filtered_df.columns:
            gb.configure_column("작업자", rowGroup=True, hide=False)
        if '라인' in filtered_df.columns:
            gb.configure_column("라인", rowGroup=True, hide=False)
        
        # 집계 함수 설정 - 필드명 확인 먼저 수행
        if '목표수량' in filtered_df.columns:
            gb.configure_column("목표수량", aggFunc="sum", type=["numericColumn", "numberColumnFilter"])
        if '생산수량' in filtered_df.columns:
            gb.configure_column("생산수량", aggFunc="sum", type=["numericColumn", "numberColumnFilter"])
        if '불량수량' in filtered_df.columns:
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