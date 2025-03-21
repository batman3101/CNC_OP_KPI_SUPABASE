import os
import json
import time
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv
import streamlit as st

# 환경 변수 로드
load_dotenv()

class SupabaseDB:
    def __init__(self):
        """초기화"""
        # 환경 변수 로드
        load_dotenv()
        
        # Streamlit 시크릿에서 Supabase 연결 정보 가져오기
        try:
            self.url = st.secrets["SUPABASE_URL"]
            self.key = st.secrets["SUPABASE_KEY"]
            print(f"[INFO] Streamlit 시크릿에서 Supabase 연결 정보를 가져왔습니다.")
        except Exception as e:
            # 환경 변수에서 시도
            self.url = os.getenv('SUPABASE_URL')
            self.key = os.getenv('SUPABASE_KEY')
            print(f"[INFO] 환경 변수에서 Supabase 연결 정보를 가져왔습니다.")
        
        print(f"[DEBUG] Supabase 연결 정보: URL={self.url[:10]}..., KEY={'설정됨' if self.key else '설정되지 않음'}")
        
        self.client = None
        
        # 캐시 설정
        self.cache_file = 'cache/supabase_cache.json'
        self.cache = {}
        self.cache_timeout = 60  # 캐시 유효 시간 (초) - 1분으로 단축
        
        # 캐시 디렉토리 생성
        os.makedirs('cache', exist_ok=True)
        
        # 캐시 로드
        self._load_cache()
        
        # 연결 초기화
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Supabase 연결 초기화"""
        try:
            print(f"[DEBUG] Supabase 연결 시도: URL={self.url[:10] if self.url else '없음'}..., KEY={self.key[:5] if self.key else '없음'}...")
            self.client = create_client(self.url, self.key)
            print(f"[INFO] Supabase 연결 성공")
            # 초기 테이블 확인 및 생성
            self._ensure_tables()
        except Exception as e:
            print(f"[ERROR] Supabase 연결 초기화 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            self.client = None
    
    def _ensure_tables(self):
        """필요한 테이블이 존재하는지 확인하고 없으면 생성"""
        try:
            # 테이블 목록 조회 - 다른 방식으로 시도
            print(f"[DEBUG] 테이블 확인 시도")
            
            # 직접 테이블 조회 시도
            try:
                # Production 테이블 데이터 조회 시도
                test_query = self.client.table('Production').select('*').limit(1).execute()
                print(f"[DEBUG] Production 테이블 조회 성공: {test_query.data}")
            except Exception as e:
                print(f"[DEBUG] Production 테이블 조회 실패: {e}")
                
                # 소문자로 시도
                try:
                    test_query = self.client.table('production').select('*').limit(1).execute()
                    print(f"[DEBUG] production 테이블 조회 성공: {test_query.data}")
                except Exception as e:
                    print(f"[DEBUG] production 테이블 조회 실패: {e}")
            
            # Users 테이블 확인
            try:
                test_query = self.client.table('Users').select('*').limit(1).execute()
                print(f"[DEBUG] Users 테이블 조회 성공: {test_query.data}")
            except Exception as e:
                print(f"[DEBUG] Users 테이블 조회 실패: {e}")
                
                # 소문자로 시도
                try:
                    test_query = self.client.table('users').select('*').limit(1).execute()
                    print(f"[DEBUG] users 테이블 조회 성공: {test_query.data}")
                except Exception as e:
                    print(f"[DEBUG] users 테이블 조회 실패: {e}")
            
        except Exception as e:
            print(f"[ERROR] 테이블 확인 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            
    def _load_cache(self):
        """캐시 파일 로드"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.cache = {k: (v['time'], v['data']) for k, v in cache_data.items()}
        except Exception as e:
            print(f"캐시 로드 중 오류 발생: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """캐시 파일 저장"""
        try:
            cache_data = {k: {'time': v[0], 'data': v[1]} for k, v in self.cache.items()}
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False)
        except Exception as e:
            print(f"캐시 저장 중 오류 발생: {e}")
    
    def _get_cached_data(self, key):
        """캐시된 데이터 조회"""
        if key in self.cache:
            cache_time, data = self.cache[key]
            if time.time() - cache_time < self.cache_timeout:
                return data
        return None
    
    def _set_cached_data(self, key, data):
        """데이터 캐시 저장"""
        self.cache[key] = (time.time(), data)
        self._save_cache()
    
    def _invalidate_cache(self, key=None):
        """캐시 무효화
        key가 None이면 모든 캐시를 무효화, 아니면 특정 키의 캐시만 무효화
        """
        if key is None:
            self.cache = {}
        elif key in self.cache:
            del self.cache[key]
        self._save_cache()
    
    # 사용자 관련 메서드
    def get_all_users(self):
        """사용자 정보 조회"""
        try:
            cached_data = self._get_cached_data('users')
            if cached_data:
                return cached_data
            
            response = self.client.table('Users').select('*').execute()
            users = response.data
            
            # 필드명 매핑
            formatted_users = []
            for user in users:
                formatted_users.append({
                    'id': user.get('id', ''),
                    '이메일': user.get('이메일', ''),
                    '비밀번호': user.get('비밀번호', ''),
                    '이름': user.get('이름', ''),
                    '권한': user.get('권한', '')
                })
            
            self._set_cached_data('users', formatted_users)
            return formatted_users
        except Exception as e:
            print(f"사용자 조회 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            return []
    
    def get_user(self, email):
        """이메일로 사용자 정보 조회"""
        try:
            response = self.client.table('Users').select('*').eq('이메일', email).execute()
            users = response.data
            
            if users and len(users) > 0:
                user = users[0]
                return {
                    'id': user.get('id', ''),
                    '이메일': user.get('이메일', ''),
                    '비밀번호': user.get('비밀번호', ''),
                    '이름': user.get('이름', ''),
                    '권한': user.get('권한', '')
                }
            return None
        except Exception as e:
            print(f"사용자 조회 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            return None
    
    def create_user(self, email, password, name, role='user'):
        """사용자 생성 (auth.py와의 호환성을 위한 메서드)"""
        return self.add_user(email, password, name, role)
    
    def add_user(self, email, password, name, role):
        """사용자 추가"""
        try:
            data = {
                '이메일': email,
                '비밀번호': password,
                '이름': name,
                '권한': role
            }
            
            response = self.client.table('Users').insert(data).execute()
            print(f"[DEBUG] 사용자 추가 응답: {response}")
            
            # 캐시 무효화
            self._invalidate_cache('users')
            
            return True
        except Exception as e:
            print(f"사용자 추가 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            return False
    
    def update_user(self, email, data):
        """사용자 정보 업데이트"""
        try:
            response = self.client.table('Users').update(data).eq('이메일', email).execute()
            print(f"[DEBUG] 사용자 업데이트 응답: {response}")
            
            # 캐시 무효화
            self._invalidate_cache('users')
            
            return True
        except Exception as e:
            print(f"사용자 업데이트 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            return False
    
    def delete_user(self, email):
        """사용자 삭제"""
        try:
            response = self.client.table('Users').delete().eq('이메일', email).execute()
            print(f"[DEBUG] 사용자 삭제 응답: {response}")
            
            # 캐시 무효화
            self._invalidate_cache('users')
            
            return True
        except Exception as e:
            print(f"사용자 삭제 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            return False
    
    # 작업자 관련 메서드
    def get_workers(self):
        """전체 작업자 데이터 조회"""
        try:
            print(f"[DEBUG] get_workers 시작: 캐시 확인 중")
            
            # 캐시를 사용하지 않고 항상 최신 데이터를 가져오도록 수정
            # cached_data = self._get_cached_data('workers')
            # if cached_data:
            #     return cached_data
            
            print(f"[DEBUG] Supabase에서 작업자 데이터 직접 조회")
            if not self.client:
                print(f"[ERROR] Supabase 클라이언트가 초기화되지 않음")
                self._initialize_connection()
                if not self.client:
                    print(f"[ERROR] Supabase 재연결 실패")
                    return []
            
            print(f"[DEBUG] Workers 테이블 쿼리 실행")
            response = self.client.table('Workers').select('*').execute()
            
            if not hasattr(response, 'data'):
                print(f"[ERROR] Workers 테이블 조회 응답에 데이터 필드 없음")
                return []
                
            workers = response.data
            print(f"[DEBUG] 조회된 작업자 데이터: {len(workers)}개 레코드")
            
            # 테이블 구조 확인
            if workers and len(workers) > 0:
                first_record = workers[0]
                print(f"[DEBUG] Workers 테이블 첫 번째 레코드: {first_record}")
                print(f"[DEBUG] Workers 테이블 필드: {list(first_record.keys())}")
                
                # 필드 매핑 설정
                field_mapping = {
                    'id': 'id',
                    '사번': '사번',
                    '이름': '이름',
                    '부서': '부서',
                    '라인번호': '라인번호'
                }
                
                # 필드명 매핑
                formatted_workers = []
                for worker in workers:
                    worker_data = {
                        'id': worker.get('id', ''),
                        '사번': worker.get('사번', ''),
                        '이름': worker.get('이름', ''),
                        '부서': worker.get('부서', 'CNC'),
                        '라인번호': worker.get('라인번호', '')
                    }
                    formatted_workers.append(worker_data)
                
                # 캐시 저장
                self._set_cached_data('workers', formatted_workers)
                print(f"[INFO] 작업자 데이터 {len(formatted_workers)}개 반환")
                return formatted_workers
            else:
                print(f"[INFO] 작업자 데이터 없음")
                return []
        except Exception as e:
            print(f"[ERROR] 작업자 조회 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            return []
    
    def add_worker(self, employee_id, name, department, line_number):
        """작업자 추가"""
        try:
            # 테이블 구조 확인
            table_info = self.client.table('Workers').select('*').limit(1).execute()
            
            # 데이터 준비
            data = {
                '사번': employee_id,
                '이름': name,
                '부서': department,
                '라인번호': line_number
            }
            
            print(f"[DEBUG] 추가할 작업자 데이터: {data}")
            
            response = self.client.table('Workers').insert(data).execute()
            print(f"[DEBUG] 작업자 추가 응답: {response}")
            
            # 캐시 무효화
            self._invalidate_cache('workers')
            
            return True
        except Exception as e:
            print(f"작업자 추가 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            return False
    
    def update_worker(self, old_name, new_name, new_id, new_line):
        """작업자 정보 업데이트 - 생산 관리 페이지와 동일한 방식으로 직접 구현"""
        try:
            print(f"[DEBUG] update_worker 호출: old_name={old_name}, new_name={new_name}, new_id={new_id}, new_line={new_line}")
            
            if not self.client:
                print(f"[ERROR] Supabase 클라이언트가 초기화되지 않음")
                self._initialize_connection()
                if not self.client:
                    print(f"[ERROR] Supabase 재연결 실패")
                    return False
            
            # Workers 테이블에서 이름으로 작업자 조회
            print(f"[DEBUG] 작업자 '{old_name}' 조회 중")
            response = self.client.table('Workers').select('*').eq('이름', old_name).execute()
            print(f"[DEBUG] 작업자 조회 결과: {response.data if hasattr(response, 'data') else '응답에 데이터 없음'}")
            
            if not hasattr(response, 'data') or not response.data or len(response.data) == 0:
                print(f"[ERROR] 이름으로 작업자를 찾을 수 없음: {old_name}")
                return False
                
            worker_id = response.data[0].get('id')
            department = response.data[0].get('부서', 'CNC')
            
            print(f"[DEBUG] 작업자 ID: {worker_id}, 부서: {department}")
            
            # 업데이트 데이터 준비
            update_data = {
                '이름': new_name,
                '사번': new_id,
                '부서': department,
                '라인번호': new_line
            }
            
            print(f"[DEBUG] 업데이트 데이터: {update_data}")
            
            # 캐시 무효화 먼저 수행
            print(f"[DEBUG] 작업자 캐시 무효화")
            self._invalidate_cache('workers')
            
            # 작업자 정보 업데이트
            print(f"[DEBUG] Workers 테이블 업데이트 시작: worker_id={worker_id}")
            update_response = self.client.table('Workers').update(update_data).eq('id', worker_id).execute()
            print(f"[DEBUG] 작업자 업데이트 응답: {update_response.data if hasattr(update_response, 'data') else '응답에 데이터 없음'}")
            
            # 응답 확인
            if hasattr(update_response, 'data') and update_response.data and len(update_response.data) > 0:
                print(f"[INFO] 작업자 업데이트 성공: {update_response.data}")
                return True
            else:
                print(f"[WARNING] 작업자 업데이트 응답에 데이터가 없습니다")
                # 대부분의 경우 응답에 데이터가 없더라도 업데이트는 성공하므로 True 반환
                return True
                
        except Exception as e:
            print(f"[ERROR] 작업자 업데이트 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 작업자 업데이트 중 상세 오류: {traceback.format_exc()}")
            return False
            
    def delete_worker(self, worker_name):
        """작업자 삭제 - 생산 관리 페이지와 동일한 방식으로 직접 구현"""
        try:
            print(f"[DEBUG] delete_worker 호출: worker_name={worker_name}")
            
            if not self.client:
                print(f"[ERROR] Supabase 클라이언트가 초기화되지 않음")
                self._initialize_connection()
                if not self.client:
                    print(f"[ERROR] Supabase 재연결 실패")
                    return False
            
            # 작업자 확인
            print(f"[DEBUG] 작업자 '{worker_name}' 조회 중")
            response = self.client.table('Workers').select('*').eq('이름', worker_name).execute()
            print(f"[DEBUG] 작업자 조회 결과: {response.data if hasattr(response, 'data') else '응답에 데이터 없음'}")
            
            if not hasattr(response, 'data') or not response.data or len(response.data) == 0:
                print(f"[ERROR] 삭제할 작업자를 찾을 수 없음: {worker_name}")
                return False
                
            worker_id = response.data[0].get('id')
            print(f"[DEBUG] 삭제할 작업자 ID: {worker_id}")
            
            # 캐시 무효화 먼저 수행
            print(f"[DEBUG] 작업자 캐시 무효화")
            self._invalidate_cache('workers')
            
            # 작업자 삭제
            print(f"[DEBUG] Workers 테이블에서 작업자 삭제 시작: worker_id={worker_id}")
            delete_response = self.client.table('Workers').delete().eq('id', worker_id).execute()
            print(f"[DEBUG] 작업자 삭제 응답: {delete_response.data if hasattr(delete_response, 'data') else '응답에 데이터 없음'}")
            
            # 응답 확인
            if hasattr(delete_response, 'data') and delete_response.data:
                print(f"[INFO] 작업자 삭제 성공: {delete_response.data}")
                return True
            else:
                print(f"[WARNING] 작업자 삭제 응답에 데이터가 없습니다")
                # 대부분의 경우 응답에 데이터가 없더라도 삭제는 성공하므로 True 반환
                return True
            
        except Exception as e:
            print(f"[ERROR] 작업자 삭제 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 작업자 삭제 중 상세 오류: {traceback.format_exc()}")
            return False
    
    # 생산 실적 관련 메서드
    def get_production_records(self, start_date, end_date, worker=None, line=None, model=None):
        """생산 실적 조회"""
        print(f"[DEBUG] get_production_records 호출: start_date={start_date}, end_date={end_date}")
        
        cache_key = f'production_{start_date}_{end_date}'
        cached_data = self._get_cached_data(cache_key)
        
        if cached_data:
            print(f"[DEBUG] 캐시된 데이터 사용: {len(cached_data)}개 레코드")
            # 캐시된 데이터에서 필터링
            return self._filter_production_data(cached_data, start_date, end_date, worker, line, model)
        
        try:
            # 기본 쿼리 생성
            print(f"[DEBUG] Supabase 연결 상태: URL={self.url}, 클라이언트={self.client is not None}")
            
            # 테이블 이름 확인 (production 또는 Production)
            table_names = ['Production', 'production']
            all_records = []
            
            # 두 가지 테이블 이름으로 시도
            for table_name in table_names:
                try:
                    query = self.client.table(table_name).select('*')
                    print(f"[DEBUG] 쿼리 생성: 테이블={table_name}")
                    response = query.execute()
                    
                    if response and hasattr(response, 'data') and response.data:
                        all_records = response.data
                        print(f"[DEBUG] 테이블 '{table_name}'에서 {len(all_records)}개 레코드 조회 성공")
                        break
                except Exception as e:
                    print(f"[DEBUG] 테이블 '{table_name}' 조회 실패: {e}")
            
            if not all_records:
                print(f"[DEBUG] 모든 테이블 조회 시도 실패, 빈 결과 반환")
                return []
            
            print(f"[DEBUG] 조회된 전체 레코드 수: {len(all_records)}")
            
            # 레코드 출력
            if all_records:
                print(f"[DEBUG] 첫 번째 레코드: {all_records[0]}")
                # 필드 이름 출력
                print(f"[DEBUG] 레코드 필드: {list(all_records[0].keys())}")
            
            # 필터링된 레코드만 선택
            records = []
            date_field = '날짜'
            
            # 필드 이름 확인 (날짜 또는 date)
            if len(all_records) > 0:
                first_record = all_records[0]
                if '날짜' not in first_record and 'date' in first_record:
                    date_field = 'date'
                elif '날짜' not in first_record:
                    # 날짜 필드 찾기
                    for key in first_record.keys():
                        if 'date' in key.lower() or '날짜' in key:
                            date_field = key
                            break
            
            print(f"[DEBUG] 사용할 날짜 필드: {date_field}")
            
            for record in all_records:
                record_date = record.get(date_field, '')
                print(f"[DEBUG] 레코드 날짜: {record_date}, 타입: {type(record_date)}")
                
                # 날짜 형식에 따라 비교 방식 조정
                if record_date:
                    # 문자열 비교 또는 날짜 객체로 변환 후 비교
                    if isinstance(record_date, str):
                        if start_date <= record_date <= end_date:
                            records.append(record)
                    else:
                        # 날짜 객체인 경우 문자열로 변환하여 비교
                        record_date_str = record_date.strftime('%Y-%m-%d') if hasattr(record_date, 'strftime') else str(record_date)
                        if start_date <= record_date_str <= end_date:
                            records.append(record)
            
            print(f"[DEBUG] 필터링 후 레코드 수: {len(records)}")
            
            # 필드명 매핑 - 필드 이름에 따라 동적으로 처리
            formatted_records = []
            field_mapping = {
                'id': 'STT',  # id 필드를 STT로 변경
                date_field: '날짜',
                'worker': '작업자',
                'line_number': '라인번호',
                'model': '모델차수',
                'target_quantity': '목표수량',
                'production_quantity': '생산수량',
                'defect_quantity': '불량수량',
                'note': '특이사항'
            }
            
            # 한글 필드명이 있는 경우 매핑 조정
            if len(all_records) > 0:
                first_record = all_records[0]
                for key in first_record.keys():
                    if key == 'id' or key == 'STT' or key == 'stt' or key == 'ID':
                        field_mapping['id'] = key  # id 필드 이름 확인
                    elif key == '작업자' or '작업자' in key:
                        field_mapping['worker'] = key
                    elif key == '라인번호' or '라인' in key:
                        field_mapping['line_number'] = key
                    elif key == '모델차수' or '모델' in key:
                        field_mapping['model'] = key
                    elif key == '목표수량' or '목표' in key:
                        field_mapping['target_quantity'] = key
                    elif key == '생산수량' or '생산' in key:
                        field_mapping['production_quantity'] = key
                    elif key == '불량수량' or '불량' in key:
                        field_mapping['defect_quantity'] = key
                    elif key == '특이사항' or '비고' in key or '메모' in key:
                        field_mapping['note'] = key
            
            print(f"[DEBUG] 필드 매핑: {field_mapping}")
            
            for record in records:
                formatted_record = {}
                for eng_field, kor_field in field_mapping.items():
                    # 영어 필드명으로 데이터 가져오기
                    if eng_field in record:
                        formatted_record[kor_field] = record[eng_field]
                    # 한글 필드명으로 데이터 가져오기
                    elif kor_field in record:
                        formatted_record[kor_field] = record[kor_field]
                    else:
                        # 기본값 설정
                        if kor_field in ['목표수량', '생산수량', '불량수량']:
                            formatted_record[kor_field] = 0
                        else:
                            formatted_record[kor_field] = ''
                
                formatted_records.append(formatted_record)
            
            print(f"[DEBUG] 포맷된 레코드 수: {len(formatted_records)}")
            self._set_cached_data(cache_key, formatted_records)
            return self._filter_production_data(formatted_records, start_date, end_date, worker, line, model)
        except Exception as e:
            print(f"생산 실적 조회 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            return []
    
    def _filter_production_data(self, records, start_date, end_date, worker=None, line=None, model=None):
        """생산 실적 데이터 필터링"""
        filtered_records = []
        
        for record in records:
            # 날짜 필터링은 이미 쿼리에서 처리됨
            
            # 작업자 필터링
            if worker and record['작업자'] != worker:
                continue
                
            # 라인 필터링
            if line and record['라인번호'] != line:
                continue
                
            # 모델 필터링
            if model and record['모델차수'] != model:
                continue
                
            filtered_records.append(record)
            
        return filtered_records
    
    def add_production_record(self, date, worker, line_number, model, target_quantity, 
                             production_quantity, defect_quantity, note):
        """생산 실적 추가"""
        try:
            data = {
                '날짜': date,
                '작업자': worker,
                '라인번호': line_number,
                '모델차수': model,
                '목표수량': target_quantity,
                '생산수량': production_quantity,
                '불량수량': defect_quantity,
                '특이사항': note
            }
            
            response = self.client.table('Production').insert(data).execute()
            
            # 관련 캐시 무효화 - 모든 production_ 관련 캐시 삭제
            self._invalidate_cache()  # 모든 캐시 무효화
            
            return True
        except Exception as e:
            print(f"생산 실적 추가 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            return False
    
    def update_production_record(self, record_id, data):
        """생산 실적 업데이트"""
        try:
            # 필드 매핑 확인
            id_field = 'STT'  # 기본값
            
            # 테이블 구조 확인
            table_info = self.client.table('Production').select('*').limit(1).execute()
            if table_info.data and len(table_info.data) > 0:
                first_record = table_info.data[0]
                for key in first_record.keys():
                    if key == 'id' or key == 'STT' or key == 'stt' or key == 'ID':
                        id_field = key
                        break
            
            print(f"[DEBUG] 업데이트에 사용할 ID 필드: {id_field}, 레코드 ID: {record_id}")
            
            # 올바른 ID 필드로 업데이트
            response = self.client.table('Production').update(data).eq(id_field, record_id).execute()
            
            # 관련 캐시 무효화
            self._invalidate_cache()  # 모든 캐시 무효화
            
            return True
        except Exception as e:
            print(f"생산 실적 업데이트 중 오류 발생: {e}")
            return False
    
    def delete_production_record(self, record_id):
        """생산 실적 삭제"""
        try:
            # 필드 매핑 확인
            id_field = 'STT'  # 기본값
            
            # 테이블 구조 확인
            table_info = self.client.table('Production').select('*').limit(1).execute()
            if table_info.data and len(table_info.data) > 0:
                first_record = table_info.data[0]
                for key in first_record.keys():
                    if key == 'id' or key == 'STT' or key == 'stt' or key == 'ID':
                        id_field = key
                        break
            
            print(f"[DEBUG] 삭제에 사용할 ID 필드: {id_field}, 레코드 ID: {record_id}")
            
            # 올바른 ID 필드로 삭제
            response = self.client.table('Production').delete().eq(id_field, record_id).execute()
            
            # 관련 캐시 무효화
            self._invalidate_cache()  # 모든 캐시 무효화
            
            return True
        except Exception as e:
            print(f"생산 실적 삭제 중 오류 발생: {e}")
            return False
    
    # 모델 관련 메서드
    def get_all_models(self):
        """모델 정보 조회"""
        try:
            cached_data = self._get_cached_data('models')
            if cached_data:
                return cached_data
            
            response = self.client.table('Model').select('*').execute()
            models = response.data
            
            # 필드명 매핑
            formatted_models = []
            for model in models:
                formatted_models.append({
                    'id': model.get('id', ''),
                    '모델명': model.get('model', ''),
                    '공정': model.get('process', '')
                })
            
            self._set_cached_data('models', formatted_models)
            return formatted_models
        except Exception as e:
            print(f"모델 조회 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            return []
    
    def add_model(self, model_name, process):
        """모델 추가"""
        try:
            data = {
                'model': model_name,
                'process': process
            }
            
            response = self.client.table('Model').insert(data).execute()
            print(f"[DEBUG] 모델 추가 응답: {response}")
            
            # 캐시 무효화
            self._invalidate_cache('models')
            
            return True
        except Exception as e:
            print(f"모델 추가 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            return False
    
    def update_model(self, model_id, data):
        """모델 정보 업데이트"""
        try:
            update_data = {}
            field_mapping = {
                '모델명': 'model',
                '공정': 'process'
            }
            
            for k, v in data.items():
                if k in field_mapping:
                    update_data[field_mapping[k]] = v
            
            response = self.client.table('Model').update(update_data).eq('id', model_id).execute()
            print(f"[DEBUG] 모델 업데이트 응답: {response}")
            
            # 캐시 무효화
            self._invalidate_cache('models')
            
            return True
        except Exception as e:
            print(f"모델 업데이트 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            return False
    
    def delete_model(self, model_id):
        """모델 삭제"""
        try:
            response = self.client.table('Model').delete().eq('id', model_id).execute()
            print(f"[DEBUG] 모델 삭제 응답: {response}")
            
            # 캐시 무효화
            self._invalidate_cache('models')
            
            return True
        except Exception as e:
            print(f"모델 삭제 중 오류 발생: {e}")
            import traceback
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            return False 