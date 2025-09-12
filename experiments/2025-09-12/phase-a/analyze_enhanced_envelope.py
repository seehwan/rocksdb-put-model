#!/usr/bin/env python3
"""
Enhanced Device Envelope 분석 스크립트
정교한 Device Envelope 측정 결과를 분석하고 시각화합니다.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import pandas as pd

def load_enhanced_envelope_data():
    """Enhanced envelope 측정 데이터 로드"""
    data_file = Path("data/enhanced_envelope_report.json")
    
    if not data_file.exists():
        print("❌ Enhanced envelope 데이터 파일을 찾을 수 없습니다!")
        return None
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    return data

def analyze_block_size_sweep(data):
    """블록 크기 스윕 분석"""
    print("\n=== 📊 블록 크기 스윕 분석 ===")
    
    bs_data = data['measurements']['block_size_sweep']
    
    # 블록 크기별 성능 추출
    block_sizes = ['4k', '8k', '16k', '32k', '64k', '128k', '256k', '512k', '1m']
    
    results = {
        'block_size': [],
        'write_bw': [],
        'read_bw': [],
        'randwrite_bw': [],
        'randread_bw': []
    }
    
    for bs in block_sizes:
        if bs in bs_data['write']:
            results['block_size'].append(bs)
            results['write_bw'].append(bs_data['write'][bs]['bandwidth_mib_s'])
            results['read_bw'].append(bs_data['read'][bs]['bandwidth_mib_s'])
            results['randwrite_bw'].append(bs_data['randwrite'][bs]['bandwidth_mib_s'])
            results['randread_bw'].append(bs_data['randread'][bs]['bandwidth_mib_s'])
    
    # 최대 성능 출력
    print("📈 최대 성능:")
    print(f"  Sequential Write: {max(results['write_bw']):.1f} MiB/s")
    print(f"  Sequential Read:  {max(results['read_bw']):.1f} MiB/s")
    print(f"  Random Write:     {max(results['randwrite_bw']):.1f} MiB/s")
    print(f"  Random Read:      {max(results['randread_bw']):.1f} MiB/s")
    
    return results

def analyze_queue_depth_sweep(data):
    """큐 깊이 스윕 분석"""
    print("\n=== 📊 큐 깊이 스윕 분석 ===")
    
    qd_data = data['measurements']['queue_depth_sweep']
    
    queue_depths = ['1', '2', '4', '8', '16', '32', '64', '128']
    
    results = {
        'queue_depth': [],
        'write_bw': [],
        'randwrite_bw': []
    }
    
    for qd in queue_depths:
        if qd in qd_data['write']:
            results['queue_depth'].append(int(qd))
            results['write_bw'].append(qd_data['write'][qd]['bandwidth_mib_s'])
            results['randwrite_bw'].append(qd_data['randwrite'][qd]['bandwidth_mib_s'])
    
    print("📈 최대 성능:")
    print(f"  Sequential Write: {max(results['write_bw']):.1f} MiB/s")
    print(f"  Random Write:     {max(results['randwrite_bw']):.1f} MiB/s")
    
    return results

def analyze_mixed_workload_sweep(data):
    """혼합 워크로드 스윕 분석"""
    print("\n=== 📊 혼합 워크로드 스윕 분석 ===")
    
    mixed_data = data['measurements']['mixed_workload_sweep']
    
    block_sizes = ['4k', '16k', '64k', '128k']
    read_ratios = [0, 10, 25, 50, 75, 90, 100]
    
    print("📈 블록 크기별 최대 성능:")
    
    for bs in block_sizes:
        if bs in mixed_data:
            max_bw = 0
            best_ratio = 0
            
            for ratio in read_ratios:
                key = f'r{ratio}'
                if key in mixed_data[bs]:
                    bw = mixed_data[bs][key]['bandwidth_mib_s']
                    if bw > max_bw:
                        max_bw = bw
                        best_ratio = ratio
            
            print(f"  {bs}: {max_bw:.1f} MiB/s (R{best_ratio}%/W{100-best_ratio}%)")

def analyze_concurrent_jobs_sweep(data):
    """동시 작업 수 스윕 분석"""
    print("\n=== 📊 동시 작업 수 스윕 분석 ===")
    
    concurrent_data = data['measurements']['concurrent_jobs_sweep']
    
    job_counts = ['1', '2', '4', '8', '16', '32']
    
    randwrite_max = 0
    randread_max = 0
    
    for jobs in job_counts:
        if jobs in concurrent_data['randwrite']:
            bw = concurrent_data['randwrite'][jobs]['bandwidth_mib_s']
            if bw > randwrite_max:
                randwrite_max = bw
        
        if jobs in concurrent_data['randread']:
            bw = concurrent_data['randread'][jobs]['bandwidth_mib_s']
            if bw > randread_max:
                randread_max = bw
    
    print("📈 최대 성능:")
    print(f"  Random Write: {randwrite_max:.1f} MiB/s")
    print(f"  Random Read:  {randread_max:.1f} MiB/s")

def analyze_rocksdb_patterns(data):
    """RocksDB 특화 패턴 분석"""
    print("\n=== 📊 RocksDB 특화 패턴 분석 ===")
    
    rocksdb_data = data['measurements']['rocksdb_patterns']
    
    patterns = {
        'MemTable Flush': rocksdb_data['memtable_flush']['bandwidth_mib_s'],
        'L0 Compaction Read': rocksdb_data['l0_compaction_read']['bandwidth_mib_s'],
        'L0 Compaction Write': rocksdb_data['l0_compaction_write']['bandwidth_mib_s'],
        'FillRandom': rocksdb_data['fillrandom']['bandwidth_mib_s'],
        'Point Lookup': rocksdb_data['point_lookup']['bandwidth_mib_s'],
        'Range Scan': rocksdb_data['range_scan']['bandwidth_mib_s'],
        'Mixed Workload (R70/W30)': rocksdb_data['mixed_workload']['bandwidth_mib_s']
    }
    
    print("📈 RocksDB 패턴별 성능:")
    for pattern, bw in patterns.items():
        print(f"  {pattern}: {bw:.1f} MiB/s")

def create_visualizations(data):
    """시각화 생성"""
    print("\n=== 📊 시각화 생성 중... ===")
    
    try:
        # 블록 크기 스윕 시각화
        bs_results = analyze_block_size_sweep(data)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Sequential Write/Read
        ax1.plot(range(len(bs_results['block_size'])), bs_results['write_bw'], 'b-o', label='Write')
        ax1.plot(range(len(bs_results['block_size'])), bs_results['read_bw'], 'r-s', label='Read')
        ax1.set_title('Sequential I/O Performance by Block Size')
        ax1.set_xlabel('Block Size')
        ax1.set_ylabel('Bandwidth (MiB/s)')
        ax1.set_xticks(range(len(bs_results['block_size'])))
        ax1.set_xticklabels(bs_results['block_size'], rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Random Write/Read
        ax2.plot(range(len(bs_results['block_size'])), bs_results['randwrite_bw'], 'g-o', label='Random Write')
        ax2.plot(range(len(bs_results['block_size'])), bs_results['randread_bw'], 'm-s', label='Random Read')
        ax2.set_title('Random I/O Performance by Block Size')
        ax2.set_xlabel('Block Size')
        ax2.set_ylabel('Bandwidth (MiB/s)')
        ax2.set_xticks(range(len(bs_results['block_size'])))
        ax2.set_xticklabels(bs_results['block_size'], rotation=45)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 큐 깊이 스윕 시각화
        qd_results = analyze_queue_depth_sweep(data)
        
        ax3.plot(qd_results['queue_depth'], qd_results['write_bw'], 'b-o', label='Sequential Write')
        ax3.plot(qd_results['queue_depth'], qd_results['randwrite_bw'], 'g-s', label='Random Write')
        ax3.set_title('Performance by Queue Depth (4k blocks)')
        ax3.set_xlabel('Queue Depth')
        ax3.set_ylabel('Bandwidth (MiB/s)')
        ax3.set_xscale('log', base=2)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # RocksDB 패턴 성능
        rocksdb_data = data['measurements']['rocksdb_patterns']
        patterns = list(rocksdb_data.keys())
        bw_values = [rocksdb_data[pattern]['bandwidth_mib_s'] for pattern in patterns]
        
        bars = ax4.bar(range(len(patterns)), bw_values, color=['skyblue', 'lightgreen', 'lightcoral', 'gold', 'plum', 'lightblue', 'orange'])
        ax4.set_title('RocksDB Pattern Performance')
        ax4.set_xlabel('Pattern')
        ax4.set_ylabel('Bandwidth (MiB/s)')
        ax4.set_xticks(range(len(patterns)))
        ax4.set_xticklabels([p.replace(' ', '\n') for p in patterns], rotation=45, ha='right')
        
        # 값 표시
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 50,
                    f'{height:.0f}', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        plt.savefig('data/enhanced_envelope_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ 시각화 저장 완료: data/enhanced_envelope_analysis.png")
        
    except Exception as e:
        print(f"❌ 시각화 생성 실패: {e}")

def generate_summary_report(data):
    """종합 요약 보고서 생성"""
    print("\n=== 📋 종합 요약 보고서 생성 ===")
    
    summary = {
        "device": data['device'],
        "test_date": data['test_date'],
        "test_type": "Enhanced Device Envelope",
        "summary": {
            "max_sequential_write": 0,
            "max_sequential_read": 0,
            "max_random_write": 0,
            "max_random_read": 0,
            "optimal_block_size_write": "",
            "optimal_block_size_read": "",
            "optimal_queue_depth": 0,
            "max_concurrent_throughput": 0,
            "rocksdb_fillrandom_performance": 0
        }
    }
    
    # 블록 크기 스윕에서 최대 성능 찾기
    bs_data = data['measurements']['block_size_sweep']
    
    max_write_bw = 0
    max_read_bw = 0
    optimal_bs_write = ""
    optimal_bs_read = ""
    
    for bs, metrics in bs_data['write'].items():
        if metrics['bandwidth_mib_s'] > max_write_bw:
            max_write_bw = metrics['bandwidth_mib_s']
            optimal_bs_write = bs
    
    for bs, metrics in bs_data['read'].items():
        if metrics['bandwidth_mib_s'] > max_read_bw:
            max_read_bw = metrics['bandwidth_mib_s']
            optimal_bs_read = bs
    
    max_randwrite_bw = 0
    max_randread_bw = 0
    
    for bs, metrics in bs_data['randwrite'].items():
        if metrics['bandwidth_mib_s'] > max_randwrite_bw:
            max_randwrite_bw = metrics['bandwidth_mib_s']
    
    for bs, metrics in bs_data['randread'].items():
        if metrics['bandwidth_mib_s'] > max_randread_bw:
            max_randread_bw = metrics['bandwidth_mib_s']
    
    # 큐 깊이에서 최대 성능 찾기
    qd_data = data['measurements']['queue_depth_sweep']
    optimal_qd = 1
    
    for qd, metrics in qd_data['write'].items():
        if int(qd) > optimal_qd:
            optimal_qd = int(qd)
    
    # 동시 작업에서 최대 처리량 찾기
    concurrent_data = data['measurements']['concurrent_jobs_sweep']
    max_concurrent_bw = 0
    
    for jobs, metrics in concurrent_data['randwrite'].items():
        if metrics['bandwidth_mib_s'] > max_concurrent_bw:
            max_concurrent_bw = metrics['bandwidth_mib_s']
    
    # RocksDB FillRandom 성능
    rocksdb_fillrandom = data['measurements']['rocksdb_patterns']['fillrandom']['bandwidth_mib_s']
    
    # 요약 업데이트
    summary['summary'].update({
        "max_sequential_write": max_write_bw,
        "max_sequential_read": max_read_bw,
        "max_random_write": max_randwrite_bw,
        "max_random_read": max_randread_bw,
        "optimal_block_size_write": optimal_bs_write,
        "optimal_block_size_read": optimal_bs_read,
        "optimal_queue_depth": optimal_qd,
        "max_concurrent_throughput": max_concurrent_bw,
        "rocksdb_fillrandom_performance": rocksdb_fillrandom
    })
    
    # 요약 저장
    with open('data/enhanced_envelope_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✅ 종합 요약 보고서 저장: data/enhanced_envelope_summary.json")
    
    # 콘솔에 요약 출력
    print("\n🎯 **Enhanced Device Envelope 요약**")
    print(f"📅 측정 일시: {data['test_date']}")
    print(f"💾 대상 장치: {data['device']}")
    print(f"\n📊 최대 성능:")
    print(f"  Sequential Write: {max_write_bw:.1f} MiB/s ({optimal_bs_write})")
    print(f"  Sequential Read:  {max_read_bw:.1f} MiB/s ({optimal_bs_read})")
    print(f"  Random Write:     {max_randwrite_bw:.1f} MiB/s")
    print(f"  Random Read:      {max_randread_bw:.1f} MiB/s")
    print(f"\n⚙️ 최적 설정:")
    print(f"  Write 최적 블록 크기: {optimal_bs_write}")
    print(f"  Read 최적 블록 크기:  {optimal_bs_read}")
    print(f"  최적 큐 깊이: {optimal_qd}")
    print(f"  최대 동시 처리량: {max_concurrent_bw:.1f} MiB/s")
    print(f"\n🗄️ RocksDB 특화:")
    print(f"  FillRandom 성능: {rocksdb_fillrandom:.1f} MiB/s")

def main():
    """메인 함수"""
    print("🚀 Enhanced Device Envelope 분석 시작...")
    
    # 데이터 로드
    data = load_enhanced_envelope_data()
    if not data:
        return
    
    # 각 분석 실행
    analyze_block_size_sweep(data)
    analyze_queue_depth_sweep(data)
    analyze_mixed_workload_sweep(data)
    analyze_concurrent_jobs_sweep(data)
    analyze_rocksdb_patterns(data)
    
    # 시각화 생성
    create_visualizations(data)
    
    # 종합 요약 보고서 생성
    generate_summary_report(data)
    
    print("\n✅ Enhanced Device Envelope 분석 완료!")

if __name__ == "__main__":
    main()
