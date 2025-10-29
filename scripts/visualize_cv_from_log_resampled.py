#!/usr/bin/env python3
"""
Resampled LOG Data with Rolling CV
LOG 파일 파싱 → 10초 간격 리샘플링 → Rolling CV 계산
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

def resample_to_10s(df):
    """10초 간격으로 리샘플링"""
    print(f"\n📊 10초 간격 리샘플링 중...")
    
    # 초 단위로 변환 (0부터 시작)
    start_time = df['datetime'].min()
    df['seconds'] = (df['datetime'] - start_time).dt.total_seconds()
    
    # 10초 간격 인덱스 생성
    max_seconds = df['seconds'].max()
    target_times = np.arange(0, max_seconds + 10, 10)
    
    # 각 10초 간격에 가장 가까운 데이터 찾기
    resampled_data = []
    for target_time in target_times:
        closest_idx = (df['seconds'] - target_time).abs().idxmin()
        resampled_data.append({
            'seconds': target_time,
            'write_rate_mbs': df.loc[closest_idx, 'write_rate_mbs']
        })
    
    df_resampled = pd.DataFrame(resampled_data)
    df_resampled['hours'] = df_resampled['seconds'] / 3600
    
    print(f"✅ 리샘플링 완료: {len(df_resampled):,}개 샘플 (10초 간격)")
    print(f"   원본: {len(df):,}개 → 리샘플: {len(df_resampled):,}개")
    
    return df_resampled

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 LOG → Resampled → Rolling CV")
    print("=" * 80)
    
    log_file = Path("experiments/2025-09-12/rocksdb_log_phase_b.log")
    
    # 1. LOG 파싱
    data = parse_log_file(log_file)
    if len(data) == 0:
        print("❌ 데이터 없음")
        return
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
    
    # 2. 10초 간격 리샘플링
    df_resampled = resample_to_10s(df)
    
    # 3. Rolling CV 계산
    window = 1000
    print(f"\n📊 Rolling CV 계산 중 (window={window})...")
    
    df_resampled['mean_rolling'] = df_resampled['write_rate_mbs'].rolling(window=window, min_periods=window).mean()
    df_resampled['std_rolling'] = df_resampled['write_rate_mbs'].rolling(window=window, min_periods=window).std()
    df_resampled['cv_rolling'] = df_resampled['std_rolling'] / df_resampled['mean_rolling']
    
    valid_samples = df_resampled['cv_rolling'].notna().sum()
    print(f"CV 통계:")
    print(f"  유효 샘플: {valid_samples:,}개")
    print(f"  CV 최소: {df_resampled['cv_rolling'].min():.6f}")
    print(f"  CV 최대: {df_resampled['cv_rolling'].max():.6f}")
    print(f"  CV 평균: {df_resampled['cv_rolling'].mean():.6f}")
    
    # 4. Phase 구분
    total_hours = df_resampled['hours'].max()
    df_resampled['phase'] = df_resampled['hours'].apply(
        lambda h: 'initial' if h < total_hours/3 else ('middle' if h < total_hours*2/3 else 'final')
    )
    
    # Phase별 통합 CV
    phase_cvs = {}
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    print(f"\n📊 Phase별 통합 CV:")
    for phase in ['initial', 'middle', 'final']:
        phase_df = df_resampled[df_resampled['phase'] == phase]
        mean = phase_df['write_rate_mbs'].mean()
        std = phase_df['write_rate_mbs'].std()
        cv = std / mean if mean > 0 else 0
        phase_cvs[phase] = cv
        print(f"  {phase}: CV={cv:.6f}, Mean={mean:.2f} MB/s")
    
    # 5. 시각화
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # 위 그래프: Rolling CV over time
    ax1.plot(df_resampled['hours'], df_resampled['cv_rolling'], 
            color='#2C3E50', alpha=0.7, linewidth=1.5, label=f'Rolling CV (window={window})')
    
    # Phase 색상
    ax1.axvspan(0, total_hours/3, color=colors['initial'], alpha=0.1, label='Initial Phase')
    ax1.axvspan(total_hours/3, total_hours*2/3, color=colors['middle'], alpha=0.1, label='Middle Phase')
    ax1.axvspan(total_hours*2/3, total_hours, color=colors['final'], alpha=0.1, label='Final Phase')
    
    # Phase boundaries
    for boundary in [total_hours/3, total_hours*2/3]:
        ax1.axvline(x=boundary, color='black', linestyle='--', alpha=0.5, linewidth=2)
    
    # Phase-level CV 표시
    for phase_name, cv_val in phase_cvs.items():
        ax1.axhline(y=cv_val, color=colors[phase_name], linestyle=':', linewidth=3, 
                   label=f'{phase_name.title()} Phase CV={cv_val:.3f}', alpha=0.8)
    
    ax1.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax1.set_ylabel('Coefficient of Variation (CV)', fontsize=22, fontfamily='Times')
    ax1.set_title(f'Rolling CV from Resampled LOG (window={window})', fontsize=24, fontfamily='Times', fontweight='bold')
    ax1.legend(fontsize=12, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='both', which='major', labelsize=18)
    
    # 아래 그래프: Write Rate
    for phase in ['initial', 'middle', 'final']:
        phase_df = df_resampled[df_resampled['phase'] == phase]
        ax2.plot(phase_df['hours'], phase_df['write_rate_mbs'], 
                color=colors[phase], alpha=0.5, linewidth=1, label=f'{phase.title()} Phase')
    
    ax2.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax2.set_ylabel('Write Rate (MB/s)', fontsize=22, fontfamily='Times')
    ax2.set_title('Write Rate Over Time (Resampled)', fontsize=24, fontfamily='Times', fontweight='bold')
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='both', which='major', labelsize=18)
    
    plt.tight_layout()
    
    output_path = Path("figs/cv_log_resampled.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"\n✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")
    print("\n📊 방법 요약:")
    print("  1. LOG 파일에서 MB/s 추출")
    print("  2. 10초 간격으로 리샘플링")
    print("  3. Window=1000으로 Rolling CV 계산")
    print("  4. 시간에 따른 CV 변화 시각화")

if __name__ == "__main__":
    main()

