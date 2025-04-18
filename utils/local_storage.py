import json
import os
from datetime import datetime
import pandas as pd
import uuid

class ProductionStorage:
    def __init__(self):
        self.file_path = 'production_data.json'
        self.production_data = self._load_data()
    
    def _load_data(self):
        """저장된 생산실적 데이터 로드"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 숫자 데이터 타입 변환
                    for record in data:
                        record['목표수량'] = int(record['목표수량'])
                        record['생산수량'] = int(record['생산수량'])
                        record['불량수량'] = int(record['불량수량'])
                    return data
            except Exception as e:
                print(f"데이터 로드 중 오류 발생: {e}")
                return []
        return []
    
    def _save_data(self):
        """생산실적 데이터 저장"""
        try:
            # 저장 전 데이터 타입 문자열로 변환
            save_data = []
            for record in self.production_data:
                save_record = record.copy()
                save_record['목표수량'] = str(save_record['목표수량'])
                save_record['생산수량'] = str(save_record['생산수량'])
                save_record['불량수량'] = str(save_record['불량수량'])
                save_data.append(save_record)
                
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"데이터 저장 중 오류 발생: {e}")
    
    def add_record(self, date, worker, line, model, target_qty, actual_qty, defect_qty, notes):
        """새로운 생산실적 추가"""
        try:
            record = {
                'STT': len(self.production_data) + 1,
                '날짜': date.strftime('%Y-%m-%d') if isinstance(date, datetime) else str(date),
                '작업자': str(worker),
                '라인번호': str(line),
                '모델차수': str(model),
                '목표수량': int(target_qty),
                '생산수량': int(actual_qty),
                '불량수량': int(defect_qty),
                '특이사항': str(notes) if notes else ""
            }
            self.production_data.append(record)
            self._save_data()
            return True
        except Exception as e:
            print(f"레코드 추가 중 오류 발생: {e}")
            return False
    
    def get_records(self, start_date=None, end_date=None, worker=None, line=None, model=None):
        """생산실적 조회"""
        try:
            if start_date:
                start_date = pd.to_datetime(start_date).date()
            if end_date:
                end_date = pd.to_datetime(end_date).date()
            
            filtered_records = []
            for record in self.production_data:
                try:
                    record_date = pd.to_datetime(record['날짜']).date()
                    
                    if start_date and record_date < start_date:
                        continue
                    if end_date and record_date > end_date:
                        continue
                    if worker and record['작업자'] != worker:
                        continue
                    if line and record['라인번호'] != line:
                        continue
                    if model and record['모델차수'] != model:
                        continue
                    
                    filtered_records.append(record)
                except Exception as e:
                    print(f"레코드 필터링 중 오류 발생: {e}")
                    continue
            
            return filtered_records
        except Exception as e:
            print(f"레코드 조회 중 오류 발생: {e}")
            return []
    
    def get_all_records(self):
        """모든 생산실적 조회"""
        return self.production_data.copy()

class LocalStorage:
    def __init__(self):
        self.data_dir = 'data'
        os.makedirs(self.data_dir, exist_ok=True)
    
    def save_production_records(self, records):
        """생산 실적 데이터 로컬 파일로 저장"""
        try:
            file_path = os.path.join(self.data_dir, 'production_records.json')
            with open(file_path, 'w', encoding='utf-8') as f:
                # 숫자 필드는 문자열로 변환하여 저장
                save_records = []
                for record in records:
                    save_record = record.copy()
                    # 필수 필드가 없는 경우 추가
                    if 'id' not in save_record:
                        save_record['id'] = str(uuid.uuid4())
                    if '목표수량' in save_record and not isinstance(save_record['목표수량'], str):
                        save_record['목표수량'] = str(save_record['목표수량'])
                    if '생산수량' in save_record and not isinstance(save_record['생산수량'], str):
                        save_record['생산수량'] = str(save_record['생산수량']) 
                    if '불량수량' in save_record and not isinstance(save_record['불량수량'], str):
                        save_record['불량수량'] = str(save_record['불량수량'])
                    save_records.append(save_record)
                
                json.dump(save_records, f, ensure_ascii=False, indent=2)
            print(f"[INFO] 생산 실적 데이터 {len(records)}개 저장 완료: {file_path}")
            return True
        except Exception as e:
            print(f"[ERROR] 생산 실적 데이터 저장 중 오류: {e}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def load_production_records(self):
        """생산 실적 데이터 로컬 파일에서 로드"""
        try:
            file_path = os.path.join(self.data_dir, 'production_records.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    records = json.load(f)
                    # 숫자 필드 변환
                    for record in records:
                        # 필수 필드가 없는 경우 추가
                        if 'id' not in record:
                            record['id'] = str(uuid.uuid4())
                        if '목표수량' in record:
                            record['목표수량'] = int(record['목표수량'])
                        if '생산수량' in record:
                            record['생산수량'] = int(record['생산수량'])
                        if '불량수량' in record:
                            record['불량수량'] = int(record['불량수량'])
                print(f"[INFO] 생산 실적 데이터 {len(records)}개 로드 완료: {file_path}")
                return records
            else:
                print(f"[INFO] 생산 실적 데이터 파일이 없습니다: {file_path}")
                return []
        except Exception as e:
            print(f"[ERROR] 생산 실적 데이터 로드 중 오류: {e}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def save_worker_records(self, records):
        """작업자 데이터 로컬 파일로 저장"""
        try:
            file_path = os.path.join(self.data_dir, 'worker_records.json')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            print(f"[INFO] 작업자 데이터 {len(records)}개 저장 완료: {file_path}")
            return True
        except Exception as e:
            print(f"[ERROR] 작업자 데이터 저장 중 오류: {e}")
            return False
    
    def load_worker_records(self):
        """작업자 데이터 로컬 파일에서 로드"""
        try:
            file_path = os.path.join(self.data_dir, 'worker_records.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    records = json.load(f)
                print(f"[INFO] 작업자 데이터 {len(records)}개 로드 완료: {file_path}")
                return records
            else:
                print(f"[INFO] 작업자 데이터 파일이 없습니다: {file_path}")
                return []
        except Exception as e:
            print(f"[ERROR] 작업자 데이터 로드 중 오류: {e}")
            return []
    
    def save_model_records(self, records):
        """모델 데이터 로컬 파일로 저장"""
        try:
            file_path = os.path.join(self.data_dir, 'model_records.json')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            print(f"[INFO] 모델 데이터 {len(records)}개 저장 완료: {file_path}")
            return True
        except Exception as e:
            print(f"[ERROR] 모델 데이터 저장 중 오류: {e}")
            return False
    
    def load_model_records(self):
        """모델 데이터 로컬 파일에서 로드"""
        try:
            file_path = os.path.join(self.data_dir, 'model_records.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    records = json.load(f)
                print(f"[INFO] 모델 데이터 {len(records)}개 로드 완료: {file_path}")
                return records
            else:
                print(f"[INFO] 모델 데이터 파일이 없습니다: {file_path}")
                return []
        except Exception as e:
            print(f"[ERROR] 모델 데이터 로드 중 오류: {e}")
            return [] 