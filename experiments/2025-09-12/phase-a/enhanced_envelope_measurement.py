#!/usr/bin/env python3
"""
Enhanced Device Envelope Measurement
다양한 조합의 Device Envelope 측정을 위한 스크립트
"""

import subprocess
import json
import time
import os
from datetime import datetime

class EnhancedEnvelopeMeasurement:
    def __init__(self, device="/dev/nvme1n1", output_dir="data"):
        self.device = device
        self.output_dir = output_dir
        self.results = {}
        
    def run_fio_test(self, name, rw, bs, iodepth, runtime=60, rwmixread=None, numjobs=1):
        """fio 테스트 실행"""
        cmd = [
            "sudo", "fio",
            f"--name={name}",
            f"--filename={self.device}",
            f"--rw={rw}",
            f"--bs={bs}",
            f"--iodepth={iodepth}",
            f"--runtime={runtime}",
            f"--numjobs={numjobs}",
            "--time_based=1",
            "--ioengine=libaio",
            "--direct=1",
            "--group_reporting=1",
            "--output-format=json"
        ]
        
        if rwmixread is not None:
            cmd.append(f"--rwmixread={rwmixread}")
            
        print(f"실행 중: {name} ({rw}, {bs}, iodepth={iodepth}, jobs={numjobs})")
        print(f"명령어: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=runtime+30)
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                print(f"오류: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            print(f"시간 초과: {name}")
            return None
        except Exception as e:
            print(f"예외 발생: {e}")
            return None
    
    def analyze_fio_result(self, fio_data):
        """fio 결과 분석"""
        if not fio_data or 'jobs' not in fio_data:
            return None
            
        job = fio_data['jobs'][0]
        
        # 읽기/쓰기 중 더 큰 값을 선택
        read_bw = job['read']['bw'] if 'read' in job else 0
        write_bw = job['write']['bw'] if 'write' in job else 0
        bw_kbps = max(read_bw, write_bw)
        
        read_iops = job['read']['iops'] if 'read' in job else 0
        write_iops = job['write']['iops'] if 'write' in job else 0
        iops = max(read_iops, write_iops)
        
        # 레이턴시
        if read_bw > write_bw:
            lat_mean = job['read']['clat']['mean'] if 'read' in job and 'clat' in job['read'] else 0
            lat_p95 = job['read']['clat']['percentile']['95.000000'] if 'read' in job and 'clat' in job['read'] and 'percentile' in job['read']['clat'] else 0
            lat_p99 = job['read']['clat']['percentile']['99.000000'] if 'read' in job and 'clat' in job['read'] and 'percentile' in job['read']['clat'] else 0
        else:
            lat_mean = job['write']['clat']['mean'] if 'write' in job and 'clat' in job['write'] else 0
            lat_p95 = job['write']['clat']['percentile']['95.000000'] if 'write' in job and 'clat' in job['write'] and 'percentile' in job['write']['clat'] else 0
            lat_p99 = job['write']['clat']['percentile']['99.000000'] if 'write' in job and 'clat' in job['write'] and 'percentile' in job['write']['clat'] else 0
        
        return {
            'bandwidth_mib_s': bw_kbps / 1024,
            'iops': iops,
            'latency_mean_us': lat_mean / 1000,
            'latency_p95_us': lat_p95 / 1000,
            'latency_p99_us': lat_p99 / 1000,
            'read_bandwidth_mib_s': read_bw / 1024,
            'write_bandwidth_mib_s': write_bw / 1024
        }
    
    def measure_block_size_sweep(self):
        """블록 크기 스윕 측정"""
        print("\n=== 블록 크기 스윕 측정 ===")
        
        block_sizes = ["4k", "8k", "16k", "32k", "64k", "128k", "256k", "512k", "1m"]
        test_configs = [
            ("write", "Sequential Write"),
            ("randwrite", "Random Write"),
            ("read", "Sequential Read"),
            ("randread", "Random Read")
        ]
        
        block_size_results = {}
        
        for rw, description in test_configs:
            print(f"\n{description} 블록 크기 스윕:")
            block_size_results[rw] = {}
            
            for bs in block_sizes:
                name = f"bs_sweep_{rw}_{bs}"
                fio_data = self.run_fio_test(name, rw, bs, 32, 30)
                
                if fio_data:
                    result = self.analyze_fio_result(fio_data)
                    if result:
                        block_size_results[rw][bs] = result
                        print(f"  {bs}: {result['bandwidth_mib_s']:.1f} MiB/s")
                        
                        # 결과 저장
                        with open(f"{self.output_dir}/{name}.json", 'w') as f:
                            json.dump(fio_data, f, indent=2)
                
                time.sleep(2)  # 잠시 대기
        
        return block_size_results
    
    def measure_queue_depth_sweep(self):
        """큐 깊이 스윕 측정"""
        print("\n=== 큐 깊이 스윕 측정 ===")
        
        queue_depths = [1, 2, 4, 8, 16, 32, 64, 128]
        test_configs = [
            ("write", "Sequential Write"),
            ("randwrite", "Random Write")
        ]
        
        queue_depth_results = {}
        
        for rw, description in test_configs:
            print(f"\n{description} 큐 깊이 스윕:")
            queue_depth_results[rw] = {}
            
            for iodepth in queue_depths:
                name = f"qd_sweep_{rw}_qd{iodepth}"
                fio_data = self.run_fio_test(name, rw, "4k", iodepth, 30)
                
                if fio_data:
                    result = self.analyze_fio_result(fio_data)
                    if result:
                        queue_depth_results[rw][iodepth] = result
                        print(f"  QD {iodepth}: {result['bandwidth_mib_s']:.1f} MiB/s")
                        
                        # 결과 저장
                        with open(f"{self.output_dir}/{name}.json", 'w') as f:
                            json.dump(fio_data, f, indent=2)
                
                time.sleep(2)
        
        return queue_depth_results
    
    def measure_mixed_workload_sweep(self):
        """혼합 워크로드 스윕 측정"""
        print("\n=== 혼합 워크로드 스윕 측정 ===")
        
        read_ratios = [0, 10, 25, 50, 75, 90, 100]  # 0% = 순수 쓰기, 100% = 순수 읽기
        block_sizes = ["4k", "16k", "64k", "128k"]
        
        mixed_results = {}
        
        for bs in block_sizes:
            print(f"\n블록 크기 {bs} 혼합 워크로드:")
            mixed_results[bs] = {}
            
            for read_ratio in read_ratios:
                name = f"mixed_sweep_{bs}_r{read_ratio}"
                fio_data = self.run_fio_test(name, "rw", bs, 16, 30, rwmixread=read_ratio)
                
                if fio_data:
                    result = self.analyze_fio_result(fio_data)
                    if result:
                        mixed_results[bs][read_ratio] = result
                        print(f"  R/W {read_ratio}%/{100-read_ratio}%: {result['bandwidth_mib_s']:.1f} MiB/s")
                        
                        # 결과 저장
                        with open(f"{self.output_dir}/{name}.json", 'w') as f:
                            json.dump(fio_data, f, indent=2)
                
                time.sleep(2)
        
        return mixed_results
    
    def measure_concurrent_jobs_sweep(self):
        """동시 작업 수 스윕 측정"""
        print("\n=== 동시 작업 수 스윕 측정 ===")
        
        num_jobs = [1, 2, 4, 8, 16, 32]
        test_configs = [
            ("randwrite", "Random Write"),
            ("randread", "Random Read")
        ]
        
        concurrent_results = {}
        
        for rw, description in test_configs:
            print(f"\n{description} 동시 작업 수 스윕:")
            concurrent_results[rw] = {}
            
            for jobs in num_jobs:
                name = f"concurrent_sweep_{rw}_jobs{jobs}"
                fio_data = self.run_fio_test(name, rw, "4k", 16, 30, numjobs=jobs)
                
                if fio_data:
                    result = self.analyze_fio_result(fio_data)
                    if result:
                        concurrent_results[rw][jobs] = result
                        print(f"  {jobs} jobs: {result['bandwidth_mib_s']:.1f} MiB/s")
                        
                        # 결과 저장
                        with open(f"{self.output_dir}/{name}.json", 'w') as f:
                            json.dump(fio_data, f, indent=2)
                
                time.sleep(2)
        
        return concurrent_results
    
    def measure_rocksdb_specific_patterns(self):
        """RocksDB 특화 패턴 측정"""
        print("\n=== RocksDB 특화 패턴 측정 ===")
        
        rocksdb_patterns = [
            # MemTable flush (순차 쓰기)
            ("memtable_flush", "write", "128k", 32, "MemTable Flush"),
            
            # L0 compaction (순차 읽기 + 쓰기)
            ("l0_compaction_read", "read", "128k", 32, "L0 Compaction Read"),
            ("l0_compaction_write", "write", "128k", 32, "L0 Compaction Write"),
            
            # FillRandom (랜덤 쓰기)
            ("fillrandom", "randwrite", "4k", 16, "FillRandom"),
            
            # Point lookup (랜덤 읽기)
            ("point_lookup", "randread", "4k", 16, "Point Lookup"),
            
            # Range scan (순차 읽기)
            ("range_scan", "read", "4k", 16, "Range Scan"),
            
            # Mixed workload (읽기 70%, 쓰기 30%)
            ("mixed_workload", "rw", "4k", 16, "Mixed Workload (R70/W30)", 70),
        ]
        
        rocksdb_results = {}
        
        for name, rw, bs, iodepth, description, *args in rocksdb_patterns:
            rwmixread = args[0] if args else None
            print(f"\n{description}:")
            
            fio_data = self.run_fio_test(name, rw, bs, iodepth, 30, rwmixread)
            
            if fio_data:
                result = self.analyze_fio_result(fio_data)
                if result:
                    rocksdb_results[name] = result
                    print(f"  {description}: {result['bandwidth_mib_s']:.1f} MiB/s")
                    
                    # 결과 저장
                    with open(f"{self.output_dir}/{name}.json", 'w') as f:
                        json.dump(fio_data, f, indent=2)
            
            time.sleep(2)
        
        return rocksdb_results
    
    def generate_envelope_report(self, all_results):
        """Device Envelope 보고서 생성"""
        report = {
            'device': self.device,
            'test_date': datetime.now().isoformat(),
            'test_type': 'enhanced_device_envelope',
            'measurements': all_results,
            'summary': {
                'max_sequential_write': 0,
                'max_sequential_read': 0,
                'max_random_write': 0,
                'max_random_read': 0,
                'optimal_block_size': {},
                'optimal_queue_depth': {},
                'mixed_workload_characteristics': {}
            }
        }
        
        # 최대 성능 찾기
        if 'block_size_sweep' in all_results:
            bs_results = all_results['block_size_sweep']
            for rw in bs_results:
                if bs_results[rw]:
                    max_bw = max(bs_results[rw].values(), key=lambda x: x['bandwidth_mib_s'])
                    report['summary'][f'max_{rw}'] = max_bw['bandwidth_mib_s']
                    report['summary']['optimal_block_size'][rw] = max_bw
        
        # 보고서 저장
        with open(f"{self.output_dir}/enhanced_envelope_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def run_full_envelope_measurement(self):
        """전체 Device Envelope 측정 실행"""
        print("=== Enhanced Device Envelope Measurement 시작 ===")
        print(f"장치: {self.device}")
        print(f"출력 디렉토리: {self.output_dir}")
        
        all_results = {}
        
        # 1. 블록 크기 스윕
        all_results['block_size_sweep'] = self.measure_block_size_sweep()
        
        # 2. 큐 깊이 스윕
        all_results['queue_depth_sweep'] = self.measure_queue_depth_sweep()
        
        # 3. 혼합 워크로드 스윕
        all_results['mixed_workload_sweep'] = self.measure_mixed_workload_sweep()
        
        # 4. 동시 작업 수 스윕
        all_results['concurrent_jobs_sweep'] = self.measure_concurrent_jobs_sweep()
        
        # 5. RocksDB 특화 패턴
        all_results['rocksdb_patterns'] = self.measure_rocksdb_specific_patterns()
        
        # 6. 보고서 생성
        report = self.generate_envelope_report(all_results)
        
        print("\n=== Enhanced Device Envelope Measurement 완료 ===")
        print(f"보고서 저장: {self.output_dir}/enhanced_envelope_report.json")
        
        return report

if __name__ == "__main__":
    # 측정 실행
    measurement = EnhancedEnvelopeMeasurement()
    report = measurement.run_full_envelope_measurement()
    
    print("\n=== 측정 결과 요약 ===")
    print(f"최대 Sequential Write: {report['summary']['max_sequential_write']:.1f} MiB/s")
    print(f"최대 Sequential Read: {report['summary']['max_sequential_read']:.1f} MiB/s")
    print(f"최대 Random Write: {report['summary']['max_random_write']:.1f} MiB/s")
    print(f"최대 Random Read: {report['summary']['max_random_read']:.1f} MiB/s")
