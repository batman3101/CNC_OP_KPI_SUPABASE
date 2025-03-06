import bcrypt
from utils.supabase_db import SupabaseDB
import streamlit as st

def initialize_admin():
    """
    초기 관리자 계정 설정
    """
    try:
        admin_email = "zetooo1972@gmail.com"
        admin_password = "admin7472"
        admin_name = "관리자"
        
        db = SupabaseDB()
        existing_user = db.get_user(admin_email)
        
        if not existing_user:
            print("관리자 계정 생성 시도...")
            # 비밀번호 해싱
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(admin_password.encode('utf-8'), salt)
            
            # 관리자 계정 생성
            success = db.create_user(
                email=admin_email,
                password=admin_password,  # 해시하지 않은 원본 비밀번호 저장
                name=admin_name,
                role='admin'
            )
            if success:
                print("관리자 계정이 성공적으로 생성되었습니다.")
            else:
                print("관리자 계정 생성 실패")
        else:
            # 기존 계정의 비밀번호를 업데이트
            db.update_user_password(admin_email, admin_password)
            print("관리자 계정 비밀번호가 업데이트되었습니다.")
            
    except Exception as e:
        print(f"관리자 계정 초기화 중 오류 발생: {e}")

def check_password(email: str, password: str) -> bool:
    """
    사용자 인증을 확인하는 함수
    """
    try:
        # Google Sheets에서 사용자 정보 가져오기
        db = SupabaseDB()
        user = db.get_user(email)
        
        if user is None:
            print(f"사용자를 찾을 수 없음: {email}")
            return False
        
        # 단순 비밀번호 비교
        stored_password = user.get('password', '')
        print(f"저장된 비밀번호: {stored_password}")
        print(f"입력된 비밀번호: {password}")
        
        return stored_password == password
            
    except Exception as e:
        print(f"로그인 검증 중 오류 발생: {e}")
        return False

def create_user(email: str, password: str, name: str, role: str = 'user') -> bool:
    """
    새 사용자를 생성하는 함수
    """
    try:
        # 비밀번호 해싱
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        # Google Sheets에 사용자 정보 저장
        db = SupabaseDB()
        return db.create_user(email, hashed.decode('utf-8'), name, role)
    except Exception as e:
        print(f"사용자 생성 중 오류 발생: {e}")
        return False 