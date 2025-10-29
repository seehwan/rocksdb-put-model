#!/usr/bin/env python3
"""
Rolling CV from LOG File
LOG 파일에서 파싱한 MB/s를 사용하여 rolling CV 계산 및 시각화
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

def calculate_rolling_cv(df, window=1000):
    """Rolling CV 계산"""
    df['mean_rolling'] = df['write_rate_mbs'].rolling(window=window, min_periods=window).mean()
    df['std_rolling'] = df['write_rate_mbs'].rolling(window=window, min_periods=window).std()
    df['cv_rolling'] = df['std_rolling'] / df['mean_rolling']
    
    return df

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 Rolling CV from LOG File")
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
    
    # Rolling CV 계산
    window = 1000
    print(f"\n📊 Rolling CV 계산 중... (window={window})")
    df = calculate_rolling_cv(df, window=window)
    
    valid_samples = df['cv_rolling'].notna().sum()
    print(f"CV 통계:")
    print(f"  유효 샘플: {valid_samples:,}개")
    print(f"  CV 최소: {df['cv_rolling'].min():.6f}")
    print(f"  CV 최대: {df['cv_rolling'].max():.6f}")
    print(f"  CV 평균: {df['cv_rolling'].mean():.6f}")
    print(f"  CV 중간값: {df['cv_rolling'].median():.6f}")
    
    # Phase 구분
    total_hours = df['hours'].max()
    df['phase'] = df['hours'].apply(lambda h: 'initial' if h < total_hours/3 else ('middle' if h < total_hours*2/3 else 'final'))
    
    # Phase별 통합 CV 계산 (참고용)
    phase_cvs = {}
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    print(f"\n📊 Phase별 통합 CV (참고):")
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        mean = phase_df['write_rate_mbs'].mean()
        std = phase_df['write_rate_mbs'].std()
        cv = std / mean if mean > 0 else 0
        phase_cvs[phase] = cv
        print(f"  {phase}: CV={cv:.6f}, Mean={mean:.2f} MB/s")
    
    # 시각화
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # 1. Rolling CV over time
    ax1.plot(df['hours'], df['cv_rolling'], 
            color='#2C3E50', alpha=0.7, linewidth=1.5, label=f'Rolling CV (window={window})')
    
    # Phase별 색상 영역
    ax1.axvspan(0, total_hours/3, color=colors['initial'], alpha=0.1, label='Initial Phase')
    ax1.axvspan(total_hours/3, total_hours*2/3, color=colors['middle'], alpha=0.1, label='Middle Phase')
    ax1.axvspan(total_hours*2/3, total_hours, color=colors['final'], alpha=0.1, label='Final Phase')
    
    # Phase boundaries
    for boundary in [total_hours/3, total_hours*2/3]:
        ax1.axvline(x=boundary, color='black', linestyle='--', alpha=0.5, linewidth=2)
    
    # Phase-level integrated CV를 수평선으로 표시
    for phase_name, cv_val in phase_cvs.items():
        ax1.axhline(y=cv_val, color=colors[phase_name], linestyle=':', linewidth=3, 
                   label=f'{phase_name.title()} Phase CV={cv_val:.3f}', alpha=0.8)
    
    ax1.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax1.set_ylabel('Coefficient of Variation (CV)', fontsize=22, fontfamily='Times')
    ax1.set_title(f'Rolling CV from LOG File (window={window})', fontsize=24, fontfamily='Times', fontweight='bold')
    ax1.legend(fontsize=12, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='both', which='major', labelsize=18)
    
    # 2. Write Rate over time (참고용)
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        ax2.plot(phase_df['hours'], phase_df['write_rate_mbs'], 
                color=colors[phase], alpha=0.5, linewidth=1, label=f'{phase.title()} Phase')
    
    ax2.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax2.set_ylabel('Write Rate (MB/s)', fontsize=22, fontfamily='Times')
    ax2.set_title('Write Rate Over Time (from LOG)', fontsize=24, fontfamily='Times', fontweight='bold')
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='both', which='major', labelsize=18)
    
    plt.tight_layout()
    
    output_path = Path("figs/cv_from_log_rolling.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")
    print("\n📊 그래프 설명:")
    print("  - 위 그래프: Rolling CV (시간에 따른 변화)")
    print("  - 아래 그래프: Write Rate (참고용)")
    print("  - 점선: Phase별 통합 CV 값")

if __name__ == "__main__":
    main()

