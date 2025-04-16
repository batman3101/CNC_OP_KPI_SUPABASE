# 데이터 관리 페이지 - StreamlitDuplicateElementId 오류 수정
# 마지막 업데이트: 2024-08-02
import streamlit as st
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import json
from utils.translations import translate

# 프로젝트 루트 디렉토리를 path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.local_storage import LocalStorage
from utils.supabase_db import SupabaseDB

# config_local.py가 있으면 관리자 계정 정보 로드, 없으면 기본값 사용
try:
    from config_local import ADMIN_EMAIL
except ImportError:
    ADMIN_EMAIL = "admin@example.com"  # 기본값

# 환경 변수 로드
load_dotenv()

def show_data_sync():
    st.title(translate("💾 데이터 관리"))
    
    # 로그인 확인
    if 'username' not in st.session_state or st.session_state.username is None:
        st.error(translate("로그인이 필요합니다."))
        return
    
    # 관리자 권한 확인을 위한 로그 출력
    print(f"[DEBUG] 데이터 관리 페이지 접근: 사용자 이메일={st.session_state.get('user_email', '없음')}, 권한={st.session_state.get('user_role', '없음')}")
    print(f"[DEBUG] 지정된 admin 이메일: {ADMIN_EMAIL}")
    
    # 관리자 권한 확인 (지정된 admin 계정은 항상 접근 허용)
    user_email = st.session_state.get('user_email', '').strip().lower()
    admin_email = ADMIN_EMAIL.strip().lower()
    is_admin = (st.session_state.user_role == '관리자' or user_email == admin_email)
    
    if not is_admin:
        st.error(translate("관리자 권한이 필요합니다."))
        st.write(translate("현재 로그인: "), st.session_state.get('username', translate('알 수 없음')))
        st.write(translate("권한: "), st.session_state.get('user_role', translate('알 수 없음')))
        return
        
    # 권한 확인 완료 로그
    print(f"[INFO] 데이터 관리 페이지 접근 권한 확인 완료: {st.session_state.get('username', '알 수 없음')}")
    
    # 세션 상태 초기화
    if 'sync_options_app' not in st.session_state:
        st.session_state.sync_options_app = [translate("작업자 데이터"), translate("생산 실적 데이터")]
        
    if 'sync_options_db' not in st.session_state:
        st.session_state.sync_options_db = [translate("작업자 데이터"), translate("생산 실적 데이터")]
    
    tab1, tab2, tab3 = st.tabs([translate("데이터 동기화"), translate("Supabase 설정"), translate("데이터 초기화")])
    
    # 데이터 동기화 탭
    with tab1:
        st.subheader(translate("데이터 동기화"))
        
        st.info(translate("앱 데이터와 Supabase 데이터베이스 간 양방향 동기화를 수행할 수 있습니다."))
        
        col1, col2 = st.columns(2)
        
        # 앱 -> Supabase 동기화
        with col1:
            st.write(translate("### 앱 -> Supabase 동기화"))
            st.write(translate("앱의 데이터를 Supabase 데이터베이스로 내보냅니다."))
            
            # 동기화 대상 선택
            st.session_state.sync_options_app = st.multiselect(
                translate("동기화할 데이터 선택"),
                options=[translate("작업자 데이터"), translate("생산 실적 데이터"), translate("사용자 데이터"), translate("모델 데이터")],
                default=st.session_state.sync_options_app,
                key="app_to_supabase_options"
            )
            
            if st.button(translate("앱 -> Supabase 동기화"), key="app_to_supabase_btn"):
                with st.spinner(translate("데이터를 동기화 중입니다...")):
                    sync_results = []
                    
                    try:
                        db = st.session_state.db
                        
                        # 작업자 데이터 동기화
                        if translate("작업자 데이터") in st.session_state.sync_options_app:
                            if 'workers' in st.session_state and st.session_state.workers:
                                for worker in st.session_state.workers:
                                    db.add_worker(
                                        employee_id=worker.get("사번", ""),
                                        name=worker.get("이름", ""),
                                        department=worker.get("부서", "CNC"),
                                        line_number=worker.get("라인번호", "")
                                    )
                                sync_results.append(translate("✅ 작업자 데이터 동기화 완료"))
                            else:
                                sync_results.append(translate("⚠️ 동기화할 작업자 데이터가 없습니다"))
                        
                        # 생산 실적 데이터 동기화
                        if translate("생산 실적 데이터") in st.session_state.sync_options_app:
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
                                sync_results.append(translate("✅ 생산 실적 데이터 동기화 완료"))
                            else:
                                sync_results.append(translate("⚠️ 동기화할 생산 실적 데이터가 없습니다"))
                        
                        # 사용자 데이터 동기화
                        if translate("사용자 데이터") in st.session_state.sync_options_app:
                            if 'users' in st.session_state and st.session_state.users:
                                for user in st.session_state.users:
                                    db.add_user(
                                        email=user.get("이메일", ""),
                                        password=user.get("비밀번호", ""),
                                        name=user.get("이름", ""),
                                        role=user.get("권한", "user")
                                    )
                                sync_results.append(translate("✅ 사용자 데이터 동기화 완료"))
                            else:
                                sync_results.append(translate("⚠️ 동기화할 사용자 데이터가 없습니다"))
                        
                        # 모델 데이터 동기화
                        if translate("모델 데이터") in st.session_state.sync_options_app:
                            if 'models' in st.session_state and st.session_state.models:
                                for model in st.session_state.models:
                                    db.add_model(
                                        model_name=model.get("모델명", ""),
                                        process=model.get("공정", "")
                                    )
                                sync_results.append(translate("✅ 모델 데이터 동기화 완료"))
                            else:
                                sync_results.append(translate("⚠️ 동기화할 모델 데이터가 없습니다"))
                        
                        st.success(translate("데이터 동기화가 완료되었습니다!"))
                        for result in sync_results:
                            st.write(result)
                            
                    except Exception as e:
                        st.error(translate(f"데이터 동기화 중 오류가 발생했습니다: {str(e)}"))
        
        # Supabase -> 앱 동기화
        with col2:
            st.write(translate("### Supabase -> 앱 동기화"))
            st.write(translate("Supabase 데이터베이스의 데이터를 앱으로 가져옵니다."))
            
            # 동기화 대상 선택
            st.session_state.sync_options_db = st.multiselect(
                translate("동기화할 데이터 선택"),
                options=[translate("작업자 데이터"), translate("생산 실적 데이터"), translate("사용자 데이터"), translate("모델 데이터")],
                default=st.session_state.sync_options_db,
                key="supabase_to_app_options"
            )
            
            if st.button(translate("Supabase -> 앱 동기화"), key="supabase_to_app_btn"):
                with st.spinner(translate("데이터를 동기화 중입니다...")):
                    sync_results = []
                    
                    try:
                        db = st.session_state.db
                        
                        # 작업자 데이터 가져오기
                        if translate("작업자 데이터") in st.session_state.sync_options_db:
                            from pages.worker_management import load_worker_data
                            st.session_state.workers = load_worker_data()
                            sync_results.append(translate(f"✅ 작업자 데이터 {len(st.session_state.workers)}개 로드 완료"))
                        
                        # 생산 실적 데이터 가져오기
                        if translate("생산 실적 데이터") in st.session_state.sync_options_db:
                            with st.spinner(translate("생산 실적 데이터 동기화 중... (대용량 데이터는 시간이 걸릴 수 있습니다)")):
                                try:
                                    # 직접 페이지네이션을 통해 모든 데이터 가져오기
                                    page_size = 1000
                                    offset = 0
                                    all_records = []
                                    
                                    # 먼저 캐시 무효화
                                    db._invalidate_cache()
                                    
                                    # 페이지네이션으로 모든 데이터 가져오기
                                    while True:
                                        print(f"[DEBUG] 생산 데이터 페이지 로드 중: offset={offset}, limit={page_size}")
                                        response = db.client.table('Production').select('*').limit(page_size).offset(offset).execute()
                                        records = response.data
                                        
                                        if not records:
                                            break
                                            
                                        all_records.extend(records)
                                        record_count = len(all_records)
                                        print(f"[DEBUG] 현재까지 로드된 생산 데이터: {record_count}개")
                                        
                                        if len(records) < page_size:
                                            break
                                            
                                        offset += page_size
                                    
                                    # 전체 데이터를 세션 상태에 저장
                                    st.session_state.production_data = all_records
                                    record_count = len(all_records)
                                    
                                    # production.py의 load_production_data 함수 대신 직접 구현
                                    sync_results.append(translate(f"✅ 생산 실적 데이터 {record_count}개 로드 완료 (페이지네이션 사용)"))
                                except Exception as e:
                                    import traceback
                                    print(f"[ERROR] 생산 데이터 페이지네이션 중 오류: {str(e)}")
                                    print(traceback.format_exc())
                                    
                                    # 오류 발생 시 기존 방식으로 시도
                                    from pages.production import load_production_data
                                    st.session_state.production_data = load_production_data()
                                    record_count = len(st.session_state.production_data)
                                    
                                    if record_count >= 10000:
                                        sync_results.append(translate(f"✅ 생산 실적 데이터 {record_count}개 로드 완료 (최대 조회 제한: 10000개)"))
                                    else:
                                        sync_results.append(translate(f"✅ 생산 실적 데이터 {record_count}개 로드 완료"))
                        
                        # 사용자 데이터 가져오기
                        if translate("사용자 데이터") in st.session_state.sync_options_db:
                            st.session_state.users = db.get_all_users()
                            sync_results.append(translate(f"✅ 사용자 데이터 {len(st.session_state.users)}개 로드 완료"))
                        
                        # 모델 데이터 가져오기
                        if translate("모델 데이터") in st.session_state.sync_options_db:
                            from pages.model_management import load_model_data
                            st.session_state.models = load_model_data()
                            sync_results.append(translate(f"✅ 모델 데이터 {len(st.session_state.models)}개 로드 완료"))
                        
                        st.success(translate("데이터 동기화가 완료되었습니다!"))
                        for result in sync_results:
                            st.write(result)
                        
                    except Exception as e:
                        st.error(translate(f"데이터 동기화 중 오류가 발생했습니다: {str(e)}"))
        
        # 데이터 백업 및 복원
        st.write(translate("### 데이터 백업 및 복원"))
        col1, col2 = st.columns(2)
        
        # 데이터 백업
        with col1:
            st.write(translate("데이터 백업"))
            if st.button(translate("JSON 파일로 백업"), key="backup_to_json_btn"):
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
                    label=translate("백업 파일 다운로드"),
                    data=json_data,
                    file_name=f"data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="download_backup_btn"
                )
                
                st.success(translate("데이터가 성공적으로 백업되었습니다."))
        
        # 데이터 복원
        with col2:
            st.write(translate("데이터 복원"))
            uploaded_file = st.file_uploader(translate("백업 파일 선택"), type=["json"], key="backup_file_uploader")
            
            if uploaded_file is not None:
                if st.button(translate("백업 파일에서 복원"), key="restore_from_backup_btn"):
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
                        
                        backup_time = backup_data.get("backup_time", translate("알 수 없음"))
                        st.success(translate(f"데이터가 성공적으로 복원되었습니다. (백업 시간: {backup_time})"))
                    except Exception as e:
                        st.error(translate(f"데이터 복원 중 오류가 발생했습니다: {str(e)}"))
    
    # Supabase 설정 탭
    with tab2:
        st.subheader(translate("Supabase 연결 설정"))
        
        # 현재 설정된 Supabase URL과 Key 표시
        current_url = os.getenv("SUPABASE_URL", "")
        current_key = os.getenv("SUPABASE_KEY", "")
        
        if current_url and current_key:
            st.success(translate("Supabase 연결이 설정되어 있습니다."))
            # 마스킹된 키 표시
            masked_key = current_key[:4] + "*" * (len(current_key) - 8) + current_key[-4:] if len(current_key) > 8 else "********"
            st.info(translate(f"현재 URL: {current_url}"))
            st.info(translate(f"현재 API Key: {masked_key}"))
            
            # 새로운 설정 입력 폼
            with st.form("supabase_settings_form_update"):
                st.write(translate("Supabase 연결 정보 설정"))
                new_url = st.text_input(translate("Supabase URL"), value=current_url, key="supabase_url_input")
                new_key = st.text_input(translate("Supabase API Key"), value=current_key, type="password", key="supabase_key_input")
                
                submitted = st.form_submit_button(translate("설정 저장"))
                
                if submitted:
                    try:
                        # .env 파일 생성 또는 업데이트
                        with open(".env", "w") as f:
                            f.write(f"SUPABASE_URL={new_url}\n")
                            f.write(f"SUPABASE_KEY={new_key}\n")
                        
                        # 환경 변수 다시 로드
                        load_dotenv(override=True)
                        
                        st.success(translate("Supabase 연결 설정이 저장되었습니다."))
                        st.info(translate("변경사항을 적용하려면 애플리케이션을 재시작해야 합니다."))
                    except Exception as e:
                        st.error(translate(f"설정 저장 중 오류가 발생했습니다: {str(e)}"))
        else:
            st.warning(translate("Supabase 연결 정보가 설정되어 있지 않습니다."))
            
            # 새로운 설정 입력 폼
            with st.form("supabase_settings_form_new_setup"):
                st.write(translate("Supabase 연결 정보 설정"))
                new_url = st.text_input(translate("Supabase URL"), value=current_url, key="supabase_url_input_new")
                new_key = st.text_input(translate("Supabase API Key"), value=current_key, type="password", key="supabase_key_input_new")
                
                submitted = st.form_submit_button(translate("설정 저장"))
                
                if submitted:
                    try:
                        # .env 파일 생성 또는 업데이트
                        with open(".env", "w") as f:
                            f.write(f"SUPABASE_URL={new_url}\n")
                            f.write(f"SUPABASE_KEY={new_key}\n")
                        
                        # 환경 변수 다시 로드
                        load_dotenv(override=True)
                        
                        st.success(translate("Supabase 연결 설정이 저장되었습니다."))
                        st.info(translate("변경사항을 적용하려면 애플리케이션을 재시작해야 합니다."))
                    except Exception as e:
                        st.error(translate(f"설정 저장 중 오류가 발생했습니다: {str(e)}"))
        
        # Supabase 테이블 생성 안내
        st.subheader(translate("Supabase 테이블 설정 안내"))
        
        with st.expander("테이블 구조 안내", expanded=False):
            table_structure = """
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
            """
            st.write("테이블 구조 안내")
            st.text(table_structure)
        
        # SQL 스크립트 제공 - 별도의 expander로 분리
        with st.expander("테이블 생성 SQL 스크립트"):
            sql_script = """
    -- Users 테이블 생성
    CREATE TABLE Users (
      id SERIAL PRIMARY KEY,
      이메일 TEXT UNIQUE NOT NULL,
      이름 TEXT NOT NULL,
      비밀번호 TEXT NOT NULL,
      권한 TEXT NOT NULL DEFAULT 'user',
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Workers 테이블 생성
    CREATE TABLE Workers (
      id SERIAL PRIMARY KEY,
      사번 TEXT UNIQUE NOT NULL,
      이름 TEXT NOT NULL,
      부서 TEXT NOT NULL,
      라인번호 TEXT NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Production 테이블 생성
    CREATE TABLE Production (
      id SERIAL PRIMARY KEY,
      날짜 DATE NOT NULL,
      작업자 TEXT NOT NULL,
      라인번호 TEXT NOT NULL,
      모델차수 TEXT NOT NULL,
      목표수량 INTEGER NOT NULL,
      생산수량 INTEGER NOT NULL,
      불량수량 INTEGER NOT NULL,
      특이사항 TEXT,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Model 테이블 생성
    CREATE TABLE Model (
      id SERIAL PRIMARY KEY,
      모델명 TEXT NOT NULL,
      공정 TEXT NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
            """
            st.code(sql_script, language="sql")
        
        st.info("위 SQL 스크립트를 Supabase의 SQL 편집기에서 실행하여 필요한 테이블을 생성할 수 있습니다.")

        # 캐시 초기화
        if 'db' in st.session_state:
            st.session_state.db._invalidate_cache()
            st.session_state.production_data = None
        
    # 데이터 초기화 탭
    with tab3:
        st.subheader(translate("데이터 초기화"))
        st.warning(translate("⚠️ 초기화 기능은 데이터를 영구적으로 삭제할 수 있습니다. 신중하게 사용하세요."))
        
        reset_type = st.selectbox(
            translate("초기화할 데이터 유형"),
            options=[translate("생산 실적"), translate("모델 데이터"), translate("작업자 데이터"), translate("사용자 데이터")]
        )
        
        confirm_text = st.text_input(translate("초기화하려면 'RESET'을 입력하세요"), value="")
        
        if st.button(translate("데이터 초기화"), key="reset_btn", disabled=(confirm_text != "RESET")):
            try:
                db = st.session_state.db
                if reset_type == translate("생산 실적"):
                    # 생산 실적 데이터 초기화
                    try:
                        result = db.client.table('Production').delete().neq('id', 0).execute()
                        st.success(translate("생산 실적 데이터가 초기화되었습니다."))
                        # 세션 상태 초기화
                        st.session_state.production_data = None
                    except Exception as e:
                        st.error(translate(f"생산 실적 데이터 초기화 중 오류 발생: {str(e)}"))
                        
                elif reset_type == translate("모델 데이터"):
                    # 모델 데이터 초기화 
                    try:
                        result = db.client.table('Model').delete().neq('id', 0).execute()
                        st.success(translate("모델 데이터가 초기화되었습니다."))
                        # 세션 상태 초기화
                        st.session_state.models = None
                    except Exception as e:
                        st.error(translate(f"모델 데이터 초기화 중 오류 발생: {str(e)}"))
                        
                elif reset_type == translate("작업자 데이터"):
                    # 작업자 데이터 초기화
                    try:
                        result = db.client.table('Workers').delete().neq('id', 0).execute()
                        st.success(translate("작업자 데이터가 초기화되었습니다."))
                        # 세션 상태 초기화
                        st.session_state.workers = None
                    except Exception as e:
                        st.error(translate(f"작업자 데이터 초기화 중 오류 발생: {str(e)}"))
                        
                elif reset_type == translate("사용자 데이터"):
                    # 사용자 데이터 초기화 (관리자 데이터는 유지)
                    try:
                        result = db.client.table('Users').delete().not_eq('권한', '관리자').execute()
                        st.success(translate(f"일반 사용자 데이터가 초기화되었습니다. (관리자 계정은 유지됩니다)"))
                        # 세션 상태 초기화
                        st.session_state.users = None
                    except Exception as e:
                        st.error(translate(f"사용자 데이터 초기화 중 오류 발생: {str(e)}"))
                
                # 캐시 초기화
                db._invalidate_cache()
                
            except Exception as e:
                st.error(translate(f"데이터 초기화 중 오류 발생: {str(e)}"))
                import traceback
                st.code(traceback.format_exc(), language="python")