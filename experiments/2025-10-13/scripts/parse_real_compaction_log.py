#!/usr/bin/env python3
"""
실제 RocksDB LOG 파일에서 Compaction 데이터 파싱 및 시각화

LOG 파일에서 'Compaction Stats [default]' 섹션을 파싱하여
시간별 레벨별 compaction 처리량을 추출하고 시각화합니다.
"""

import re
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import sys
import os
from collections import defaultdict

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


def parse_rocksdb_log(log_file_path):
    """
    RocksDB LOG 파일에서 Compaction Stats 파싱
    
    Returns:
        dict: {
            'timestamps': [...],  # 시간 (초)
            'L0': {'read_gb': [...], 'write_gb': [...]},
            'L1': {...},
            ...
        }
    """
    
    print(f"LOG 파일 파싱 중: {log_file_path}")
    
    compaction_records = []
    
    with open(log_file_path, 'r', errors='ignore') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Compaction Stats 섹션 찾기
        if '** Compaction Stats [default] **' in line:
            # 다음 줄이 헤더
            i += 1
            if i >= len(lines):
                break
            
            header = lines[i]
            if 'Level' in header and 'Files' in header:
                i += 2  # 구분선 건너뛰기
                
                # Uptime 찾기 (현재 기록의 시간)
                uptime_sec = None
                for j in range(i, min(i+30, len(lines))):
                    if 'Uptime(secs):' in lines[j]:
                        match = re.search(r'Uptime\(secs\):\s+([\d.]+)\s+total', lines[j])
                        if match:
                            uptime_sec = float(match.group(1))
                        break
                
                if uptime_sec is None:
                    i += 1
                    continue
                
                # 레벨 데이터 파싱
                level_stats = {}
                while i < len(lines):
                    level_line = lines[i]
                    
                    # Sum 라인이 나오면 종료
                    if level_line.strip().startswith('Sum'):
                        break
                    
                    # 레벨 라인 파싱
                    match = re.match(r'\s*(L\d+)\s+', level_line)
                    if match:
                        level = match.group(1)
                        parts = level_line.split()
                        
                        try:
                            # Read(GB)와 Write(GB) 추출
                            read_gb = float(parts[4])   # Read(GB) 컬럼
                            write_gb = float(parts[7])  # Write(GB) 컬럼
                            
                            level_stats[level] = {
                                'read_gb': read_gb,
                                'write_gb': write_gb
                            }
                        except (IndexError, ValueError):
                            pass
                    
                    i += 1
                
                if level_stats:
                    compaction_records.append({
                        'time': uptime_sec,
                        'levels': level_stats
                    })
        
        i += 1
    
    print(f"✓ {len(compaction_records)}개의 Compaction Stats 레코드 파싱 완료")
    
    # 데이터 구조 변환
    return convert_to_timeseries(compaction_records)


def convert_to_timeseries(records):
    """레코드를 시계열 데이터로 변환"""
    
    if not records:
        return None
    
    # 시간 순으로 정렬
    records.sort(key=lambda x: x['time'])
    
    # 모든 레벨 찾기
    all_levels = set()
    for record in records:
        all_levels.update(record['levels'].keys())
    all_levels = sorted(all_levels)
    
    # 시계열 데이터 구성
    timeseries = {
        'time': [],
        'time_minutes': [],
    }
    
    for level in all_levels:
        timeseries[level] = {
            'read_gb': [],
            'write_gb': [],
            'read_rate': [],  # GB/min
            'write_rate': []  # GB/min
        }
    
    # 데이터 채우기
    prev_time = 0
    prev_stats = {level: {'read': 0, 'write': 0} for level in all_levels}
    
    for record in records:
        time_sec = record['time']
        time_min = time_sec / 60.0
        
        timeseries['time'].append(time_sec)
        timeseries['time_minutes'].append(time_min)
        
        interval_sec = time_sec - prev_time if prev_time > 0 else time_sec
        interval_min = interval_sec / 60.0
        
        for level in all_levels:
            if level in record['levels']:
                read_gb = record['levels'][level]['read_gb']
                write_gb = record['levels'][level]['write_gb']
            else:
                read_gb = 0
                write_gb = 0
            
            timeseries[level]['read_gb'].append(read_gb)
            timeseries[level]['write_gb'].append(write_gb)
            
            # Rate 계산 (GB/min)
            if interval_min > 0:
                read_rate = (read_gb - prev_stats[level]['read']) / interval_min
                write_rate = (write_gb - prev_stats[level]['write']) / interval_min
            else:
                read_rate = 0
                write_rate = 0
            
            timeseries[level]['read_rate'].append(max(0, read_rate))
            timeseries[level]['write_rate'].append(max(0, write_rate))
            
            prev_stats[level]['read'] = read_gb
            prev_stats[level]['write'] = write_gb
        
        prev_time = time_sec
    
    return timeseries, all_levels


def plot_real_compaction_data(timeseries, levels, output_dir):
    """실제 데이터로 시각화"""
    
    time_min = np.array(timeseries['time_minutes'])
    
    # 색상 팔레트
    colors = {
        'L0': '#FF6B6B',
        'L1': '#4ECDC4',
        'L2': '#45B7D1',
        'L3': '#FFA07A',
        'L4': '#98D8C8',
        'L5': '#F7DC6F',
        'L6': '#BB8FCE'
    }
    
    # 1. Write Rate 플롯
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
    
    # 상단: 라인 플롯
    for level in levels:
        write_rate = np.array(timeseries[level]['write_rate'])
        ax1.plot(time_min, write_rate, 
                label=level, color=colors.get(level, '#999999'), 
                linewidth=2, alpha=0.8)
    
    ax1.set_xlabel('Time (minutes)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Compaction Write Rate (GB/min)', fontsize=12, fontweight='bold')
    ax1.set_title('Real Per-Level Compaction Write Throughput Over Time', 
                  fontsize=14, fontweight='bold', pad=20)
    ax1.legend(loc='upper right', ncol=len(levels), fontsize=10)
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # 하단: 누적 영역 플롯
    write_rates = [np.array(timeseries[level]['write_rate']) for level in levels]
    ax2.stackplot(time_min, *write_rates, 
                 labels=levels, 
                 colors=[colors.get(level, '#999999') for level in levels], 
                 alpha=0.7)
    
    ax2.set_xlabel('Time (minutes)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Cumulative Compaction Write Rate (GB/min)', fontsize=12, fontweight='bold')
    ax2.set_title('Cumulative Real Per-Level Compaction Write Throughput', 
                  fontsize=14, fontweight='bold', pad=20)
    ax2.legend(loc='upper right', ncol=len(levels), fontsize=10)
    ax2.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'real_per_level_compaction_writes.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    # 2. Read Rate 플롯
    fig, ax = plt.subplots(figsize=(16, 8))
    
    for level in levels:
        read_rate = np.array(timeseries[level]['read_rate'])
        ax.plot(time_min, read_rate, 
               label=level, color=colors.get(level, '#999999'), 
               linewidth=2, alpha=0.8)
    
    ax.set_xlabel('Time (minutes)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Compaction Read Rate (GB/min)', fontsize=12, fontweight='bold')
    ax.set_title('Real Per-Level Compaction Read Throughput Over Time', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', ncol=len(levels), fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'real_per_level_compaction_reads.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    # 3. 히트맵
    fig, ax = plt.subplots(figsize=(16, 6))
    
    write_matrix = np.array([timeseries[level]['write_rate'] for level in levels])
    
    im = ax.imshow(write_matrix, aspect='auto', cmap='YlOrRd', interpolation='bilinear')
    
    ax.set_yticks(range(len(levels)))
    ax.set_yticklabels(levels, fontsize=11)
    ax.set_xlabel('Time Index', fontsize=12, fontweight='bold')
    ax.set_ylabel('LSM Level', fontsize=12, fontweight='bold')
    ax.set_title('Real Compaction Activity Heatmap: Time × Level', 
                 fontsize=14, fontweight='bold', pad=20)
    
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Compaction Write Rate (GB/min)', rotation=270, labelpad=20, fontsize=11)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'real_compaction_heatmap.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")


def print_statistics(timeseries, levels):
    """통계 요약 출력"""
    
    print("\n" + "="*70)
    print("실제 Compaction 처리량 통계 요약")
    print("="*70)
    
    for level in levels:
        write_gb = timeseries[level]['write_gb']
        read_gb = timeseries[level]['read_gb']
        write_rate = np.array(timeseries[level]['write_rate'])
        read_rate = np.array(timeseries[level]['read_rate'])
        
        total_write = write_gb[-1] if write_gb else 0
        total_read = read_gb[-1] if read_gb else 0
        
        active_write = write_rate[write_rate > 0]
        active_read = read_rate[read_rate > 0]
        
        print(f"\n{level}:")
        print(f"  총 Write: {total_write:.2f} GB")
        print(f"  총 Read: {total_read:.2f} GB")
        
        if len(active_write) > 0:
            print(f"  평균 Write Rate: {np.mean(active_write):.3f} GB/min")
            print(f"  최대 Write Rate: {np.max(active_write):.3f} GB/min")
        
        if len(active_read) > 0:
            print(f"  평균 Read Rate: {np.mean(active_read):.3f} GB/min")
            print(f"  최대 Read Rate: {np.max(active_read):.3f} GB/min")
    
    # 전체 통계
    total_write_gb = sum(timeseries[level]['write_gb'][-1] for level in levels if timeseries[level]['write_gb'])
    total_read_gb = sum(timeseries[level]['read_gb'][-1] for level in levels if timeseries[level]['read_gb'])
    
    print(f"\n{'='*70}")
    print(f"전체 총 Compaction Write: {total_write_gb:.2f} GB")
    print(f"전체 총 Compaction Read: {total_read_gb:.2f} GB")
    print(f"실행 시간: {timeseries['time_minutes'][-1]:.1f} 분 ({timeseries['time'][-1]:.0f} 초)")
    print("="*70 + "\n")


def main():
    """메인 실행 함수"""
    
    print("\n" + "="*70)
    print("실제 RocksDB LOG 파일에서 Compaction 데이터 추출 및 시각화")
    print("="*70 + "\n")
    
    # LOG 파일 경로
    log_file = "/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/rocksdb_log_phase_b.log"
    
    if not os.path.exists(log_file):
        print(f"❌ LOG 파일을 찾을 수 없습니다: {log_file}")
        print("다른 경로를 지정하려면 스크립트에 경로를 인자로 전달하세요.")
        return 1
    
    # 출력 디렉토리
    output_dir = "/home/sslab/rocksdb-put-model/experiments/2025-10-13/results"
    os.makedirs(output_dir, exist_ok=True)
    
    # LOG 파일 파싱
    result = parse_rocksdb_log(log_file)
    
    if result is None:
        print("❌ Compaction Stats를 찾을 수 없습니다.")
        return 1
    
    timeseries, levels = result
    
    # 통계 출력
    print_statistics(timeseries, levels)
    
    # 시각화
    print("시각화 생성 중...\n")
    plot_real_compaction_data(timeseries, levels, output_dir)
    
    print("\n" + "="*70)
    print("✓ 실제 데이터 분석 및 시각화 완료!")
    print(f"✓ 결과 저장 위치: {output_dir}")
    print("="*70 + "\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
