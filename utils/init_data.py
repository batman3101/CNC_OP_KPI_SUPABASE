from datetime import datetime, timedelta
import random

def initialize_test_data(db):
    """테스트 데이터 초기화"""
    # 작업자 데이터 생성
    workers = [
        ('W001', '김작업', '생산1팀', 'L1'),
        ('W002', '이생산', '생산1팀', 'L2'),
        ('W003', '박공정', '생산2팀', 'L1'),
        ('W004', '최조립', '생산2팀', 'L2'),
    ]
    
    for emp_id, name, dept, line in workers:
        db.create_worker(emp_id, name, dept, line)
    
    # 생산 실적 데이터 생성
    models = ['A모델', 'B모델', 'C모델']
    
    # 최근 3개월 데이터 생성
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    current_date = start_date
    
    while current_date <= end_date:
        for worker in workers:
            target_qty = random.randint(80, 120)
            actual_qty = random.randint(70, target_qty)
            defect_qty = random.randint(0, 5)
            
            db.create_production_record(
                current_date,
                worker[1],  # 작업자 이름
                worker[3],  # 라인번호
                random.choice(models),
                target_qty,
                actual_qty,
                defect_qty,
                "정상 생산" if defect_qty == 0 else "품질 이슈 발생"
            )
        current_date += timedelta(days=1)

# 앱 시작 시 테스트 데이터 초기화
if __name__ == "__main__":
    from utils.supabase_db import SupabaseDB
    db = SupabaseDB()
    initialize_test_data(db) 