#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CNC_OP_KPI_SUPABASE 앱의 한국어 텍스트 추출 스크립트
번역 작업을 위한 JSON 형식의 번역 파일을 생성합니다.
"""

import os
import re
import json
from glob import glob

# 한국어 패턴 (한글 문자가 하나 이상 포함된 문자열)
KOR_PATTERN = re.compile(r'[가-힣]+')

# 추출할 한국어 텍스트를 저장할 딕셔너리
translations = {
    "ko": {},    # 원본 한국어
    "vi": {}     # 베트남어 번역 (빈 값으로 초기화)
}

# 무시할 디렉토리/파일 패턴
IGNORE_PATTERNS = [
    '__pycache__',
    '.git',
    '.venv',
    'venv',
    'env',
    '.ipynb_checkpoints',
    '.pytest_cache',
    'node_modules',
    '*.pyc',
    '*.swp',
    '.DS_Store',
    '*.json',
    '*.md',
]

# 검사할 파일 확장자
FILE_EXTENSIONS = ['.py', '.html', '.js', '.css']

# 무시할 문자열 패턴
IGNORE_STRINGS = [
    'print',
    'debug',
    'trace',
    'import',
    'from',
    'os.path',
    'st.'
]

def should_ignore_file(file_path):
    """파일을 무시해야 하는지 확인합니다."""
    for pattern in IGNORE_PATTERNS:
        if pattern.startswith('*'):
            if file_path.endswith(pattern[1:]):
                return True
        else:
            if pattern in file_path:
                return True
    return False

def should_ignore_string(text_string):
    """특정 텍스트 문자열을 무시해야 하는지 확인합니다."""
    for pattern in IGNORE_STRINGS:
        if pattern in text_string.lower():
            return True
    return False

def extract_korean_text(file_path):
    """파일에서 한국어 텍스트를 추출합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 문자열 추출 (작은따옴표)
        single_quoted = re.findall(r"'([^']*)'", content)
        
        # 문자열 추출 (큰따옴표)
        double_quoted = re.findall(r'"([^"]*)"', content)
        
        # 문자열 추출 (삼중 큰따옴표)
        triple_quoted = re.findall(r'"""([^"]*)"""', content)
        
        # 문자열 추출 (삼중 작은따옴표)
        triple_single_quoted = re.findall(r"'''([^']*)'''", content)
        
        all_strings = single_quoted + double_quoted + triple_quoted + triple_single_quoted
        
        # 한국어가 포함된 문자열만 필터링
        korean_strings = [s for s in all_strings if KOR_PATTERN.search(s) and not should_ignore_string(s)]
        
        return korean_strings
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def find_files_recursively(base_dir):
    """지정된 디렉토리에서 파일을 재귀적으로 찾습니다."""
    all_files = []
    
    for extension in FILE_EXTENSIONS:
        for file_path in glob(os.path.join(base_dir, f"**/*{extension}"), recursive=True):
            if not should_ignore_file(file_path):
                all_files.append(file_path)
                
    return all_files

def main():
    print("한국어 텍스트 추출을 시작합니다...")
    
    # 현재 디렉토리
    current_dir = os.getcwd()
    
    # 중요 디렉토리 목록
    important_dirs = ['pages', 'utils', '.']
    
    # 모든 파일 찾기
    all_files = []
    for dir_name in important_dirs:
        dir_path = os.path.join(current_dir, dir_name)
        if os.path.exists(dir_path):
            all_files.extend(find_files_recursively(dir_path))
    
    # 중복 제거
    all_files = list(set(all_files))
    
    # 각 파일에서 한국어 추출
    all_korean_texts = set()
    for file_path in all_files:
        korean_texts = extract_korean_text(file_path)
        all_korean_texts.update(korean_texts)
    
    print(f"총 {len(all_korean_texts)}개의 한국어 텍스트를 추출했습니다.")
    
    # 딕셔너리 구성
    for idx, text in enumerate(sorted(all_korean_texts)):
        key = f"text_{idx+1}"
        translations["ko"][key] = text
        translations["vi"][key] = ""  # 베트남어 번역은 빈 문자열로 초기화
    
    # JSON 파일로 저장
    with open('translations.json', 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)
    
    # Excel 형식 CSV 파일로도 저장 (번역 작업용)
    with open('translations_for_translator.csv', 'w', encoding='utf-8') as f:
        f.write("Key,Korean,Vietnamese\n")
        for key, text in translations["ko"].items():
            escaped_text = text.replace('"', '""')
            f.write(f'"{key}","{escaped_text}",""\n')
    
    print("번역 파일이 생성되었습니다:")
    print("1. translations.json - 최종적으로 앱에서 사용할 JSON 파일")
    print("2. translations_for_translator.csv - 번역가를 위한 CSV 파일")
    print("\n번역가는 CSV 파일의 Vietnamese 열에 번역을 작성하면 됩니다.")
    print("번역 작업 완료 후, 다음 명령어로 CSV를 다시 JSON으로 변환할 수 있습니다:")
    print("python convert_csv_to_json.py")

if __name__ == "__main__":
    main() 