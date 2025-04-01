"""
공통 유틸리티 함수 모듈
"""
import os
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

def format_date(date_str):
    """날짜 포맷팅"""
    try:
        if isinstance(date_str, datetime):
            return date_str.strftime('%Y-%m-%d')
        return pd.to_datetime(date_str).strftime('%Y-%m-%d')
    except:
        return str(date_str)

def format_number(number, decimal_places=0):
    """숫자 포맷팅"""
    try:
        if decimal_places > 0:
            return f"{float(number):,.{decimal_places}f}"
        return f"{int(number):,}"
    except:
        return str(number)

def format_percentage(value, decimal_places=1):
    """퍼센트 포맷팅"""
    try:
        return f"{float(value):.{decimal_places}f}%"
    except:
        return f"{value}%"

def calculate_efficiency(production, target):
    """작업 효율 계산"""
    try:
        if float(target) == 0:
            return 0
        return (float(production) / float(target)) * 100
    except:
        return 0

def calculate_defect_rate(production, defect):
    """불량률 계산"""
    try:
        if float(production) == 0:
            return 0
        return (float(defect) / float(production)) * 100
    except:
        return 0

def get_date_range(days=7):
    """날짜 범위 생성"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

def create_data_dir():
    """데이터 디렉토리 생성"""
    os.makedirs('data', exist_ok=True)
    return os.path.abspath('data') 