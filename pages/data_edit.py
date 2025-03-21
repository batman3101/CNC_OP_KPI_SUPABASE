import streamlit as st
import pandas as pd
from datetime import datetime
import json

def show_data_edit():
    st.title("📝 데이터 수정")
    
    # 탭 생성
    tab1, tab2 = st.tabs(["모델 데이터", "데이터 동기화"])
    
    with tab1:
        st.subheader("모델 데이터 수정")
        
        # 모델 데이터 로드
        if 'models' not in st.session_state:
            st.session_state.models = st.session_state.db.get_all_models()
        
        if st.session_state.models:
            model_df = pd.DataFrame(st.session_state.models)
            
            # 데이터 표시 - 인덱스 숨김
            st.dataframe(
                model_df,
                use_container_width=True,
                hide_index=True
            )
            
            # 수정 기능
            st.subheader("모델 데이터 수정")
            
            # 수정할 모델 선택
            model_options = [m.get('모델명', '') for m in st.session_state.models]
            selected_model_name = st.selectbox(
                "수정할 모델 선택",
                options=model_options
            )
            
            # 선택된 모델 데이터
            selected_model_data = next((m for m in st.session_state.models if m.get('모델명') == selected_model_name), None)
            
            if selected_model_data:
                col1, col2 = st.columns(2)
                
                # 수정 폼
                with col1:
                    with st.form("edit_model_form"):
                        # 수정 필드
                        new_model_name = st.text_input("모델명", value=selected_model_data.get('모델명', ''))
                        new_process = st.text_input("공정", value=selected_model_data.get('공정', ''))
                        
                        # 저장 버튼
                        submit = st.form_submit_button("저장")
                        
                        if submit:
                            # 데이터 업데이트
                            st.session_state.db.update_model(
                                old_model=selected_model_data.get('모델명', ''),
                                new_model=new_model_name,
                                new_process=new_process
                            )
                            st.success("모델 데이터가 성공적으로 업데이트되었습니다.")
                            # 모델 데이터 다시 로드
                            st.session_state.models = st.session_state.db.get_all_models()
                            st.rerun()
                
                # 삭제 기능 추가
                with col2:
                    with st.form("delete_model_form"):
                        st.warning(f"'{selected_model_name}' 모델을 삭제하시겠습니까?")
                        delete_submit = st.form_submit_button("삭제", type="primary")
                        
                        if delete_submit:
                            # 데이터 삭제
                            success = st.session_state.db.delete_model(model_name=selected_model_name)
                            if success:
                                st.success(f"'{selected_model_name}' 모델이 성공적으로 삭제되었습니다.")
                                # 모델 데이터 다시 로드
                                st.session_state.models = st.session_state.db.get_all_models()
                                st.rerun()
                            else:
                                st.error(f"'{selected_model_name}' 모델 삭제 중 오류가 발생했습니다.")
        else:
            st.info("모델 데이터가 없습니다.")
    
    with tab2:
        st.subheader("데이터 동기화")
        
        # 데이터 동기화 옵션
        st.write("데이터를 외부 파일로 내보내거나 가져올 수 있습니다.")
        
        col1, col2 = st.columns(2)
        
        # 데이터 내보내기
        with col1:
            st.write("##### 데이터 내보내기")
            
            export_type = st.radio(
                "내보낼 데이터 유형",
                options=["생산 실적", "모델 데이터", "모든 데이터"]
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
                options=["생산 실적", "모델 데이터", "모든 데이터"]
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
                        
                        st.rerun()
                
                except Exception as e:
                    st.error(f"데이터 가져오기 중 오류 발생: {str(e)}")
                    
        # 데이터 초기화 섹션
        st.write("---")
        st.subheader("데이터 초기화")
        st.warning("⚠️ 초기화 기능은 데이터를 영구적으로 삭제할 수 있습니다. 신중하게 사용하세요.")
        
        reset_type = st.selectbox(
            "초기화할 데이터 유형",
            options=["생산 실적", "모델 데이터"]
        )
        
        confirm_text = st.text_input("초기화하려면 'RESET'을 입력하세요", value="")
        
        if st.button("데이터 초기화", key="reset_btn", disabled=(confirm_text != "RESET")):
            try:
                if reset_type == "생산 실적":
                    # TODO: 생산 실적 데이터 초기화 로직 구현
                    st.error("현재 이 기능은 지원되지 않습니다. Supabase 콘솔에서 직접 테이블을 초기화해주세요.")
                elif reset_type == "모델 데이터":
                    # TODO: 모델 데이터 초기화 로직 구현
                    st.error("현재 이 기능은 지원되지 않습니다. Supabase 콘솔에서 직접 테이블을 초기화해주세요.")
            except Exception as e:
                st.error(f"데이터 초기화 중 오류 발생: {str(e)}") 