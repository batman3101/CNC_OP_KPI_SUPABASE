import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from utils.supabase_db import SupabaseDB

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
        print(f"[DEBUG] 로드된 생산 데이터: {len(records)}개")
        
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
    
    tab1, tab2, tab3 = st.tabs(["실적 입력", "실적 수정", "실적 조회"])
    
    with tab1:
        st.subheader("생산 실적 입력")
        
        # 입력 폼
        with st.form("production_input_form"):
            # 날짜 선택
            date = st.date_input(
                "날짜",
                value=datetime.now()
            )
            
            # 작업자 선택
            worker_options = [""] + [f"{w['이름']} ({w['사번']})" for w in st.session_state.workers]
            selected_worker = st.selectbox(
                "작업자",
                options=worker_options
            )
            
            # 라인번호 선택 (드롭다운)
            line_options = [""] + sorted(list(set(w["라인번호"] for w in st.session_state.workers)))
            line_number = st.selectbox(
                "라인번호",
                options=line_options
            )
            
            # 모델 선택
            model_options = [""] + [f"{m.get('모델명', '')} - {m.get('공정', '')}" for m in st.session_state.models]
            model = st.selectbox(
                "모델차수",
                options=model_options
            )
            
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
            if not selected_worker:
                st.error("작업자를 선택해주세요.")
            elif not line_number:
                st.error("라인번호를 선택해주세요.")
            elif not model:
                st.error("모델을 선택해주세요.")
            else:
                # 작업자 이름만 추출 (사번 제외)
                worker_name = selected_worker.split(" (")[0] if selected_worker else ""
                
                record = {
                    "날짜": date.strftime("%Y-%m-%d"),
                    "작업자": worker_name,
                    "라인번호": line_number,
                    "모델차수": model,
                    "목표수량": int(target),
                    "생산수량": int(prod),
                    "불량수량": int(defect),
                    "등록시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                st.session_state.production_data.append(record)
                
                if save_production_data(record):
                    st.success("생산 실적이 저장되었습니다.")
                    # 세션 스테이트 갱신
                    st.session_state.production_data = load_production_data()
                    # 탭 전환을 위한 세션 상태 추가
                    st.session_state.active_tab = "실적 조회"
                    st.rerun()
    
    with tab2:
        st.subheader("생산 실적 수정/삭제")
        
        if st.session_state.production_data:
            # 날짜 선택기 개선
            col1, col2 = st.columns(2)
            with col1:
                selected_start_date = st.date_input(
                    "시작일",
                    datetime.now()
                )
            with col2:
                selected_end_date = st.date_input(
                    "종료일",
                    datetime.now()
                )
            
            # 데이터 조회
            records = st.session_state.db.get_production_records(
                start_date=selected_start_date.strftime('%Y-%m-%d'),
                end_date=selected_end_date.strftime('%Y-%m-%d')
            )
            
            if records:
                df = pd.DataFrame(records)
                
                # 필터링 옵션 추가
                filter_col1, filter_col2 = st.columns(2)
                
                with filter_col1:
                    # 작업자 데이터 로드
                    if 'worker_data' not in st.session_state:
                        # 작업자 데이터가 없는 경우 기본값 사용
                        worker_options = df['작업자'].unique().tolist()
                    else:
                        # 작업자 데이터가 있는 경우 해당 데이터 사용
                        worker_options = [w.get('이름', '') for w in st.session_state.workers]
                    
                    # 작업자 선택
                    selected_worker = st.selectbox(
                        "작업자",
                        options=["전체"] + sorted(worker_options),
                        key="edit_worker_select"
                    )
                
                with filter_col2:
                    # 라인 선택
                    line_options = ["전체"] + sorted(df['라인번호'].unique().tolist())
                    selected_line = st.selectbox("라인", options=line_options, key="edit_line_select")
                
                # 선택된 필터로 데이터 필터링
                filtered_df = df.copy()
                if selected_worker != "전체":
                    filtered_df = filtered_df[filtered_df['작업자'] == selected_worker]
                if selected_line != "전체":
                    filtered_df = filtered_df[filtered_df['라인번호'] == selected_line]
                
                # 데이터 표시 - 인덱스 숨김
                st.dataframe(filtered_df, use_container_width=True, hide_index=True)
                
                # 수정 기능
                st.subheader("데이터 수정")
                
                # 수정할 행 선택
                if not filtered_df.empty:
                    row_indices = list(range(len(filtered_df)))
                    selected_row = st.selectbox(
                        "수정할 행 선택", 
                        options=row_indices, 
                        format_func=lambda i: f"{filtered_df.iloc[i]['날짜']} - {filtered_df.iloc[i]['작업자']} - {filtered_df.iloc[i]['라인번호']}",
                        key="edit_row_select"
                    )
                    
                    # 선택된 행 데이터
                    row_data = filtered_df.iloc[selected_row].to_dict()
                    
                    # 수정 폼
                    with st.form("edit_production_form"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            new_target = st.number_input("목표수량", min_value=0, value=int(row_data.get('목표수량', 0)))
                        with col2:
                            new_production = st.number_input("생산수량", min_value=0, value=int(row_data.get('생산수량', 0)))
                        with col3:
                            new_defects = st.number_input("불량수량", min_value=0, value=int(row_data.get('불량수량', 0)))
                        
                        # 특이사항 필드 추가
                        new_note = st.text_area("특이사항", value=row_data.get('특이사항', ''))
                        
                        # 저장 버튼
                        submit = st.form_submit_button("저장")
                        
                        if submit:
                            # 데이터 업데이트
                            success = st.session_state.db.update_production_record(
                                record_id=row_data.get('STT', row_data.get('id', '')),
                                data={
                                    '날짜': row_data['날짜'],
                                    '작업자': row_data['작업자'],
                                    '라인번호': row_data['라인번호'],
                                    '모델차수': row_data.get('모델차수', ''),
                                    '목표수량': new_target,
                                    '생산수량': new_production,
                                    '불량수량': new_defects,
                                    '특이사항': new_note
                                }
                            )
                            if success:
                                st.success("데이터가 성공적으로 업데이트되었습니다.")
                                st.session_state.production_data = load_production_data()  # 데이터 새로고침
                                st.rerun()
                            else:
                                st.error("데이터 업데이트 중 오류가 발생했습니다.")
                    
                    # 데이터 삭제 기능 추가
                    with st.form("delete_production_form"):
                        st.warning(f"선택한 생산 데이터를 삭제하시겠습니까?")
                        delete_button = st.form_submit_button("데이터 삭제", type="primary")
                        
                        if delete_button:
                            # 데이터 삭제
                            success = st.session_state.db.delete_production_record(
                                record_id=row_data.get('STT', row_data.get('id', ''))
                            )
                            if success:
                                st.success("데이터가 성공적으로 삭제되었습니다.")
                                st.session_state.production_data = load_production_data()  # 데이터 새로고침
                                st.rerun()
                            else:
                                st.error("데이터 삭제 중 오류가 발생했습니다.")
                else:
                    st.info(f"선택한 조건에 맞는 생산 실적이 없습니다.")
            else:
                st.info(f"선택한 기간의 생산 실적이 없습니다.")
        else:
            st.info("수정할 생산 실적이 없습니다.")
    
    with tab3:
        # 활성 탭이 "실적 조회"인 경우 자동 선택
        if 'active_tab' in st.session_state and st.session_state.active_tab == "실적 조회":
            st.session_state.active_tab = None  # 상태 초기화
        
        st.subheader("등록된 생산 실적")
        
        if st.session_state.production_data:
            df = pd.DataFrame(st.session_state.production_data)
            st.dataframe(df, hide_index=True)
        else:
            st.info("등록된 생산 실적이 없습니다.")

if __name__ == "__main__":
    show_production_management() 