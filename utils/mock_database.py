import pandas as pd
from datetime import datetime, timedelta
import random

class MockDatabase:
    def __init__(self):
        self.users = []
        self.workers = []
        self.production_records = []
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        # 사용자 데이터 초기화
        self.users = [
            {'email': 'admin@example.com', 'password': 'admin123', 'name': '관리자', 'role': 'admin'},
            {'email': 'user1@example.com', 'password': 'user123', 'name': '사용자1', 'role': 'user'},
        ]
        
        # 작업자 데이터 초기화
        workers = [
            {'STT': 1, '사번': 'W001', '이름': '김작업', '부서': '생산1팀', '라인번호': 'L1'},
            {'STT': 2, '사번': 'W002', '이름': '이생산', '부서': '생산1팀', '라인번호': 'L2'},
            {'STT': 3, '사번': 'W003', '이름': '박공정', '부서': '생산2팀', '라인번호': 'L1'},
            {'STT': 4, '사번': 'W004', '이름': '최조립', '부서': '생산2팀', '라인번호': 'L2'},
        ]
        self.workers = workers
        
        # 생산 실적 데이터 초기화
        models = ['A모델', 'B모델', 'C모델']
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1년치 데이터
        
        records = []
        current_date = start_date
        stt = 1
        
        while current_date <= end_date:
            for worker in workers:
                target_qty = random.randint(80, 120)
                actual_qty = random.randint(70, target_qty)
                defect_qty = random.randint(0, 5)
                
                record = {
                    'STT': stt,
                    '날짜': current_date.strftime('%Y-%m-%d'),
                    '작업자': worker['이름'],
                    '라인번호': worker['라인번호'],
                    '모델차수': random.choice(models),
                    '목표수량': target_qty,
                    '생산수량': actual_qty,
                    '불량수량': defect_qty,
                    '특이사항': "정상 생산" if defect_qty == 0 else "품질 이슈 발생"
                }
                records.append(record)
                stt += 1
            current_date += timedelta(days=1)
        
        self.production_records = records
    
    def get_all_users(self):
        return self.users
    
    def get_all_workers(self):
        return self.workers
    
    def get_production_records(self, start_date, end_date, worker=None, line=None, model=None):
        start_date = pd.to_datetime(start_date).date()
        end_date = pd.to_datetime(end_date).date()
        
        filtered_records = []
        for record in self.production_records:
            record_date = pd.to_datetime(record['날짜']).date()
            
            if start_date <= record_date <= end_date:
                if worker and record['작업자'] != worker:
                    continue
                if line and record['라인번호'] != line:
                    continue
                if model and record['모델차수'] != model:
                    continue
                filtered_records.append(record)
        
        return filtered_records
    
    def get_line_numbers(self):
        return sorted(list(set(w['라인번호'] for w in self.workers)))
    
    def get_models(self):
        return sorted(list(set(r['모델차수'] for r in self.production_records)))
    
    def create_production_record(self, date, worker, line, model, target_qty, actual_qty, defect_qty, notes):
        stt = len(self.production_records) + 1
        record = {
            'STT': stt,
            '날짜': date.strftime('%Y-%m-%d'),
            '작업자': worker,
            '라인번호': line,
            '모델차수': model,
            '목표수량': target_qty,
            '생산수량': actual_qty,
            '불량수량': defect_qty,
            '특이사항': notes
        }
        self.production_records.append(record)
        return True
    
    def create_worker(self, emp_id, name, dept, line):
        stt = len(self.workers) + 1
        worker = {
            'STT': stt,
            '사번': emp_id,
            '이름': name,
            '부서': dept,
            '라인번호': line
        }
        self.workers.append(worker)
        return True
    
    def update_worker(self, name, new_dept, new_line):
        for worker in self.workers:
            if worker['이름'] == name:
                worker['부서'] = new_dept
                worker['라인번호'] = new_line
                return True
        return False 