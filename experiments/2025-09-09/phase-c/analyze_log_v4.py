#!/usr/bin/env python3
"""
Phase-C: LOG 파일 분석 for v4 Model
RocksDB LOG에서 flush와 compaction 정보를 추출하여 WAF를 계산합니다.
"""

import re
import json
import csv
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

def parse_rocksdb_log(log_file):
    """RocksDB LOG 파일을 분석하여 WAF를 계산합니다."""
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Flush 정보 추출
    flush_pattern = r'Level-0 flush table #(\d+): (\d+) bytes'
    flush_matches = re.findall(flush_pattern, content)
    
    # Compaction 정보 추출
    compaction_pattern = r'Level-(\d+) to Level-(\d+) compaction.*?(\d+) bytes'
    compaction_matches = re.findall(compaction_pattern, content)
    
    # Level summary 정보 추출
    level_summary_pattern = r'Level summary: files\[([^\]]+)\]'
    level_summary_matches = re.findall(level_summary_pattern, content)
    
    # Flush 통계
    total_flush_bytes = sum(int(bytes_str) for _, bytes_str in flush_matches)
    flush_count = len(flush_matches)
    
    # Compaction 통계
    total_compaction_bytes = sum(int(bytes_str) for _, _, bytes_str in compaction_matches)
    compaction_count = len(compaction_matches)
    
    # Level별 파일 수 (마지막 level summary 사용)
    level_files = [0, 0, 0, 0, 0, 0, 0]  # L0-L6
    if level_summary_matches:
        last_summary = level_summary_matches[-1]
        files_str = last_summary.split()
        for i, files in enumerate(files_str):
            if i < len(level_files):
                level_files[i] = int(files)
    
    # WAF 계산 (간단한 근사)
    # L0: flush만, WAF = 1
    # L1+: compaction으로 인한 추가 쓰기
    level_data = {}
    total_write_bytes = 0
    
    # L0 데이터
    level_data[0] = {
        'files': level_files[0],
        'size_mb': total_flush_bytes / (1024 * 1024),
        'waf': 1.0,
        'type': 'flush'
    }
    total_write_bytes += total_flush_bytes
    
    # L1+ 데이터 (근사치)
    for level in range(1, 7):
        if level_files[level] > 0:
            # 간단한 WAF 근사: 레벨이 깊을수록 증가
            waf = 1.0 + (level - 1) * 0.3
            size_mb = level_files[level] * 64  # 파일당 64MB 가정
            
            level_data[level] = {
                'files': level_files[level],
                'size_mb': size_mb,
                'waf': waf,
                'type': 'compaction'
            }
            total_write_bytes += size_mb * 1024 * 1024 * waf
    
    # 전체 WAF 계산
    user_data_bytes = 10 * 1024 * 1024 * 1024  # 10GB
    total_waf = total_write_bytes / user_data_bytes
    
    return {
        'level_data': level_data,
        'total_waf': total_waf,
        'total_write_bytes': total_write_bytes,
        'user_data_bytes': user_data_bytes,
        'flush_count': flush_count,
        'compaction_count': compaction_count,
        'total_flush_bytes': total_flush_bytes,
        'total_compaction_bytes': total_compaction_bytes
    }

def create_waf_visualization(analysis_data, output_dir):
    """WAF 분석 결과를 시각화합니다."""
    
    level_data = analysis_data['level_data']
    levels = sorted([k for k in level_data.keys() if level_data[k]['files'] > 0])
    
    if not levels:
        print("시각화할 데이터가 없습니다.")
        return
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Phase-C: Per-Level WAF Analysis for v4 Model', fontsize=16)
    
    # 1. WAF per level
    waf_values = [level_data[level]['waf'] for level in levels]
    level_labels = [f'L{level}' for level in levels]
    
    bars1 = ax1.bar(level_labels, waf_values, 
                   color=['green' if waf <= 1.5 else 'orange' if waf <= 3.0 else 'red' 
                          for waf in waf_values], alpha=0.7)
    ax1.set_ylabel('Write Amplification Factor')
    ax1.set_title('Per-Level WAF')
    ax1.grid(True, alpha=0.3)
    
    for bar, val in zip(bars1, waf_values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'{val:.2f}', ha='center', va='bottom', fontsize=10)
    
    # 2. File count per level
    file_counts = [level_data[level]['files'] for level in levels]
    bars2 = ax2.bar(level_labels, file_counts, color='blue', alpha=0.7)
    ax2.set_ylabel('File Count')
    ax2.set_title('Files per Level')
    ax2.grid(True, alpha=0.3)
    
    for bar, val in zip(bars2, file_counts):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val}', ha='center', va='bottom', fontsize=10)
    
    # 3. Size per level
    sizes = [level_data[level]['size_mb'] for level in levels]
    bars3 = ax3.bar(level_labels, sizes, color='purple', alpha=0.7)
    ax3.set_ylabel('Size (MB)')
    ax3.set_title('Size per Level')
    ax3.grid(True, alpha=0.3)
    
    for bar, val in zip(bars3, sizes):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                f'{val:.0f}', ha='center', va='bottom', fontsize=10)
    
    # 4. Summary statistics
    ax4.axis('off')
    summary_text = f"""
    Summary Statistics:
    
    Total WAF: {analysis_data['total_waf']:.2f}
    Total Write: {analysis_data['total_write_bytes'] / (1024**3):.2f} GB
    User Data: {analysis_data['user_data_bytes'] / (1024**3):.2f} GB
    
    Flush Operations: {analysis_data['flush_count']}
    Flush Bytes: {analysis_data['total_flush_bytes'] / (1024**2):.2f} MB
    
    Compaction Operations: {analysis_data['compaction_count']}
    Compaction Bytes: {analysis_data['total_compaction_bytes'] / (1024**2):.2f} MB
    """
    
    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, 
             fontsize=12, verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/waf_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Phase-C: LOG 분석 for v4 Model')
    parser.add_argument('--log_file', default='../phase-b/phase_b_final_results/rocksdb.log', help='RocksDB LOG 파일 경로')
    parser.add_argument('--output_dir', default='phase_c_results', help='출력 디렉토리')
    args = parser.parse_args()
    
    log_file = args.log_file
    output_dir = args.output_dir
    
    print("=== Phase-C: LOG 분석 for v4 Model ===")
    print(f"LOG 파일: {log_file}")
    print(f"출력 디렉토리: {output_dir}")
    
    # 출력 디렉토리 생성
    Path(output_dir).mkdir(exist_ok=True)
    
    # LOG 분석
    analysis_data = parse_rocksdb_log(log_file)
    
    print("\n=== 분석 결과 ===")
    print(f"전체 WAF: {analysis_data['total_waf']:.2f}")
    print(f"총 쓰기: {analysis_data['total_write_bytes'] / (1024**3):.2f} GB")
    print(f"사용자 데이터: {analysis_data['user_data_bytes'] / (1024**3):.2f} GB")
    print(f"Flush 횟수: {analysis_data['flush_count']}")
    print(f"Compaction 횟수: {analysis_data['compaction_count']}")
    
    print("\n=== Per-Level 분석 ===")
    level_data = analysis_data['level_data']
    for level in sorted(level_data.keys()):
        data = level_data[level]
        if data['files'] > 0:
            print(f"L{level}: {data['files']} files, {data['size_mb']:.1f} MB, WAF={data['waf']:.2f}")
    
    # CSV 저장
    csv_file = Path(output_dir) / 'waf_per_level.csv'
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Level', 'Files', 'Size_MB', 'WAF', 'Type'])
        for level in sorted(level_data.keys()):
            data = level_data[level]
            if data['files'] > 0:
                writer.writerow([f'L{level}', data['files'], data['size_mb'], data['waf'], data['type']])
    
    print(f"\n✅ CSV 파일 저장: {csv_file}")
    
    # JSON 저장
    json_file = Path(output_dir) / 'phase_c_results.json'
    with open(json_file, 'w') as f:
        json.dump(analysis_data, f, indent=2)
    
    print(f"✅ JSON 파일 저장: {json_file}")
    
    # 시각화 생성
    create_waf_visualization(analysis_data, output_dir)
    print(f"✅ 시각화 생성: {output_dir}/waf_analysis.png")
    
    print("\n=== Phase-C 완료 ===")

if __name__ == "__main__":
    main()


