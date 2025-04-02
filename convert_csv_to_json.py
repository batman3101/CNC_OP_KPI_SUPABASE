#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
번역된 CSV 파일을 JSON 형식으로 변환하는 스크립트
번역가가 작업한 CSV 파일을 앱에서 사용할 JSON 파일로 변환합니다.
"""

import csv
import json
import os

def convert_csv_to_json():
    """번역된 CSV 파일을 JSON으로 변환합니다."""
    print("CSV 파일을 JSON으로 변환하는 중...")
    
    csv_file = 'translations_for_translator.csv'
    json_file = 'translations.json'
    
    # 입력 파일 확인
    if not os.path.exists(csv_file):
        print(f"오류: {csv_file} 파일을 찾을 수 없습니다.")
        return False
    
    # 기존 JSON 파일 백업
    if os.path.exists(json_file):
        backup_file = f"{json_file}.bak"
        try:
            with open(json_file, 'r', encoding='utf-8') as src:
                with open(backup_file, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            print(f"기존 JSON 파일을 {backup_file}으로 백업했습니다.")
        except Exception as e:
            print(f"백업 중 오류 발생: {e}")
    
    # 번역 딕셔너리 준비
    translations = {
        "ko": {},
        "vi": {}
    }
    
    # CSV 파일 읽기
    with open(csv_file, mode='r', encoding='utf-8') as file:
        # CSV 파일에서 첫 줄을 건너뛰기 위해 DictReader 사용
        reader = csv.DictReader(file)
        
        # 각 행에서 key, korean, vietnamese 값 추출
        for row in reader:
            key = row['Key']
            korean = row['Korean']
            vietnamese = row['Vietnamese']
            
            # 한국어와 베트남어를 각각 딕셔너리에 추가
            translations["ko"][key] = korean
            translations["vi"][key] = vietnamese
    
    # JSON 파일로 저장
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)
    
    print(f"변환 완료! {json_file} 파일이 생성되었습니다.")
    print(f"총 {len(translations['ko'])} 항목의 번역이 처리되었습니다.")
    
    # 번역되지 않은 항목 확인
    untranslated = sum(1 for key in translations["vi"] if not translations["vi"][key])
    if untranslated > 0:
        print(f"주의: {untranslated}개 항목이 아직 번역되지 않았습니다.")
    
    return True

if __name__ == "__main__":
    convert_csv_to_json() 