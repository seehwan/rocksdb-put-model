#!/usr/bin/env python3
"""
CV Over Time with Rolling Calculation
각 시간점에서 rolling window CV를 계산하여 시간에 따른 CV 변화를 시각화
"""

import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

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
    print("📊 CV Over Time with Rolling Calculation")
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
    
    # 시간 순 정렬
    df = df.sort_values('hours')
    
    # Rolling CV 계산 (window=1000)
    window = 1000
    df['cv_rolling'] = df['write_rate_mbs'].rolling(window=window, min_periods=window).apply(
        lambda x: x.std() / x.mean() if x.mean() > 0 else 0, raw=True
    )
    
    print(f"\n📊 Rolling CV 통계:")
    print(f"  유효 샘플: {df['cv_rolling'].notna().sum():,}개")
    print(f"  CV 최소: {df['cv_rolling'].min():.6f}")
    print(f"  CV 최대: {df['cv_rolling'].max():.6f}")
    print(f"  CV 평균: {df['cv_rolling'].mean():.6f}")
    
    # Phase 구분
    total_hours = df['hours'].max()
    df['phase'] = df['hours'].apply(lambda h: 'initial' if h < total_hours/3 else ('middle' if h < total_hours*2/3 else 'final'))
    
    # Phase별 통합 CV 계산 (참고용)
    phase_cvs = {}
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        mean = phase_df['write_rate_mbs'].mean()
        std = phase_df['write_rate_mbs'].std()
        cv = std / mean if mean > 0 else 0
        phase_cvs[phase] = cv
    
    print(f"\n📊 Phase별 통합 CV (참고):")
    print(f"  Initial: {phase_cvs['initial']:.6f}")
    print(f"  Middle: {phase_cvs['middle']:.6f}")
    print(f"  Final: {phase_cvs['final']:.6f}")
    
    # 시각화
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # 1. Rolling CV over time
    ax1.plot(df['hours'], df['cv_rolling'], 
            color='#2C3E50', alpha=0.7, linewidth=1.5, label='Rolling CV (window=1000)')
    
    # Phase별 색상 영역
    ax1.axvspan(0, total_hours/3, color=colors['initial'], alpha=0.1, label='Initial Phase')
    ax1.axvspan(total_hours/3, total_hours*2/3, color=colors['middle'], alpha=0.1, label='Middle Phase')
    ax1.axvspan(total_hours*2/3, total_hours, color=colors['final'], alpha=0.1, label='Final Phase')
    
    # Phase boundaries
    for boundary in [total_hours/3, total_hours*2/3]:
        ax1.axvline(x=boundary, color='black', linestyle='--', alpha=0.5, linewidth=2)
    
    ax1.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax1.set_ylabel('Coefficient of Variation (CV)', fontsize=22, fontfamily='Times')
    ax1.set_title('CV Over Time (Rolling Window CV)', fontsize=24, fontfamily='Times', fontweight='bold')
    ax1.legend(fontsize=14, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='both', which='major', labelsize=18)
    
    # 2. Phase별 통합 CV 표시
    phases = list(phase_cvs.keys())
    cvs = [phase_cvs[p] for p in phases]
    
    bars = ax2.bar(phases, cvs, color=[colors[p] for p in phases], alpha=0.7, width=0.6)
    ax2.set_xlabel('Phase', fontsize=22, fontfamily='Times')
    ax2.set_ylabel('Coefficient of Variation (CV)', fontsize=22, fontfamily='Times')
    ax2.set_title('Phase-Level Integrated CV', fontsize=24, fontfamily='Times', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.tick_params(axis='both', which='major', labelsize=18)
    
    # CV 값 표시
    for i, (phase, cv) in enumerate(phase_cvs.items()):
        height = cvs[i]
        ax2.text(i, height + 0.01, f'{cv:.3f}', ha='center', va='bottom', 
                 fontsize=18, fontweight='bold', fontfamily='Times')
    
    ax2.set_ylim(0, max(cvs) * 1.3)
    
    plt.tight_layout()
    
    output_path = Path("figs/cv_over_time_rolling.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")
    print("\n📊 그래프 설명:")
    print("  - 위 그래프: 시간에 따른 Rolling CV 변화 (각 샘플마다 계산)")
    print("  - 아래 그래프: Phase별 통합 CV 비교")

if __name__ == "__main__":
    main()

