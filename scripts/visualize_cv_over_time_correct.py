#!/usr/bin/env python3
"""
CV Over Time (Correct Version)
X축: 시간, Y축: CV 값 (phase별 통합 CV를 시간별로 표시)
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
    print("📊 CV Over Time (X: 시간, Y: CV)")
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
    
    # Phase별로 구분 및 통합 CV 계산
    total_hours = df['hours'].max()
    df['phase'] = df['hours'].apply(lambda h: 'initial' if h < total_hours/3 else ('middle' if h < total_hours*2/3 else 'final'))
    
    # Phase별 통합 CV 계산
    phase_cvs = {}
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        mean = phase_df['write_rate_mbs'].mean()
        std = phase_df['write_rate_mbs'].std()
        cv = std / mean if mean > 0 else 0
        phase_cvs[phase] = cv
        print(f"{phase}: CV={cv:.6f}")
        
        # Phase의 각 샘플에 CV 값 할당
        df.loc[df['phase'] == phase, 'cv'] = cv
    
    print(f"\n📊 Phase별 CV:")
    print(f"  Initial: {phase_cvs['initial']:.6f}")
    print(f"  Middle: {phase_cvs['middle']:.6f}")
    print(f"  Final: {phase_cvs['final']:.6f}")
    
    # 시각화
    fig, ax = plt.subplots(1, 1, figsize=(16, 8))
    
    # Phase별로 색상 구분하여 CV 플롯
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        ax.plot(phase_df['hours'], phase_df['cv'], 
                color=colors[phase], alpha=0.7, linewidth=2, 
                label=f'{phase.title()} Phase (CV={phase_cvs[phase]:.3f})')
    
    # Phase boundaries
    for boundary in [total_hours/3, total_hours*2/3]:
        ax.axvline(x=boundary, color='black', linestyle='--', alpha=0.5, linewidth=2)
    
    ax.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax.set_ylabel('Coefficient of Variation (CV)', fontsize=22, fontfamily='Times')
    ax.set_title('CV Over Time (Phase-Integrated)', fontsize=24, fontfamily='Times', fontweight='bold')
    ax.legend(fontsize=14, loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='both', which='major', labelsize=18)
    
    # Y축 범위 설정
    min_cv = min(phase_cvs.values()) * 0.9
    max_cv = max(phase_cvs.values()) * 1.1
    ax.set_ylim(min_cv, max_cv)
    
    plt.tight_layout()
    
    output_path = Path("figs/cv_over_time_correct.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")
    print("\n📊 그래프 설명:")
    print("  - X축: Time (hours)")
    print("  - Y축: Coefficient of Variation (CV)")
    print("  - 각 phase별로 통합 CV 값이 수평선으로 표시됨")

if __name__ == "__main__":
    main()

