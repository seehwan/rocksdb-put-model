#!/usr/bin/env python3
"""
Phase-B 시간별 Flush 및 Flush+Compaction 처리량 분석
"""

import re
import json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from datetime import datetime
import seaborn as sns

# Liberation Serif 폰트 설정 (Times 스타일)
plt.rcParams['font.family'] = 'Liberation Serif'
plt.rcParams['axes.unicode_minus'] = False

class HourlyFlushCompactionAnalyzer:
    def __init__(self):
        self.flush_events = []
        self.compaction_events = []
        self.stats_events = []
        
    def parse_log_file(self, log_file):
        """LOG 파일 파싱"""
        print(f"📖 LOG 파일 파싱: {log_file}")
        
        with open(log_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    # Flush 이벤트 파싱
                    flush_data = self.parse_flush_line(line)
                    if flush_data:
                        self.flush_events.append(flush_data)
                    
                    # Compaction 이벤트 파싱
                    compaction_data = self.parse_compaction_line(line)
                    if compaction_data:
                        self.compaction_events.append(compaction_data)
                    
                    # Stats 이벤트 파싱
                    stats_data = self.parse_stats_line(line)
                    if stats_data:
                        self.stats_events.append(stats_data)
                        
                except Exception as e:
                    if line_num % 10000 == 0:
                        print(f"  처리 중... 라인 {line_num}")
                    continue
        
        print(f"✅ 파싱 완료: Flush {len(self.flush_events)}, Compaction {len(self.compaction_events)}, Stats {len(self.stats_events)}")
    
    def parse_flush_line(self, line):
        """Flush 라인 파싱"""
        try:
            # Flush 시작/완료 이벤트 (EVENT_LOG_v1 형식)
            if "flush_started" in line or "flush_finished" in line:
                timestamp_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
                timestamp = timestamp_match.group(1) if timestamp_match else None
                
                # Flush 크기 추출 (flush_started에서만 total_data_size가 있음)
                size_mb = 0.0
                if "flush_started" in line:
                    size_match = re.search(r'"total_data_size": (\d+)', line)
                    if size_match:
                        size_bytes = int(size_match.group(1))
                        size_mb = size_bytes / (1024 * 1024)  # bytes to MB
                
                # Flush 타입
                flush_type = "start" if "flush_started" in line else "finish"
                
                return {
                    'timestamp': timestamp,
                    'type': flush_type,
                    'size_mb': size_mb,
                    'line': line.strip()
                }
        except Exception:
            return None
    
    def parse_compaction_line(self, line):
        """Compaction 라인 파싱"""
        try:
            # Compaction 시작/완료 이벤트 (EVENT_LOG_v1 형식)
            if "compaction_started" in line or "compaction_finished" in line:
                timestamp_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
                timestamp = timestamp_match.group(1) if timestamp_match else None
                
                # Compaction 크기 추출
                if "compaction_started" in line:
                    # input_data_size에서 크기 추출
                    size_match = re.search(r'"input_data_size": (\d+)', line)
                    if size_match:
                        size_bytes = int(size_match.group(1))
                        size_mb = size_bytes / (1024 * 1024)  # bytes to MB
                    else:
                        size_mb = 0.0
                else:  # compaction_finished
                    # total_output_size에서 크기 추출
                    size_match = re.search(r'"total_output_size": (\d+)', line)
                    if size_match:
                        size_bytes = int(size_match.group(1))
                        size_mb = size_bytes / (1024 * 1024)  # bytes to MB
                    else:
                        size_mb = 0.0
                
                # Level 정보 추출
                level_match = re.search(r'"output_level": (\d+)', line)
                if level_match:
                    level = int(level_match.group(1))
                else:
                    level = -1
                
                # Compaction 타입
                compaction_type = "start" if "compaction_started" in line else "finish"
                
                return {
                    'timestamp': timestamp,
                    'type': compaction_type,
                    'size_mb': size_mb,
                    'level': level,
                    'line': line.strip()
                }
        except Exception:
            return None
    
    def parse_stats_line(self, line):
        """Stats 라인 파싱"""
        try:
            # Stats 라인에서 처리량 정보 추출
            if "Cumulative writes" in line and "ingest:" in line:
                timestamp_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
                timestamp = timestamp_match.group(1) if timestamp_match else None
                
                # MB/s에서 처리량 계산
                mbps_match = re.search(r'ingest: [\d.]+ GB, ([\d.]+) MB/s', line)
                if mbps_match:
                    mbps = float(mbps_match.group(1))
                    # MB/s를 ops/sec로 변환 (1KB 키+값 가정)
                    ops_per_sec = mbps * 1024  # MB/s * 1024 = ops/sec (1KB per op)
                else:
                    ops_per_sec = 0
                
                # Cumulative writes 추출
                cum_writes_match = re.search(r'Cumulative writes: (\d+)K writes', line)
                if cum_writes_match:
                    cum_writes = int(cum_writes_match.group(1)) * 1000
                else:
                    cum_writes_match = re.search(r'Cumulative writes: (\d+) writes', line)
                    cum_writes = int(cum_writes_match.group(1)) if cum_writes_match else 0
                
                return {
                    'timestamp': timestamp,
                    'ops_per_sec': ops_per_sec,
                    'cumulative_writes': cum_writes,
                    'line': line.strip()
                }
        except Exception:
            return None
    
    def analyze_hourly_throughput(self):
        """시간별 처리량 분석"""
        print("📊 시간별 처리량 분석 중...")
        
        # 시간별 데이터 정리
        hourly_data = {}
        
        # Flush 이벤트 처리
        for event in self.flush_events:
            if event['timestamp']:
                hour = event['timestamp'][:13]  # YYYY/MM/DD-HH
                if hour not in hourly_data:
                    hourly_data[hour] = {
                        'flush_count': 0,
                        'flush_size_mb': 0.0,
                        'compaction_count': 0,
                        'compaction_size_mb': 0.0,
                        'total_ops_per_sec': 0.0,
                        'stats_count': 0
                    }
                
                if event['type'] == 'start':  # 시작된 flush의 크기 계산
                    hourly_data[hour]['flush_count'] += 1
                    hourly_data[hour]['flush_size_mb'] += event['size_mb']
        
        # Compaction 이벤트 처리
        for event in self.compaction_events:
            if event['timestamp']:
                hour = event['timestamp'][:13]  # YYYY/MM/DD-HH
                if hour not in hourly_data:
                    hourly_data[hour] = {
                        'flush_count': 0,
                        'flush_size_mb': 0.0,
                        'compaction_count': 0,
                        'compaction_size_mb': 0.0,
                        'total_ops_per_sec': 0.0,
                        'stats_count': 0
                    }
                
                if event['type'] == 'finish':  # 완료된 compaction만 계산
                    hourly_data[hour]['compaction_count'] += 1
                    hourly_data[hour]['compaction_size_mb'] += event['size_mb']
        
        # Stats 이벤트 처리
        for event in self.stats_events:
            if event['timestamp']:
                hour = event['timestamp'][:13]  # YYYY/MM/DD-HH
                if hour not in hourly_data:
                    hourly_data[hour] = {
                        'flush_count': 0,
                        'flush_size_mb': 0.0,
                        'compaction_count': 0,
                        'compaction_size_mb': 0.0,
                        'total_ops_per_sec': 0.0,
                        'stats_count': 0
                    }
                
                hourly_data[hour]['total_ops_per_sec'] += event['ops_per_sec']
                hourly_data[hour]['stats_count'] += 1
        
        # 평균 처리량 계산
        for hour in hourly_data:
            if hourly_data[hour]['stats_count'] > 0:
                hourly_data[hour]['avg_ops_per_sec'] = hourly_data[hour]['total_ops_per_sec'] / hourly_data[hour]['stats_count']
            else:
                hourly_data[hour]['avg_ops_per_sec'] = 0.0
        
        return hourly_data
    
    def create_visualizations(self, hourly_data):
        """시각화 생성"""
        print("📈 시각화 생성 중...")
        
        # 시간순 정렬
        sorted_hours = sorted(hourly_data.keys())
        
        # 데이터 추출
        hours = []
        flush_counts = []
        flush_sizes = []
        compaction_counts = []
        compaction_sizes = []
        avg_ops_per_sec = []
        
        for hour in sorted_hours:
            data = hourly_data[hour]
            hours.append(hour)
            flush_counts.append(data['flush_count'])
            flush_sizes.append(data['flush_size_mb'])
            compaction_counts.append(data['compaction_count'])
            compaction_sizes.append(data['compaction_size_mb'])
            avg_ops_per_sec.append(data['avg_ops_per_sec'])
        
        # 1. 시간별 Flush vs Compaction 처리량 비교
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Flush 처리량 (MB)
        ax1.bar(range(len(hours)), flush_sizes, alpha=0.7, color='skyblue', label='Flush Size (MB)')
        ax1.set_title('Hourly Flush Throughput (MB)', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Time (Hour)', fontsize=12)
        ax1.set_ylabel('Flush Size (MB)', fontsize=12)
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Compaction 처리량 (MB)
        ax2.bar(range(len(hours)), compaction_sizes, alpha=0.7, color='lightcoral', label='Compaction Size (MB)')
        ax2.set_title('Hourly Compaction Throughput (MB)', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Time (Hour)', fontsize=12)
        ax2.set_ylabel('Compaction Size (MB)', fontsize=12)
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Flush + Compaction 총 처리량
        total_sizes = [f + c for f, c in zip(flush_sizes, compaction_sizes)]
        ax3.bar(range(len(hours)), total_sizes, alpha=0.7, color='lightgreen', label='Total (Flush + Compaction)')
        ax3.set_title('Hourly Total Throughput (Flush + Compaction)', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Time (Hour)', fontsize=12)
        ax3.set_ylabel('Total Size (MB)', fontsize=12)
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # 평균 Ops/sec
        ax4.plot(range(len(hours)), avg_ops_per_sec, marker='o', linewidth=2, color='purple', label='Avg Ops/sec')
        ax4.set_title('Hourly Average Operations per Second', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Time (Hour)', fontsize=12)
        ax4.set_ylabel('Ops/sec', fontsize=12)
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        
        # X축 레이블 설정
        for ax in [ax1, ax2, ax3, ax4]:
            ax.set_xticks(range(len(hours)))
            ax.set_xticklabels([h.split('-')[1] for h in hours], rotation=45)
        
        plt.tight_layout()
        plt.savefig('hourly_flush_compaction_throughput.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. 상세 분석 차트
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Flush vs Compaction 비교
        x = np.arange(len(hours))
        width = 0.35
        
        ax1.bar(x - width/2, flush_sizes, width, label='Flush (MB)', alpha=0.8, color='skyblue')
        ax1.bar(x + width/2, compaction_sizes, width, label='Compaction (MB)', alpha=0.8, color='lightcoral')
        ax1.set_title('Flush vs Compaction Throughput Comparison', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Time (Hour)', fontsize=12)
        ax1.set_ylabel('Size (MB)', fontsize=12)
        ax1.set_xticks(x)
        ax1.set_xticklabels([h.split('-')[1] for h in hours], rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 처리량 비율 분석
        flush_ratios = []
        compaction_ratios = []
        for i in range(len(hours)):
            total = flush_sizes[i] + compaction_sizes[i]
            if total > 0:
                flush_ratios.append(flush_sizes[i] / total * 100)
                compaction_ratios.append(compaction_sizes[i] / total * 100)
            else:
                flush_ratios.append(0)
                compaction_ratios.append(0)
        
        ax2.bar(x, flush_ratios, width, label='Flush Ratio (%)', alpha=0.8, color='skyblue')
        ax2.bar(x, compaction_ratios, width, bottom=flush_ratios, label='Compaction Ratio (%)', alpha=0.8, color='lightcoral')
        ax2.set_title('Flush vs Compaction Ratio Analysis', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Time (Hour)', fontsize=12)
        ax2.set_ylabel('Ratio (%)', fontsize=12)
        ax2.set_xticks(x)
        ax2.set_xticklabels([h.split('-')[1] for h in hours], rotation=45)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('hourly_flush_compaction_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ 시각화 완료: hourly_flush_compaction_throughput.png, hourly_flush_compaction_analysis.png")
    
    def generate_summary_report(self, hourly_data):
        """요약 보고서 생성"""
        print("📝 요약 보고서 생성 중...")
        
        # 통계 계산
        total_flush_size = sum(data['flush_size_mb'] for data in hourly_data.values())
        total_compaction_size = sum(data['compaction_size_mb'] for data in hourly_data.values())
        total_size = total_flush_size + total_compaction_size
        
        avg_flush_size = np.mean([data['flush_size_mb'] for data in hourly_data.values()])
        avg_compaction_size = np.mean([data['compaction_size_mb'] for data in hourly_data.values()])
        
        max_flush_hour = max(hourly_data.keys(), key=lambda h: hourly_data[h]['flush_size_mb'])
        max_compaction_hour = max(hourly_data.keys(), key=lambda h: hourly_data[h]['compaction_size_mb'])
        
        summary = {
            'analysis_type': 'Hourly Flush and Compaction Throughput Analysis',
            'total_hours_analyzed': len(hourly_data),
            'total_flush_size_mb': total_flush_size,
            'total_compaction_size_mb': total_compaction_size,
            'total_combined_size_mb': total_size,
            'average_flush_size_mb': avg_flush_size,
            'average_compaction_size_mb': avg_compaction_size,
            'flush_compaction_ratio': total_flush_size / total_compaction_size if total_compaction_size > 0 else 0,
            'max_flush_hour': max_flush_hour,
            'max_flush_size_mb': hourly_data[max_flush_hour]['flush_size_mb'],
            'max_compaction_hour': max_compaction_hour,
            'max_compaction_size_mb': hourly_data[max_compaction_hour]['compaction_size_mb'],
            'hourly_breakdown': hourly_data
        }
        
        # JSON 저장
        with open('hourly_flush_compaction_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        # MD 보고서 생성
        with open('hourly_flush_compaction_report.md', 'w') as f:
            f.write("# Hourly Flush and Compaction Throughput Analysis\n\n")
            f.write("## Summary\n\n")
            f.write(f"- **Total Hours Analyzed**: {len(hourly_data)}\n")
            f.write(f"- **Total Flush Size**: {total_flush_size:.2f} MB\n")
            f.write(f"- **Total Compaction Size**: {total_compaction_size:.2f} MB\n")
            f.write(f"- **Total Combined Size**: {total_size:.2f} MB\n")
            f.write(f"- **Average Flush Size per Hour**: {avg_flush_size:.2f} MB\n")
            f.write(f"- **Average Compaction Size per Hour**: {avg_compaction_size:.2f} MB\n")
            f.write(f"- **Flush/Compaction Ratio**: {total_flush_size/total_compaction_size:.2f}\n\n")
            
            f.write("## Peak Performance\n\n")
            f.write(f"- **Max Flush Hour**: {max_flush_hour} ({hourly_data[max_flush_hour]['flush_size_mb']:.2f} MB)\n")
            f.write(f"- **Max Compaction Hour**: {max_compaction_hour} ({hourly_data[max_compaction_hour]['compaction_size_mb']:.2f} MB)\n\n")
            
            f.write("## Hourly Breakdown\n\n")
            f.write("| Hour | Flush Size (MB) | Compaction Size (MB) | Total Size (MB) | Flush Count | Compaction Count |\n")
            f.write("|------|----------------|---------------------|-----------------|-------------|------------------|\n")
            
            for hour in sorted(hourly_data.keys()):
                data = hourly_data[hour]
                total = data['flush_size_mb'] + data['compaction_size_mb']
                f.write(f"| {hour} | {data['flush_size_mb']:.2f} | {data['compaction_size_mb']:.2f} | {total:.2f} | {data['flush_count']} | {data['compaction_count']} |\n")
        
        print("✅ 요약 보고서 완료: hourly_flush_compaction_summary.json, hourly_flush_compaction_report.md")

def main():
    """메인 함수"""
    print("🚀 Phase-B 시간별 Flush 및 Compaction 처리량 분석 시작...")
    
    # LOG 파일 찾기
    log_files = list(Path('.').glob('LOG*')) + list(Path('logs').glob('LOG*'))
    
    if not log_files:
        print("❌ LOG 파일을 찾을 수 없습니다!")
        print("Phase-B 실행 후 LOG 파일이 생성되었는지 확인하세요.")
        return
    
    # 가장 큰 LOG 파일 선택 (메인 로그)
    main_log = max(log_files, key=lambda f: f.stat().st_size)
    print(f"📖 메인 LOG 파일: {main_log}")
    
    # 분석기 초기화
    analyzer = HourlyFlushCompactionAnalyzer()
    
    # LOG 파일 파싱
    analyzer.parse_log_file(main_log)
    
    if not analyzer.flush_events and not analyzer.compaction_events:
        print("❌ 분석할 데이터가 없습니다!")
        print("LOG 파일에 Flush 또는 Compaction 이벤트가 없습니다.")
        return
    
    # 시간별 처리량 분석
    hourly_data = analyzer.analyze_hourly_throughput()
    
    if not hourly_data:
        print("❌ 시간별 데이터가 없습니다!")
        return
    
    # 시각화 생성
    analyzer.create_visualizations(hourly_data)
    
    # 요약 보고서 생성
    analyzer.generate_summary_report(hourly_data)
    
    print("🎉 Phase-B 시간별 Flush 및 Compaction 처리량 분석 완료!")

if __name__ == "__main__":
    main()
