#!/usr/bin/env python3
"""
Dynamic CV-based Phase Detection
Runtime에서 CV 변화를 감지하여 phase 전환 포인트 탐지
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import deque

class DynamicPhaseDetector:
    """Runtime CV 변화 기반 Phase 탐지기"""
    
    def __init__(self, lookback_window=5000, change_threshold=0.02):
        """
        Args:
            lookback_window: CV 변화 분석을 위한 윈도우 크기
            change_threshold: Phase 전환으로 판단할 CV 변화 임계값
        """
        self.lookback_window = lookback_window
        self.change_threshold = change_threshold
        self.cv_history = deque(maxlen=lookback_window)
        self.detected_transitions = []
    
    def detect_phase_transitions(self, cv_series, time_series):
        """
        CV 변화를 분석하여 phase 전환 포인트 탐지
        
        Returns:
            List of (time, cv_value, transition_type) tuples
        """
        # CV 변화율 계산
        cv_diff = np.diff(cv_series)
        time_diff = np.diff(time_series)
        
        # 시간에 따른 CV 변화 분석
        transitions = []
        
        # Method 1: CV 변화율이 급격히 변하는 지점 찾기
        n_segments = 20  # 전체를 20 구간으로 나눠 분석
        segment_size = len(cv_series) // n_segments
        
        cv_by_segment = []
        for i in range(n_segments):
            start_idx = i * segment_size
            end_idx = (i + 1) * segment_size if i < n_segments - 1 else len(cv_series)
            segment_cv = cv_series[start_idx:end_idx]
            time_mid = time_series[(start_idx + end_idx) // 2]
            
            cv_by_segment.append({
                'time': time_mid,
                'mean_cv': np.mean(segment_cv),
                'cv_trend': np.mean(np.diff(segment_cv)) if len(segment_cv) > 1 else 0
            })
        
        # CV 추세 분석
        for i in range(1, len(cv_by_segment) - 1):
            prev_cv = cv_by_segment[i-1]['mean_cv']
            curr_cv = cv_by_segment[i]['mean_cv']
            next_cv = cv_by_segment[i+1]['mean_cv']
            
            # CV가 급격히 감소하는 지점 (Initial → Middle)
            if (prev_cv - curr_cv) > self.change_threshold and curr_cv > 0.50:
                transitions.append({
                    'time': cv_by_segment[i]['time'],
                    'cv': curr_cv,
                    'type': 'initial_to_middle',
                    'reason': f'CV drop: {prev_cv:.3f} → {curr_cv:.3f}'
                })
            
            # CV가 최종적으로 안정화되는 지점 (Middle → Final)
            if (curr_cv - next_cv) < 0.01 and curr_cv < 0.50:
                transitions.append({
                    'time': cv_by_segment[i]['time'],
                    'cv': curr_cv,
                    'type': 'middle_to_final',
                    'reason': f'CV stable: {curr_cv:.3f}'
                })
        
        return transitions
    
    def analyze_cv_trend(self, cv_values):
        """CV 값의 추세 분석"""
        if len(cv_values) < 10:
            return 'unknown'
        
        # 최근 N개 샘플의 평균과 전체 평균 비교
        recent_mean = np.mean(cv_values[-100:])
        overall_mean = np.mean(cv_values)
        
        # CV 추세 판단
        trend_change = recent_mean - overall_mean
        
        if trend_change > 0.02:
            return 'increasing'  # Initial phase
        elif trend_change < -0.02:
            return 'decreasing'  # Final phase
        else:
            return 'stable'  # Middle phase

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 Dynamic CV-based Phase Detection")
    print("=" * 80)
    
    # 데이터 로드
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    df['qps'] = df['interval_qps']
    
    # Rolling CV 계산
    window = 1000
    df['mean_rolling'] = df['qps'].rolling(window=window, min_periods=window).mean()
    df['std_rolling'] = df['qps'].rolling(window=window, min_periods=window).std()
    df['cv_rolling'] = df['std_rolling'] / df['mean_rolling']
    
    # NaN 제거
    df_valid = df[df['cv_rolling'].notna()].copy()
    
    # Dynamic phase detector 생성
    detector = DynamicPhaseDetector(lookback_window=5000, change_threshold=0.02)
    
    # Phase 전환 포인트 탐지
    transitions = detector.detect_phase_transitions(
        df_valid['cv_rolling'].values,
        df_valid['time_hours'].values
    )
    
    print(f"\n📊 탐지된 Phase 전환 포인트:")
    for trans in transitions:
        print(f"  {trans['time']:.2f}h: {trans['type']} (CV={trans['cv']:.3f})")
        print(f"    이유: {trans['reason']}")
    
    # 실제 boundary 찾기
    detected_10h = None
    detected_42h = None
    
    if transitions:
        # 가장 가까운 transition point 찾기
        for trans in transitions:
            if trans['type'] == 'initial_to_middle' and detected_10h is None:
                detected_10h = trans['time']
            elif trans['type'] == 'middle_to_final' and detected_42h is None:
                detected_42h = trans['time']
    
    print(f"\n📊 탐지된 경계:")
    if detected_10h:
        print(f"  Initial → Middle: {detected_10h:.2f}h")
    if detected_42h:
        print(f"  Middle → Final: {detected_42h:.2f}h")
    
    # Phase 할당 (탐지된 boundary 사용)
    detected_10h = detected_10h or 10.0  # fallback
    detected_42h = detected_42h or 42.0  # fallback
    
    df['phase_dynamic'] = df['time_hours'].apply(
        lambda h: 'initial' if h < detected_10h else ('middle' if h < detected_42h else 'final')
    )
    
    # df_valid에도 phase 정보 추가
    df_valid = df[df['cv_rolling'].notna()].copy()
    df_valid['phase_dynamic'] = df_valid['time_hours'].apply(
        lambda h: 'initial' if h < detected_10h else ('middle' if h < detected_42h else 'final')
    )
    
    # Phase별 통계
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    print(f"\n📊 Phase별 통계 (Dynamic Detection):")
    phase_info = {}
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_dynamic'] == phase]
        cv_valid = phase_df['cv_rolling'].dropna()
        
        if len(cv_valid) > 0:
            qps_mean = phase_df['qps'].mean()
            qps_std = phase_df['qps'].std()
            cv_integrated = qps_std / qps_mean if qps_mean > 0 else 0
            
            time_min = phase_df['time_hours'].min()
            time_max = phase_df['time_hours'].max()
            
            phase_info[phase] = {
                'samples': len(phase_df),
                'cv_integrated': cv_integrated,
                'qps_mean': qps_mean,
                'time_range': (time_min, time_max)
            }
            
            print(f"  {phase}:")
            print(f"    시간: {time_min:.2f} ~ {time_max:.2f} hours")
            print(f"    샘플: {len(phase_df):,}개")
            print(f"    통합 CV: {cv_integrated:.6f}")
            print(f"    QPS 평균: {qps_mean:.0f} ops/sec")
    
    # 시각화
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # 1. CV over Time with Detected Boundaries
    ax1.plot(df_valid['time_hours'], df_valid['cv_rolling'], 
            color='#2C3E50', alpha=0.7, linewidth=1.5, label='Rolling CV')
    
    for phase in ['initial', 'middle', 'final']:
        phase_mask = (df_valid['phase_dynamic'] == phase)
        if phase_mask.any():
            ax1.scatter(df_valid[phase_mask]['time_hours'], df_valid[phase_mask]['cv_rolling'], 
                       color=colors[phase], alpha=0.3, s=1, label=f'{phase.title()} Phase')
    
    # Detected boundaries
    for boundary, color in [(detected_10h, 'red'), (detected_42h, 'blue')]:
        if boundary:
            ax1.axvline(x=boundary, color=color, linestyle='--', linewidth=3, 
                       label=f'Detected: {boundary:.1f}h', alpha=0.8)
    
    ax1.set_xlabel('Time (hours)', fontsize=18, fontfamily='Times')
    ax1.set_ylabel('Rolling CV', fontsize=18, fontfamily='Times')
    ax1.set_title('Dynamic CV-based Phase Detection', fontsize=20, fontfamily='Times', fontweight='bold')
    ax1.legend(fontsize=12, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='both', which='major', labelsize=16)
    
    # 2. CV 변화율 분석
    cv_diff = np.diff(df_valid['cv_rolling'].values)
    time_diff = np.diff(df_valid['time_hours'].values)
    cv_change_rate = cv_diff / (time_diff + 1e-10)  # 시간당 CV 변화율
    
    ax2.plot(df_valid['time_hours'].iloc[1:], cv_change_rate, 
            color='#8B0000', alpha=0.7, linewidth=1, label='CV Change Rate')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.3)
    ax2.axhline(y=0.02, color='green', linestyle='--', linewidth=2, label='+0.02 threshold')
    ax2.axhline(y=-0.02, color='red', linestyle='--', linewidth=2, label='-0.02 threshold')
    
    ax2.set_xlabel('Time (hours)', fontsize=18, fontfamily='Times')
    ax2.set_ylabel('CV Change Rate (/hour)', fontsize=18, fontfamily='Times')
    ax2.set_title('CV Change Rate Over Time', fontsize=20, fontfamily='Times', fontweight='bold')
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='both', which='major', labelsize=16)
    
    # 3. QPS over Time
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_dynamic'] == phase]
        ax3.plot(phase_df['time_hours'], phase_df['qps'], 
                color=colors[phase], alpha=0.5, linewidth=1, label=f'{phase.title()} Phase')
    
    for boundary, color in [(detected_10h, 'red'), (detected_42h, 'blue')]:
        if boundary:
            ax3.axvline(x=boundary, color=color, linestyle='--', linewidth=2, alpha=0.7)
    
    ax3.set_xlabel('Time (hours)', fontsize=18, fontfamily='Times')
    ax3.set_ylabel('QPS (ops/sec)', fontsize=18, fontfamily='Times')
    ax3.set_title('QPS Over Time (Dynamic Detection)', fontsize=20, fontfamily='Times', fontweight='bold')
    ax3.legend(fontsize=12)
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='both', which='major', labelsize=16)
    ax3.set_yscale('log')
    
    # 4. Phase별 통합 CV
    if phase_info:
        phases = list(phase_info.keys())
        cvs = [phase_info[p]['cv_integrated'] for p in phases]
        
        bars = ax4.bar(phases, cvs, color=[colors[p] for p in phases], alpha=0.7, width=0.6)
        for i, phase in enumerate(phases):
            cv_val = cvs[i]
            ax4.text(i, cv_val + max(cvs)*0.05, f'{cv_val:.3f}', ha='center', va='bottom', 
                    fontsize=18, fontweight='bold', fontfamily='Times')
        
        ax4.set_xlabel('Phase', fontsize=18, fontfamily='Times')
        ax4.set_ylabel('Integrated CV', fontsize=18, fontfamily='Times')
        ax4.set_title('Phase-Level Integrated CV', fontsize=20, fontfamily='Times', fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.tick_params(axis='both', which='major', labelsize=16)
        if cvs:
            ax4.set_ylim(0, max(cvs) * 1.3)
    
    plt.tight_layout()
    
    output_path = Path("figs/dynamic_cv_phase_detection.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"\n✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")
    print("\n📊 Runtime Phase Detection 방법:")
    print("  1. CV 변화율 모니터링 (시간당 CV 변화)")
    print("  2. Phase 전환 임계값: ±0.02")
    print("  3. CV 추세 분석: increasing/stable/decreasing")
    print("  4. 구간별 평균 CV 비교")

if __name__ == "__main__":
    main()

