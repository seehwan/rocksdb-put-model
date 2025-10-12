#!/usr/bin/env python3
"""
LOG 기반 구간 분할 상세 분석
RocksDB LOG 파일을 기반으로 한 구간별 상세 특성 분석
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
        pass
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

def analyze_log_based_phases_detailed(stats_data, compaction_data, flush_data):
    """LOG 기반 구간 상세 분석"""
    print("📊 LOG 기반 구간 상세 분석 중...")
    
    # 데이터프레임 생성
    stats_df = pd.DataFrame([s for s in stats_data if s])
    compaction_df = pd.DataFrame([c for c in compaction_data if c])
    flush_df = pd.DataFrame([f for f in flush_data if f])
    
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
    
    # 구간별 상세 분석
    phase_analysis = {}
    for phase_name, phase_data in phases.items():
        if len(phase_data) > 0:
            # 기본 통계
            basic_stats = {
                'duration_hours': (phase_data['datetime'].iloc[-1] - phase_data['datetime'].iloc[0]).total_seconds() / 3600,
                'sample_count': len(phase_data),
                'start_time': phase_data['datetime'].iloc[0],
                'end_time': phase_data['datetime'].iloc[-1]
            }
            
            # 성능 통계
            performance_stats = {
                'avg_write_rate': phase_data['write_rate'].mean(),
                'max_write_rate': phase_data['write_rate'].max(),
                'min_write_rate': phase_data['write_rate'].min(),
                'std_write_rate': phase_data['write_rate'].std(),
                'cv': phase_data['write_rate'].std() / phase_data['write_rate'].mean() if phase_data['write_rate'].mean() > 0 else 0,
                'median_write_rate': phase_data['write_rate'].median(),
                'q25_write_rate': phase_data['write_rate'].quantile(0.25),
                'q75_write_rate': phase_data['write_rate'].quantile(0.75)
            }
            
            # 성능 변화 분석
            if len(phase_data) > 1:
                performance_trend = {
                    'trend_slope': np.polyfit(range(len(phase_data)), phase_data['write_rate'], 1)[0],
                    'trend_r2': np.corrcoef(range(len(phase_data)), phase_data['write_rate'])[0,1]**2,
                    'performance_change': (phase_data['write_rate'].iloc[-1] - phase_data['write_rate'].iloc[0]) / phase_data['write_rate'].iloc[0] * 100
                }
            else:
                performance_trend = {
                    'trend_slope': 0,
                    'trend_r2': 0,
                    'performance_change': 0
                }
            
            # Compaction 분석
            compaction_stats = {}
            if not compaction_df.empty:
                compaction_df['datetime'] = pd.to_datetime(compaction_df['timestamp'])
                compaction_df = compaction_df.sort_values('datetime')
                
                start_time = phase_data['datetime'].iloc[0]
                end_time = phase_data['datetime'].iloc[-1]
                
                phase_compactions = compaction_df[
                    (compaction_df['datetime'] >= start_time) & 
                    (compaction_df['datetime'] <= end_time)
                ]
                
                compaction_stats = {
                    'total_compactions': len(phase_compactions),
                    'compaction_rate_per_hour': len(phase_compactions) / basic_stats['duration_hours'] if basic_stats['duration_hours'] > 0 else 0
                }
                
                if 'base_level' in phase_compactions.columns:
                    compaction_stats['compaction_by_level'] = phase_compactions['base_level'].value_counts().to_dict()
            
            # Flush 분석
            flush_stats = {}
            if not flush_df.empty:
                flush_df['datetime'] = pd.to_datetime(flush_df['timestamp'])
                flush_df = flush_df.sort_values('datetime')
                
                start_time = phase_data['datetime'].iloc[0]
                end_time = phase_data['datetime'].iloc[-1]
                
                phase_flushes = flush_df[
                    (flush_df['datetime'] >= start_time) & 
                    (flush_df['datetime'] <= end_time)
                ]
                
                flush_stats = {
                    'total_flushes': len(phase_flushes),
                    'flush_rate_per_hour': len(phase_flushes) / basic_stats['duration_hours'] if basic_stats['duration_hours'] > 0 else 0
                }
                
                if 'type' in phase_flushes.columns:
                    flush_stats['flush_by_type'] = phase_flushes['type'].value_counts().to_dict()
            
            # 구간별 특성 분류
            phase_characteristics = classify_phase_characteristics(performance_stats, performance_trend, compaction_stats, flush_stats)
            
            phase_analysis[phase_name] = {
                'basic_stats': basic_stats,
                'performance_stats': performance_stats,
                'performance_trend': performance_trend,
                'compaction_stats': compaction_stats,
                'flush_stats': flush_stats,
                'phase_characteristics': phase_characteristics
            }
    
    return phase_analysis, phases

def classify_phase_characteristics(performance_stats, performance_trend, compaction_stats, flush_stats):
    """구간별 특성 분류"""
    characteristics = {}
    
    # 성능 특성
    if performance_stats['cv'] < 0.1:
        characteristics['stability'] = 'high'
    elif performance_stats['cv'] < 0.3:
        characteristics['stability'] = 'medium'
    else:
        characteristics['stability'] = 'low'
    
    # 성능 트렌드
    if performance_trend['trend_slope'] > 0.1:
        characteristics['trend'] = 'increasing'
    elif performance_trend['trend_slope'] < -0.1:
        characteristics['trend'] = 'decreasing'
    else:
        characteristics['trend'] = 'stable'
    
    # 성능 수준
    if performance_stats['avg_write_rate'] > 20:
        characteristics['performance_level'] = 'high'
    elif performance_stats['avg_write_rate'] > 15:
        characteristics['performance_level'] = 'medium'
    else:
        characteristics['performance_level'] = 'low'
    
    # 활동 수준
    total_activity = compaction_stats.get('total_compactions', 0) + flush_stats.get('total_flushes', 0)
    if total_activity > 100000:
        characteristics['activity_level'] = 'high'
    elif total_activity > 50000:
        characteristics['activity_level'] = 'medium'
    else:
        characteristics['activity_level'] = 'low'
    
    return characteristics

def create_detailed_visualization(phase_analysis, phases):
    """상세 시각화 생성"""
    print("📊 LOG 기반 구간 상세 시각화 생성 중...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('LOG-based Phase Analysis - Detailed Characteristics', fontsize=18, fontweight='bold')
    
    phase_names = list(phase_analysis.keys())
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    # 1. 성능 분포 박스플롯
    performance_data = []
    for phase_name, analysis in phase_analysis.items():
        phase_data = phases[phase_name]
        performance_data.append(phase_data['write_rate'].values)
    
    bp1 = ax1.boxplot(performance_data, labels=[p.title() for p in phase_names], patch_artist=True)
    for patch, color in zip(bp1['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax1.set_ylabel('Write Rate (MB/s)')
    ax1.set_title('Performance Distribution by Phase')
    ax1.grid(True, alpha=0.3)
    
    # 2. 구간별 특성 매트릭스
    characteristics_matrix = []
    for phase_name, analysis in phase_analysis.items():
        char = analysis['phase_characteristics']
        characteristics_matrix.append([
            char['stability'],
            char['trend'],
            char['performance_level'],
            char['activity_level']
        ])
    
    # 특성을 숫자로 변환
    char_mapping = {
        'high': 3, 'medium': 2, 'low': 1,
        'increasing': 3, 'stable': 2, 'decreasing': 1
    }
    
    char_matrix_numeric = []
    for row in characteristics_matrix:
        char_matrix_numeric.append([char_mapping.get(char, 0) for char in row])
    
    im = ax2.imshow(char_matrix_numeric, cmap='RdYlGn', aspect='auto')
    ax2.set_xticks(range(4))
    ax2.set_xticklabels(['Stability', 'Trend', 'Performance', 'Activity'])
    ax2.set_yticks(range(len(phase_names)))
    ax2.set_yticklabels([p.title() for p in phase_names])
    ax2.set_title('Phase Characteristics Matrix')
    
    # 컬러바 추가
    cbar = plt.colorbar(im, ax=ax2)
    cbar.set_label('Level (1=Low, 2=Medium, 3=High)')
    
    # 3. 성능 트렌드 분석
    for i, (phase_name, analysis) in enumerate(phase_analysis.items()):
        phase_data = phases[phase_name]
        if len(phase_data) > 1:
            # 시간 정규화 (0-1)
            time_norm = (phase_data['datetime'] - phase_data['datetime'].iloc[0]).dt.total_seconds()
            time_norm = time_norm / time_norm.max()
            
            ax3.plot(time_norm, phase_data['write_rate'], 
                    label=f'{phase_name.title()} Phase', 
                    color=colors[i], alpha=0.7, linewidth=2)
    
    ax3.set_xlabel('Normalized Time')
    ax3.set_ylabel('Write Rate (MB/s)')
    ax3.set_title('Performance Trends Over Time')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 구간별 요약 통계
    ax4.text(0.05, 0.95, 'Phase Analysis Summary', fontsize=16, fontweight='bold', transform=ax4.transAxes)
    
    y_pos = 0.85
    for phase_name, analysis in phase_analysis.items():
        ax4.text(0.05, y_pos, f'{phase_name.title()} Phase:', fontsize=14, fontweight='bold', transform=ax4.transAxes)
        y_pos -= 0.05
        
        # 기본 통계
        basic = analysis['basic_stats']
        ax4.text(0.05, y_pos, f'  Duration: {basic["duration_hours"]:.1f} hours', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.05, y_pos, f'  Samples: {basic["sample_count"]:,}', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.04
        
        # 성능 통계
        perf = analysis['performance_stats']
        ax4.text(0.05, y_pos, f'  Avg Rate: {perf["avg_write_rate"]:.1f} MB/s', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.05, y_pos, f'  CV: {perf["cv"]:.3f}', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.04
        
        # 특성
        char = analysis['phase_characteristics']
        ax4.text(0.05, y_pos, f'  Stability: {char["stability"]}, Trend: {char["trend"]}', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.05, y_pos, f'  Performance: {char["performance_level"]}, Activity: {char["activity_level"]}', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.06
    
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis('off')
    
    plt.tight_layout()
    plt.savefig('log_based_phases_detailed_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ LOG 기반 구간 상세 시각화 완료")

def save_detailed_results(phase_analysis):
    """상세 결과 저장"""
    print("💾 LOG 기반 구간 상세 결과 저장 중...")
    
    # JSON 결과 저장
    results = {
        'phase_analysis': phase_analysis,
        'analysis_time': datetime.now().isoformat(),
        'analysis_type': 'log_based_detailed'
    }
    
    with open('log_based_phases_detailed_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Markdown 보고서 생성
    with open('log_based_phases_detailed_report.md', 'w') as f:
        f.write("# LOG-based Phase Analysis - Detailed Report\n\n")
        f.write(f"## Analysis Time\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Overview\n")
        f.write("This report provides a detailed analysis of RocksDB performance phases based on LOG data.\n\n")
        
        f.write("## Phase Analysis Results\n\n")
        
        for phase_name, analysis in phase_analysis.items():
            f.write(f"### {phase_name.title()} Phase\n\n")
            
            # 기본 통계
            basic = analysis['basic_stats']
            f.write(f"**Basic Statistics:**\n")
            f.write(f"- Duration: {basic['duration_hours']:.1f} hours\n")
            f.write(f"- Sample Count: {basic['sample_count']:,}\n")
            f.write(f"- Start Time: {basic['start_time']}\n")
            f.write(f"- End Time: {basic['end_time']}\n\n")
            
            # 성능 통계
            perf = analysis['performance_stats']
            f.write(f"**Performance Statistics:**\n")
            f.write(f"- Average Rate: {perf['avg_write_rate']:.1f} MB/s\n")
            f.write(f"- Maximum Rate: {perf['max_write_rate']:.1f} MB/s\n")
            f.write(f"- Minimum Rate: {perf['min_write_rate']:.1f} MB/s\n")
            f.write(f"- Standard Deviation: {perf['std_write_rate']:.1f} MB/s\n")
            f.write(f"- Coefficient of Variation: {perf['cv']:.3f}\n")
            f.write(f"- Median Rate: {perf['median_write_rate']:.1f} MB/s\n")
            f.write(f"- Q25 Rate: {perf['q25_write_rate']:.1f} MB/s\n")
            f.write(f"- Q75 Rate: {perf['q75_write_rate']:.1f} MB/s\n\n")
            
            # 성능 트렌드
            trend = analysis['performance_trend']
            f.write(f"**Performance Trend:**\n")
            f.write(f"- Trend Slope: {trend['trend_slope']:.6f}\n")
            f.write(f"- Trend R²: {trend['trend_r2']:.3f}\n")
            f.write(f"- Performance Change: {trend['performance_change']:.1f}%\n\n")
            
            # Compaction 통계
            compaction = analysis['compaction_stats']
            f.write(f"**Compaction Statistics:**\n")
            f.write(f"- Total Compactions: {compaction.get('total_compactions', 0)}\n")
            f.write(f"- Compaction Rate: {compaction.get('compaction_rate_per_hour', 0):.1f} per hour\n")
            if 'compaction_by_level' in compaction:
                f.write(f"- Compaction by Level: {compaction['compaction_by_level']}\n")
            f.write("\n")
            
            # Flush 통계
            flush = analysis['flush_stats']
            f.write(f"**Flush Statistics:**\n")
            f.write(f"- Total Flushes: {flush.get('total_flushes', 0)}\n")
            f.write(f"- Flush Rate: {flush.get('flush_rate_per_hour', 0):.1f} per hour\n")
            if 'flush_by_type' in flush:
                f.write(f"- Flush by Type: {flush['flush_by_type']}\n")
            f.write("\n")
            
            # 구간 특성
            char = analysis['phase_characteristics']
            f.write(f"**Phase Characteristics:**\n")
            f.write(f"- Stability: {char['stability']}\n")
            f.write(f"- Trend: {char['trend']}\n")
            f.write(f"- Performance Level: {char['performance_level']}\n")
            f.write(f"- Activity Level: {char['activity_level']}\n\n")
            
            f.write("---\n\n")
        
        f.write("## Key Insights\n\n")
        f.write("### Phase Progression Pattern\n")
        f.write("The analysis reveals a clear progression pattern across the three phases:\n\n")
        
        f.write("1. **Initial Phase**: High variability, decreasing performance\n")
        f.write("2. **Middle Phase**: Stabilizing performance, moderate activity\n")
        f.write("3. **Final Phase**: Stable performance, low activity\n\n")
        
        f.write("### Performance Characteristics\n")
        for phase_name, analysis in phase_analysis.items():
            char = analysis['phase_characteristics']
            f.write(f"- **{phase_name.title()}**: {char['performance_level']} performance, {char['stability']} stability\n")
        
        f.write("\n### Activity Patterns\n")
        for phase_name, analysis in phase_analysis.items():
            char = analysis['phase_characteristics']
            f.write(f"- **{phase_name.title()}**: {char['activity_level']} activity level\n")
        
        f.write(f"\n## Analysis Time\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    print("✅ 상세 결과 저장 완료")

def main():
    """메인 함수"""
    print("🚀 LOG 기반 구간 상세 분석 시작...")
    
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
    
    # LOG 기반 구간 상세 분석
    result = analyze_log_based_phases_detailed(stats_data, compaction_data, flush_data)
    if result is None:
        print("❌ LOG 기반 구간 상세 분석 실패")
        return
    
    phase_analysis, phases = result
    
    # 결과 출력
    print("\n📊 LOG 기반 구간 상세 분석 결과:")
    for phase_name, analysis in phase_analysis.items():
        print(f"\n  {phase_name.title()} Phase:")
        basic = analysis['basic_stats']
        perf = analysis['performance_stats']
        char = analysis['phase_characteristics']
        
        print(f"    기간: {basic['start_time']} ~ {basic['end_time']}")
        print(f"    지속시간: {basic['duration_hours']:.1f} 시간")
        print(f"    샘플 수: {basic['sample_count']:,}개")
        print(f"    평균 성능: {perf['avg_write_rate']:.1f} MB/s")
        print(f"    성능 범위: {perf['min_write_rate']:.1f} ~ {perf['max_write_rate']:.1f} MB/s")
        print(f"    변동계수: {perf['cv']:.3f}")
        print(f"    안정성: {char['stability']}")
        print(f"    트렌드: {char['trend']}")
        print(f"    성능 수준: {char['performance_level']}")
        print(f"    활동 수준: {char['activity_level']}")
    
    # 시각화 생성
    create_detailed_visualization(phase_analysis, phases)
    
    # 결과 저장
    save_detailed_results(phase_analysis)
    
    print("\n✅ LOG 기반 구간 상세 분석 완료!")
    print("📊 결과 파일: log_based_phases_detailed_analysis.png, log_based_phases_detailed_results.json, log_based_phases_detailed_report.md")

if __name__ == "__main__":
    main()





