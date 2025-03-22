# 데이터 관리 페이지 - StreamlitDuplicateElementId 오류 수정
# 마지막 업데이트: 2024-08-02
import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import json

# config_local.py가 있으면 관리자 계정 정보 로드, 없으면 기본값 사용
try:
    from config_local import ADMIN_EMAIL
except ImportError:
    ADMIN_EMAIL = "admin@example.com"  # 기본값

# 환경 변수 로드
load_dotenv()

def show_data_sync():
    st.title("📊 데이터 관리")
    
    # 로그인 확인
    if 'username' not in st.session_state or st.session_state.username is None:
        st.error("로그인이 필요합니다.")
        return
    
    # 관리자 권한 확인을 위한 로그 출력
    print(f"[DEBUG] 데이터 관리 페이지 접근: 사용자 이메일={st.session_state.get('user_email', '없음')}, 권한={st.session_state.get('user_role', '없음')}")
    print(f"[DEBUG] 지정된 admin 이메일: {ADMIN_EMAIL}")
    
    # 관리자 권한 확인 (지정된 admin 계정은 항상 접근 허용)
    user_email = st.session_state.get('user_email', '').strip().lower()
    admin_email = ADMIN_EMAIL.strip().lower()
    is_admin = (st.session_state.user_role == '관리자' or user_email == admin_email)
    
    if not is_admin:
        st.error("관리자 권한이 필요합니다.")
        st.write("현재 로그인: ", st.session_state.get('username', '알 수 없음'))
        st.write("권한: ", st.session_state.get('user_role', '알 수 없음'))
        return
        
    # 권한 확인 완료 로그
    print(f"[INFO] 데이터 관리 페이지 접근 권한 확인 완료: {st.session_state.get('username', '알 수 없음')}")
    
    # 세션 상태 초기화
    if 'sync_options_app' not in st.session_state:
        st.session_state.sync_options_app = ["작업자 데이터", "생산 실적 데이터"]
        
    if 'sync_options_db' not in st.session_state:
        st.session_state.sync_options_db = ["작업자 데이터", "생산 실적 데이터"]
    
    tab1, tab2 = st.tabs(["데이터 동기화", "Supabase 설정"])
    
    # 데이터 동기화 탭
    with tab1:
        st.subheader("데이터 동기화")
        
        st.info("앱 데이터와 Supabase 데이터베이스 간 양방향 동기화를 수행할 수 있습니다.")
        
        col1, col2 = st.columns(2)
        
        # 앱 -> Supabase 동기화
        with col1:
            st.write("### 앱 -> Supabase 동기화")
            st.write("앱의 데이터를 Supabase 데이터베이스로 내보냅니다.")
            
            # 동기화 대상 선택
            st.session_state.sync_options_app = st.multiselect(
                "동기화할 데이터 선택",
                options=["작업자 데이터", "생산 실적 데이터", "사용자 데이터", "모델 데이터"],
                default=st.session_state.sync_options_app,
                key="app_to_supabase_options_1"
            )
            
            if st.button("앱 -> Supabase 동기화", key="app_to_supabase_btn_1"):
                with st.spinner("데이터를 동기화 중입니다..."):
                    sync_results = []
                    
                    try:
                        db = st.session_state.db
                        
                        # 작업자 데이터 동기화
                        if "작업자 데이터" in st.session_state.sync_options_app:
                            if 'workers' in st.session_state and st.session_state.workers:
                                for worker in st.session_state.workers:
                                    db.add_worker(
                                        employee_id=worker.get("사번", ""),
                                        name=worker.get("이름", ""),
                                        department=worker.get("부서", "CNC"),
                                        line_number=worker.get("라인번호", "")
                                    )
                                sync_results.append("✅ 작업자 데이터 동기화 완료")
                            else:
                                sync_results.append("⚠️ 동기화할 작업자 데이터가 없습니다")
                        
                        # 생산 실적 데이터 동기화
                        if "생산 실적 데이터" in st.session_state.sync_options_app:
                            if 'production_data' in st.session_state and st.session_state.production_data:
                                for record in st.session_state.production_data:
                                    db.add_production_record(
                                        date=record.get("날짜", datetime.now().strftime("%Y-%m-%d")),
                                        worker=record.get("작업자", ""),
                                        line_number=record.get("라인번호", ""),
                                        model=record.get("모델차수", ""),
                                        target_quantity=record.get("목표수량", 0),
                                        production_quantity=record.get("생산수량", 0),
                                        defect_quantity=record.get("불량수량", 0),
                                        note=record.get("특이사항", "")
                                    )
                                sync_results.append("✅ 생산 실적 데이터 동기화 완료")
                            else:
                                sync_results.append("⚠️ 동기화할 생산 실적 데이터가 없습니다")
                        
                        # 사용자 데이터 동기화
                        if "사용자 데이터" in st.session_state.sync_options_app:
                            if 'users' in st.session_state and st.session_state.users:
                                for user in st.session_state.users:
                                    db.add_user(
                                        email=user.get("이메일", ""),
                                        password=user.get("비밀번호", ""),
                                        name=user.get("이름", ""),
                                        role=user.get("권한", "user")
                                    )
                                sync_results.append("✅ 사용자 데이터 동기화 완료")
                            else:
                                sync_results.append("⚠️ 동기화할 사용자 데이터가 없습니다")
                        
                        # 모델 데이터 동기화
                        if "모델 데이터" in st.session_state.sync_options_app:
                            if 'models' in st.session_state and st.session_state.models:
                                for model in st.session_state.models:
                                    db.add_model(
                                        model_name=model.get("모델명", ""),
                                        process=model.get("공정", "")
                                    )
                                sync_results.append("✅ 모델 데이터 동기화 완료")
                            else:
                                sync_results.append("⚠️ 동기화할 모델 데이터가 없습니다")
                        
                        st.success("데이터 동기화가 완료되었습니다!")
                        for result in sync_results:
                            st.write(result)
                            
                    except Exception as e:
                        st.error(f"데이터 동기화 중 오류가 발생했습니다: {str(e)}")
        
        # Supabase -> 앱 동기화
        with col2:
            st.write("### Supabase -> 앱 동기화")
            st.write("Supabase 데이터베이스의 데이터를 앱으로 가져옵니다.")
            
            # 동기화 대상 선택
            st.session_state.sync_options_db = st.multiselect(
                "동기화할 데이터 선택",
                options=["작업자 데이터", "생산 실적 데이터", "사용자 데이터", "모델 데이터"],
                default=st.session_state.sync_options_db,
                key="supabase_to_app_options_1"
            )
            
            if st.button("Supabase -> 앱 동기화", key="supabase_to_app_btn_1"):
                with st.spinner("데이터를 동기화 중입니다..."):
                    sync_results = []
                    
                    try:
                        db = st.session_state.db
                        
                        # 작업자 데이터 가져오기
                        if "작업자 데이터" in st.session_state.sync_options_db:
                            from pages.worker_management import load_worker_data
                            st.session_state.workers = load_worker_data()
                            sync_results.append(f"✅ 작업자 데이터 {len(st.session_state.workers)}개 로드 완료")
                        
                        # 생산 실적 데이터 가져오기
                        if "생산 실적 데이터" in st.session_state.sync_options_db:
                            from pages.production import load_production_data
                            st.session_state.production_data = load_production_data()
                            sync_results.append(f"✅ 생산 실적 데이터 {len(st.session_state.production_data)}개 로드 완료")
                        
                        # 사용자 데이터 가져오기
                        if "사용자 데이터" in st.session_state.sync_options_db:
                            st.session_state.users = db.get_all_users()
                            sync_results.append(f"✅ 사용자 데이터 {len(st.session_state.users)}개 로드 완료")
                        
                        # 모델 데이터 가져오기
                        if "모델 데이터" in st.session_state.sync_options_db:
                            from pages.model_management import load_model_data
                            st.session_state.models = load_model_data()
                            sync_results.append(f"✅ 모델 데이터 {len(st.session_state.models)}개 로드 완료")
                        
                        st.success("데이터 동기화가 완료되었습니다!")
                        for result in sync_results:
                            st.write(result)
                        
                    except Exception as e:
                        st.error(f"데이터 동기화 중 오류가 발생했습니다: {str(e)}")
        
        # 데이터 백업 및 복원
        st.write("### 데이터 백업 및 복원")
        col1, col2 = st.columns(2)
        
        # 데이터 백업
        with col1:
            st.write("데이터 백업")
            if st.button("JSON 파일로 백업", key="backup_to_json_btn_1"):
                # 세션 상태의 데이터 수집
                backup_data = {
                    "workers": st.session_state.get("workers", []),
                    "production_data": st.session_state.get("production_data", []),
                    "models": st.session_state.get("models", []),
                    "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # JSON 문자열로 변환
                json_data = json.dumps(backup_data, ensure_ascii=False, indent=2)
                
                # 다운로드 링크 생성
                st.download_button(
                    label="백업 파일 다운로드",
                    data=json_data,
                    file_name=f"data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="download_backup_btn_1"
                )
                
                st.success("데이터가 성공적으로 백업되었습니다.")
        
        # 데이터 복원
        with col2:
            st.write("데이터 복원")
            uploaded_file = st.file_uploader("백업 파일 선택", type=["json"], key="backup_file_uploader_1")
            
            if uploaded_file is not None:
                if st.button("백업 파일에서 복원", key="restore_from_backup_btn_1"):
                    try:
                        # JSON 파일 로드
                        backup_data = json.loads(uploaded_file.getvalue().decode('utf-8'))
                        
                        # 데이터 복원
                        if "workers" in backup_data:
                            st.session_state.workers = backup_data["workers"]
                        
                        if "production_data" in backup_data:
                            st.session_state.production_data = backup_data["production_data"]
                        
                        if "models" in backup_data:
                            st.session_state.models = backup_data["models"]
                        
                        backup_time = backup_data.get("backup_time", "알 수 없음")
                        st.success(f"데이터가 성공적으로 복원되었습니다. (백업 시간: {backup_time})")
                    except Exception as e:
                        st.error(f"데이터 복원 중 오류가 발생했습니다: {str(e)}")
    
    # Supabase 설정 탭
    with tab2:
        st.subheader("Supabase 연결 설정")
        
        # 현재 설정된 Supabase URL과 Key 표시
        current_url = os.getenv("SUPABASE_URL", "")
        current_key = os.getenv("SUPABASE_KEY", "")
        
        if current_url and current_key:
            st.success("Supabase 연결이 설정되어 있습니다.")
            # 마스킹된 키 표시
            masked_key = current_key[:4] + "*" * (len(current_key) - 8) + current_key[-4:] if len(current_key) > 8 else "********"
            st.info(f"현재 URL: {current_url}")
            st.info(f"현재 API Key: {masked_key}")
            
            # 새로운 설정 입력 폼
            with st.expander("연결 설정 변경", expanded=False):
                with st.form("supabase_settings_form_1"):
                    st.write("Supabase 연결 정보 설정")
                    new_url = st.text_input("Supabase URL", value=current_url, key="supabase_url_input_1")
                    new_key = st.text_input("Supabase API Key", value=current_key, type="password", key="supabase_key_input_1")
                    
                    submitted = st.form_submit_button("설정 저장", key="save_settings_btn_1")
                    
                    if submitted:
                        try:
                            # .env 파일 생성 또는 업데이트
                            with open(".env", "w") as f:
                                f.write(f"SUPABASE_URL={new_url}\n")
                                f.write(f"SUPABASE_KEY={new_key}\n")
                            
                            # 환경 변수 다시 로드
                            load_dotenv(override=True)
                            
                            st.success("Supabase 연결 설정이 저장되었습니다.")
                            st.info("변경사항을 적용하려면 애플리케이션을 재시작해야 합니다.")
                        except Exception as e:
                            st.error(f"설정 저장 중 오류가 발생했습니다: {str(e)}")
        else:
            st.warning("Supabase 연결 정보가 설정되어 있지 않습니다.")
            
            # 새로운 설정 입력 폼
            with st.form("supabase_settings_form_2"):
                st.write("Supabase 연결 정보 설정")
                new_url = st.text_input("Supabase URL", value=current_url, key="supabase_url_input_2")
                new_key = st.text_input("Supabase API Key", value=current_key, type="password", key="supabase_key_input_2")
                
                submitted = st.form_submit_button("설정 저장", key="save_settings_btn_2")
                
                if submitted:
                    try:
                        # .env 파일 생성 또는 업데이트
                        with open(".env", "w") as f:
                            f.write(f"SUPABASE_URL={new_url}\n")
                            f.write(f"SUPABASE_KEY={new_key}\n")
                        
                        # 환경 변수 다시 로드
                        load_dotenv(override=True)
                        
                        st.success("Supabase 연결 설정이 저장되었습니다.")
                        st.info("변경사항을 적용하려면 애플리케이션을 재시작해야 합니다.")
                    except Exception as e:
                        st.error(f"설정 저장 중 오류가 발생했습니다: {str(e)}")
        
        # Supabase 테이블 생성 안내
        st.subheader("Supabase 테이블 설정 안내")
        
        with st.expander("테이블 구조 안내", expanded=False):
            st.write("""
            Supabase 대시보드에서 다음 테이블을 생성해야 합니다:
            
            1. **Users 테이블**
               - `id`: 자동 생성 ID (primary key)
               - `이메일`: 이메일 (unique)
               - `비밀번호`: 비밀번호
               - `이름`: 이름
               - `권한`: 권한
            
            2. **Workers 테이블**
               - `id`: 자동 생성 ID (primary key)
               - `STT`: 순번
               - `사번`: 사번 (unique)
               - `이름`: 이름
               - `부서`: 부서
               - `라인번호`: 라인번호
            
            3. **Production 테이블**
               - `id`: 자동 생성 ID (primary key)
               - `날짜`: 날짜
               - `작업자`: 작업자
               - `라인번호`: 라인번호
               - `모델차수`: 모델차수
               - `목표수량`: 목표수량
               - `생산수량`: 생산수량
               - `불량수량`: 불량수량
               - `특이사항`: 특이사항
            
            4. **Model 테이블**
               - `id`: 자동 생성 ID (primary key)
               - `STT`: 순번
               - `MODEL`: 모델명
               - `PROCESS`: 공정
            """)
            
            # SQL 스크립트 제공
            with st.expander("테이블 생성 SQL 스크립트", key="table_sql_expander_1"):
                st.code("""
    -- Users 테이블 생성
    CREATE TABLE Users (
      id SERIAL PRIMARY KEY,
      이메일 VARCHAR(255) UNIQUE NOT NULL,
      비밀번호 VARCHAR(255) NOT NULL,
      이름 VARCHAR(255) NOT NULL,
      권한 VARCHAR(50) NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Workers 테이블 생성
    CREATE TABLE Workers (
      id SERIAL PRIMARY KEY,
      STT INT4,
      사번 VARCHAR(50) UNIQUE NOT NULL,
      이름 VARCHAR(255) NOT NULL,
      부서 VARCHAR(100) DEFAULT 'CNC',
      라인번호 VARCHAR(50),
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Production 테이블 생성
    CREATE TABLE Production (
      id SERIAL PRIMARY KEY,
      날짜 DATE NOT NULL,
      작업자 VARCHAR(255) NOT NULL,
      라인번호 VARCHAR(50),
      모델차수 VARCHAR(255),
      목표수량 INTEGER DEFAULT 0,
      생산수량 INTEGER DEFAULT 0,
      불량수량 INTEGER DEFAULT 0,
      특이사항 TEXT,
      worker_id UUID REFERENCES Workers(id),
      model_process_id UUID REFERENCES Model(id),
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Model 테이블 생성
    CREATE TABLE Model (
      id SERIAL PRIMARY KEY,
      STT NUMERIC,
      MODEL TEXT NOT NULL,
      PROCESS TEXT,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
                """, language="sql")
                
            st.info("위 SQL 스크립트를 Supabase의 SQL 편집기에서 실행하여 필요한 테이블을 생성할 수 있습니다.") 