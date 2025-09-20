#!/usr/bin/env python3
"""
Phase-B LOG 기반 3구간 분석
RocksDB LOG 파일을 기반으로 한 3구간 분할 분석
"""

import os
import re
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Liberation Serif 폰트 설정 (Times 스타일)
plt.rcParams['font.family'] = 'Liberation Serif'
plt.rcParams['axes.unicode_minus'] = False

def parse_log_file(log_file):
    """LOG 파일 파싱"""
    print(f"📖 LOG 파일 파싱 중: {log_file}")
    
    stats_data = []
    compaction_data = []
    flush_data = []
    current_timestamp = None
    
    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            
            # 시간 정보 추출
            time_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
            if time_match:
                current_timestamp = time_match.group(1)
            
            # Stats 로그 파싱
            if "Cumulative writes:" in line:
                stats_data.append(parse_stats_line(line, current_timestamp))
            
            # Compaction 로그 파싱
            elif "Compaction start" in line:
                compaction_data.append(parse_compaction_start_line(line, current_timestamp))
            elif "compacted to:" in line:
                compaction_data.append(parse_compaction_finish_line(line, current_timestamp))
            
            # Flush 로그 파싱
            elif "Flushing memtable" in line or "Flush lasted" in line:
                flush_data.append(parse_flush_line(line, current_timestamp))
    
    print(f"✅ 파싱 완료: Stats {len(stats_data)}개, Compaction {len(compaction_data)}개, Flush {len(flush_data)}개")
    return stats_data, compaction_data, flush_data

def parse_stats_line(line, timestamp):
    """Stats 라인 파싱"""
    try:
        # Cumulative writes: 1130K writes, 1130K keys, 72K commit groups, 15.5 writes per commit group, ingest: 1.10 GB, 280.18 MB/s
        write_match = re.search(r'Cumulative writes: (\d+[KM]?) writes', line)
        mbps_match = re.search(r'(\d+\.\d+) MB/s', line)
        
        if write_match and mbps_match:
            # K, M 단위 처리
            writes_str = write_match.group(1)
            if writes_str.endswith('K'):
                cumulative_writes = int(writes_str[:-1]) * 1000
            elif writes_str.endswith('M'):
                cumulative_writes = int(writes_str[:-1]) * 1000000
            else:
                cumulative_writes = int(writes_str)
            
            return {
                'timestamp': timestamp,
                'cumulative_writes': cumulative_writes,
                'write_rate': float(mbps_match.group(1))
            }
    except Exception as e:
        print(f"⚠️ Stats 파싱 오류: {e}")
    return None

def parse_compaction_start_line(line, timestamp):
    """Compaction 시작 라인 파싱"""
    try:
        # Compaction start: Level 0 -> Level 1
        level_match = re.search(r'Level (\d+) -> Level (\d+)', line)
        if level_match:
            return {
                'timestamp': timestamp,
                'type': 'start',
                'base_level': int(level_match.group(1)),
                'target_level': int(level_match.group(2))
            }
    except Exception:
        pass
    return None

def parse_compaction_finish_line(line, timestamp):
    """Compaction 완료 라인 파싱"""
    try:
        # compacted to: Level 1
        level_match = re.search(r'compacted to: Level (\d+)', line)
        if level_match:
            return {
                'timestamp': timestamp,
                'type': 'finish',
                'target_level': int(level_match.group(1))
            }
    except Exception:
        pass
    return None

def parse_flush_line(line, timestamp):
    """Flush 라인 파싱"""
    try:
        if "Flushing memtable" in line:
            return {
                'timestamp': timestamp,
                'type': 'start'
            }
        elif "Flush lasted" in line:
            return {
                'timestamp': timestamp,
                'type': 'finish'
            }
    except Exception:
        pass
    return None

def analyze_3_phases(stats_data, compaction_data, flush_data):
    """3구간 분석"""
    print("📊 3구간 분석 중...")
    
    # 데이터프레임 생성
    print(f"📊 데이터 정리 중: Stats {len(stats_data)}개, Compaction {len(compaction_data)}개, Flush {len(flush_data)}개")
    
    stats_df = pd.DataFrame([s for s in stats_data if s])
    compaction_df = pd.DataFrame([c for c in compaction_data if c])
    flush_df = pd.DataFrame([f for f in flush_data if f])
    
    print(f"📊 데이터프레임 크기: Stats {len(stats_df)}행, Compaction {len(compaction_df)}행, Flush {len(flush_df)}행")
    
    if stats_df.empty:
        print("❌ Stats 데이터가 없습니다.")
        return None
    
    # 시간 변환
    stats_df['datetime'] = pd.to_datetime(stats_df['timestamp'])
    stats_df = stats_df.sort_values('datetime')
    
    # 3구간 분할 (시간 기반)
    total_duration = (stats_df['datetime'].iloc[-1] - stats_df['datetime'].iloc[0]).total_seconds()
    phase_duration = total_duration / 3
    
    phase_boundaries = [
        stats_df['datetime'].iloc[0] + timedelta(seconds=phase_duration),
        stats_df['datetime'].iloc[0] + timedelta(seconds=phase_duration * 2)
    ]
    
    # 구간별 데이터 분할
    phases = {
        'initial': stats_df[stats_df['datetime'] < phase_boundaries[0]],
        'middle': stats_df[(stats_df['datetime'] >= phase_boundaries[0]) & (stats_df['datetime'] < phase_boundaries[1])],
        'final': stats_df[stats_df['datetime'] >= phase_boundaries[1]]
    }
    
    # 구간별 분석
    phase_analysis = {}
    for phase_name, phase_data in phases.items():
        if len(phase_data) > 0:
            phase_analysis[phase_name] = {
                'duration_hours': (phase_data['datetime'].iloc[-1] - phase_data['datetime'].iloc[0]).total_seconds() / 3600,
                'sample_count': len(phase_data),
                'avg_write_rate': phase_data['write_rate'].mean(),
                'max_write_rate': phase_data['write_rate'].max(),
                'min_write_rate': phase_data['write_rate'].min(),
                'std_write_rate': phase_data['write_rate'].std(),
                'cv': phase_data['write_rate'].std() / phase_data['write_rate'].mean() if phase_data['write_rate'].mean() > 0 else 0,
                'start_time': phase_data['datetime'].iloc[0],
                'end_time': phase_data['datetime'].iloc[-1]
            }
    
    # Compaction 분석 (구간별)
    if not compaction_df.empty:
        compaction_df['datetime'] = pd.to_datetime(compaction_df['timestamp'])
        compaction_df = compaction_df.sort_values('datetime')
        
        for phase_name, phase_data in phases.items():
            if len(phase_data) > 0:
                start_time = phase_data['datetime'].iloc[0]
                end_time = phase_data['datetime'].iloc[-1]
                
                phase_compactions = compaction_df[
                    (compaction_df['datetime'] >= start_time) & 
                    (compaction_df['datetime'] <= end_time)
                ]
                
                if phase_name not in phase_analysis:
                    phase_analysis[phase_name] = {}
                
                phase_analysis[phase_name]['compaction_count'] = len(phase_compactions)
                if 'base_level' in phase_compactions.columns:
                    phase_analysis[phase_name]['compaction_by_level'] = phase_compactions['base_level'].value_counts().to_dict()
    
    # Flush 분석 (구간별)
    if not flush_df.empty:
        flush_df['datetime'] = pd.to_datetime(flush_df['timestamp'])
        flush_df = flush_df.sort_values('datetime')
        
        for phase_name, phase_data in phases.items():
            if len(phase_data) > 0:
                start_time = phase_data['datetime'].iloc[0]
                end_time = phase_data['datetime'].iloc[-1]
                
                phase_flushes = flush_df[
                    (flush_df['datetime'] >= start_time) & 
                    (flush_df['datetime'] <= end_time)
                ]
                
                if phase_name not in phase_analysis:
                    phase_analysis[phase_name] = {}
                
                phase_analysis[phase_name]['flush_count'] = len(phase_flushes)
                if 'type' in phase_flushes.columns:
                    phase_analysis[phase_name]['flush_by_type'] = phase_flushes['type'].value_counts().to_dict()
    
    return phase_analysis, phases

def create_3_phases_visualization(phase_analysis, phases):
    """3구간 시각화 생성"""
    print("📊 3구간 시각화 생성 중...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle('Phase-B 3-Phase Analysis Based on LOG Data', fontsize=16, fontweight='bold')
    
    # 1. 구간별 성능 분포
    phase_names = list(phase_analysis.keys())
    avg_rates = [phase_analysis[phase]['avg_write_rate'] for phase in phase_names]
    max_rates = [phase_analysis[phase]['max_write_rate'] for phase in phase_names]
    min_rates = [phase_analysis[phase]['min_write_rate'] for phase in phase_names]
    
    x = np.arange(len(phase_names))
    width = 0.25
    
    ax1.bar(x - width, avg_rates, width, label='Average', color='skyblue', alpha=0.7)
    ax1.bar(x, max_rates, width, label='Maximum', color='lightgreen', alpha=0.7)
    ax1.bar(x + width, min_rates, width, label='Minimum', color='lightcoral', alpha=0.7)
    
    ax1.set_ylabel('Write Rate (ops/sec)')
    ax1.set_title('Performance by Phase (LOG-based)')
    ax1.set_xticks(x)
    ax1.set_xticklabels([p.title() for p in phase_names])
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 구간별 안정성 (CV)
    cv_values = [phase_analysis[phase]['cv'] for phase in phase_names]
    colors = ['red' if cv > 0.6 else 'orange' if cv > 0.3 else 'green' for cv in cv_values]
    
    bars = ax2.bar([p.title() for p in phase_names], cv_values, color=colors, alpha=0.7)
    ax2.set_ylabel('Coefficient of Variation')
    ax2.set_title('Stability by Phase (CV)')
    ax2.grid(True, alpha=0.3)
    
    for bar, cv in zip(bars, cv_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{cv:.3f}', ha='center', va='bottom', fontsize=10)
    
    # 3. Compaction 분석
    compaction_counts = [phase_analysis[phase].get('compaction_count', 0) for phase in phase_names]
    flush_counts = [phase_analysis[phase].get('flush_count', 0) for phase in phase_names]
    
    x = np.arange(len(phase_names))
    width = 0.35
    
    ax3.bar(x - width/2, compaction_counts, width, label='Compaction', color='lightcoral', alpha=0.7)
    ax3.bar(x + width/2, flush_counts, width, label='Flush', color='lightblue', alpha=0.7)
    
    ax3.set_ylabel('Event Count')
    ax3.set_title('Compaction vs Flush Events by Phase')
    ax3.set_xticks(x)
    ax3.set_xticklabels([p.title() for p in phase_names])
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 구간별 요약
    ax4.text(0.1, 0.9, 'Phase Analysis Summary:', fontsize=14, fontweight='bold', transform=ax4.transAxes)
    
    y_pos = 0.8
    for phase_name, analysis in phase_analysis.items():
        ax4.text(0.1, y_pos, f'{phase_name.title()} Phase:', fontsize=12, fontweight='bold', transform=ax4.transAxes)
        y_pos -= 0.05
        ax4.text(0.1, y_pos, f'  Duration: {analysis["duration_hours"]:.1f} hours', fontsize=10, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.1, y_pos, f'  Avg Rate: {analysis["avg_write_rate"]:.1f} ops/sec', fontsize=10, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.1, y_pos, f'  CV: {analysis["cv"]:.3f}', fontsize=10, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.1, y_pos, f'  Compactions: {analysis.get("compaction_count", 0)}', fontsize=10, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.1, y_pos, f'  Flushes: {analysis.get("flush_count", 0)}', fontsize=10, transform=ax4.transAxes)
        y_pos -= 0.06
    
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis('off')
    ax4.set_title('Phase Summary')
    
    plt.tight_layout()
    plt.savefig('phase_b_3_phases_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ 3구간 시각화 완료")

def main():
    """메인 함수"""
    print("🚀 Phase-B 3구간 분석 시작...")
    
    # LOG 파일 경로 설정
    main_log = "rocksdb_log_phase_b.log"
    
    if not os.path.exists(main_log):
        print("❌ LOG 파일을 찾을 수 없습니다!")
        return
    
    print(f"📖 메인 LOG 파일: {main_log}")
    
    # LOG 파일 분석
    stats_data, compaction_data, flush_data = parse_log_file(main_log)
    
    if not stats_data:
        print("❌ Stats 데이터가 없습니다.")
        return
    
    # 3구간 분석
    result = analyze_3_phases(stats_data, compaction_data, flush_data)
    if result is None:
        print("❌ 3구간 분석 실패")
        return
    
    phase_analysis, phases = result
    
    # 결과 출력
    print("\n📊 3구간 분석 결과:")
    for phase_name, analysis in phase_analysis.items():
        print(f"\n  {phase_name.title()} Phase:")
        print(f"    기간: {analysis['start_time']} ~ {analysis['end_time']}")
        print(f"    지속시간: {analysis['duration_hours']:.1f} 시간")
        print(f"    샘플 수: {analysis['sample_count']:,}개")
        print(f"    평균 성능: {analysis['avg_write_rate']:.1f} ops/sec")
        print(f"    최대 성능: {analysis['max_write_rate']:.1f} ops/sec")
        print(f"    최소 성능: {analysis['min_write_rate']:.1f} ops/sec")
        print(f"    표준편차: {analysis['std_write_rate']:.1f} ops/sec")
        print(f"    변동계수: {analysis['cv']:.3f}")
        print(f"    Compaction: {analysis.get('compaction_count', 0)}회")
        print(f"    Flush: {analysis.get('flush_count', 0)}회")
    
    # 시각화 생성
    create_3_phases_visualization(phase_analysis, phases)
    
    # JSON 결과 저장
    results = {
        'phase_analysis': phase_analysis,
        'analysis_time': datetime.now().isoformat()
    }
    
    with open('phase_b_3_phases_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n✅ Phase-B 3구간 분석 완료!")
    print("📊 결과 파일: phase_b_3_phases_analysis.png, phase_b_3_phases_results.json")

if __name__ == "__main__":
    main()
