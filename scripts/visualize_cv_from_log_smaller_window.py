#!/usr/bin/env python3
"""
Rolling CV with Smaller Window
더 작은 window로 rolling CV 계산하여 더 많은 샘플 확보
"""

import re
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def parse_log_file(log_file_path):
    """LOG 파일 파싱"""
    print(f"📖 LOG 파일 파싱 중...")
    
    data = []
    current_timestamp = None
    
    with open(log_file_path, 'r') as f:
        for line in f:
            time_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
            if time_match:
                current_timestamp = time_match.group(1)
            
            if 'Cumulative writes:' in line and 'MB/s' in line:
                mbps_match = re.search(r'(\d+\.\d+) MB/s', line)
                if mbps_match and current_timestamp:
                    data.append({
                        'timestamp': current_timestamp,
                        'write_rate_mbs': float(mbps_match.group(1))
                    })
    
    print(f"✅ 파싱 완료: {len(data):,}개 샘플")
    return data

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 Rolling CV Comparison (Different Windows)")
    print("=" * 80)
    
    # LOG 파일 경로
    log_file = Path("experiments/2025-09-12/rocksdb_log_phase_b.log")
    data = parse_log_file(log_file)
    
    if len(data) == 0:
        print("❌ 데이터 없음")
        return
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
    start_time = df['datetime'].min()
    df['hours'] = (df['datetime'] - start_time).dt.total_seconds() / 3600
    df = df.sort_values('hours')
    
    # Phase 구분
    total_hours = df['hours'].max()
    df['phase'] = df['hours'].apply(lambda h: 'initial' if h < total_hours/3 else ('middle' if h < total_hours*2/3 else 'final'))
    
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    # 다양한 window 크기 비교
    windows = [100, 500, 1000]
    
    fig, axes = plt.subplots(len(windows) + 1, 1, figsize=(16, 4*len(windows)))
    
    # Phase별 통합 CV 계산
    phase_cvs = {}
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        mean = phase_df['write_rate_mbs'].mean()
        std = phase_df['write_rate_mbs'].std()
        cv = std / mean if mean > 0 else 0
        phase_cvs[phase] = cv
    
    # 각 window에 대해 그래프 생성
    for idx, window in enumerate(windows):
        ax = axes[idx]
        
        # Rolling CV 계산
        df[f'cv_{window}'] = df['write_rate_mbs'].rolling(window=window, min_periods=window).apply(
            lambda x: x.std() / x.mean() if x.mean() > 0 else 0, raw=True
        )
        
        # 그래프
        ax.plot(df['hours'], df[f'cv_{window}'], color='#2C3E50', alpha=0.7, linewidth=1.5)
        
        # Phase 색상
        ax.axvspan(0, total_hours/3, color=colors['initial'], alpha=0.1)
        ax.axvspan(total_hours/3, total_hours*2/3, color=colors['middle'], alpha=0.1)
        ax.axvspan(total_hours*2/3, total_hours, color=colors['final'], alpha=0.1)
        
        for boundary in [total_hours/3, total_hours*2/3]:
            ax.axvline(x=boundary, color='black', linestyle='--', alpha=0.5, linewidth=2)
        
        # Phase-level CV 표시
        for phase, cv_val in phase_cvs.items():
            ax.axhline(y=cv_val, color=colors[phase], linestyle=':', linewidth=3, alpha=0.8)
        
        valid = df[f'cv_{window}'].notna().sum()
        ax.set_ylabel('CV', fontsize=18, fontfamily='Times')
        ax.set_title(f'Rolling CV (window={window}, valid={valid:,} samples)', fontsize=20, fontfamily='Times', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', which='major', labelsize=16)
    
    # Phase별 통합 CV 비교
    ax = axes[-1]
    phases = list(phase_cvs.keys())
    cvs = [phase_cvs[p] for p in phases]
    
    bars = ax.bar(phases, cvs, color=[colors[p] for p in phases], alpha=0.7, width=0.6)
    for i, (phase, cv) in enumerate(phase_cvs.items()):
        ax.text(i, cv + 0.01, f'{cv:.3f}', ha='center', va='bottom', 
                fontsize=18, fontweight='bold', fontfamily='Times')
    
    ax.set_xlabel('Phase', fontsize=22, fontfamily='Times')
    ax.set_ylabel('CV (Phase-Integrated)', fontsize=22, fontfamily='Times')
    ax.set_title('Phase-Level Integrated CV (Reference)', fontsize=24, fontfamily='Times', fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    ax.tick_params(axis='both', which='major', labelsize=18)
    
    plt.tight_layout()
    
    output_path = Path("figs/cv_rolling_comparison.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"\n✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")
    print("\n📊 결론:")
    print("  - Rolling CV는 window 크기에 따라 달라짐")
    print("  - Phase-level integrated CV가 가장 안정적")

if __name__ == "__main__":
    main()

