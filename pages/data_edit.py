import streamlit as st
import pandas as pd
from datetime import datetime
import json

def show_data_edit():
    st.title("📝 데이터 수정")
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["생산 실적 데이터", "작업자 데이터", "데이터 동기화"])
    
    with tab1:
        st.subheader("생산 실적 데이터 수정")
        
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
                    worker_options = [w.get('이름', '') for w in st.session_state.worker_data]
                
                # 작업자 선택
                selected_worker = st.selectbox(
                    "작업자",
                    options=["전체"] + sorted(worker_options)
                )
            
            with filter_col2:
                # 라인 선택
                line_options = ["전체"] + sorted(df['라인번호'].unique().tolist())
                selected_line = st.selectbox("라인", options=line_options)
            
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
                selected_row = st.selectbox("수정할 행 선택", options=row_indices, format_func=lambda i: f"{filtered_df.iloc[i]['날짜']} - {filtered_df.iloc[i]['작업자']} - {filtered_df.iloc[i]['라인번호']}")
                
                # 선택된 행 데이터
                row_data = filtered_df.iloc[selected_row].to_dict()
                
                # 수정 폼
                with st.form("edit_form"):
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
                        st.session_state.db.update_production_record(
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
                        st.success("데이터가 성공적으로 업데이트되었습니다.")
                        st.rerun()
                
                # 데이터 삭제 기능 추가
                with st.form("delete_form"):
                    st.warning(f"선택한 생산 데이터를 삭제하시겠습니까?")
                    delete_button = st.form_submit_button("데이터 삭제", type="primary")
                    
                    if delete_button:
                        # 데이터 삭제
                        success = st.session_state.db.delete_production_record(
                            record_id=row_data.get('STT', row_data.get('id', ''))
                        )
                        if success:
                            st.success("데이터가 성공적으로 삭제되었습니다.")
                            st.rerun()
                        else:
                            st.error("데이터 삭제 중 오류가 발생했습니다.")
        else:
            st.info(f"선택한 기간의 생산 실적이 없습니다.")
    
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
                        width="medium"
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
                col1, col2 = st.columns(2)
                
                # 수정 폼
                with col1:
                    with st.form("edit_worker_form"):
                        # 수정 필드
                        new_name = st.text_input("이름", value=selected_worker_data.get('이름', ''))
                        new_id = st.text_input("사번", value=selected_worker_data.get('사번', ''))
                        new_dept = st.text_input("부서", value=selected_worker_data.get('부서', 'CNC'))
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
                with col2:
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
    
    with tab3:
        st.subheader("데이터 동기화")
        
        # 데이터 동기화 옵션
        st.write("데이터를 외부 파일로 내보내거나 가져올 수 있습니다.")
        
        col1, col2 = st.columns(2)
        
        # 데이터 내보내기
        with col1:
            st.write("##### 데이터 내보내기")
            
            export_type = st.radio(
                "내보낼 데이터 유형",
                options=["생산 실적", "작업자 데이터", "모델 데이터", "모든 데이터"]
            )
            
            if st.button("데이터 내보내기", key="export_btn"):
                try:
                    export_data = {}
                    
                    if export_type == "생산 실적" or export_type == "모든 데이터":
                        # 생산 실적 데이터 가져오기
                        production_data = st.session_state.db.get_production_records(
                            start_date="2000-01-01",
                            end_date="2100-12-31"
                        )
                        export_data["production"] = production_data
                        
                    if export_type == "작업자 데이터" or export_type == "모든 데이터":
                        # 작업자 데이터 가져오기
                        worker_data = st.session_state.db.get_workers()
                        export_data["workers"] = worker_data
                        
                    if export_type == "모델 데이터" or export_type == "모든 데이터":
                        # 모델 데이터 가져오기
                        model_data = st.session_state.db.get_all_models()
                        export_data["models"] = model_data
                    
                    # 데이터를 JSON으로 변환
                    json_data = json.dumps(export_data, ensure_ascii=False, indent=2)
                    
                    # 다운로드 링크 생성
                    st.download_button(
                        label="JSON 파일 다운로드",
                        data=json_data,
                        file_name=f"data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                    
                    st.success("데이터가 성공적으로 추출되었습니다. 다운로드 버튼을 눌러 저장하세요.")
                except Exception as e:
                    st.error(f"데이터 내보내기 중 오류 발생: {str(e)}")
        
        # 데이터 가져오기
        with col2:
            st.write("##### 데이터 가져오기")
            
            import_type = st.radio(
                "가져올 데이터 유형",
                options=["생산 실적", "작업자 데이터", "모델 데이터", "모든 데이터"]
            )
            
            uploaded_file = st.file_uploader("JSON 파일 업로드", type=["json"])
            
            if uploaded_file is not None:
                try:
                    # JSON 파일 로드
                    import_data = json.load(uploaded_file)
                    
                    if st.button("데이터 가져오기", key="import_btn"):
                        success_count = 0
                        error_count = 0
                        
                        # 생산 실적 가져오기
                        if (import_type == "생산 실적" or import_type == "모든 데이터") and "production" in import_data:
                            for record in import_data["production"]:
                                try:
                                    st.session_state.db.add_production_record(
                                        date=record.get("날짜", ""),
                                        worker=record.get("작업자", ""),
                                        line_number=record.get("라인번호", ""),
                                        model=record.get("모델차수", ""),
                                        target_quantity=record.get("목표수량", 0),
                                        production_quantity=record.get("생산수량", 0),
                                        defect_quantity=record.get("불량수량", 0),
                                        note=record.get("특이사항", "")
                                    )
                                    success_count += 1
                                except Exception as e:
                                    error_count += 1
                        
                        # 작업자 데이터 가져오기
                        if (import_type == "작업자 데이터" or import_type == "모든 데이터") and "workers" in import_data:
                            for worker in import_data["workers"]:
                                try:
                                    st.session_state.db.add_worker(
                                        employee_id=worker.get("사번", ""),
                                        name=worker.get("이름", ""),
                                        department=worker.get("부서", "CNC"),
                                        line_number=worker.get("라인번호", "")
                                    )
                                    success_count += 1
                                except Exception as e:
                                    error_count += 1
                        
                        # 모델 데이터 가져오기
                        if (import_type == "모델 데이터" or import_type == "모든 데이터") and "models" in import_data:
                            for model in import_data["models"]:
                                try:
                                    st.session_state.db.add_model(
                                        model_name=model.get("모델명", ""),
                                        process=model.get("공정", "")
                                    )
                                    success_count += 1
                                except Exception as e:
                                    error_count += 1
                        
                        # 결과 표시
                        if success_count > 0:
                            st.success(f"{success_count}개 항목을 성공적으로 가져왔습니다.")
                        if error_count > 0:
                            st.warning(f"{error_count}개 항목을 가져오지 못했습니다.")
                        
                        # 세션 상태 갱신
                        st.session_state.worker_data = st.session_state.db.get_workers()
                        st.rerun()
                
                except Exception as e:
                    st.error(f"데이터 가져오기 중 오류 발생: {str(e)}")
                    
        # 데이터 초기화 섹션
        st.write("---")
        st.subheader("데이터 초기화")
        st.warning("⚠️ 초기화 기능은 데이터를 영구적으로 삭제할 수 있습니다. 신중하게 사용하세요.")
        
        reset_type = st.selectbox(
            "초기화할 데이터 유형",
            options=["생산 실적", "작업자 데이터", "모델 데이터"]
        )
        
        confirm_text = st.text_input("초기화하려면 'RESET'을 입력하세요", value="")
        
        if st.button("데이터 초기화", key="reset_btn", disabled=(confirm_text != "RESET")):
            try:
                if reset_type == "생산 실적":
                    # TODO: 생산 실적 데이터 초기화 로직 구현
                    st.error("현재 이 기능은 지원되지 않습니다. Supabase 콘솔에서 직접 테이블을 초기화해주세요.")
                elif reset_type == "작업자 데이터":
                    # TODO: 작업자 데이터 초기화 로직 구현
                    st.error("현재 이 기능은 지원되지 않습니다. Supabase 콘솔에서 직접 테이블을 초기화해주세요.")
                elif reset_type == "모델 데이터":
                    # TODO: 모델 데이터 초기화 로직 구현
                    st.error("현재 이 기능은 지원되지 않습니다. Supabase 콘솔에서 직접 테이블을 초기화해주세요.")
            except Exception as e:
                st.error(f"데이터 초기화 중 오류 발생: {str(e)}") 