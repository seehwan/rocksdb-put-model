#!/usr/bin/env python3
"""
CV Visualization with Write Rate (MB/s)
실험에서 사용한 MB/s 기준으로 CV 계산 및 시각화
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

def calculate_correct_cv(df):
    """실험 방식대로 CV 계산 (MB/s 기준)"""
    
    phase_data = {
        'initial': df[df['time_hours'] < 32.2],
        'middle': df[(df['time_hours'] >= 32.2) & (df['time_hours'] < 64.4)],
        'final': df[df['time_hours'] >= 64.4]
    }
    
    phase_cvs = {}
    for phase_name, phase_df in phase_data.items():
        if len(phase_df) > 0:
            # MB/s 기준 CV 계산
            mean = phase_df['write_rate_mbs'].mean()
            std = phase_df['write_rate_mbs'].std()
            cv = std / mean
            phase_cvs[phase_name] = cv
            print(f'{phase_name}: CV={cv:.3f}, Mean={mean:.2f} MB/s, Std={std:.2f} MB/s')
    
    return phase_cvs, phase_data

def visualize_correct_cv(df, phase_cvs, phase_data):
    """올바른 CV 시각화"""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    
    # Phase별 time series
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    for phase_name, phase_df in phase_data.items():
        if len(phase_df) > 0:
            ax1.plot(phase_df['time_hours'], phase_df['write_rate_mbs'], 
                    color=colors[phase_name], alpha=0.6, linewidth=1,
                    label=f'{phase_name.title()} Phase')
    
    ax1.set_xlabel('Time (hours)', fontsize=20, fontfamily='Times')
    ax1.set_ylabel('Write Rate (MB/s)', fontsize=20, fontfamily='Times')
    ax1.set_title('Phase-Based Performance Timeline (MB/s)', fontsize=22, fontfamily='Times', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=16)
    ax1.tick_params(axis='both', which='major', labelsize=16)
    
    # Phase boundaries
    for boundary in [32.2, 64.4]:
        ax1.axvline(x=boundary, color='black', linestyle='--', alpha=0.5, linewidth=2)
    
    # Phase-level CV 표시
    bars = ax2.bar(phase_cvs.keys(), phase_cvs.values(), color=[colors[k] for k in phase_cvs.keys()], alpha=0.7)
    ax2.set_xlabel('Phase', fontsize=20, fontfamily='Times')
    ax2.set_ylabel('Coefficient of Variation (CV)', fontsize=20, fontfamily='Times')
    ax2.set_title('Phase-Level Integrated CV (MB/s)', fontsize=22, fontfamily='Times', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.tick_params(axis='both', which='major', labelsize=16)
    
    # CV 값 표시
    for i, (phase, cv) in enumerate(phase_cvs.items()):
        ax2.text(i, cv + 0.01, f'{cv:.3f}', ha='center', fontsize=18, fontweight='bold', fontfamily='Times')
    
    # Detection thresholds
    ax2.axhline(y=0.30, color='red', linestyle='--', linewidth=2, label='Initial threshold (CV=0.30)')
    ax2.axhline(y=0.01, color='blue', linestyle='--', linewidth=2, label='Final threshold (CV=0.01)')
    ax2.legend(fontsize=14)
    ax2.set_ylim(0, max(phase_cvs.values()) * 1.2)
    
    plt.tight_layout()
    return fig

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 Correct CV Visualization (MB/s)")
    print("=" * 80)
    
    # 데이터 로드
    df = load_data()
    print(f"✅ 데이터 로드: {len(df):,} 샘플")
    
    # Phase-level CV 계산
    print("\n📊 Phase-level 통합 CV 계산 (MB/s 기준):")
    phase_cvs, phase_data = calculate_correct_cv(df)
    
    # 시각화
    print("\n📈 시각화 생성 중...")
    fig = visualize_correct_cv(df, phase_cvs, phase_data)
    
    output_path = Path("figs/cv_correct_mbs.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 저장됨: {output_path}")
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()

