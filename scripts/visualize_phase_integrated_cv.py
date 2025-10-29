#!/usr/bin/env python3
"""
Phase-Integrated CV Visualization (No Rolling Window)
LOG 파일에서 추출한 MB/s를 시간별로 정렬하고, phase별로 통합 CV 계산
"""

import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

def parse_log_file(log_file_path):
    """LOG 파일 파싱하여 시간별 write rate 추출"""
    print(f"📖 LOG 파일 파싱 중...")
    
    data = []
    current_timestamp = None
    
    with open(log_file_path, 'r') as f:
        for line in f:
            # 시간 정보 추출
            time_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
            if time_match:
                current_timestamp = time_match.group(1)
            
            # Cumulative writes 라인 찾기
            if "Cumulative writes:" in line and "MB/s" in line:
                try:
                    # MB/s 추출
                    mbps_match = re.search(r'(\d+\.\d+) MB/s', line)
                    if mbps_match and current_timestamp:
                        mbps = float(mbps_match.group(1))
                        data.append({
                            'timestamp': current_timestamp,
                            'write_rate_mbs': mbps
                        })
                except Exception as e:
                    continue
    
    print(f"✅ 파싱 완료: {len(data):,}개 샘플")
    return data

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 Phase-Integrated CV Visualization")
    print("=" * 80)
    
    # LOG 파일 경로
    log_file = Path("experiments/2025-09-12/rocksdb_log_phase_b.log")
    
    # LOG 파일 파싱
    data = parse_log_file(log_file)
    
    if len(data) == 0:
        print("❌ 데이터 없음")
        return
    
    # 데이터프레임 생성
    df = pd.DataFrame(data)
    
    # 시간 변환
    df['datetime'] = pd.to_datetime(df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
    start_time = df['datetime'].min()
    df['hours'] = (df['datetime'] - start_time).dt.total_seconds() / 3600
    
    # Phase별로 구분 (시간 기반 3-way split)
    total_hours = df['hours'].max()
    df['phase'] = df['hours'].apply(lambda h: 'initial' if h < total_hours/3 else ('middle' if h < total_hours*2/3 else 'final'))
    
    # Phase별 통합 CV 계산
    phase_cvs = {}
    phase_stats = {}
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    print("\n📊 Phase별 통합 CV 계산:")
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        mean = phase_df['write_rate_mbs'].mean()
        std = phase_df['write_rate_mbs'].std()
        cv = std / mean if mean > 0 else 0
        phase_cvs[phase] = cv
        phase_stats[phase] = {
            'mean': mean,
            'std': std,
            'cv': cv,
            'samples': len(phase_df),
            'duration': phase_df['hours'].max() - phase_df['hours'].min()
        }
        print(f"  {phase}: CV={cv:.6f}, Mean={mean:.2f} MB/s, Std={std:.2f} MB/s")
    
    # 시각화
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # 1. Time series with phase coloring
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        ax1.plot(phase_df['hours'], phase_df['write_rate_mbs'], 
                color=colors[phase], alpha=0.5, linewidth=1, label=f'{phase.title()} Phase')
    
    ax1.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax1.set_ylabel('Write Rate (MB/s)', fontsize=22, fontfamily='Times')
    ax1.set_title('Write Rate Over Time by Phase', fontsize=24, fontfamily='Times', fontweight='bold')
    ax1.legend(fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='both', which='major', labelsize=18)
    
    # Phase boundaries
    for boundary in [total_hours/3, total_hours*2/3]:
        ax1.axvline(x=boundary, color='black', linestyle='--', alpha=0.5, linewidth=2)
    
    # 2. Phase-level integrated CV
    phases = list(phase_cvs.keys())
    cvs = [phase_cvs[p] for p in phases]
    
    bars = ax2.bar(phases, cvs, color=[colors[p] for p in phases], alpha=0.7, width=0.6)
    ax2.set_xlabel('Phase', fontsize=22, fontfamily='Times')
    ax2.set_ylabel('Coefficient of Variation (CV)', fontsize=22, fontfamily='Times')
    ax2.set_title('Phase-Level Integrated CV (No Rolling Window)', fontsize=24, fontfamily='Times', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.tick_params(axis='both', which='major', labelsize=18)
    
    # CV 값 표시
    for i, (phase, cv) in enumerate(phase_cvs.items()):
        height = cvs[i]
        ax2.text(i, height + 0.01, f'{cv:.3f}', ha='center', va='bottom', 
                 fontsize=18, fontweight='bold', fontfamily='Times')
        # 샘플 수 표시
        samples = phase_stats[phase]['samples']
        mean_rate = phase_stats[phase]['mean']
        ax2.text(i, -0.02, f'Mean: {mean_rate:.1f}\nMB/s', 
                 ha='center', va='top', fontsize=12, fontfamily='Times')
    
    ax2.set_ylim(-0.1, max(cvs) * 1.3)
    
    plt.tight_layout()
    
    output_path = Path("figs/phase_integrated_cv.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()

