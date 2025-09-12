#!/bin/bash
# Phase-A 재실행 스크립트 (백그라운드 실행용)
# 실행일: 2025-09-09 (새 환경)
# 장치: /dev/nvme1n1p2

echo "=== Phase-A 재실행 시작 (백그라운드) ===" | tee phase_a_rerun.log
echo "시작 시간: $(date)" | tee -a phase_a_rerun.log
echo "장치: /dev/nvme1n1p2" | tee -a phase_a_rerun.log
echo "테스트: 핵심 3개 (Sequential Write, Random Write, Mixed R/W)" | tee -a phase_a_rerun.log
echo "" | tee -a phase_a_rerun.log

# 1. Sequential Write Test (RocksDB와 가장 관련)
echo "1. Sequential Write Test 실행 중..." | tee -a phase_a_rerun.log
echo "  시작: $(date)" | tee -a phase_a_rerun.log
sudo fio --name=seq_write_test --filename=/dev/nvme1n1p2 --rw=write --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > seq_write_test.json 2>&1
echo "  완료: $(date)" | tee -a phase_a_rerun.log

# 2. Random Write Test (fillrandom과 관련)
echo "2. Random Write Test 실행 중..." | tee -a phase_a_rerun.log
echo "  시작: $(date)" | tee -a phase_a_rerun.log
sudo fio --name=rand_write_test --filename=/dev/nvme1n1p2 --rw=randwrite --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > rand_write_test.json 2>&1
echo "  완료: $(date)" | tee -a phase_a_rerun.log

# 3. Mixed Read/Write Test (실제 워크로드와 관련)
echo "3. Mixed Read/Write Test 실행 중..." | tee -a phase_a_rerun.log
echo "  시작: $(date)" | tee -a phase_a_rerun.log
sudo fio --name=mixed_rw_test --filename=/dev/nvme1n1p2 --rw=rw --rwmixread=50 --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > mixed_rw_test.json 2>&1
echo "  완료: $(date)" | tee -a phase_a_rerun.log

# 4. 결과 분석
echo "4. 결과 분석 중..." | tee -a phase_a_rerun.log
python3 - << 'PY'
import json
import sys
from datetime import datetime

def analyze_fio_json(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        job = data['jobs'][0]
        bw_kbps = job['bw']
        iops = job['iops']
        lat_mean = job['clat']['mean'] if job['clat']['mean'] is not None else 0
        
        return {
            'bandwidth_mib_s': bw_kbps / 1024,
            'iops': iops,
            'latency_mean_us': lat_mean
        }
    except Exception as e:
        print(f"Error analyzing {filename}: {e}")
        return None

# 각 테스트 결과 분석
print("결과 분석 중...")
seq_write_results = analyze_fio_json('seq_write_test.json')
rand_write_results = analyze_fio_json('rand_write_test.json')
mixed_rw_results = analyze_fio_json('mixed_rw_test.json')

# 종합 결과 생성
device_rerun_calibration = {
    'device': '/dev/nvme1n1p2',
    'test_date': '2025-09-09',
    'test_type': 'rerun_after_device_initialization',
    'environment': 'fresh_partition_new_environment',
    'seq_write_test': seq_write_results,
    'rand_write_test': rand_write_results,
    'mixed_rw_test': mixed_rw_results,
    'summary': {
        'seq_write_bandwidth_mib_s': seq_write_results['bandwidth_mib_s'] if seq_write_results else 0,
        'rand_write_bandwidth_mib_s': rand_write_results['bandwidth_mib_s'] if rand_write_results else 0,
        'mixed_rw_bandwidth_mib_s': mixed_rw_results['bandwidth_mib_s'] if mixed_rw_results else 0,
        'avg_write_bandwidth_mib_s': 0,
        'environmental_factor': 'fresh_partition'
    }
}

if seq_write_results and rand_write_results:
    device_rerun_calibration['summary']['avg_write_bandwidth_mib_s'] = (
        seq_write_results['bandwidth_mib_s'] + rand_write_results['bandwidth_mib_s']
    ) / 2

# 결과 저장
with open('device_rerun_calibration_results.json', 'w') as f:
    json.dump(device_rerun_calibration, f, indent=2)

print("Phase-A 재실행 결과:")
if seq_write_results:
    print(f"  Sequential Write: {seq_write_results['bandwidth_mib_s']:.1f} MiB/s")
if rand_write_results:
    print(f"  Random Write: {rand_write_results['bandwidth_mib_s']:.1f} MiB/s")
if mixed_rw_results:
    print(f"  Mixed R/W: {mixed_rw_results['bandwidth_mib_s']:.1f} MiB/s")
print(f"  평균 Write: {device_rerun_calibration['summary']['avg_write_bandwidth_mib_s']:.1f} MiB/s")
PY

# 5. 완료 메시지
echo "=== Phase-A 재실행 완료 ===" | tee -a phase_a_rerun.log
echo "완료 시간: $(date)" | tee -a phase_a_rerun.log
echo "결과 파일:" | tee -a phase_a_rerun.log
ls -la *.json *.log | tee -a phase_a_rerun.log
echo "" | tee -a phase_a_rerun.log
echo "분석을 위해 다음 명령을 실행하세요:" | tee -a phase_a_rerun.log
echo "  python3 analyze_phase_a_rerun_results.py" | tee -a phase_a_rerun.log


