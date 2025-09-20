#!/usr/bin/env python3
"""
Phase-B LOG 기반 분석
RocksDB LOG 파일을 기반으로 한 정확한 Phase-B 분석
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
        # cumulative_writes 추출 (K 단위 처리)
        cum_writes_match = re.search(r'Cumulative writes: (\d+)K writes', line)
        if cum_writes_match:
            cum_writes = int(cum_writes_match.group(1)) * 1000
        else:
            cum_writes_match = re.search(r'Cumulative writes: (\d+) writes', line)
            cum_writes = int(cum_writes_match.group(1)) if cum_writes_match else 0
        
        # MB/s에서 write_rate 계산
        mbps_match = re.search(r'ingest: [\d.]+ GB, ([\d.]+) MB/s', line)
        if mbps_match:
            mbps = float(mbps_match.group(1))
            write_rate = mbps * 1024  # MB/s * 1024 = ops/sec (1KB per op)
        else:
            write_rate = 0
        
        return {
            'timestamp': timestamp,
            'write_rate': write_rate,
            'cumulative_writes': cum_writes
        }
    except Exception as e:
        return None

def parse_compaction_start_line(line, timestamp):
    """Compaction start 라인 파싱"""
    try:
        # Base level 추출
        base_level_match = re.search(r'Base level (\d+)', line)
        base_level = int(base_level_match.group(1)) if base_level_match else -1
        
        # Input files 추출
        inputs_match = re.search(r'inputs: \[([^\]]+)\]', line)
        input_files = inputs_match.group(1) if inputs_match else ""
        
        return {
            'timestamp': timestamp,
            'type': 'start',
            'base_level': base_level,
            'input_files': input_files,
            'output_files': "",
            'compaction_type': f"Level-{base_level}"
        }
    except Exception as e:
        return None

def parse_compaction_finish_line(line, timestamp):
    """Compaction finish 라인 파싱 (compacted to 패턴)"""
    try:
        # files[6 3 0 0 0 0 0] 패턴에서 레벨별 파일 수 추출
        files_match = re.search(r'files\[([^\]]+)\]', line)
        if files_match:
            files_str = files_match.group(1)
            files_per_level = [int(x) for x in files_str.split()]
            
            # Base level 추출 (level 정보에서)
            level_match = re.search(r'level (\d+)', line)
            base_level = int(level_match.group(1)) if level_match else -1
            
            return {
                'timestamp': timestamp,
                'type': 'finished',
                'base_level': base_level,
                'input_files': "",
                'output_files': files_str,
                'compaction_type': f"Level-{base_level}",
                'files_per_level': files_per_level
            }
        return None
    except Exception as e:
        return None

def parse_flush_line(line, timestamp):
    """Flush 라인 파싱"""
    try:
        # Flush 타입 추출
        flush_type = "unknown"
        if "Flushing memtable" in line:
            flush_type = "start"
        elif "Flush lasted" in line:
            flush_type = "finished"
        
        return {
            'timestamp': timestamp,
            'type': flush_type
        }
    except Exception as e:
        return None

def analyze_phase_b_log_based(stats_data, compaction_data, flush_data):
    """Phase-B LOG 기반 분석"""
    print("📊 Phase-B LOG 기반 분석 중...")
    
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
        
        # 시간별 그룹화 (시간 단위)
        stats_df['hour'] = stats_df['datetime'].dt.floor('h')
        if not compaction_df.empty:
            compaction_df['hour'] = compaction_df['datetime'].dt.floor('h')
        if not flush_df.empty:
            flush_df['hour'] = flush_df['datetime'].dt.floor('h')
        
        # 시각화 생성
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
        
        # 1. 성능 지표 시간별 변화
        ax1.plot(stats_df['datetime'], stats_df['write_rate'], 'b-', linewidth=2, alpha=0.7, label='Write Rate')
        ax1.set_title('Write Rate Time Series (LOG-based)', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Write Rate (ops/sec)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.tick_params(axis='x', rotation=45)
        
        # 이동평균 추가
        stats_df['ma_10'] = stats_df['write_rate'].rolling(window=10).mean()
        ax1.plot(stats_df['datetime'], stats_df['ma_10'], 'r--', alpha=0.8, linewidth=2, label='10-point MA')
        ax1.legend()
        
        # 2. Compaction Flow 분석
        if not compaction_df.empty:
            # Base Level별 Compaction 분포
            base_level_counts = compaction_df['base_level'].value_counts().sort_index()
            colors = plt.cm.Set3(np.linspace(0, 1, len(base_level_counts)))
            
            bars = ax2.bar(range(len(base_level_counts)), base_level_counts.values, color=colors, alpha=0.8)
            ax2.set_title('Compaction Distribution by Base Level', fontsize=16, fontweight='bold')
            ax2.set_xlabel('Base Level')
            ax2.set_ylabel('Compaction Count')
            ax2.set_xticks(range(len(base_level_counts)))
            ax2.set_xticklabels([f'Level {l}' for l in base_level_counts.index])
            ax2.grid(True, alpha=0.3)
            
            # 값 표시
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{int(height)}', ha='center', va='bottom', fontsize=10)
        
        # 3. Flush vs Compaction 비교
        if not flush_df.empty and not compaction_df.empty:
            hourly_flush = flush_df.groupby('hour').size()
            hourly_compaction = compaction_df.groupby('hour').size()
            
            ax3.plot(hourly_flush.index, hourly_flush.values, 'b-', linewidth=2, marker='o', label='Flush I/O')
            ax3.plot(hourly_compaction.index, hourly_compaction.values, 'r-', linewidth=2, marker='s', label='Compaction I/O')
            ax3.set_title('Flush vs Compaction I/O Comparison', fontsize=16, fontweight='bold')
            ax3.set_xlabel('Time')
            ax3.set_ylabel('I/O Count per Hour')
            ax3.grid(True, alpha=0.3)
            ax3.legend()
            ax3.tick_params(axis='x', rotation=45)
        
        # 4. 레벨별 Compaction Flow 히트맵
        if not compaction_df.empty:
            hourly_base_level = compaction_df.groupby(['hour', 'base_level']).size().unstack(fill_value=0)
            
            if not hourly_base_level.empty:
                # 레벨 순서 정렬
                level_order = sorted([col for col in hourly_base_level.columns if col != -1])
                hourly_base_level_sorted = hourly_base_level[level_order]
                
                im = ax4.imshow(hourly_base_level_sorted.T.values, cmap='YlOrRd', aspect='auto')
                ax4.set_title('Hourly Compaction Flow Heatmap', fontsize=16, fontweight='bold')
                ax4.set_xlabel('Time (Hours)')
                ax4.set_ylabel('Base Level')
                ax4.set_yticks(range(len(level_order)))
                ax4.set_yticklabels([f'Level {l}' for l in level_order])
                
                # 시간 축 레이블 (24시간마다)
                time_labels = hourly_base_level_sorted.index[::24]
                time_positions = range(0, len(hourly_base_level_sorted), 24)
                ax4.set_xticks(time_positions)
                ax4.set_xticklabels([t.strftime('%m/%d %H:%M') for t in time_labels], rotation=45)
                
                # 컬러바 추가
                cbar = plt.colorbar(im, ax=ax4)
                cbar.set_label('Compaction Count')
        
        plt.tight_layout()
        plt.savefig('phase_b_log_based_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Phase-B LOG 기반 분석 시각화 저장 완료: phase_b_log_based_analysis.png")
        
        # 상세 분석 결과 출력
        print("\n📊 Phase-B LOG 기반 분석 결과:")
        print(f"  분석 기간: {len(stats_df)} 데이터 포인트")
        print(f"  초기 성능: {stats_df['write_rate'].iloc[0]:.1f} ops/sec")
        print(f"  최종 성능: {stats_df['write_rate'].iloc[-1]:.1f} ops/sec")
        print(f"  평균 성능: {stats_df['write_rate'].mean():.1f} ops/sec")
        print(f"  최대 성능: {stats_df['write_rate'].max():.1f} ops/sec")
        print(f"  최소 성능: {stats_df['write_rate'].min():.1f} ops/sec")
        
        # Compaction 분석
        if not compaction_df.empty:
            print(f"\n  Compaction 분석:")
            print(f"    총 Compaction: {len(compaction_df)}회")
            base_level_counts = compaction_df['base_level'].value_counts().sort_index()
            for level, count in base_level_counts.items():
                level_name = f'Level {level}'
                percentage = (count / base_level_counts.sum()) * 100
                print(f"    {level_name}: {count:,}회 ({percentage:.1f}%)")
        
        # Flush 분석
        if not flush_df.empty:
            print(f"\n  Flush 분석:")
            print(f"    총 Flush: {len(flush_df)}회")
            flush_type_counts = flush_df['type'].value_counts()
            for flush_type, count in flush_type_counts.items():
                print(f"    {flush_type}: {count}회")
        
        # 성능 저하 분석
        initial_performance = stats_df['write_rate'].iloc[0]
        final_performance = stats_df['write_rate'].iloc[-1]
        if initial_performance > 0:
            degradation_percent = ((initial_performance - final_performance) / initial_performance) * 100
            print(f"\n  성능 저하 분석:")
            print(f"    초기 성능: {initial_performance:.1f} ops/sec")
            print(f"    최종 성능: {final_performance:.1f} ops/sec")
            print(f"    성능 저하율: {degradation_percent:.1f}%")
        
    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("🚀 Phase-B LOG 기반 분석 시작...")
    
    # LOG 파일 경로 설정
    main_log = "rocksdb_log_phase_b.log"
    
    if not os.path.exists(main_log):
        print("❌ LOG 파일을 찾을 수 없습니다!")
        print("Phase-B 실행 후 LOG 파일이 생성되었는지 확인하세요.")
        return
    
    print(f"📖 메인 LOG 파일: {main_log}")
    
    # LOG 파일 분석
    stats_data, compaction_data, flush_data = parse_log_file(main_log)
    
    if not stats_data:
        print("❌ 분석할 데이터가 없습니다!")
        return
    
    # Phase-B LOG 기반 분석
    analyze_phase_b_log_based(stats_data, compaction_data, flush_data)
    
    print("\n✅ Phase-B LOG 기반 분석 완료!")

if __name__ == "__main__":
    main()


