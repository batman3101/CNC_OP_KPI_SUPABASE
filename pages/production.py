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
        db = SupabaseDB()
        
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
            # 수정할 실적 선택
            production_options = {
                f"{p['날짜']} - {p['작업자']} ({p['모델차수']})": i 
                for i, p in enumerate(st.session_state.production_data)
            }
            
            selected_production = st.selectbox(
                "수정할 실적 선택",
                options=list(production_options.keys())
            )
            
            if selected_production:
                idx = production_options[selected_production]
                record = st.session_state.production_data[idx]
                
                # 수정 폼
                with st.form("production_edit_form"):
                    edit_date = st.date_input(
                        "날짜",
                        value=datetime.strptime(record["날짜"], "%Y-%m-%d")
                    )
                    
                    worker_options = [""] + [f"{w['이름']} ({w['사번']})" for w in st.session_state.workers]
                    edit_worker = st.selectbox(
                        "작업자",
                        options=worker_options,
                        index=worker_options.index(next(
                            w for w in worker_options if record["작업자"] in w
                        )) if record["작업자"] in str(worker_options) else 0
                    )
                    
                    line_options = [""] + sorted(list(set(w["라인번호"] for w in st.session_state.workers)))
                    edit_line = st.selectbox(
                        "라인번호",
                        options=line_options,
                        index=line_options.index(record["라인번호"]) if record["라인번호"] in line_options else 0
                    )
                    
                    model_options = [""] + [f"{m.get('모델명', '')} - {m.get('공정', '')}" for m in st.session_state.models]
                    edit_model = st.selectbox(
                        "모델차수",
                        options=model_options,
                        index=model_options.index(record["모델차수"]) if record["모델차수"] in model_options else 0
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        edit_target = st.number_input("목표수량", value=record["목표수량"])
                    with col2:
                        edit_prod = st.number_input("생산수량", value=record["생산수량"])
                    with col3:
                        edit_defect = st.number_input("불량수량", value=record["불량수량"])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("수정"):
                            worker_name = edit_worker.split(" (")[0] if edit_worker else ""
                            
                            updated_record = {
                                "id": record.get("id"),  # ID가 있는 경우 포함
                                "STT": record.get("STT", record.get("id")),  # STT 필드 추가
                                "날짜": edit_date.strftime("%Y-%m-%d"),
                                "작업자": worker_name,
                                "라인번호": edit_line,
                                "모델차수": edit_model,
                                "목표수량": int(edit_target),
                                "생산수량": int(edit_prod),
                                "불량수량": int(edit_defect),
                                "특이사항": record.get("특이사항", ""),
                                "수정시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            # 세션 상태 업데이트
                            st.session_state.production_data[idx].update(updated_record)
                            
                            # Supabase DB 업데이트
                            db = SupabaseDB()
                            if record.get("id") and db.update_production_record(record.get("id"), updated_record):
                                st.success("생산 실적이 수정되었습니다.")
                                st.rerun()
                            elif save_production_data(updated_record):  # ID가 없는 경우 새로 저장
                                st.success("생산 실적이 수정되었습니다.")
                                st.rerun()
                            else:
                                st.error("생산 실적 수정 중 오류가 발생했습니다.")
                
                # 삭제 버튼
                if st.button("삭제", key=f"delete_{idx}"):
                    # 세션 상태에서 삭제
                    deleted_record = st.session_state.production_data.pop(idx)
                    
                    # Supabase DB에서 삭제
                    db = SupabaseDB()
                    if deleted_record.get("id") and db.delete_production_record(deleted_record.get("id")):
                        st.success("생산 실적이 삭제되었습니다.")
                        st.rerun()
                    else:
                        st.error("생산 실적 삭제 중 오류가 발생했습니다.")
                        # 삭제 실패 시 세션 상태 복원
                        st.session_state.production_data.insert(idx, deleted_record)
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