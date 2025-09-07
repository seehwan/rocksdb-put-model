#!/usr/bin/env python3
"""
Phase-A: Device Calibration (2025-09-08)

디바이스 I/O 성능을 정확히 측정하여 v4 모델의 Device Envelope Modeling에 필요한 파라미터를 확보합니다.
"""

import subprocess
import json
import time
import re
from pathlib import Path

class DeviceCalibrator:
    """디바이스 캘리브레이션 클래스"""
    
    def __init__(self, device_path: str = "/dev/nvme1n1p1"):
        """초기화"""
        self.device_path = device_path
        self.results = {}
        
    def run_fio_test(self, test_name: str, rw: str, rwmixread: int = None) -> dict:
        """fio 테스트 실행"""
        print(f"🔧 {test_name} 테스트 실행 중...")
        
        # fio 명령어 구성
        cmd = [
            "fio",
            "--name=fio_test",
            f"--filename={self.device_path}",
            f"--rw={rw}",
            "--bs=128k",
            "--iodepth=32",
            "--numjobs=1",
            "--time_based=1",
            "--runtime=60",
            "--output-format=json"
        ]
        
        if rwmixread is not None:
            cmd.append(f"--rwmixread={rwmixread}")
            
        try:
            # fio 실행
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                print(f"❌ {test_name} 테스트 실패: {result.stderr}")
                return None
                
            # JSON 결과 파싱
            fio_output = json.loads(result.stdout)
            job = fio_output['jobs'][0]
            
            # 결과 추출
            read_bw = job['read']['bw'] / 1024  # KiB/s to MiB/s
            write_bw = job['write']['bw'] / 1024  # KiB/s to MiB/s
            read_iops = job['read']['iops']
            write_iops = job['write']['iops']
            read_lat = job['read']['lat_ns']['mean'] / 1000  # ns to us
            write_lat = job['write']['lat_ns']['mean'] / 1000  # ns to us
            
            result_data = {
                'bandwidth_mib_s': read_bw + write_bw if rwmixread else (read_bw if rw == 'read' else write_bw),
                'read_bandwidth_mib_s': read_bw,
                'write_bandwidth_mib_s': write_bw,
                'read_iops': read_iops,
                'write_iops': write_iops,
                'read_latency_us': read_lat,
                'write_latency_us': write_lat,
                'utilization_percent': job['sys_cpu']
            }
            
            print(f"✅ {test_name} 완료: {result_data['bandwidth_mib_s']:.1f} MiB/s")
            return result_data
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_name} 테스트 시간 초과")
            return None
        except Exception as e:
            print(f"❌ {test_name} 테스트 오류: {e}")
            return None
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("=== Phase-A: Device Calibration (2025-09-08) ===")
        print(f"디바이스: {self.device_path}")
        print()
        
        # Write Test
        self.results['write_test'] = self.run_fio_test("Write", "write")
        
        # Read Test  
        self.results['read_test'] = self.run_fio_test("Read", "read")
        
        # Mixed Test
        self.results['mixed_test'] = self.run_fio_test("Mixed", "rw", 50)
        
        # 결과 분석
        self.analyze_results()
        
    def analyze_results(self):
        """결과 분석"""
        print("\n📊 결과 분석:")
        
        if not all(self.results.values()):
            print("❌ 일부 테스트가 실패했습니다.")
            return
            
        write_bw = self.results['write_test']['bandwidth_mib_s']
        read_bw = self.results['read_test']['bandwidth_mib_s']
        mixed_bw = self.results['mixed_test']['bandwidth_mib_s']
        
        print(f"  Write Bandwidth (B_w): {write_bw:.1f} MiB/s")
        print(f"  Read Bandwidth (B_r): {read_bw:.1f} MiB/s")
        print(f"  Mixed Bandwidth (B_eff): {mixed_bw:.1f} MiB/s")
        
        # 성능 분석
        read_degradation = (read_bw - self.results['mixed_test']['read_bandwidth_mib_s']) / read_bw * 100
        write_degradation = (write_bw - self.results['mixed_test']['write_bandwidth_mib_s']) / write_bw * 100
        
        print(f"\n📈 성능 분석:")
        print(f"  읽기 성능 저하: {read_degradation:.1f}%")
        print(f"  쓰기 성능 저하: {write_degradation:.1f}%")
        print(f"  읽기/쓰기 비율: {read_bw/write_bw:.2f}")
        
        # 결과 저장
        self.save_results()
        
    def save_results(self):
        """결과 저장"""
        output_file = Path("device_calibration_results.json")
        
        # 실험 정보 추가
        experiment_data = {
            "experiment_info": {
                "date": "2025-09-08",
                "phase": "Phase-A",
                "test_type": "Device Calibration",
                "device": self.device_path,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "device_calibration": self.results,
            "performance_analysis": {
                "read_vs_write_ratio": self.results['read_test']['bandwidth_mib_s'] / self.results['write_test']['bandwidth_mib_s'],
                "read_performance_degradation_mixed": (self.results['read_test']['bandwidth_mib_s'] - self.results['mixed_test']['read_bandwidth_mib_s']) / self.results['read_test']['bandwidth_mib_s'],
                "write_performance_degradation_mixed": (self.results['write_test']['bandwidth_mib_s'] - self.results['mixed_test']['write_bandwidth_mib_s']) / self.results['write_test']['bandwidth_mib_s'],
                "concurrency_interference": "significant" if (self.results['read_test']['bandwidth_mib_s'] + self.results['write_test']['bandwidth_mib_s']) > self.results['mixed_test']['bandwidth_mib_s'] * 1.1 else "minimal"
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(experiment_data, f, indent=2)
            
        print(f"\n💾 결과 저장: {output_file}")
        print("✅ Phase-A 완료!")

def main():
    """메인 함수"""
    calibrator = DeviceCalibrator()
    calibrator.run_all_tests()

if __name__ == "__main__":
    main()
