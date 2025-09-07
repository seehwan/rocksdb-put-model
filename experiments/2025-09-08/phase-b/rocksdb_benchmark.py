#!/usr/bin/env python3
"""
Phase-B: RocksDB Benchmark Execution (2025-09-08)

실제 RocksDB 시스템에서 측정된 성능을 바탕으로 v4 모델의 정확성을 검증합니다.
"""

import subprocess
import json
import time
import re
import os
from pathlib import Path

class RocksDBBenchmark:
    """RocksDB 벤치마크 클래스"""
    
    def __init__(self, db_path: str = "/rocksdb/data", wal_dir: str = "/rocksdb/wal"):
        """초기화"""
        self.db_path = db_path
        self.wal_dir = wal_dir
        self.results = {}
        
    def setup_directories(self):
        """디렉토리 설정"""
        print("📁 디렉토리 설정 중...")
        
        # 디렉토리 생성
        Path(self.db_path).mkdir(parents=True, exist_ok=True)
        Path(self.wal_dir).mkdir(parents=True, exist_ok=True)
        
        print(f"  DB 경로: {self.db_path}")
        print(f"  WAL 경로: {self.wal_dir}")
        
    def run_benchmark(self, num_operations: int = 300000000, value_size: int = 1024, threads: int = 16):
        """RocksDB 벤치마크 실행"""
        print("🚀 RocksDB 벤치마크 실행 중...")
        
        # db_bench 명령어 구성
        cmd = [
            "./db_bench",
            "--options_file=options-leveled.ini",
            "--benchmarks=fillrandom",
            f"--num={num_operations}",
            f"--value_size={value_size}",
            f"--threads={threads}",
            f"--db={self.db_path}",
            f"--wal_dir={self.wal_dir}",
            "--statistics=1",
            "--stats_dump_period_sec=60"
        ]
        
        print(f"명령어: {' '.join(cmd)}")
        print()
        
        try:
            # db_bench 실행
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=36000)  # 10시간 타임아웃
            end_time = time.time()
            
            if result.returncode != 0:
                print(f"❌ 벤치마크 실패: {result.stderr}")
                return None
                
            # 결과 파싱
            self.parse_benchmark_output(result.stdout, end_time - start_time)
            
            return self.results
            
        except subprocess.TimeoutExpired:
            print("⏰ 벤치마크 시간 초과")
            return None
        except Exception as e:
            print(f"❌ 벤치마크 오류: {e}")
            return None
    
    def parse_benchmark_output(self, output: str, duration: float):
        """벤치마크 출력 파싱"""
        print("📊 결과 파싱 중...")
        
        # 기본 성능 지표 추출
        perf_match = re.search(r'fillrandom\s+:\s+([\d.]+)\s+micros/op\s+([\d.]+)\s+ops/sec\s+([\d.]+)\s+seconds\s+([\d.]+)\s+operations;\s+([\d.]+)\s+MB/s', output)
        
        if perf_match:
            self.results['performance'] = {
                'microseconds_per_operation': float(perf_match.group(1)),
                'operations_per_second': float(perf_match.group(2)),
                'duration_seconds': float(perf_match.group(3)),
                'total_operations': float(perf_match.group(4)),
                'put_rate_mb_s': float(perf_match.group(5)),
                'put_rate_mib_s': float(perf_match.group(5)) * 0.953674  # MB/s to MiB/s
            }
        
        # 통계 정보 파싱
        self.parse_statistics(output)
        
    def parse_statistics(self, output: str):
        """STATISTICS 섹션 파싱"""
        print("📈 통계 정보 파싱 중...")
        
        stats = {}
        
        # 주요 통계 추출
        patterns = {
            'bytes_written': r'rocksdb\.bytes\.written COUNT : ([\d.]+)',
            'bytes_read': r'rocksdb\.bytes\.read COUNT : ([\d.]+)',
            'stall_micros': r'rocksdb\.stall\.micros COUNT : ([\d.]+)',
            'compaction_read_bytes': r'rocksdb\.compact\.read\.bytes COUNT : ([\d.]+)',
            'compaction_write_bytes': r'rocksdb\.compact\.write\.bytes COUNT : ([\d.]+)',
            'flush_write_bytes': r'rocksdb\.flush\.write\.bytes COUNT : ([\d.]+)',
            'bytes_compressed_from': r'rocksdb\.bytes\.compressed\.from COUNT : ([\d.]+)',
            'bytes_compressed_to': r'rocksdb\.bytes\.compressed\.to COUNT : ([\d.]+)',
            'number_keys_written': r'rocksdb\.number\.keys\.written COUNT : ([\d.]+)',
            'compaction_count': r'rocksdb\.compaction\.times\.micros COUNT : ([\d.]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output)
            if match:
                stats[key] = float(match.group(1))
        
        # Write Amplification 계산
        if 'bytes_written' in stats and 'number_keys_written' in stats:
            user_bytes = stats['number_keys_written'] * 1024  # 1KB per key
            stats['write_amplification'] = stats['bytes_written'] / user_bytes
        
        # 압축률 계산
        if 'bytes_compressed_from' in stats and 'bytes_compressed_to' in stats:
            stats['compression_ratio'] = stats['bytes_compressed_to'] / stats['bytes_compressed_from']
        
        # Stall 비율 계산
        if 'stall_micros' in stats and 'duration_seconds' in self.results.get('performance', {}):
            total_micros = self.results['performance']['duration_seconds'] * 1_000_000
            stats['stall_percentage'] = (stats['stall_micros'] / total_micros) * 100
        
        self.results['statistics'] = stats
        
    def save_results(self):
        """결과 저장"""
        output_file = Path("benchmark_results.json")
        
        # 실험 정보 추가
        experiment_data = {
            "experiment_info": {
                "date": "2025-09-08",
                "phase": "Phase-B",
                "test_type": "RocksDB fillrandom benchmark",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "benchmark_configuration": {
                "num_operations": 300000000,
                "value_size_bytes": 1024,
                "threads": 16,
                "db_path": self.db_path,
                "wal_dir": self.wal_dir
            },
            "performance_results": self.results.get('performance', {}),
            "statistics": self.results.get('statistics', {})
        }
        
        with open(output_file, 'w') as f:
            json.dump(experiment_data, f, indent=2)
            
        print(f"\n💾 결과 저장: {output_file}")
        print("✅ Phase-B 완료!")

def main():
    """메인 함수"""
    benchmark = RocksDBBenchmark()
    benchmark.setup_directories()
    benchmark.run_benchmark()
    benchmark.save_results()

if __name__ == "__main__":
    main()
