#!/usr/bin/env python3
"""
CV 기반 자동 phase 감지 분석
실제 데이터에서 CV 기반 phase 구분이 어떻게 되는지 분석
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def analyze_cv_distribution():
    """CV 분포 분석"""
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    
    window = 100
    df['mean'] = df['interval_qps'].rolling(window=window).mean()
    df['std'] = df['interval_qps'].rolling(window=window).std()
    df['cv'] = df['std'] / df['mean']
    
    # CV 분포 출력
    print("=" * 80)
    print("CV 분포 분석")
    print("=" * 80)
    print(f"\n전체 CV 범위: {df['cv'].min():.3f} ~ {df['cv'].max():.3f}")
    print(f"평균 CV: {df['cv'].mean():.3f}")
    print(f"중간값 CV: {df['cv'].median():.3f}")
    print("\nCV 분위수:")
    for p in [0, 0.25, 0.5, 0.75, 1.0]:
        print(f"  {p*100:5.1f}%: {df['cv'].quantile(p):.3f}")
    
    # 다양한 threshold로 phase 구분 테스트
    print("\n" + "=" * 80)
    print("다양한 CV Threshold 테스트")
    print("=" * 80)
    
    thresholds = [
        (0.30, 0.015),
        (0.50, 0.45),
        (0.60, 0.50),
        (0.70, 0.55)
    ]
    
    for threshold_initial, threshold_middle in thresholds:
        print(f"\nThreshold: Initial > {threshold_initial}, Final < {threshold_middle}")
        
        def detect_phase(cv):
            if pd.isna(cv):
                return 'unknown'
            elif cv > threshold_initial:
                return 'initial'
            elif cv > threshold_middle:
                return 'middle'
            else:
                return 'final'
        
        df['detected_phase'] = df['cv'].apply(detect_phase)
        
        for phase in ['initial', 'middle', 'final']:
            count = len(df[df['detected_phase'] == phase])
            if count > 0:
                avg_cv = df[df['detected_phase'] == phase]['cv'].mean()
                pct = count / len(df) * 100
                print(f"  {phase:8s}: {count:7,} 샘플 ({pct:5.1f}%), 평균 CV={avg_cv:.3f}")
    
    return df

def visualize_cv_time_series(df):
    """CV time series with phase detection visualization"""
    
    # Optimal threshold 찾기
    threshold_initial = 0.60  # 상위 구간
    threshold_final = 0.55    # 중간 구간
    
    def detect_phase(cv):
        if pd.isna(cv):
            return 'unknown'
        elif cv > threshold_initial:
            return 'initial'
        elif cv > threshold_final:
            return 'middle'
        else:
            return 'final'
    
    df['detected_phase'] = df['cv'].apply(detect_phase)
    
    # Phase별 색상
    color_map = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Phase별로 그룹화하여 plot
    for phase in ['initial', 'middle', 'final']:
        phase_data = df[df['detected_phase'] == phase]
        if len(phase_data) > 0:
            ax.scatter(phase_data['time_hours'], phase_data['cv'], 
                      c=color_map[phase], label=f'{phase.title()} (CV-based)', 
                      alpha=0.6, s=10)
    
    # Detection thresholds
    ax.axhline(y=threshold_initial, color='red', linestyle='--', linewidth=2, 
               label=f'Initial threshold (CV={threshold_initial})')
    ax.axhline(y=threshold_final, color='blue', linestyle='--', linewidth=2, 
               label=f'Final threshold (CV={threshold_final})')
    
    # Time-based phase boundaries
    total_time = df['time_hours'].max()
    for start, end, name in [(0, total_time*0.33, 'Initial'), 
                               (total_time*0.33, total_time*0.67, 'Middle'),
                               (total_time*0.67, total_time, 'Final')]:
        ax.axvline(x=start, color='black', linestyle=':', alpha=0.5, linewidth=1)
        if name == 'Final':
            ax.axvline(x=end, color='black', linestyle=':', alpha=0.5, linewidth=1)
    
    ax.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax.set_ylabel('Coefficient of Variation (CV)', fontsize=22, fontfamily='Times')
    ax.set_title('CV-Based Automatic Phase Detection vs Time-Based Boundaries', 
                 fontsize=24, fontfamily='Times', fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=16)
    ax.tick_params(axis='both', which='major', labelsize=18)
    
    plt.tight_layout()
    return fig

def main():
    """메인 함수"""
    print("=" * 80)
    print("CV 기반 자동 Phase 감지 분석")
    print("=" * 80)
    
    # CV 분포 분석
    df = analyze_cv_distribution()
    
    # 시각화
    print("\n📈 CV-based phase detection 시각화 생성 중...")
    fig = visualize_cv_time_series(df)
    
    output_path = Path("figs/cv_phase_detection_comparison.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 저장됨: {output_path}")
    
    print("\n✅ 분석 완료!")

if __name__ == "__main__":
    main()

