import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def show_data_sync():
    st.title("Supabase 데이터베이스 설정")
    
    # 관리자 권한 확인
    if 'username' not in st.session_state or st.session_state.username is None:
        st.error("로그인이 필요합니다.")
        return
    
    # 관리자 권한 확인 (여기서는 간단히 이메일이 admin_accounts에 있는지 확인)
    if st.session_state.username not in st.session_state.admin_accounts:
        st.error("관리자 권한이 필요합니다.")
        return
    
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
            with st.form("supabase_settings"):
                st.write("Supabase 연결 정보 설정")
                new_url = st.text_input("Supabase URL", value=current_url)
                new_key = st.text_input("Supabase API Key", value=current_key, type="password")
                
                submitted = st.form_submit_button("설정 저장")
                
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
        with st.form("supabase_settings"):
            st.write("Supabase 연결 정보 설정")
            new_url = st.text_input("Supabase URL", value=current_url)
            new_key = st.text_input("Supabase API Key", value=current_key, type="password")
            
            submitted = st.form_submit_button("설정 저장")
            
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
        with st.expander("테이블 생성 SQL 스크립트"):
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