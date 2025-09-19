#!/usr/bin/env python3
"""
상세 레벨별 I/O 분석
RocksDB LOG 파일에서 레벨별 I/O 패턴의 세부 분석
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
            elif "Compaction start" in line or "Compaction finished" in line:
                compaction_data.append(parse_compaction_line(line))
            
            # Flush 로그 파싱
            elif "Flush start" in line or "Flush finished" in line:
                flush_data.append(parse_flush_line(line))
    
    print(f"✅ 파싱 완료: Stats {len(stats_data)}개, Compaction {len(compaction_data)}개, Flush {len(flush_data)}개")
    return stats_data, compaction_data, flush_data

def parse_stats_line(line, timestamp):
    """Stats 라인 파싱"""
    try:
        write_rate_match = re.search(r'write_rate:(\d+(?:\.\d+)?)', line)
        write_rate = float(write_rate_match.group(1)) if write_rate_match else 0
        
        cum_writes_match = re.search(r'Cumulative writes:(\d+)', line)
        cum_writes = int(cum_writes_match.group(1)) if cum_writes_match else 0
        
        return {
            'timestamp': timestamp,
            'write_rate': write_rate,
            'cumulative_writes': cum_writes
        }
    except Exception as e:
        return None

def parse_compaction_line(line):
    """Compaction 라인 파싱"""
    try:
        level_match = re.search(r'level:(\d+)', line)
        level = int(level_match.group(1)) if level_match else -1
        
        timestamp_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
        timestamp = timestamp_match.group(1) if timestamp_match else None
        
        # Compaction 타입 추출
        compaction_type = "unknown"
        if "start" in line:
            compaction_type = "start"
        elif "finished" in line:
            compaction_type = "finished"
        
        return {
            'timestamp': timestamp,
            'level': level,
            'type': compaction_type
        }
    except Exception as e:
        return None

def parse_flush_line(line):
    """Flush 라인 파싱"""
    try:
        timestamp_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
        timestamp = timestamp_match.group(1) if timestamp_match else None
        
        # Flush 타입 추출
        flush_type = "unknown"
        if "start" in line:
            flush_type = "start"
        elif "finished" in line:
            flush_type = "finished"
        
        return {
            'timestamp': timestamp,
            'type': flush_type
        }
    except Exception as e:
        return None

def analyze_detailed_level_io(stats_data, compaction_data, flush_data):
    """상세 레벨별 I/O 분석"""
    print("📊 상세 레벨별 I/O 분석 중...")
    
    try:
        # 데이터프레임 생성
        stats_df = pd.DataFrame([d for d in stats_data if d is not None])
        compaction_df = pd.DataFrame([d for d in compaction_data if d is not None])
        flush_df = pd.DataFrame([d for d in flush_data if d is not None])
        
        if stats_df.empty:
            print("❌ 데이터가 없습니다!")
            return
        
        # 시간 변환
        stats_df['datetime'] = pd.to_datetime(stats_df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
        if not compaction_df.empty:
            compaction_df['datetime'] = pd.to_datetime(compaction_df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
        if not flush_df.empty:
            flush_df['datetime'] = pd.to_datetime(flush_df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
        
        # 시간별 그룹화
        stats_df['hour'] = stats_df['datetime'].dt.floor('h')
        
        # 시각화 생성
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
        
        # 1. 성능 지표 시간별 변화
        ax1.plot(stats_df['datetime'], stats_df['write_rate'], 'b-', linewidth=2, alpha=0.7, label='Write Rate')
        ax1.set_title('Write Rate Time Series', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Write Rate (ops/sec)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.tick_params(axis='x', rotation=45)
        
        # 이동평균 추가
        stats_df['ma_10'] = stats_df['write_rate'].rolling(window=10).mean()
        ax1.plot(stats_df['datetime'], stats_df['ma_10'], 'r--', alpha=0.8, linewidth=2, label='10-point MA')
        ax1.legend()
        
        # 2. 누적 쓰기 vs 성능 상관관계
        ax2.scatter(stats_df['cumulative_writes'], stats_df['write_rate'], 
                   c=range(len(stats_df)), cmap='viridis', alpha=0.6, s=50)
        ax2.set_title('Cumulative Writes vs Write Rate', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Cumulative Writes')
        ax2.set_ylabel('Write Rate (ops/sec)')
        ax2.grid(True, alpha=0.3)
        
        # 컬러바 추가
        cbar = plt.colorbar(ax2.collections[0], ax=ax2)
        cbar.set_label('Time Progression')
        
        # 3. 시간대별 성능 분포
        stats_df['hour_of_day'] = stats_df['datetime'].dt.hour
        hourly_stats = stats_df.groupby('hour_of_day')['write_rate'].agg(['mean', 'std', 'min', 'max'])
        
        ax3.errorbar(hourly_stats.index, hourly_stats['mean'], 
                    yerr=hourly_stats['std'], fmt='o-', capsize=5, capthick=2, linewidth=2)
        ax3.fill_between(hourly_stats.index, 
                        hourly_stats['mean'] - hourly_stats['std'],
                        hourly_stats['mean'] + hourly_stats['std'], 
                        alpha=0.3)
        ax3.set_title('Hourly Performance Distribution', fontsize=16, fontweight='bold')
        ax3.set_xlabel('Hour of Day')
        ax3.set_ylabel('Write Rate (ops/sec)')
        ax3.grid(True, alpha=0.3)
        ax3.set_xticks(range(0, 24, 2))
        
        # 4. 성능 저하 분석
        # 초기 10% vs 마지막 10% 성능 비교
        initial_10_percent = int(len(stats_df) * 0.1)
        final_10_percent = int(len(stats_df) * 0.9)
        
        initial_performance = stats_df.iloc[:initial_10_percent]['write_rate'].mean()
        final_performance = stats_df.iloc[final_10_percent:]['write_rate'].mean()
        degradation_percent = ((initial_performance - final_performance) / initial_performance) * 100
        
        # 성능 구간별 분석
        performance_ranges = [
            (stats_df['write_rate'].quantile(0.8), stats_df['write_rate'].max(), 'High'),
            (stats_df['write_rate'].quantile(0.6), stats_df['write_rate'].quantile(0.8), 'Medium-High'),
            (stats_df['write_rate'].quantile(0.4), stats_df['write_rate'].quantile(0.6), 'Medium-Low'),
            (stats_df['write_rate'].min(), stats_df['write_rate'].quantile(0.4), 'Low')
        ]
        
        range_counts = []
        range_labels = []
        for min_val, max_val, label in performance_ranges:
            count = len(stats_df[(stats_df['write_rate'] >= min_val) & (stats_df['write_rate'] < max_val)])
            range_counts.append(count)
            range_labels.append(f'{label}\n({min_val:.1f}-{max_val:.1f})')
        
        colors = ['red', 'orange', 'yellow', 'green']
        bars = ax4.bar(range_labels, range_counts, color=colors, alpha=0.7)
        ax4.set_title('Performance Range Distribution', fontsize=16, fontweight='bold')
        ax4.set_xlabel('Performance Range (ops/sec)')
        ax4.set_ylabel('Data Points Count')
        ax4.grid(True, alpha=0.3)
        ax4.tick_params(axis='x', rotation=45)
        
        # 값 표시
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{int(height)}', ha='center', va='bottom', fontsize=10)
        
        # 성능 저하 정보 추가
        degradation_text = f"""
        Performance Degradation Analysis:
        Initial Performance: {initial_performance:.1f} ops/sec
        Final Performance: {final_performance:.1f} ops/sec
        Degradation: {degradation_percent:.1f}%
        """
        ax4.text(0.02, 0.98, degradation_text, transform=ax4.transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig('detailed_level_io_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ 상세 레벨별 I/O 분석 시각화 저장 완료: detailed_level_io_analysis.png")
        
        # 상세 분석 결과 출력
        print("\n📊 상세 레벨별 I/O 분석 결과:")
        print(f"  분석 기간: {len(stats_df)} 데이터 포인트")
        print(f"  초기 성능: {initial_performance:.1f} ops/sec")
        print(f"  최종 성능: {final_performance:.1f} ops/sec")
        print(f"  성능 저하율: {degradation_percent:.1f}%")
        print(f"  평균 성능: {stats_df['write_rate'].mean():.1f} ops/sec")
        print(f"  성능 표준편차: {stats_df['write_rate'].std():.1f} ops/sec")
        print(f"  최대 성능: {stats_df['write_rate'].max():.1f} ops/sec")
        print(f"  최소 성능: {stats_df['write_rate'].min():.1f} ops/sec")
        
        # Compaction 분석 (있는 경우)
        if not compaction_df.empty:
            print(f"\n  Compaction 분석:")
            print(f"    총 Compaction: {len(compaction_df)}회")
            level_counts = compaction_df['level'].value_counts().sort_index()
            for level, count in level_counts.items():
                level_name = f'Level {level}' if level != -1 else 'Memtable'
                print(f"    {level_name}: {count}회")
        
        # Flush 분석 (있는 경우)
        if not flush_df.empty:
            print(f"\n  Flush 분석:")
            print(f"    총 Flush: {len(flush_df)}회")
            flush_type_counts = flush_df['type'].value_counts()
            for flush_type, count in flush_type_counts.items():
                print(f"    {flush_type}: {count}회")
        
    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("🚀 상세 레벨별 I/O 분석 시작...")
    
    # LOG 파일 찾기
    log_files = list(Path('.').glob('LOG*')) + list(Path('logs').glob('LOG*'))
    
    if not log_files:
        print("❌ LOG 파일을 찾을 수 없습니다!")
        print("Phase-B 실행 후 LOG 파일이 생성되었는지 확인하세요.")
        return
    
    # 가장 큰 LOG 파일 선택 (메인 로그)
    main_log = max(log_files, key=lambda f: f.stat().st_size)
    print(f"📖 메인 LOG 파일: {main_log}")
    
    # LOG 파일 분석
    stats_data, compaction_data, flush_data = parse_log_file(main_log)
    
    if not stats_data:
        print("❌ 분석할 데이터가 없습니다!")
        return
    
    # 상세 레벨별 I/O 분석
    analyze_detailed_level_io(stats_data, compaction_data, flush_data)
    
    print("\n✅ 상세 레벨별 I/O 분석 완료!")

if __name__ == "__main__":
    main()


