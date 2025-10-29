#!/usr/bin/env python3
"""
CV Visualization from RocksDB LOG
RocksDB LOG 파일에서 파싱한 MB/s 기준 CV 시각화
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
from datetime import datetime

def parse_rocksdb_log(log_file):
    """RocksDB LOG에서 시간별 write rate 추출"""
    print(f"📖 RocksDB LOG 파싱 중: {log_file}")
    
    data = []
    
    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Cumulative writes 라인 찾기
            if "Cumulative writes:" in line and "MB/s" in line:
                try:
                    # 시간 추출
                    time_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
                    if not time_match:
                        continue
                    
                    timestamp_str = time_match.group(1)
                    
                    # MB/s 추출
                    mbps_match = re.search(r'(\d+\.\d+) MB/s', line)
                    if mbps_match:
                        mbps = float(mbps_match.group(1))
                        
                        # Cumulative writes 추출
                        write_match = re.search(r'Cumulative writes: (\d+[KM]?) writes', line)
                        if write_match:
                            writes_str = write_match.group(1)
                            if writes_str.endswith('K'):
                                cumulative_writes = int(writes_str[:-1]) * 1000
                            elif writes_str.endswith('M'):
                                cumulative_writes = int(writes_str[:-1]) * 1000000
                            else:
                                cumulative_writes = int(writes_str)
                            
                            data.append({
                                'timestamp': timestamp_str,
                                'mbps': mbps,
                                'cumulative_writes': cumulative_writes
                            })
                except Exception as e:
                    continue
    
    print(f"✅ 파싱 완료: {len(data)}개 샘플")
    return data

def calculate_time_and_cv(data):
    """시간 및 CV 계산"""
    df = pd.DataFrame(data)
    
    # Timestamp를 datetime으로 변환
    df['datetime'] = pd.to_datetime(df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
    
    # 시작 시간 기준으로 시간 계산
    start_time = df['datetime'].min()
    df['hours'] = (df['datetime'] - start_time).dt.total_seconds() / 3600
    
    # Phase 구분
    def get_phase(hours):
        if hours < 32.2:
            return 'initial'
        elif hours < 64.4:
            return 'middle'
        else:
            return 'final'
    
    df['phase'] = df['hours'].apply(get_phase)
    
    # Phase별 CV 계산
    phase_cvs = {}
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        if len(phase_df) > 0:
            mean = phase_df['mbps'].mean()
            std = phase_df['mbps'].std()
            cv = std / mean
            phase_cvs[phase] = cv
            print(f"{phase}: Mean={mean:.2f} MB/s, Std={std:.2f} MB/s, CV={cv:.3f}")
    
    return df, phase_cvs

def visualize_cv_from_log(df, phase_cvs):
    """LOG 기반 CV 시각화"""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    
    # Phase별 time series
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    for phase_name in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase_name]
        if len(phase_df) > 0:
            ax1.plot(phase_df['hours'], phase_df['mbps'], 
                    color=colors[phase_name], alpha=0.6, linewidth=1.5,
                    label=f'{phase_name.title()} Phase')
    
    ax1.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax1.set_ylabel('Write Rate (MB/s)', fontsize=22, fontfamily='Times')
    ax1.set_title('RocksDB LOG Write Rate Over Time', fontsize=24, fontfamily='Times', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=16)
    ax1.tick_params(axis='both', which='major', labelsize=18)
    
    # Phase boundaries
    for boundary in [32.2, 64.4]:
        ax1.axvline(x=boundary, color='black', linestyle='--', alpha=0.5, linewidth=2)
    
    # Phase-level CV 표시
    phases = list(phase_cvs.keys())
    cvs = list(phase_cvs.values())
    bars = ax2.bar(phases, cvs, color=[colors[p] for p in phases], alpha=0.7)
    ax2.set_xlabel('Phase', fontsize=22, fontfamily='Times')
    ax2.set_ylabel('Coefficient of Variation (CV)', fontsize=22, fontfamily='Times')
    ax2.set_title('Phase-Level CV from RocksDB LOG', fontsize=24, fontfamily='Times', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.tick_params(axis='both', which='major', labelsize=18)
    
    # CV 값 표시
    for i, (phase, cv) in enumerate(phase_cvs.items()):
        ax2.text(i, cv + max(cvs) * 0.05, f'{cv:.3f}', ha='center', fontsize=18, fontweight='bold', fontfamily='Times')
    
    # Detection thresholds
    ax2.axhline(y=0.30, color='red', linestyle='--', linewidth=2, label='Initial threshold (CV=0.30)')
    ax2.axhline(y=0.01, color='blue', linestyle='--', linewidth=2, label='Final threshold (CV=0.01)')
    ax2.legend(fontsize=14)
    ax2.set_ylim(0, max(cvs) * 1.3)
    
    plt.tight_layout()
    return fig

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 CV Visualization from RocksDB LOG")
    print("=" * 80)
    
    # LOG 파일 파싱
    log_file = Path("experiments/2025-09-12/rocksdb_log_phase_b.log")
    if not log_file.exists():
        print(f"❌ LOG 파일 없음: {log_file}")
        return
    
    data = parse_rocksdb_log(log_file)
    
    if len(data) == 0:
        print("❌ 데이터 없음")
        return
    
    # 시간 및 CV 계산
    print("\n📊 Phase별 CV 계산:")
    df, phase_cvs = calculate_time_and_cv(data)
    
    # 시각화
    print("\n📈 시각화 생성 중...")
    fig = visualize_cv_from_log(df, phase_cvs)
    
    output_path = Path("figs/cv_from_log.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 저장됨: {output_path}")
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()

