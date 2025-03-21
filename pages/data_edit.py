import streamlit as st
import pandas as pd
from datetime import datetime

def show_data_edit():
    st.title("데이터 수정")
    
    # 탭 생성
    tab1, tab2 = st.tabs(["생산 실적 데이터", "작업자 데이터"])
    
    with tab1:
        st.subheader("생산 실적 데이터 수정")
        
        # 날짜 선택
        selected_date = st.date_input(
            "시작일",
            datetime.now()
        )
        
        # 데이터 조회
        records = st.session_state.db.get_production_records(
            start_date=selected_date.strftime('%Y-%m-%d'),
            end_date=selected_date.strftime('%Y-%m-%d')
        )
        
        if records:
            df = pd.DataFrame(records)
            
            # 수정할 레코드 선택
            if 'worker_data' not in st.session_state:
                # 작업자 데이터가 없는 경우 기본값 사용
                worker_options = df['작업자'].unique().tolist()
            else:
                # 작업자 데이터가 있는 경우 해당 데이터 사용
                worker_options = [w.get('이름', '') for w in st.session_state.worker_data]
            
            # 작업자 선택
            selected_worker = st.selectbox(
                "작업자",
                options=["전체"] + sorted(worker_options)
            )
            
            # 선택된 작업자의 데이터만 필터링
            if selected_worker != "전체":
                filtered_df = df[df['작업자'] == selected_worker]
            else:
                filtered_df = df
            
            # 데이터 표시 - 인덱스 숨김
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
            
            # 수정 기능
            st.subheader("데이터 수정")
            
            # 수정할 행 선택
            if not filtered_df.empty:
                row_indices = list(range(len(filtered_df)))
                selected_row = st.selectbox("수정할 행 선택", options=row_indices, format_func=lambda i: f"{filtered_df.iloc[i]['날짜']} - {filtered_df.iloc[i]['작업자']} - {filtered_df.iloc[i]['라인번호']}")
                
                # 선택된 행 데이터
                row_data = filtered_df.iloc[selected_row].to_dict()
                
                # 수정 폼
                with st.form("edit_form"):
                    # 수정 필드
                    new_target = st.number_input("목표수량", min_value=0, value=int(row_data.get('목표수량', 0)))
                    new_production = st.number_input("생산수량", min_value=0, value=int(row_data.get('생산수량', 0)))
                    new_defects = st.number_input("불량수량", min_value=0, value=int(row_data.get('불량수량', 0)))
                    
                    # 저장 버튼
                    submit = st.form_submit_button("저장")
                    
                    if submit:
                        # 데이터 업데이트
                        st.session_state.db.update_production_record(
                            date=row_data['날짜'],
                            worker=row_data['작업자'],
                            line=row_data['라인번호'],
                            target=new_target,
                            production=new_production,
                            defects=new_defects
                        )
                        st.success("데이터가 성공적으로 업데이트되었습니다.")
                        st.rerun()
        else:
            st.info(f"{selected_date.strftime('%Y-%m-%d')} 날짜의 생산 실적이 없습니다.")
    
    with tab2:
        st.subheader("작업자 데이터 수정")
        
        # 작업자 데이터 로드
        if 'worker_data' not in st.session_state:
            st.session_state.worker_data = st.session_state.db.get_workers()
        
        if st.session_state.worker_data:
            worker_df = pd.DataFrame(st.session_state.worker_data)
            
            # 사번 컬럼이 있는 경우 문자열로 변환하여 콤마 제거
            if '사번' in worker_df.columns:
                worker_df['사번'] = worker_df['사번'].astype(str)
            
            # 데이터 표시 - 인덱스 숨김
            st.dataframe(
                worker_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "사번": st.column_config.TextColumn(
                        "사번",
                        help="작업자 사번",
                        width="medium",
                        # 숫자 포맷 지정 없음 (콤마 제거)
                    )
                }
            )
            
            # 수정 기능
            st.subheader("작업자 데이터 수정")
            
            # 수정할 작업자 선택
            worker_options = [w.get('이름', '') for w in st.session_state.worker_data]
            selected_worker_name = st.selectbox(
                "수정할 작업자 선택",
                options=worker_options
            )
            
            # 선택된 작업자 데이터
            selected_worker_data = next((w for w in st.session_state.worker_data if w.get('이름') == selected_worker_name), None)
            
            if selected_worker_data:
                # 수정 폼
                with st.form("edit_worker_form"):
                    # 수정 필드
                    new_name = st.text_input("이름", value=selected_worker_data.get('이름', ''))
                    new_id = st.text_input("사번", value=selected_worker_data.get('사번', ''))
                    new_line = st.text_input("라인번호", value=selected_worker_data.get('라인번호', ''))
                    
                    # 저장 버튼
                    submit = st.form_submit_button("저장")
                    
                    if submit:
                        # 데이터 업데이트
                        st.session_state.db.update_worker(
                            old_name=selected_worker_data.get('이름', ''),
                            new_name=new_name,
                            new_id=new_id,
                            new_line=new_line
                        )
                        st.success("작업자 데이터가 성공적으로 업데이트되었습니다.")
                        # 작업자 데이터 다시 로드
                        st.session_state.worker_data = st.session_state.db.get_workers()
                        st.rerun()
                
                # 삭제 기능 추가
                with st.form("delete_worker_form"):
                    st.warning(f"'{selected_worker_name}' 작업자를 삭제하시겠습니까?")
                    delete_submit = st.form_submit_button("삭제", type="primary")
                    
                    if delete_submit:
                        # 데이터 삭제
                        success = st.session_state.db.delete_worker(worker_name=selected_worker_name)
                        if success:
                            st.success(f"'{selected_worker_name}' 작업자가 성공적으로 삭제되었습니다.")
                            # 작업자 데이터 다시 로드
                            st.session_state.worker_data = st.session_state.db.get_workers()
                            st.rerun()
                        else:
                            st.error(f"'{selected_worker_name}' 작업자 삭제 중 오류가 발생했습니다.")
        else:
            st.info("작업자 데이터가 없습니다.") 