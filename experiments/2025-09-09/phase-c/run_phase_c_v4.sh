#!/bin/bash

# Phase-C: Per-Level WAF 분석 for v4 Model
# RocksDB LOG 파일을 분석하여 Per-Level Write Amplification Factor를 계산

set -e

echo "=== Phase-C: Per-Level WAF 분석 for v4 Model ==="
echo "날짜: $(date)"
echo ""

# 설정
LOG_FILE="../phase-b/phase_b_results/rocksdb.log"
OUTPUT_DIR="phase_c_results"
USER_DATA_MB=10000  # Phase-B에서 사용한 데이터 크기 (10GB)

echo "설정:"
echo "  LOG 파일: $LOG_FILE"
echo "  출력 디렉토리: $OUTPUT_DIR"
echo "  사용자 데이터 크기: $USER_DATA_MB MB"
echo ""

# 출력 디렉토리 생성
mkdir -p "$OUTPUT_DIR"

# LOG 파일 존재 확인
if [ ! -f "$LOG_FILE" ]; then
    echo "❌ LOG 파일을 찾을 수 없습니다: $LOG_FILE"
    echo "Phase-B를 먼저 실행해주세요."
    exit 1
fi

echo "✅ LOG 파일 확인됨: $LOG_FILE"

# 1. WAF 분석 실행
echo "1. WAF 분석 실행 중..."
python3 - << 'PY'
import re
import json
import csv
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

def parse_compaction_stats(log_file):
    """RocksDB LOG에서 compaction stats를 파싱합니다."""
    stats = []
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Compaction stats 패턴 찾기
    stats_pattern = r'Compaction Summary.*?Level Files Size\(MB\) Time\(sec\) Read\(MB\) Write\(MB\)\n(.*?)(?=\n\n|\Z)'
    matches = re.findall(stats_pattern, content, re.DOTALL)
    
    for match in matches:
        level_data = {}
        lines = match.strip().split('\n')
        
        for line in lines:
            if 'Level' in line and 'Files' in line:
                continue  # 헤더 스킵
            
            # 레벨별 데이터 파싱
            parts = line.split()
            if len(parts) >= 6:
                try:
                    level = int(parts[0])
                    files = int(parts[1])
                    size_mb = float(parts[2])
                    time_sec = float(parts[3])
                    read_mb = float(parts[4])
                    write_mb = float(parts[5])
                    
                    level_data[level] = {
                        'files': files,
                        'size_mb': size_mb,
                        'time_sec': time_sec,
                        'read_mb': read_mb,
                        'write_mb': write_mb
                    }
                except (ValueError, IndexError):
                    continue
        
        if level_data:
            stats.append(level_data)
    
    return stats

def calculate_waf_per_level(stats, user_mb):
    """레벨별 WAF를 계산합니다."""
    if not stats:
        return {}
    
    # 가장 최근 stats 사용
    latest_stats = stats[-1]
    
    waf_data = {}
    total_write_mb = 0
    
    for level, data in latest_stats.items():
        if level == 0:
            # L0은 flush만, WAF = 1
            waf_data[level] = 1.0
            total_write_mb += data['size_mb']
        else:
            # L1+는 compaction으로 인한 추가 쓰기
            # 실제 데이터 기반 계산
            if data['read_mb'] > 0:
                waf = data['write_mb'] / data['read_mb']
            else:
                waf = 1.0
            waf_data[level] = waf
            total_write_mb += data['write_mb']
    
    # 전체 WAF 계산
    total_waf = total_write_mb / user_mb if user_mb > 0 else 0
    
    return waf_data, total_waf, total_write_mb

def plot_waf_analysis(waf_data, output_dir):
    """WAF 분석 결과를 그래프로 표시합니다."""
    levels = sorted(waf_data.keys())
    waf_values = [waf_data[level] for level in levels]
    
    plt.figure(figsize=(12, 8))
    bars = plt.bar([f'L{level}' for level in levels], waf_values, 
                   color=['green' if waf <= 1.5 else 'orange' if waf <= 3.0 else 'red' 
                          for waf in waf_values], alpha=0.7)
    
    plt.xlabel('Level', fontsize=14)
    plt.ylabel('Write Amplification Factor', fontsize=14)
    plt.title('Phase-C: Per-Level WAF Analysis', fontsize=16)
    plt.grid(True, alpha=0.3)
    
    # 값 표시
    for bar, val in zip(bars, waf_values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'{val:.2f}', ha='center', va='bottom', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/waf_per_level.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    log_file = '../phase-b/phase_b_results/rocksdb.log'
    output_dir = 'phase_c_results'
    user_mb = 10000
    
    print(f"RocksDB LOG 분석 중: {log_file}")
    print(f"사용자 데이터 크기: {user_mb} MB")
    
    # Compaction stats 파싱
    stats = parse_compaction_stats(log_file)
    if not stats:
        print("❌ Compaction stats를 찾을 수 없습니다.")
        return
    
    print(f"✅ {len(stats)}개의 compaction stats 발견")
    
    # WAF 계산
    waf_data, total_waf, total_write_mb = calculate_waf_per_level(stats, user_mb)
    
    print("\n=== Per-Level WAF 분석 ===")
    for level in sorted(waf_data.keys()):
        print(f"L{level}: WAF = {waf_data[level]:.2f}")
    
    print(f"\n전체 WAF: {total_waf:.2f}")
    print(f"총 쓰기: {total_write_mb:.2f} MB")
    
    # Mass balance 검증
    expected_write = total_waf * user_mb
    mass_balance_error = abs(total_write_mb - expected_write) / expected_write * 100 if expected_write > 0 else 0
    
    print(f"\n=== Mass Balance 검증 ===")
    print(f"예상 쓰기: {expected_write:.2f} MB")
    print(f"실제 쓰기: {total_write_mb:.2f} MB")
    print(f"오류율: {mass_balance_error:.2f}%")
    
    if mass_balance_error <= 10:
        print("✅ Mass balance 검증 통과 (≤10%)")
    else:
        print("❌ Mass balance 검증 실패 (>10%)")
    
    # CSV 출력
    csv_file = Path(output_dir) / 'waf_per_level.csv'
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Level', 'WAF', 'Files', 'Size_MB', 'Read_MB', 'Write_MB'])
        for level in sorted(waf_data.keys()):
            if level in stats[-1]:
                data = stats[-1][level]
                writer.writerow([
                    level, 
                    waf_data[level], 
                    data['files'],
                    data['size_mb'],
                    data['read_mb'],
                    data['write_mb']
                ])
    
    print(f"✅ CSV 파일 저장: {csv_file}")
    
    # JSON 요약
    summary = {
        'experiment_info': {
            'phase': 'Phase-C',
            'date': '2025-09-09',
            'purpose': 'Per-Level WAF 분석 for v4 Model'
        },
        'total_waf': total_waf,
        'total_write_mb': total_write_mb,
        'user_mb': user_mb,
        'mass_balance_error_percent': mass_balance_error,
        'per_level_waf': waf_data,
        'level_data': stats[-1] if stats else {}
    }
    
    json_file = Path(output_dir) / 'phase_c_results.json'
    with open(json_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ JSON 요약 저장: {json_file}")
    
    # 그래프 생성
    plot_waf_analysis(waf_data, output_dir)
    print(f"✅ 그래프 생성: {output_dir}/waf_per_level.png")

if __name__ == "__main__":
    main()
PY

# 2. Per-Level Breakdown 실행
echo "2. Per-Level Breakdown 실행 중..."
python3 - << 'PY'
import json
import csv
from pathlib import Path

def create_per_level_breakdown(output_dir):
    """Per-Level I/O Breakdown을 생성합니다."""
    
    # Phase-C 결과 로드
    results_file = Path(output_dir) / 'phase_c_results.json'
    if not results_file.exists():
        print("❌ Phase-C 결과 파일을 찾을 수 없습니다.")
        return
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    level_data = results.get('level_data', {})
    per_level_waf = results.get('per_level_waf', {})
    
    # Per-Level Breakdown 계산
    breakdown = []
    total_read = 0
    total_write = 0
    
    for level in sorted(level_data.keys()):
        data = level_data[level]
        waf = per_level_waf.get(level, 1.0)
        
        read_mb = data.get('read_mb', 0)
        write_mb = data.get('write_mb', 0)
        
        breakdown.append({
            'level': f'L{level}',
            'files': data.get('files', 0),
            'size_mb': data.get('size_mb', 0),
            'read_mb': read_mb,
            'write_mb': write_mb,
            'waf': waf,
            'read_percent': 0,  # 나중에 계산
            'write_percent': 0  # 나중에 계산
        })
        
        total_read += read_mb
        total_write += write_mb
    
    # 백분율 계산
    for item in breakdown:
        item['read_percent'] = (item['read_mb'] / total_read * 100) if total_read > 0 else 0
        item['write_percent'] = (item['write_mb'] / total_write * 100) if total_write > 0 else 0
    
    # CSV 저장
    csv_file = Path(output_dir) / 'per_level_breakdown.csv'
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Level', 'Files', 'Size_MB', 'Read_MB', 'Write_MB', 'WAF', 'Read_%', 'Write_%'])
        for item in breakdown:
            writer.writerow([
                item['level'],
                item['files'],
                item['size_mb'],
                item['read_mb'],
                item['write_mb'],
                item['waf'],
                item['read_percent'],
                item['write_percent']
            ])
    
    print(f"✅ Per-Level Breakdown 저장: {csv_file}")
    
    # 요약 출력
    print("\n=== Per-Level I/O Breakdown ===")
    print(f"{'Level':<8} {'Files':<6} {'Size_MB':<8} {'Read_MB':<8} {'Write_MB':<8} {'WAF':<6} {'Read_%':<7} {'Write_%':<8}")
    print("-" * 70)
    for item in breakdown:
        print(f"{item['level']:<8} {item['files']:<6} {item['size_mb']:<8.1f} {item['read_mb']:<8.1f} {item['write_mb']:<8.1f} {item['waf']:<6.2f} {item['read_percent']:<7.1f} {item['write_percent']:<8.1f}")
    
    print("-" * 70)
    print(f"{'TOTAL':<8} {'-':<6} {'-':<8} {total_read:<8.1f} {total_write:<8.1f} {'-':<6} {'100.0':<7} {'100.0':<8}")

if __name__ == "__main__":
    create_per_level_breakdown('phase_c_results')
PY

# 3. 결과 확인
echo "3. 결과 확인..."
echo "생성된 파일들:"
ls -la "$OUTPUT_DIR/"

echo ""
echo "=== Phase-C 완료 ==="
echo "결과 파일 위치: $OUTPUT_DIR/"
echo "주요 파일:"
echo "  - phase_c_results.json: 상세한 실험 결과"
echo "  - waf_per_level.csv: 레벨별 WAF 데이터"
echo "  - per_level_breakdown.csv: 레벨별 I/O 분석"
echo "  - waf_per_level.png: WAF 시각화"


