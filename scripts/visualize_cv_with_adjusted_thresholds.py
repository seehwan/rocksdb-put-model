#!/usr/bin/env python3
"""
CV over Time with Adjusted Phase Detection
CV 값 범위에 맞춘 새로운 임계값으로 phase 구분
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

def calculate_rolling_cv(df, window=1000):
    """Rolling window CV 계산"""
    df['mean_rolling'] = df['write_rate_mbs'].rolling(window=window).mean()
    df['std_rolling'] = df['write_rate_mbs'].rolling(window=window).std()
    df['cv_rolling'] = df['std_rolling'] / df['mean_rolling']
    
    return df

def detect_phase_from_cv_adjusted(cv_value):
    """
    CV 값으로 phase 감지 (조정된 임계값)
    Rolling CV 범위: 0.001 ~ 0.399
    """
    if cv_value > 0.10:  # 높은 변동성
        return 'initial'
    elif cv_value > 0.03:  # 중간 변동성
        return 'middle'
    else:  # 낮은 변동성
        return 'final'

def visualize_cv_with_adjusted_detection(df):
    """CV over time 시각화 및 조정된 phase detection"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
    
    # 1. CV over time with phase boundaries
    ax1.plot(df['hours'], df['cv_rolling'], 
            color='#2C3E50', alpha=0.7, linewidth=2, label='Rolling CV (window=1000)')
    
    # Phase별 색상 영역 (시간 기반)
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    ax1.axvspan(0, 32.2, color=colors['initial'], alpha=0.1, label='Initial Phase (time-based)')
    ax1.axvspan(32.2, 64.4, color=colors['middle'], alpha=0.1, label='Middle Phase (time-based)')
    ax1.axvspan(64.4, df['hours'].max(), color=colors['final'], alpha=0.1, label='Final Phase (time-based)')
    
    # 조정된 detection thresholds
    ax1.axhline(y=0.10, color='red', linestyle='--', linewidth=2, 
                label='Initial threshold (CV=0.10)', alpha=0.7)
    ax1.axhline(y=0.03, color='blue', linestyle='--', linewidth=2, 
                label='Final threshold (CV=0.03)', alpha=0.7)
    
    # Phase boundaries
    for boundary in [32.2, 64.4]:
        ax1.axvline(x=boundary, color='black', linestyle='--', alpha=0.5, linewidth=2)
    
    ax1.set_xlabel('Time (hours)', fontsize=18, fontfamily='Times')
    ax1.set_ylabel('Coefficient of Variation (CV)', fontsize=18, fontfamily='Times')
    ax1.set_title('CV Over Time with Adjusted Thresholds', fontsize=20, fontfamily='Times', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10, loc='upper right')
    ax1.tick_params(axis='both', which='major', labelsize=16)
    
    # Y축 범위 설정
    max_cv = df['cv_rolling'].max() * 1.1
    ax1.set_ylim(0, max_cv)
    
    # 2. Phase detection results
    
    # Time-based phase
    def get_phase_from_time(hours):
        if hours < 32.2:
            return 'initial'
        elif hours < 64.4:
            return 'middle'
        else:
            return 'final'
    
    df['phase_time'] = df['hours'].apply(get_phase_from_time)
    
    # CV-based phase (조정된 임계값)
    df['phase_cv'] = df['cv_rolling'].apply(detect_phase_from_cv_adjusted)
    
    # Phase detection accuracy
    accuracy = (df['phase_time'] == df['phase_cv']).sum() / len(df) * 100
    
    print(f"\n📊 Phase Detection Accuracy (Adjusted Thresholds):")
    print(f"  Time-based vs CV-based: {accuracy:.2f}%")
    
    # Phase별 통계
    for phase in ['initial', 'middle', 'final']:
        time_phase = df[df['phase_time'] == phase]
        cv_phase = df[df['phase_cv'] == phase]
        match = df[(df['phase_time'] == phase) & (df['phase_cv'] == phase)]
        
        print(f"\n  {phase.upper()} Phase:")
        print(f"    Time-based: {len(time_phase):,} samples")
        print(f"    CV-based: {len(cv_phase):,} samples")
        print(f"    Match: {len(match):,} samples ({len(match)/len(time_phase)*100:.1f}%)")
    
    # Phase comparison visualization
    phase_names = ['initial', 'middle', 'final']
    time_counts = [len(df[df['phase_time'] == p]) for p in phase_names]
    cv_counts = [len(df[df['phase_cv'] == p]) for p in phase_names]
    match_counts = [len(df[(df['phase_time'] == p) & (df['phase_cv'] == p)]) for p in phase_names]
    
    x = np.arange(len(phase_names))
    width = 0.25
    
    ax2.bar(x - width, time_counts, width, label='Time-based', color='#FF6B6B', alpha=0.7)
    ax2.bar(x, cv_counts, width, label='CV-based', color='#4ECDC4', alpha=0.7)
    ax2.bar(x + width, match_counts, width, label='Match', color='#45B7D1', alpha=0.7)
    
    ax2.set_xlabel('Phase', fontsize=18, fontfamily='Times')
    ax2.set_ylabel('Sample Count', fontsize=18, fontfamily='Times')
    ax2.set_title(f'Phase Detection Comparison ({accuracy:.1f}% match)', 
                  fontsize=20, fontfamily='Times', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([p.title() for p in phase_names])
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.tick_params(axis='both', which='major', labelsize=16)
    
    # 3. CV distribution by phase
    for phase in ['initial', 'middle', 'final']:
        phase_data = df[df['phase_time'] == phase]
        ax3.hist(phase_data['cv_rolling'].dropna(), bins=50, alpha=0.6, 
                label=f'{phase.title()} Phase', color=colors[phase])
    
    ax3.axvline(x=0.10, color='red', linestyle='--', linewidth=2, label='CV=0.10', alpha=0.7)
    ax3.axvline(x=0.03, color='blue', linestyle='--', linewidth=2, label='CV=0.03', alpha=0.7)
    
    ax3.set_xlabel('CV Value', fontsize=18, fontfamily='Times')
    ax3.set_ylabel('Frequency', fontsize=18, fontfamily='Times')
    ax3.set_title('CV Distribution by Time-based Phase', fontsize=20, fontfamily='Times', fontweight='bold')
    ax3.legend(fontsize=12)
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='both', which='major', labelsize=16)
    
    # 4. Scatter plot: Time vs CV
    for phase in ['initial', 'middle', 'final']:
        phase_data = df[df['phase_time'] == phase]
        ax4.scatter(phase_data['hours'], phase_data['cv_rolling'], 
                   alpha=0.3, s=1, label=f'{phase.title()} Phase', color=colors[phase])
    
    ax4.set_xlabel('Time (hours)', fontsize=18, fontfamily='Times')
    ax4.set_ylabel('CV Value', fontsize=18, fontfamily='Times')
    ax4.set_title('Time vs CV (by Phase)', fontsize=20, fontfamily='Times', fontweight='bold')
    ax4.legend(fontsize=12)
    ax4.grid(True, alpha=0.3)
    ax4.tick_params(axis='both', which='major', labelsize=16)
    
    plt.tight_layout()
    return fig

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 CV over Time with Adjusted Phase Detection")
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
    
    # Rolling CV 계산
    print("\n📊 Rolling CV 계산 중...")
    df = calculate_rolling_cv(df, window=1000)
    
    print(f"CV 통계:")
    print(f"  최소: {df['cv_rolling'].min():.3f}")
    print(f"  최대: {df['cv_rolling'].max():.3f}")
    print(f"  평균: {df['cv_rolling'].mean():.3f}")
    print(f"  중간값: {df['cv_rolling'].median():.3f}")
    
    # 시각화
    print("\n📈 시각화 생성 중...")
    fig = visualize_cv_with_adjusted_detection(df)
    
    output_path = Path("figs/cv_with_adjusted_detection.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()

