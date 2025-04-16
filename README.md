# ALMUS TECH CNC 작업자 KPI 관리 시스템

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.24.0+-red.svg)
![Supabase](https://img.shields.io/badge/Supabase-2.0.0+-green.svg)

CNC 작업자의 생산성과 품질을 실시간으로 추적하고 분석하는 종합 KPI 관리 시스템입니다. 직관적인 대시보드와 상세한 리포트를 통해 생산 현장의 효율성을 파악하고 개선 포인트를 도출할 수 있습니다.

## 1. 주요 기능

### 관리자 메뉴
- **관리자 및 사용자 관리**: 사용자 계정 생성, 수정, 삭제 및 권한 관리
- **작업자 등록 및 관리**: 작업자 정보 등록, 수정, 삭제 기능
- **생산 모델 관리**: 제품 모델 및 공정 정보 관리
- **생산 실적 관리**: 생산 실적 데이터 입력, 수정, 삭제 및 데이터 그리드 기능
- **데이터 관리**: Supabase 데이터베이스 동기화, 백업 및 복원 기능

### 리포트 메뉴
- **종합 대시보드**: 생산목표 달성률, 불량률, 작업효율 등 핵심 KPI를 시각화
  - 목표 달성률: 96%
  - 작업효율: 95%
  - 불량률: 0.02%
- **일간 리포트**: 일별 생산 실적 및 KPI 분석 기능
- **주간 리포트**: 주 단위 생산 실적 및 KPI 추이 분석
- **월간 리포트**: 월 단위 생산 성과 및 작업자별 KPI 비교
- **연간 리포트**: 연간 생산 실적 추이 및 성과 분석

### 기타 기능
- **다국어 지원**: 한국어/베트남어 전환 기능
- **반응형 UI**: 다양한 디바이스에 최적화된 인터페이스
- **데이터 시각화**: Plotly를 활용한 인터랙티브 차트와 그래프
- **데이터 그리드**: 필터링, 정렬, 페이지네이션이 지원되는 고급 데이터 테이블
- **알림 시스템**: KPI 목표 달성 여부에 따른 알림 기능

## 2. 사용 방법

### 설치
1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
- `.env` 파일 생성 및 Supabase 연결 정보 설정
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

3. 애플리케이션 실행:
```bash
streamlit run app.py
```

### 초기 설정
1. 관리자 계정으로 로그인합니다 (기본 계정: admin@example.com / password)
2. '데이터 관리' 메뉴에서 Supabase 연결 설정
3. 데이터베이스에 필요한 테이블 생성
4. '작업자 등록 및 관리'에서 작업자 정보 등록
5. '생산 모델 관리'에서 생산 모델 등록
6. '생산 실적 관리'에서 생산 데이터 입력 시작

### 일상적인 사용
1. 로그인 후 '생산 실적 관리'에서 당일 생산 데이터 입력
2. '종합 대시보드'에서 실시간 KPI 확인
3. 기간별 리포트(일간/주간/월간/연간)로 세부 분석 수행
4. 필요시 '데이터 관리'에서 데이터 백업/복원

## 3. 기술 스택

### 프론트엔드
- **Streamlit 1.24.0+**: 파이썬 기반 웹 애플리케이션 프레임워크
- **Plotly 5.14.1+**: 인터랙티브 데이터 시각화 라이브러리
- **Streamlit-AgGrid 1.1.0+**: 고급 데이터 그리드 컴포넌트

### 백엔드
- **Python 3.9+**: 주요 프로그래밍 언어
- **Pandas 1.5.3+**: 데이터 처리 및 분석
- **NumPy 1.24.3+**: 수치 계산
- **bcrypt 4.0.1+**: 비밀번호 암호화

### 데이터베이스
- **Supabase 2.0.0+**: PostgreSQL 기반 백엔드 데이터베이스 및 API
- **python-dotenv 1.0.0+**: 환경 변수 관리

### 개발 도구
- **Git**: 버전 관리 시스템
- **VS Code**: 코드 편집기

## 4. 폴더 구조

```
CNC_OP_KPI_SUPABASE/
│
├── app.py                # 메인 애플리케이션 파일
├── requirements.txt      # 프로젝트 의존성 패키지 목록
├── .env                  # 환경 변수 파일 (Supabase 연결 정보)
├── translations.json     # 다국어 지원을 위한 번역 데이터
│
├── utils/                # 유틸리티 함수 및 클래스
│   ├── supabase_db.py    # Supabase 데이터베이스 관리 클래스
│   ├── login.py          # 로그인 관련 기능
│   ├── auth.py           # 인증 및 권한 관리
│   ├── local_storage.py  # 로컬 데이터 스토리지 관리
│   ├── translations.py   # 다국어 지원 기능
│   ├── common.py         # 공통 유틸리티 함수
│   ├── sidebar.py        # 사이드바 관련 기능
│   └── mock_database.py  # 테스트용 모의 데이터베이스
│
├── pages/                # 각 페이지별 Python 파일
│   ├── admin_management.py  # 관리자 및 사용자 관리 페이지
│   ├── worker_management.py # 작업자 관리 페이지
│   ├── model_management.py  # 모델 관리 페이지
│   ├── production.py        # 생산 실적 관리 페이지
│   ├── data_sync.py         # 데이터 동기화 페이지
│   ├── dashboard.py         # 종합 대시보드 페이지
│   ├── daily_report.py      # 일간 리포트 페이지
│   ├── weekly_report.py     # 주간 리포트 페이지
│   ├── monthly_report.py    # 월간 리포트 페이지
│   └── yearly_report.py     # 연간 리포트 페이지
│
└── cache/                # 데이터 캐시 저장 디렉토리
    └── supabase_cache.json  # Supabase 데이터 캐시 파일
```

## 5. 데이터베이스

이 프로젝트는 Supabase(PostgreSQL 기반)를 데이터베이스로 사용합니다.

### Supabase 설정 방법

1. [Supabase](https://supabase.com/) 계정 생성 및 프로젝트 생성
2. 프로젝트의 API URL과 API Key(anon public) 복사
3. `.env` 파일에 Supabase 연결 정보 설정
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```
4. 애플리케이션의 '데이터 관리' 메뉴에서 필요한 테이블 생성 (SQL 스크립트 제공)

### 연결 설정

- 기본적으로 앱은 `.env` 파일에서 연결 정보를 읽어옵니다.
- Streamlit Cloud에 배포할 경우 Streamlit Secrets를 통해 연결 정보를 관리할 수 있습니다.
- 앱 내에서 '데이터 관리' > 'Supabase 설정' 메뉴를 통해 연결 정보를 업데이트할 수 있습니다.

## 6. 테이블 구조

### Users (사용자)
| 필드명    | 데이터 타입 | 설명                        |
|----------|------------|----------------------------|
| id       | SERIAL     | 기본 키                    |
| 이메일    | TEXT       | 사용자 로그인 이메일 (유니크) |
| 비밀번호   | TEXT       | bcrypt로 암호화된 비밀번호   |
| 이름      | TEXT       | 사용자 실명                |
| 권한      | TEXT       | 권한 (관리자/사용자)         |
| created_at | TIMESTAMP | 생성 시간                  |
| updated_at | TIMESTAMP | 최종 수정 시간              |

### Workers (작업자)
| 필드명    | 데이터 타입 | 설명                     |
|----------|------------|--------------------------|
| id       | SERIAL     | 기본 키                  |
| 사번      | TEXT       | 작업자 사번 (유니크)       |
| 이름      | TEXT       | 작업자 이름               |
| 부서      | TEXT       | 소속 부서                 |
| 라인번호   | TEXT       | 작업 라인                 |
| created_at | TIMESTAMP | 생성 시간                 |
| updated_at | TIMESTAMP | 최종 수정 시간             |

### Production (생산 실적)
| 필드명    | 데이터 타입 | 설명                     |
|----------|------------|--------------------------|
| id       | SERIAL     | 기본 키                  |
| 날짜      | DATE       | 생산 날짜                 |
| 작업자    | TEXT       | 작업자 이름               |
| 라인번호   | TEXT       | 생산 라인                 |
| 모델차수   | TEXT       | 생산 모델                 |
| 목표수량   | INTEGER    | 일일 목표 생산량           |
| 생산수량   | INTEGER    | 실제 생산량               |
| 불량수량   | INTEGER    | 불량품 수량               |
| 특이사항   | TEXT       | 비고                     |
| created_at | TIMESTAMP | 생성 시간                 |
| updated_at | TIMESTAMP | 최종 수정 시간             |

### Model (모델 정보)
| 필드명    | 데이터 타입 | 설명                     |
|----------|------------|--------------------------|
| id       | SERIAL     | 기본 키                  |
| 모델명    | TEXT       | 모델명                   |
| 공정      | TEXT       | 공정명                   |
| created_at | TIMESTAMP | 생성 시간                 |
| updated_at | TIMESTAMP | 최종 수정 시간             |

## 7. 보안

### 사용자 인증
- 이메일과 비밀번호를 통한 로그인 시스템
- 비밀번호는 bcrypt를 사용하여 암호화 저장
- 로그인 세션 관리로 인증되지 않은 접근 차단

### 접근 제어
- 관리자와 일반 사용자 권한 구분
- 권한에 따른 메뉴 접근 제한
- 관리자만 사용자 관리, 데이터 초기화 등 중요 기능 접근 가능

### 데이터 보안
- Supabase의 보안 기능 활용
- API 키 환경 변수로 관리
- 민감한 설정 정보 .env 파일 분리 (.gitignore에 포함)

### 추가 보안 조치
- 세션 타임아웃 설정
- 모든 입력값 검증을 통한 인젝션 공격 방지
- 캐시 데이터 타임아웃 설정 (30초)

## 8. 기타 사항

### 성능 최적화
- 데이터 캐싱 시스템으로 빠른 응답 시간 보장
- 페이지네이션을 통한 대용량 데이터 효율적 처리
- 불필요한 데이터베이스 쿼리 최소화

### 다국어 지원
- 한국어 및 베트남어 지원
- translations.json 파일을 통한 번역 데이터 관리
- 언제든지 추가 언어 확장 가능

### 로깅 및 디버깅
- 콘솔 로깅을 통한 문제 추적
- 오류 시 상세 메시지 제공
- try-except 구문을 사용한 예외 처리

### 데이터 백업 및 복원
- JSON 형식으로 전체 데이터 백업 가능
- 백업 파일 다운로드 및 복원 기능
- 데이터 타입별 선택적 초기화 기능

### 확장성
- 모듈식 설계로 새로운 기능 추가 용이
- 새로운 페이지와 기능을 독립적으로 추가 가능
- API 기반 설계로 다른 시스템과 통합 가능

---

© 2023 ALMUS TECH. All Rights Reserved.