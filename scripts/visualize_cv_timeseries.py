#!/usr/bin/env python3
"""
CV Time Series Visualization
시간에 따른 실제 CV 값 시각화

실험 원본 데이터에서 시간별 CV를 계산하여 시각화
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

def load_raw_data():
    """실험 원본 데이터 로드"""
    # CSV 파일로 로드
    data_file = Path("experiments/2025-09-12/phase-b/fillrandom_results.json")
    
    if not data_file.exists():
        print(f"❌ 데이터 파일 없음: {data_file}")
        return None
    
    # CSV로 읽기
    df = pd.read_csv(data_file)
    return df

def calculate_rolling_cv(df, window=100):
    """Rolling CV 계산"""
    df['mean'] = df['interval_qps'].rolling(window=window).mean()
    df['std'] = df['interval_qps'].rolling(window=window).std()
    df['cv'] = df['std'] / df['mean']
    return df

def create_cv_timeseries_viz(df):
    """CV time series 시각화"""
    # 시간 단위로 변환 (초 → 시간)
    df['time_hours'] = df['secs_elapsed'] / 3600
    
    # Rolling CV 계산 (1000 샘플 윈도우 - 더 장기적인 CV)
    df = calculate_rolling_cv(df, window=1000)
    
    # Phase boundaries (96.6시간 실험 기준)
    phase_boundaries = [
        (0, 32.2, 'Initial', '#FF6B6B'),
        (32.2, 64.4, 'Middle', '#4ECDC4'),
        (64.4, 96.6, 'Final', '#45B7D1')
    ]
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot CV over time
    ax.plot(df['time_hours'], df['cv'], linewidth=2, color='#2C3E50', alpha=0.8, label='CV over Time')
    
    # Phase regions 표시
    for start, end, label, color in phase_boundaries:
        ax.axvspan(start, end, alpha=0.2, color=color, label=f'{label} Phase')
    
    # Phase boundaries 표시
    for start, end, _, _ in phase_boundaries:
        ax.axvline(x=start, color='black', linestyle='--', alpha=0.5, linewidth=2)
    ax.axvline(x=phase_boundaries[-1][1], color='black', linestyle='--', alpha=0.5, linewidth=2)
    
    # Detection thresholds 표시
    ax.axhline(y=0.30, color='red', linestyle=':', linewidth=2, label='Initial threshold (CV=0.30)')
    ax.axhline(y=0.015, color='blue', linestyle=':', linewidth=2, label='Final threshold (CV=0.015)')
    
    ax.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax.set_ylabel('Coefficient of Variation (CV)', fontsize=22, fontfamily='Times')
    ax.set_title('CV Evolution Over 96.6-Hour Experiment', fontsize=24, fontfamily='Times', fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=16, loc='upper right')
    ax.tick_params(axis='both', which='major', labelsize=18)
    
    # CV statistics 표시
    stats_text = f"Statistics:\nMax CV: {df['cv'].max():.3f}\nMin CV: {df['cv'].min():.3f}\nMean CV: {df['cv'].mean():.3f}"
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=14, 
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            fontfamily='Times')
    
    plt.tight_layout()
    return fig

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 CV Time Series Visualization")
    print("=" * 80)
    
    # 데이터 로드
    print("\n📁 데이터 로드 중...")
    df = load_raw_data()
    
    if df is None or df.empty:
        print("❌ 데이터 로드 실패")
        return
    
    print(f"✅ 데이터 로드 완료: {len(df):,} 샘플")
    
    # 시각화
    print("\n📈 CV time series 생성 중...")
    fig = create_cv_timeseries_viz(df)
    
    # 저장
    output_path = Path("figs/cv_timeseries.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 저장됨: {output_path}")
    
    print("\n✅ CV time series 시각화 완료!")

if __name__ == "__main__":
    main()

