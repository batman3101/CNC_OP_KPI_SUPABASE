import json
import os
from utils.supabase_db import SupabaseDB

def load_user_data():
    try:
        # Supabase에서 사용자 데이터 로드
        db = SupabaseDB()
        users = db.get_all_users()
        
        # 사용자 데이터 형식 변환
        user_accounts = {}
        for user in users:
            email = user.get('이메일', '')
            if email:
                user_accounts[email] = {
                    "password": user.get('비밀번호', ''),
                    "name": user.get('이름', ''),
                    "department": user.get('권한', ''),
                    "created_at": user.get('created_at', '')
                }
        
        print(f"[DEBUG] 로드된 사용자 데이터: {len(user_accounts)}개")
        return user_accounts
    except Exception as e:
        print(f"사용자 데이터 로드 실패: {str(e)}")
        import traceback
        print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
        
        # 로컬 파일에서 로드 시도 (백업)
        try:
            if os.path.exists('data/users.json'):
                with open('data/users.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}

def save_user_data(user_data):
    try:
        # Supabase에 사용자 데이터 저장
        db = SupabaseDB()
        
        # 기존 사용자 데이터 로드
        existing_users = {user.get('이메일', ''): user for user in db.get_all_users()}
        
        # 사용자 데이터 업데이트
        for email, user_info in user_data.items():
            if email in existing_users:
                # 기존 사용자 업데이트
                update_data = {
                    '비밀번호': user_info.get('password', ''),
                    '이름': user_info.get('name', ''),
                    '권한': user_info.get('department', '')
                }
                db.update_user(email, update_data)
            else:
                # 새 사용자 추가
                db.add_user(
                    email=email,
                    password=user_info.get('password', ''),
                    name=user_info.get('name', ''),
                    role=user_info.get('department', '')
                )
        
        # 삭제된 사용자 처리
        for email in existing_users:
            if email not in user_data:
                db.delete_user(email)
        
        # 로컬 파일에도 백업
        os.makedirs('data', exist_ok=True)
        with open('data/users.json', 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"사용자 데이터 저장 실패: {str(e)}")
        import traceback
        print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
        return False 