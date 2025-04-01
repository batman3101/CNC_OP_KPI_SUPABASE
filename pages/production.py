import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import sys
import uuid
from utils.supabase_db import SupabaseDB
from utils.local_storage import LocalStorage
import utils.common as common

# 프로젝트 루트 디렉토리를 path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

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
    with st.form("수정_필터_조건", clear_on_submit=False):
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
                if 'production_data' not in st.session_state or st.session_state.production_data is None:
                    st.session_state.production_data = load_production_data()
                
                records = st.session_state.production_data or []
                for record in records:
                    record_date = str(record.get('날짜', ''))
                    if str_start_date <= record_date <= str_end_date:
                        if not search_worker or search_worker.lower() in str(record.get('작업자', '')).lower():
                            filtered_records.append(record)
                
                st.session_state['filtered_records'] = filtered_records
            else:
                if 'filtered_records' in st.session_state:
                    filtered_records = st.session_state['filtered_records'] or []
            
            # 필터링 결과 표시
            record_count = len(filtered_records) if filtered_records is not None else 0
            if record_count == 0:
                st.warning("조건에 맞는 데이터가 없습니다.")
                return
            
            st.markdown("---")
            st.markdown("### 📝 데이터 수정/삭제")
            st.info(f"총 {record_count}개의 데이터가 검색되었습니다. 수정할 데이터를 선택하세요.")
            
            # DataFrame 생성 및 표시 (AgGrid 대신)
            df = pd.DataFrame(filtered_records)
            
            if df.empty:
                st.warning("표시할 데이터가 없습니다.")
                return
                
            # 페이지네이션 설정
            if 'edit_page_number' not in st.session_state:
                st.session_state.edit_page_number = 1
            page_size = 10
            
            # 페이지네이션된 데이터프레임 가져오기
            paginated_df, total_pages = paginate_dataframe(df, page_size, st.session_state.edit_page_number)
            
            # 테이블 표시
            st.dataframe(paginated_df, use_container_width=True)
            
            # 페이지네이션 UI
            col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
            with col1:
                if st.button("◀️ 이전", disabled=st.session_state.edit_page_number <= 1):
                    st.session_state.edit_page_number -= 1
                    st.experimental_rerun()
            with col2:
                if st.button("다음 ▶️", disabled=st.session_state.edit_page_number >= total_pages):
                    st.session_state.edit_page_number += 1
                    st.experimental_rerun()
            with col3:
                st.write(f"페이지: {st.session_state.edit_page_number}/{total_pages}")
            with col4:
                new_page = st.number_input("페이지 이동", min_value=1, max_value=total_pages, value=st.session_state.edit_page_number, step=1)
                if new_page != st.session_state.edit_page_number:
                    st.session_state.edit_page_number = new_page
                    st.experimental_rerun()
            
            # 데이터 선택 기능
            st.markdown("### 🔍 데이터 선택")
            selected_index = st.selectbox(
                "수정할 데이터를 선택하세요",
                options=paginated_df.index.tolist(),
                format_func=lambda x: f"{paginated_df.loc[x, '날짜']} - {paginated_df.loc[x, '작업자']} - {paginated_df.loc[x, '모델차수']} (목표: {paginated_df.loc[x, '목표수량']}, 생산: {paginated_df.loc[x, '생산수량']})"
            )
            
            if selected_index is not None:
                selected_row = df.loc[selected_index].to_dict()
                
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
                                if 'production_data' in st.session_state:
                                    del st.session_state['production_data']
                                if 'filtered_records' in st.session_state:
                                    del st.session_state['filtered_records']
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
                                    if 'production_data' in st.session_state:
                                        del st.session_state['production_data']
                                    if 'filtered_records' in st.session_state:
                                        del st.session_state['filtered_records']
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
    
    try:
        # 항상 최신 데이터 로드
        if 'production_data' not in st.session_state or st.session_state.production_data is None:
            st.session_state.production_data = load_production_data()
        
        # 필터 UI
        st.markdown("### 🔍 데이터 검색")
        with st.form("조회_필터_조건", clear_on_submit=False):
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
        
        # 필터링 (안전하게 처리)
        if not hasattr(st.session_state, 'production_data') or st.session_state.production_data is None:
            st.session_state.production_data = load_production_data()
        
        records = st.session_state.production_data or []
        filtered_records = []
        
        # 필터 적용 여부에 따라 처리
        if filter_submitted:
            str_start_date = start_date.strftime("%Y-%m-%d")
            str_end_date = end_date.strftime("%Y-%m-%d")
            
            filter_key = f"{str_start_date}_{str_end_date}_{search_worker}"
            st.session_state['filtered_key'] = filter_key
            
            # 데이터 필터링
            if records:
                for record in records:
                    record_date = str(record.get('날짜', ''))
                    if str_start_date <= record_date <= str_end_date:
                        if not search_worker or search_worker.lower() in str(record.get('작업자', '')).lower():
                            filtered_records.append(record)
            
            st.session_state['filtered_records'] = filtered_records
        elif 'filtered_key' in st.session_state and 'filtered_records' in st.session_state:
            filtered_records = st.session_state['filtered_records'] or []
        else:
            # 필터 미적용 시 모든 데이터 표시
            filtered_records = records
        
        # 결과 표시
        record_count = len(filtered_records) if filtered_records is not None else 0
        if record_count == 0:
            st.warning("조건에 맞는 데이터가 없습니다.")
            return
        
        st.info(f"총 {record_count}개의 데이터가 검색되었습니다.")
        
        # DataFrame 생성 및 표시
        df = pd.DataFrame(filtered_records)
        
        if df.empty:
            st.warning("표시할 데이터가 없습니다.")
            return
        
        # 페이지네이션 설정
        if 'view_page_number' not in st.session_state:
            st.session_state.view_page_number = 1
        page_size = 10
        
        # 페이지네이션된 데이터프레임 가져오기
        paginated_df, total_pages = paginate_dataframe(df, page_size, st.session_state.view_page_number)
        
        # 테이블 표시
        st.dataframe(paginated_df, use_container_width=True)
        
        # 페이지네이션 UI
        col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
        with col1:
            if st.button("◀️ 이전", key="view_prev", disabled=st.session_state.view_page_number <= 1):
                st.session_state.view_page_number -= 1
                st.experimental_rerun()
        with col2:
            if st.button("다음 ▶️", key="view_next", disabled=st.session_state.view_page_number >= total_pages):
                st.session_state.view_page_number += 1
                st.experimental_rerun()
        with col3:
            st.write(f"페이지: {st.session_state.view_page_number}/{total_pages}")
        with col4:
            new_page = st.number_input("페이지 이동", min_value=1, max_value=total_pages, value=st.session_state.view_page_number, step=1, key="view_page_input")
            if new_page != st.session_state.view_page_number:
                st.session_state.view_page_number = new_page
                st.experimental_rerun()
        
        # 통계 계산 및 표시
        if not df.empty and '목표수량' in df.columns and '생산수량' in df.columns:
            try:
                st.markdown("### 📊 통계")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_target = df['목표수량'].sum()
                    st.metric("총 목표수량", f"{total_target:,}")
                
                with col2:
                    total_production = df['생산수량'].sum()
                    st.metric("총 생산수량", f"{total_production:,}")
                
                with col3:
                    if total_target > 0:
                        achievement_rate = (total_production / total_target) * 100
                        st.metric("달성률", f"{achievement_rate:.1f}%")
            except Exception as e:
                st.warning(f"통계 계산 중 오류가 발생했습니다: {str(e)}")
        
        # 선택된 데이터 상세 정보
        st.markdown("### 🔍 데이터 선택")
        selected_index = st.selectbox(
            "상세 정보를 볼 데이터를 선택하세요",
            options=paginated_df.index.tolist(),
            format_func=lambda x: f"{paginated_df.loc[x, '날짜']} - {paginated_df.loc[x, '작업자']} - {paginated_df.loc[x, '모델차수']} (목표: {paginated_df.loc[x, '목표수량']}, 생산: {paginated_df.loc[x, '생산수량']})"
        )
        
        if selected_index is not None:
            with st.expander("📄 선택한 데이터 상세 정보", expanded=True):
                st.json(df.loc[selected_index].to_dict())
    
    except Exception as e:
        st.error(f"데이터 처리 중 오류가 발생했습니다: {str(e)}")
        import traceback
        print(f"[ERROR] 상세 오류: {traceback.format_exc()}")

if __name__ == "__main__":
    show_production_management() 