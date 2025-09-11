#!/usr/bin/env python3

import re
import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import seaborn as sns

def parse_fillrandom_results(file_path):
    """FillRandom 결과에서 성능 데이터 추출"""
    data = []
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 30초 간격 통계 추출
    pattern = r'thread (\d+): \((\d+),(\d+)\) ops and \(([\d.]+),([\d.]+)\) ops/second in \(([\d.]+),([\d.]+)\) seconds'
    matches = re.findall(pattern, content)
    
    for match in matches:
        thread_id, current_ops, total_ops, current_ops_sec, total_ops_sec, current_time, total_time = match
        data.append({
            'thread': int(thread_id),
            'current_ops': int(current_ops),
            'total_ops': int(total_ops),
            'current_ops_sec': float(current_ops_sec),
            'total_ops_sec': float(total_ops_sec),
            'current_time': float(current_time),
            'total_time': float(total_time)
        })
    
    return pd.DataFrame(data)

def extract_benchmark_summary(file_path):
    """벤치마크 요약 정보 추출"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 최종 결과 추출
    pattern = r'(\w+)\s+:\s+([\d.]+)\s+micros/op\s+([\d.]+)\s+ops/sec\s+([\d.]+)\s+seconds\s+([\d.]+)\s+operations'
    match = re.search(pattern, content)
    
    if match:
        benchmark, micros_per_op, ops_per_sec, duration, operations = match.groups()
        return {
            'benchmark': benchmark,
            'micros_per_op': float(micros_per_op),
            'ops_per_sec': float(ops_per_sec),
            'duration': float(duration),
            'operations': float(operations)
        }
    return None

def parse_rocksdb_log(log_path):
    """RocksDB LOG에서 Flush/Compaction 이벤트 추출"""
    flush_events = []
    compaction_events = []
    
    with open(log_path, 'r') as f:
        for line in f:
            # Flush 이벤트
            if 'flush' in line.lower() and 'level' in line:
                flush_events.append(line.strip())
            
            # Compaction 이벤트
            if 'compaction' in line.lower() and 'level' in line:
                compaction_events.append(line.strip())
    
    return flush_events, compaction_events

def create_performance_visualizations():
    """성능 시각화 생성"""
    results_dir = Path("phase_b_final_results")
    output_dir = Path("phase_b_visualizations")
    output_dir.mkdir(exist_ok=True)
    
    print("=== Phase-B 결과 시각화 ===")
    
    # 1. FillRandom 성능 추이
    print("1. FillRandom 성능 추이 분석...")
    try:
        df = parse_fillrandom_results(results_dir / "fillrandom_results.txt")
        if not df.empty:
            plt.figure(figsize=(15, 10))
            
            # 서브플롯 1: 스레드별 성능 추이
            plt.subplot(2, 2, 1)
            for thread in df['thread'].unique():
                thread_data = df[df['thread'] == thread]
                plt.plot(thread_data['total_time'], thread_data['current_ops_sec'], 
                        label=f'Thread {thread}', alpha=0.7)
            plt.xlabel('Time (seconds)')
            plt.ylabel('Operations/sec')
            plt.title('FillRandom: Thread Performance Over Time')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # 서브플롯 2: 전체 성능 추이
            plt.subplot(2, 2, 2)
            total_ops_sec = df.groupby('total_time')['current_ops_sec'].sum()
            plt.plot(total_ops_sec.index, total_ops_sec.values, 'b-', linewidth=2)
            plt.xlabel('Time (seconds)')
            plt.ylabel('Total Operations/sec')
            plt.title('FillRandom: Total Throughput Over Time')
            plt.grid(True, alpha=0.3)
            
            # 서브플롯 3: 스레드별 누적 작업량
            plt.subplot(2, 2, 3)
            for thread in df['thread'].unique():
                thread_data = df[df['thread'] == thread]
                plt.plot(thread_data['total_time'], thread_data['total_ops'], 
                        label=f'Thread {thread}', alpha=0.7)
            plt.xlabel('Time (seconds)')
            plt.ylabel('Cumulative Operations')
            plt.title('FillRandom: Cumulative Operations by Thread')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # 서브플롯 4: 성능 분포
            plt.subplot(2, 2, 4)
            plt.hist(df['current_ops_sec'], bins=30, alpha=0.7, edgecolor='black')
            plt.xlabel('Operations/sec')
            plt.ylabel('Frequency')
            plt.title('FillRandom: Performance Distribution')
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(output_dir / "fillrandom_performance.png", dpi=300, bbox_inches='tight')
            plt.close()
            print(f"  ✅ FillRandom 성능 차트 저장: {output_dir / 'fillrandom_performance.png'}")
    except Exception as e:
        print(f"  ❌ FillRandom 분석 오류: {e}")
    
    # 2. 벤치마크 비교
    print("2. 벤치마크 성능 비교...")
    benchmarks = ['fillrandom', 'readrandomwriterandom', 'overwrite', 'mixgraph']
    benchmark_data = []
    
    for bench in benchmarks:
        file_path = results_dir / f"{bench}_results.txt"
        if file_path.exists():
            summary = extract_benchmark_summary(file_path)
            if summary:
                benchmark_data.append(summary)
    
    if benchmark_data:
        df_bench = pd.DataFrame(benchmark_data)
        
        plt.figure(figsize=(15, 5))
        
        # 서브플롯 1: Ops/sec 비교
        plt.subplot(1, 3, 1)
        bars = plt.bar(df_bench['benchmark'], df_bench['ops_per_sec'], 
                      color=['skyblue', 'lightgreen', 'lightcoral', 'gold'])
        plt.ylabel('Operations/sec')
        plt.title('Benchmark Throughput Comparison')
        plt.xticks(rotation=45)
        for bar, ops in zip(bars, df_bench['ops_per_sec']):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(df_bench['ops_per_sec'])*0.01,
                    f'{ops:,.0f}', ha='center', va='bottom', fontsize=8)
        plt.grid(True, alpha=0.3)
        
        # 서브플롯 2: Latency 비교
        plt.subplot(1, 3, 2)
        bars = plt.bar(df_bench['benchmark'], df_bench['micros_per_op'], 
                      color=['skyblue', 'lightgreen', 'lightcoral', 'gold'])
        plt.ylabel('Microseconds/Operation')
        plt.title('Benchmark Latency Comparison')
        plt.xticks(rotation=45)
        for bar, lat in zip(bars, df_bench['micros_per_op']):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(df_bench['micros_per_op'])*0.01,
                    f'{lat:.1f}', ha='center', va='bottom', fontsize=8)
        plt.grid(True, alpha=0.3)
        
        # 서브플롯 3: 총 작업량 비교
        plt.subplot(1, 3, 3)
        bars = plt.bar(df_bench['benchmark'], df_bench['operations']/1e6, 
                      color=['skyblue', 'lightgreen', 'lightcoral', 'gold'])
        plt.ylabel('Operations (Millions)')
        plt.title('Total Operations Comparison')
        plt.xticks(rotation=45)
        for bar, ops in zip(bars, df_bench['operations']/1e6):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(df_bench['operations']/1e6)*0.01,
                    f'{ops:.1f}M', ha='center', va='bottom', fontsize=8)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / "benchmark_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ 벤치마크 비교 차트 저장: {output_dir / 'benchmark_comparison.png'}")
    
    # 3. RocksDB LOG 분석
    print("3. RocksDB LOG 이벤트 분석...")
    try:
        flush_events, compaction_events = parse_rocksdb_log(results_dir / "rocksdb.log")
        
        plt.figure(figsize=(12, 8))
        
        # 서브플롯 1: 이벤트 타입별 개수
        plt.subplot(2, 2, 1)
        event_counts = {'Flush Events': len(flush_events), 'Compaction Events': len(compaction_events)}
        bars = plt.bar(event_counts.keys(), event_counts.values(), 
                      color=['lightblue', 'lightgreen'])
        plt.ylabel('Event Count')
        plt.title('RocksDB Event Distribution')
        for bar, count in zip(bars, event_counts.values()):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(event_counts.values())*0.01,
                    f'{count}', ha='center', va='bottom', fontsize=12)
        plt.grid(True, alpha=0.3)
        
        # 서브플롯 2: Flush 이벤트 시간 분포 (간단한 분석)
        plt.subplot(2, 2, 2)
        if flush_events:
            # 간단한 시간 추출 (실제로는 더 정교한 파싱 필요)
            flush_times = [i for i in range(len(flush_events))]
            plt.hist(flush_times, bins=min(20, len(flush_times)), alpha=0.7, color='lightblue', edgecolor='black')
            plt.xlabel('Event Index')
            plt.ylabel('Frequency')
            plt.title('Flush Events Distribution')
        else:
            plt.text(0.5, 0.5, 'No Flush Events Found', ha='center', va='center', transform=plt.gca().transAxes)
        plt.grid(True, alpha=0.3)
        
        # 서브플롯 3: Compaction 이벤트 시간 분포
        plt.subplot(2, 2, 3)
        if compaction_events:
            compaction_times = [i for i in range(len(compaction_events))]
            plt.hist(compaction_times, bins=min(20, len(compaction_times)), alpha=0.7, color='lightgreen', edgecolor='black')
            plt.xlabel('Event Index')
            plt.ylabel('Frequency')
            plt.title('Compaction Events Distribution')
        else:
            plt.text(0.5, 0.5, 'No Compaction Events Found', ha='center', va='center', transform=plt.gca().transAxes)
        plt.grid(True, alpha=0.3)
        
        # 서브플롯 4: 이벤트 비율
        plt.subplot(2, 2, 4)
        total_events = len(flush_events) + len(compaction_events)
        if total_events > 0:
            sizes = [len(flush_events), len(compaction_events)]
            labels = ['Flush', 'Compaction']
            colors = ['lightblue', 'lightgreen']
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.title('Event Type Ratio')
        else:
            plt.text(0.5, 0.5, 'No Events Found', ha='center', va='center', transform=plt.gca().transAxes)
        
        plt.tight_layout()
        plt.savefig(output_dir / "rocksdb_events.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ RocksDB 이벤트 분석 차트 저장: {output_dir / 'rocksdb_events.png'}")
    except Exception as e:
        print(f"  ❌ RocksDB LOG 분석 오류: {e}")
    
    # 4. 실험 요약 대시보드
    print("4. 실험 요약 대시보드 생성...")
    try:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 실험 정보
        ax1.text(0.1, 0.8, "Phase-B Final Experiment Summary", fontsize=16, fontweight='bold', transform=ax1.transAxes)
        ax1.text(0.1, 0.7, f"Completion Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", transform=ax1.transAxes)
        ax1.text(0.1, 0.6, "Key Count: 1,000,000,000 (1 billion)", transform=ax1.transAxes)
        ax1.text(0.1, 0.5, "Expected Data Size: 1000 GB", transform=ax1.transAxes)
        ax1.text(0.1, 0.4, "Completed Workloads: 4", transform=ax1.transAxes)
        ax1.text(0.1, 0.3, "Total Duration: ~2 days 15 hours", transform=ax1.transAxes)
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
        ax1.axis('off')
        ax1.set_title('Experiment Overview', fontsize=14, fontweight='bold')
        
        # 주요 개선사항
        improvements = [
            "✅ 데이터 크기 10배 증가 (10억 키)",
            "✅ 자동 디스크 정리 및 초기화",
            "✅ 각 벤치마크 사이 Compaction 대기 시간 추가",
            "✅ 백그라운드 작업 수 최적화 (8→4)",
            "✅ Compaction 상태 모니터링"
        ]
        ax2.text(0.1, 0.8, "Key Improvements:", fontsize=14, fontweight='bold', transform=ax2.transAxes)
        for i, improvement in enumerate(improvements):
            ax2.text(0.1, 0.7 - i*0.1, improvement, fontsize=10, transform=ax2.transAxes)
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)
        ax2.axis('off')
        ax2.set_title('Improvements', fontsize=14, fontweight='bold')
        
        # 성능 요약 (간단한 막대 차트)
        if benchmark_data:
            df_bench = pd.DataFrame(benchmark_data)
            ax3.bar(df_bench['benchmark'], df_bench['ops_per_sec']/1000, 
                   color=['skyblue', 'lightgreen', 'lightcoral', 'gold'])
            ax3.set_ylabel('Throughput (K ops/sec)')
            ax3.set_title('Benchmark Performance Summary')
            ax3.tick_params(axis='x', rotation=45)
            ax3.grid(True, alpha=0.3)
        
        # 파일 크기 분포
        result_files = list(results_dir.glob("*.txt"))
        file_sizes = [f.stat().st_size / (1024*1024) for f in result_files]  # MB
        file_names = [f.stem for f in result_files]
        
        ax4.bar(range(len(file_names)), file_sizes, color='lightcoral')
        ax4.set_ylabel('File Size (MB)')
        ax4.set_title('Result Files Size Distribution')
        ax4.set_xticks(range(len(file_names)))
        ax4.set_xticklabels(file_names, rotation=45, ha='right')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / "experiment_dashboard.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✅ 실험 대시보드 저장: {output_dir / 'experiment_dashboard.png'}")
    except Exception as e:
        print(f"  ❌ 대시보드 생성 오류: {e}")
    
    # 5. 요약 JSON 생성
    print("5. 시각화 요약 JSON 생성...")
    summary = {
        'visualization_info': {
            'created_at': datetime.now().isoformat(),
            'total_charts': 4,
            'charts_created': [
                'fillrandom_performance.png',
                'benchmark_comparison.png', 
                'rocksdb_events.png',
                'experiment_dashboard.png'
            ]
        },
        'data_summary': {
            'fillrandom_data_points': len(df) if 'df' in locals() and not df.empty else 0,
            'benchmark_count': len(benchmark_data),
            'rocksdb_events': {
                'flush_events': len(flush_events) if 'flush_events' in locals() else 0,
                'compaction_events': len(compaction_events) if 'compaction_events' in locals() else 0
            }
        }
    }
    
    with open(output_dir / "visualization_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"  ✅ 시각화 요약 저장: {output_dir / 'visualization_summary.json'}")
    
    print(f"\n=== 시각화 완료 ===")
    print(f"출력 디렉토리: {output_dir}")
    print(f"생성된 차트:")
    for chart_file in output_dir.glob("*.png"):
        print(f"  📊 {chart_file.name}")

if __name__ == "__main__":
    create_performance_visualizations()
