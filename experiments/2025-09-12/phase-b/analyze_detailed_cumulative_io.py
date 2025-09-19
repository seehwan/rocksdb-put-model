#!/usr/bin/env python3
"""
상세 누적 I/O 처리량 분석
Flush부터 각 레벨까지의 상세한 누적 I/O 처리량 분석
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
            elif "Flushing memtable" in line or "Flush lasted" in line:
                flush_data.append(parse_flush_line(line))
    
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

def parse_compaction_line(line):
    """Compaction 라인 파싱"""
    try:
        timestamp_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
        timestamp = timestamp_match.group(1) if timestamp_match else None
        
        # level 추출 (Base level 정보에서)
        level_match = re.search(r'Base level (\d+)', line)
        level = int(level_match.group(1)) if level_match else -1
        
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

def analyze_detailed_cumulative_io(stats_data, compaction_data, flush_data):
    """상세 누적 I/O 처리량 분석"""
    print("📊 상세 누적 I/O 처리량 분석 중...")
    
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
        
        # 1. 시간별 누적 I/O 처리량 (Flush + Compaction)
        if not flush_df.empty:
            hourly_flush = flush_df.groupby('hour').size()
            ax1.plot(hourly_flush.index, hourly_flush.values, 'b-', linewidth=2, marker='o', label='Flush I/O')
        
        if not compaction_df.empty:
            # 레벨별 시간별 I/O 량 계산
            hourly_level_io = compaction_df.groupby(['hour', 'level']).size().unstack(fill_value=0)
            
            # 레벨별 누적 I/O 처리량
            level_order = sorted([col for col in hourly_level_io.columns if col != -1])
            colors = plt.cm.Set3(np.linspace(0, 1, len(level_order)))
            
            for i, level in enumerate(level_order):
                if level in hourly_level_io.columns:
                    ax1.plot(hourly_level_io.index, hourly_level_io[level], 
                            color=colors[i], linewidth=2, marker='s', markersize=4,
                            label=f'Level {level} I/O')
        
        ax1.set_title('Hourly Cumulative I/O Volume by Level', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('I/O Count per Hour')
        ax1.grid(True, alpha=0.3)
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. 레벨별 누적 I/O 처리량 히트맵
        if not compaction_df.empty:
            # 시간별 레벨별 I/O 량 히트맵
            hourly_level_io = compaction_df.groupby(['hour', 'level']).size().unstack(fill_value=0)
            
            if not hourly_level_io.empty:
                # 레벨 순서 정렬
                level_order = sorted([col for col in hourly_level_io.columns if col != -1])
                hourly_level_io_sorted = hourly_level_io[level_order]
                
                im = ax2.imshow(hourly_level_io_sorted.T.values, cmap='YlOrRd', aspect='auto')
                ax2.set_title('Hourly I/O Volume Heatmap by Level', fontsize=16, fontweight='bold')
                ax2.set_xlabel('Time (Hours)')
                ax2.set_ylabel('Level')
                ax2.set_yticks(range(len(level_order)))
                ax2.set_yticklabels([f'Level {l}' for l in level_order])
                
                # 시간 축 레이블 (24시간마다)
                time_labels = hourly_level_io_sorted.index[::24]
                time_positions = range(0, len(hourly_level_io_sorted), 24)
                ax2.set_xticks(time_positions)
                ax2.set_xticklabels([t.strftime('%m/%d %H:%M') for t in time_labels], rotation=45)
                
                # 컬러바 추가
                cbar = plt.colorbar(im, ax=ax2)
                cbar.set_label('I/O Count')
        
        # 3. 레벨별 I/O 처리량 분포 (박스플롯)
        if not compaction_df.empty:
            level_data = []
            level_labels = []
            for level in level_order:
                if level in hourly_level_io.columns:
                    level_data.append(hourly_level_io[level].values)
                    level_labels.append(f'Level {level}')
            
            if level_data:
                bp = ax3.boxplot(level_data, labels=level_labels, patch_artist=True)
                colors = plt.cm.Set3(np.linspace(0, 1, len(level_data)))
                for patch, color in zip(bp['boxes'], colors):
                    patch.set_facecolor(color)
                    patch.set_alpha(0.7)
        
        ax3.set_title('I/O Volume Distribution by Level', fontsize=16, fontweight='bold')
        ax3.set_xlabel('Level')
        ax3.set_ylabel('I/O Count per Hour')
        ax3.grid(True, alpha=0.3)
        ax3.tick_params(axis='x', rotation=45)
        
        # 4. 누적 I/O 처리량 비율 (파이 차트)
        if not compaction_df.empty:
            total_io_by_level = compaction_df['level'].value_counts().sort_index()
            level_labels_pie = [f'Level {l}' for l in total_io_by_level.index]
            colors_pie = plt.cm.Set3(np.linspace(0, 1, len(total_io_by_level)))
            
            wedges, texts, autotexts = ax4.pie(total_io_by_level.values, labels=level_labels_pie, 
                                              autopct='%1.1f%%', colors=colors_pie, startangle=90)
            ax4.set_title('Cumulative I/O Volume Ratio by Level', fontsize=16, fontweight='bold')
            
            # 통계 정보 추가
            stats_text = f"""
            Total I/O Operations: {total_io_by_level.sum():,}
            Analysis Period: {len(hourly_level_io)} hours
            Most Active Level: {level_labels_pie[total_io_by_level.idxmax()]}
            """
            ax4.text(1.3, 0.5, stats_text, transform=ax4.transAxes, fontsize=10,
                    verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig('detailed_cumulative_io_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ 상세 누적 I/O 처리량 분석 시각화 저장 완료: detailed_cumulative_io_analysis.png")
        
        # 상세 분석 결과 출력
        print("\n📊 상세 누적 I/O 처리량 분석 결과:")
        print(f"  분석 기간: {len(hourly_level_io)} 시간")
        print(f"  총 I/O 작업: {total_io_by_level.sum():,}회")
        print(f"  레벨별 I/O 량:")
        for level, count in total_io_by_level.items():
            level_name = f'Level {level}'
            percentage = (count / total_io_by_level.sum()) * 100
            print(f"    {level_name}: {count:,}회 ({percentage:.1f}%)")
        
        # Flush 분석 (있는 경우)
        if not flush_df.empty:
            print(f"\n  Flush 분석:")
            print(f"    총 Flush: {len(flush_df)}회")
            flush_type_counts = flush_df['type'].value_counts()
            for flush_type, count in flush_type_counts.items():
                print(f"    {flush_type}: {count}회")
        
        # 시간대별 분석
        print(f"\n  시간대별 I/O 패턴:")
        hourly_total = hourly_level_io.sum(axis=1)
        peak_hour = hourly_total.idxmax()
        min_hour = hourly_total.idxmin()
        print(f"    최대 I/O 시간: {peak_hour.strftime('%Y-%m-%d %H:%M')} ({hourly_total.max():,}회)")
        print(f"    최소 I/O 시간: {min_hour.strftime('%Y-%m-%d %H:%M')} ({hourly_total.min():,}회)")
        print(f"    평균 I/O 량: {hourly_total.mean():.1f}회/시간")
        
    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("🚀 상세 누적 I/O 처리량 분석 시작...")
    
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
    
    # 상세 누적 I/O 처리량 분석
    analyze_detailed_cumulative_io(stats_data, compaction_data, flush_data)
    
    print("\n✅ 상세 누적 I/O 처리량 분석 완료!")

if __name__ == "__main__":
    main()


