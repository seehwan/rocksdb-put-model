#!/usr/bin/env python3
"""
Phase-C: Phase-B 통계 분석 for v4 Model
Phase-B 벤치마크 결과에서 RocksDB 통계를 추출하여 WAF를 계산합니다.
"""

import re
import json
import csv
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

def parse_rocksdb_stats(file_path):
    """RocksDB 통계 파일을 분석하여 WAF를 계산합니다."""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 주요 통계 추출
    stats = {}
    
    # Flush 통계
    flush_bytes_match = re.search(r'rocksdb\.flush\.write\.bytes COUNT : (\d+)', content)
    if flush_bytes_match:
        stats['flush_write_bytes'] = int(flush_bytes_match.group(1))
    
    # Compaction 통계
    compaction_time_match = re.search(r'rocksdb\.compaction\.total\.time\.cpu_micros COUNT : (\d+)', content)
    if compaction_time_match:
        stats['compaction_time_cpu_micros'] = int(compaction_time_match.group(1))
    
    # Write 통계
    db_write_match = re.search(r'rocksdb\.db\.write\.micros.*?COUNT : (\d+) SUM : (\d+)', content)
    if db_write_match:
        stats['db_write_count'] = int(db_write_match.group(1))
        stats['db_write_sum_micros'] = int(db_write_match.group(2))
    
    # Block cache 통계
    cache_miss_match = re.search(r'rocksdb\.block\.cache\.miss COUNT : (\d+)', content)
    if cache_miss_match:
        stats['block_cache_miss'] = int(cache_miss_match.group(1))
    
    cache_hit_match = re.search(r'rocksdb\.block\.cache\.hit COUNT : (\d+)', content)
    if cache_hit_match:
        stats['block_cache_hit'] = int(cache_hit_match.group(1))
    
    # Compaction key drop 통계
    key_drop_new_match = re.search(r'rocksdb\.compaction\.key\.drop\.new COUNT : (\d+)', content)
    if key_drop_new_match:
        stats['compaction_key_drop_new'] = int(key_drop_new_match.group(1))
    
    # Memtable 통계
    memtable_bytes_match = re.search(r'rocksdb\.memtable\.bytes COUNT : (\d+)', content)
    if memtable_bytes_match:
        stats['memtable_bytes'] = int(memtable_bytes_match.group(1))
    
    # SST 파일 통계
    sst_read_match = re.search(r'rocksdb\.sst\.read\.micros.*?COUNT : (\d+)', content)
    if sst_read_match:
        stats['sst_read_count'] = int(sst_read_match.group(1))
    
    # WAL 통계
    wal_write_match = re.search(r'rocksdb\.wal\.write\.bytes COUNT : (\d+)', content)
    if wal_write_match:
        stats['wal_write_bytes'] = int(wal_write_match.group(1))
    
    return stats

def calculate_waf_from_stats(stats, user_data_bytes):
    """통계에서 WAF를 계산합니다."""
    
    # Flush write bytes가 실제 디스크에 쓰여진 데이터
    flush_bytes = stats.get('flush_write_bytes', 0)
    
    # WAF = 실제 쓰기 / 사용자 데이터
    if user_data_bytes > 0:
        waf = flush_bytes / user_data_bytes
    else:
        waf = 0.0
    
    return waf, flush_bytes

def analyze_all_benchmarks():
    """모든 벤치마크 결과를 분석합니다."""
    
    benchmark_files = {
        'fillrandom': '../phase-b/phase_b_final_results/fillrandom_results.txt',
        'readrandomwriterandom': '../phase-b/phase_b_final_results/readrandomwriterandom_results.txt',
        'overwrite': '../phase-b/phase_b_final_results/overwrite_results.txt',
        'mixgraph': '../phase-b/phase_b_final_results/mixgraph_results.txt'
    }
    
    results = {}
    
    for benchmark, file_path in benchmark_files.items():
        if Path(file_path).exists():
            print(f"분석 중: {benchmark}")
            stats = parse_rocksdb_stats(file_path)
            results[benchmark] = stats
        else:
            print(f"파일 없음: {file_path}")
    
    return results

def create_comprehensive_analysis():
    """종합적인 분석을 수행합니다."""
    
    print("=== Phase-C: Phase-B 통계 분석 for v4 Model ===")
    
    # 출력 디렉토리 생성
    output_dir = Path("phase_c_results")
    output_dir.mkdir(exist_ok=True)
    
    # 모든 벤치마크 분석
    benchmark_results = analyze_all_benchmarks()
    
    # FillRandom 결과를 기준으로 WAF 계산 (10억 키, 1KB 값)
    user_data_bytes = 1000000000 * 1024  # 10억 키 * 1KB
    
    analysis_summary = {
        'experiment_info': {
            'user_data_bytes': user_data_bytes,
            'user_data_gb': user_data_bytes / (1024**3),
            'key_count': 1000000000,
            'value_size': 1024
        },
        'benchmark_results': {}
    }
    
    print(f"\n=== 분석 결과 ===")
    print(f"사용자 데이터: {user_data_bytes / (1024**3):.2f} GB")
    
    for benchmark, stats in benchmark_results.items():
        waf, flush_bytes = calculate_waf_from_stats(stats, user_data_bytes)
        
        analysis_summary['benchmark_results'][benchmark] = {
            'waf': waf,
            'flush_bytes': flush_bytes,
            'flush_gb': flush_bytes / (1024**3),
            'stats': stats
        }
        
        print(f"\n{benchmark.upper()}:")
        print(f"  WAF: {waf:.2f}")
        print(f"  Flush bytes: {flush_bytes / (1024**3):.2f} GB")
        if 'db_write_count' in stats:
            print(f"  DB write count: {stats['db_write_count']:,}")
        if 'compaction_time_cpu_micros' in stats:
            print(f"  Compaction time: {stats['compaction_time_cpu_micros'] / 1000000:.2f} seconds")
    
    # JSON 저장
    json_file = output_dir / 'phase_c_comprehensive_analysis.json'
    with open(json_file, 'w') as f:
        json.dump(analysis_summary, f, indent=2)
    
    print(f"\n✅ JSON 파일 저장: {json_file}")
    
    # CSV 저장
    csv_file = output_dir / 'waf_analysis.csv'
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Benchmark', 'WAF', 'Flush_GB', 'User_Data_GB', 'DB_Write_Count', 'Compaction_Time_Sec'])
        
        for benchmark, data in analysis_summary['benchmark_results'].items():
            stats = data['stats']
            writer.writerow([
                benchmark,
                f"{data['waf']:.2f}",
                f"{data['flush_gb']:.2f}",
                f"{analysis_summary['experiment_info']['user_data_gb']:.2f}",
                stats.get('db_write_count', 0),
                stats.get('compaction_time_cpu_micros', 0) / 1000000
            ])
    
    print(f"✅ CSV 파일 저장: {csv_file}")
    
    # 시각화 생성
    create_waf_visualization(analysis_summary, output_dir)
    
    print(f"\n=== Phase-C 완료 ===")

def create_waf_visualization(analysis_data, output_dir):
    """WAF 분석 시각화를 생성합니다."""
    
    benchmarks = list(analysis_data['benchmark_results'].keys())
    wafs = [analysis_data['benchmark_results'][b]['waf'] for b in benchmarks]
    flush_gbs = [analysis_data['benchmark_results'][b]['flush_gb'] for b in benchmarks]
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # WAF 비교
    bars1 = ax1.bar(benchmarks, wafs, color=['skyblue', 'lightgreen', 'lightcoral', 'gold'])
    ax1.set_ylabel('Write Amplification Factor')
    ax1.set_title('WAF by Benchmark')
    ax1.tick_params(axis='x', rotation=45)
    for bar, waf in zip(bars1, wafs):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(wafs)*0.01,
                f'{waf:.2f}', ha='center', va='bottom')
    ax1.grid(True, alpha=0.3)
    
    # Flush bytes 비교
    bars2 = ax2.bar(benchmarks, flush_gbs, color=['skyblue', 'lightgreen', 'lightcoral', 'gold'])
    ax2.set_ylabel('Flush Bytes (GB)')
    ax2.set_title('Flush Bytes by Benchmark')
    ax2.tick_params(axis='x', rotation=45)
    for bar, gb in zip(bars2, flush_gbs):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(flush_gbs)*0.01,
                f'{gb:.1f}', ha='center', va='bottom')
    ax2.grid(True, alpha=0.3)
    
    # WAF vs Flush bytes 산점도
    ax3.scatter(flush_gbs, wafs, s=100, alpha=0.7, c=['skyblue', 'lightgreen', 'lightcoral', 'gold'])
    for i, benchmark in enumerate(benchmarks):
        ax3.annotate(benchmark, (flush_gbs[i], wafs[i]), xytext=(5, 5), textcoords='offset points')
    ax3.set_xlabel('Flush Bytes (GB)')
    ax3.set_ylabel('WAF')
    ax3.set_title('WAF vs Flush Bytes')
    ax3.grid(True, alpha=0.3)
    
    # 통계 요약
    ax4.text(0.1, 0.8, f"User Data: {analysis_data['experiment_info']['user_data_gb']:.1f} GB", 
             transform=ax4.transAxes, fontsize=12, fontweight='bold')
    ax4.text(0.1, 0.7, f"Key Count: {analysis_data['experiment_info']['key_count']:,}", 
             transform=ax4.transAxes, fontsize=12)
    ax4.text(0.1, 0.6, f"Value Size: {analysis_data['experiment_info']['value_size']} bytes", 
             transform=ax4.transAxes, fontsize=12)
    
    ax4.text(0.1, 0.4, "Benchmark Results:", transform=ax4.transAxes, fontsize=12, fontweight='bold')
    y_pos = 0.3
    for benchmark, data in analysis_data['benchmark_results'].items():
        ax4.text(0.1, y_pos, f"{benchmark}: WAF={data['waf']:.2f}", 
                 transform=ax4.transAxes, fontsize=10)
        y_pos -= 0.05
    
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis('off')
    ax4.set_title('Analysis Summary')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'comprehensive_waf_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ 시각화 생성: {output_dir}/comprehensive_waf_analysis.png")

if __name__ == "__main__":
    create_comprehensive_analysis()
