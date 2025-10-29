#!/usr/bin/env python3
"""
CV Over Time Visualization
X축: 시간 (hours), Y축: CV (rolling window CV)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_data():
    """데이터 로드"""
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    
    # ops/sec를 MB/s로 변환 (1040 bytes/record 기준)
    df['write_rate_mbs'] = df['interval_qps'] * 1040 / (1024 * 1024)
    
    return df

def calculate_rolling_cv(df, window=1000):
    """Rolling CV 계산"""
    df['mean_rolling'] = df['write_rate_mbs'].rolling(window=window).mean()
    df['std_rolling'] = df['write_rate_mbs'].rolling(window=window).std()
    df['cv_rolling'] = df['std_rolling'] / df['mean_rolling']
    
    return df

def visualize_cv_over_time(df):
    """CV over time 시각화"""
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 8))
    
    # Rolling CV 플롯
    ax.plot(df['time_hours'], df['cv_rolling'], 
            color='#2C3E50', alpha=0.7, linewidth=2, label='Rolling CV (window=1000)')
    
    # Phase별 색상 영역
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    # Initial phase
    ax.axvspan(0, 32.2, color=colors['initial'], alpha=0.1, label='Initial Phase')
    # Middle phase
    ax.axvspan(32.2, 64.4, color=colors['middle'], alpha=0.1, label='Middle Phase')
    # Final phase
    ax.axvspan(64.4, df['time_hours'].max(), color=colors['final'], alpha=0.1, label='Final Phase')
    
    # Phase boundaries
    for boundary in [32.2, 64.4]:
        ax.axvline(x=boundary, color='black', linestyle='--', alpha=0.5, linewidth=2)
    
    # Detection thresholds
    ax.axhline(y=0.30, color='red', linestyle='--', linewidth=2, label='Initial threshold (CV=0.30)', alpha=0.7)
    ax.axhline(y=0.01, color='blue', linestyle='--', linewidth=2, label='Final threshold (CV=0.01)', alpha=0.7)
    
    # Phase-level integrated CV 표시
    phase_data = {
        'initial': df[df['time_hours'] < 32.2],
        'middle': df[(df['time_hours'] >= 32.2) & (df['time_hours'] < 64.4)],
        'final': df[df['time_hours'] >= 64.4]
    }
    
    phase_cvs = {}
    for phase_name, phase_df in phase_data.items():
        if len(phase_df) > 0:
            mean = phase_df['write_rate_mbs'].mean()
            std = phase_df['write_rate_mbs'].std()
            cv = std / mean
            phase_cvs[phase_name] = cv
    
    # Phase-level CV를 수평선으로 표시
    for i, (phase_name, cv_val) in enumerate(phase_cvs.items()):
        ax.axhline(y=cv_val, color=colors[phase_name], linestyle=':', linewidth=3, 
                   label=f'{phase_name.title()} Phase CV={cv_val:.3f}', alpha=0.8)
    
    ax.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax.set_ylabel('Coefficient of Variation (CV)', fontsize=22, fontfamily='Times')
    ax.set_title('CV Over Time with Phase Boundaries', fontsize=24, fontfamily='Times', fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=12, loc='upper right')
    ax.tick_params(axis='both', which='major', labelsize=18)
    
    # Y축 범위 설정
    max_cv = max(df['cv_rolling'].max(), max(phase_cvs.values())) * 1.1
    ax.set_ylim(0, max_cv)
    
    plt.tight_layout()
    return fig

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 CV Over Time Visualization")
    print("=" * 80)
    
    # 데이터 로드
    df = load_data()
    print(f"✅ 데이터 로드: {len(df):,} 샘플")
    
    # Rolling CV 계산
    print("\n📊 Rolling CV 계산 중...")
    df = calculate_rolling_cv(df)
    
    print(f"CV 통계:")
    print(f"  최소: {df['cv_rolling'].min():.3f}")
    print(f"  최대: {df['cv_rolling'].max():.3f}")
    print(f"  평균: {df['cv_rolling'].mean():.3f}")
    
    # Phase별 CV 계산
    phase_cvs = {}
    phase_boundaries = {
        'initial': (0, 32.2),
        'middle': (32.2, 64.4),
        'final': (64.4, df['time_hours'].max())
    }
    
    for phase_name, (start, end) in phase_boundaries.items():
        phase_df = df[(df['time_hours'] >= start) & (df['time_hours'] < end)]
        if len(phase_df) > 0:
            mean = phase_df['write_rate_mbs'].mean()
            std = phase_df['write_rate_mbs'].std()
            cv = std / mean
            phase_cvs[phase_name] = cv
            print(f"  {phase_name}: CV={cv:.3f}, Mean={mean:.2f} MB/s")
    
    # 시각화
    print("\n📈 시각화 생성 중...")
    fig = visualize_cv_over_time(df)
    
    output_path = Path("figs/cv_over_time.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()
