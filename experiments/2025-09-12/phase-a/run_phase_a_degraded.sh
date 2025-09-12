#!/bin/bash
# Phase-A: 열화상태 장치 성능 측정 스크립트
# 실행일: 2025-09-12
# 목적: Phase-B 완료 후 열화된 상태에서의 성능 측정

echo "=== Phase-A: 열화상태 장치 성능 측정 시작 ===" | tee phase_a_degraded.log
echo "시작 시간: $(date)" | tee -a phase_a_degraded.log
echo "장치: /dev/nvme1n1" | tee -a phase_a_degraded.log
echo "마운트 포인트: /rocksdb" | tee -a phase_a_degraded.log
echo "주의: 이 스크립트는 Phase-B 완료 후에 실행해야 합니다!" | tee -a phase_a_degraded.log
echo "" | tee -a phase_a_degraded.log

# 초기 상태 결과 확인
if [ ! -f "data/initial_state_results.json" ]; then
    echo "ERROR: 초기 상태 결과 파일이 없습니다!" | tee -a phase_a_degraded.log
    echo "먼저 ./run_phase_a_initial.sh 를 실행하세요." | tee -a phase_a_degraded.log
    exit 1
fi

echo "초기 상태 결과 파일 확인됨: data/initial_state_results.json" | tee -a phase_a_degraded.log

# 1. 열화 상태 fio 벤치마크 (초기 상태와 동일한 테스트)
echo "1. 열화 상태 fio 벤치마크 실행 중..." | tee -a phase_a_degraded.log
echo "  (초기 상태와 동일한 조건으로 재측정)" | tee -a phase_a_degraded.log

# 1.1 Sequential Write Test
echo "  - Sequential Write Test..." | tee -a phase_a_degraded.log
echo "    시작: $(date)" | tee -a phase_a_degraded.log
sudo fio --name=seq_write_degraded --filename=/dev/nvme1n1 --rw=write --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > seq_write_degraded.json 2>&1
echo "    완료: $(date)" | tee -a phase_a_degraded.log

# 1.2 Random Write Test
echo "  - Random Write Test..." | tee -a phase_a_degraded.log
echo "    시작: $(date)" | tee -a phase_a_degraded.log
sudo fio --name=rand_write_degraded --filename=/dev/nvme1n1 --rw=randwrite --bs=4k --iodepth=16 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > rand_write_degraded.json 2>&1
echo "    완료: $(date)" | tee -a phase_a_degraded.log

# 1.3 Sequential Read Test
echo "  - Sequential Read Test..." | tee -a phase_a_degraded.log
echo "    시작: $(date)" | tee -a phase_a_degraded.log
sudo fio --name=seq_read_degraded --filename=/dev/nvme1n1 --rw=read --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > seq_read_degraded.json 2>&1
echo "    완료: $(date)" | tee -a phase_a_degraded.log

# 1.4 Random Read Test
echo "  - Random Read Test..." | tee -a phase_a_degraded.log
echo "    시작: $(date)" | tee -a phase_a_degraded.log
sudo fio --name=rand_read_degraded --filename=/dev/nvme1n1 --rw=randread --bs=4k --iodepth=16 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > rand_read_degraded.json 2>&1
echo "    완료: $(date)" | tee -a phase_a_degraded.log

# 1.5 Mixed Read/Write Test
echo "  - Mixed Read/Write Test..." | tee -a phase_a_degraded.log
echo "    시작: $(date)" | tee -a phase_a_degraded.log
sudo fio --name=mixed_rw_degraded --filename=/dev/nvme1n1 --rw=rw --rwmixread=50 --bs=4k --iodepth=16 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > mixed_rw_degraded.json 2>&1
echo "    완료: $(date)" | tee -a phase_a_degraded.log

# 2. 열화 상태 결과 분석
echo "2. 열화 상태 결과 분석 중..." | tee -a phase_a_degraded.log
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
        lat_p95 = job['clat']['percentile']['95.000000'] if 'percentile' in job['clat'] else 0
        lat_p99 = job['clat']['percentile']['99.000000'] if 'percentile' in job['clat'] else 0
        
        return {
            'bandwidth_mib_s': bw_kbps / 1024,
            'iops': iops,
            'latency_mean_us': lat_mean,
            'latency_p95_us': lat_p95,
            'latency_p99_us': lat_p99
        }
    except Exception as e:
        print(f"Error analyzing {filename}: {e}")
        return None

# 각 테스트 결과 분석
print("열화 상태 결과 분석 중...")
seq_write_results = analyze_fio_json('seq_write_degraded.json')
rand_write_results = analyze_fio_json('rand_write_degraded.json')
seq_read_results = analyze_fio_json('seq_read_degraded.json')
rand_read_results = analyze_fio_json('rand_read_degraded.json')
mixed_rw_results = analyze_fio_json('mixed_rw_degraded.json')

# 열화 상태 결과 생성
degraded_state_results = {
    'device': '/dev/nvme1n1',
    'mount_point': '/rocksdb',
    'test_date': '2025-09-12',
    'test_type': 'degraded_state_measurement',
    'environment': 'after_phase_b_fillrandom_experiment',
    'tests': {
        'sequential_write': seq_write_results,
        'random_write': rand_write_results,
        'sequential_read': seq_read_results,
        'random_read': rand_read_results,
        'mixed_rw': mixed_rw_results
    },
    'summary': {
        'max_write_bandwidth_mib_s': max(seq_write_results['bandwidth_mib_s'] if seq_write_results else 0, 
                                         rand_write_results['bandwidth_mib_s'] if rand_write_results else 0),
        'max_read_bandwidth_mib_s': max(seq_read_results['bandwidth_mib_s'] if seq_read_results else 0,
                                        rand_read_results['bandwidth_mib_s'] if rand_read_results else 0),
        'avg_write_bandwidth_mib_s': 0,
        'avg_read_bandwidth_mib_s': 0,
        'mixed_bandwidth_mib_s': mixed_rw_results['bandwidth_mib_s'] if mixed_rw_results else 0,
        'environmental_factor': 'degraded_state'
    }
}

# 평균 계산
write_tests = [seq_write_results, rand_write_results]
read_tests = [seq_read_results, rand_read_results]

if write_tests[0] and write_tests[1]:
    degraded_state_results['summary']['avg_write_bandwidth_mib_s'] = (
        write_tests[0]['bandwidth_mib_s'] + write_tests[1]['bandwidth_mib_s']
    ) / 2

if read_tests[0] and read_tests[1]:
    degraded_state_results['summary']['avg_read_bandwidth_mib_s'] = (
        read_tests[0]['bandwidth_mib_s'] + read_tests[1]['bandwidth_mib_s']
    ) / 2

# 결과 저장
with open('degraded_state_results.json', 'w') as f:
    json.dump(degraded_state_results, f, indent=2)

print("열화 상태 측정 결과:")
if seq_write_results:
    print(f"  Sequential Write: {seq_write_results['bandwidth_mib_s']:.1f} MiB/s")
if rand_write_results:
    print(f"  Random Write: {rand_write_results['bandwidth_mib_s']:.1f} MiB/s")
if seq_read_results:
    print(f"  Sequential Read: {seq_read_results['bandwidth_mib_s']:.1f} MiB/s")
if rand_read_results:
    print(f"  Random Read: {rand_read_results['bandwidth_mib_s']:.1f} MiB/s")
if mixed_rw_results:
    print(f"  Mixed R/W: {mixed_rw_results['bandwidth_mib_s']:.1f} MiB/s")

print(f"  평균 Write: {degraded_state_results['summary']['avg_write_bandwidth_mib_s']:.1f} MiB/s")
print(f"  평균 Read: {degraded_state_results['summary']['avg_read_bandwidth_mib_s']:.1f} MiB/s")
PY

# 3. Device Envelope 모델 구축
echo "3. Device Envelope 모델 구축 중..." | tee -a phase_a_degraded.log
python3 - << 'PY'
import json
import sys
from datetime import datetime

# 초기 상태와 열화 상태 결과 로드
try:
    with open('data/initial_state_results.json', 'r') as f:
        initial_results = json.load(f)
except:
    print("ERROR: 초기 상태 결과 파일을 찾을 수 없습니다.")
    sys.exit(1)

try:
    with open('degraded_state_results.json', 'r') as f:
        degraded_results = json.load(f)
except:
    print("ERROR: 열화 상태 결과 파일을 찾을 수 없습니다.")
    sys.exit(1)

# 성능 열화 분석
def calculate_degradation(initial, degraded):
    if initial and degraded:
        degradation = ((initial - degraded) / initial) * 100
        return degradation
    return 0

# Device Envelope 모델 생성
device_envelope_model = {
    'device': '/dev/nvme1n1',
    'mount_point': '/rocksdb',
    'model_date': '2025-09-12',
    'model_type': 'device_envelope_with_time_dependency',
    'initial_state': initial_results,
    'degraded_state': degraded_results,
    'degradation_analysis': {
        'sequential_write_degradation_percent': calculate_degradation(
            initial_results['tests']['sequential_write']['bandwidth_mib_s'],
            degraded_results['tests']['sequential_write']['bandwidth_mib_s']
        ),
        'random_write_degradation_percent': calculate_degradation(
            initial_results['tests']['random_write']['bandwidth_mib_s'],
            degraded_results['tests']['random_write']['bandwidth_mib_s']
        ),
        'sequential_read_degradation_percent': calculate_degradation(
            initial_results['tests']['sequential_read']['bandwidth_mib_s'],
            degraded_results['tests']['sequential_read']['bandwidth_mib_s']
        ),
        'random_read_degradation_percent': calculate_degradation(
            initial_results['tests']['random_read']['bandwidth_mib_s'],
            degraded_results['tests']['random_read']['bandwidth_mib_s']
        ),
        'mixed_rw_degradation_percent': calculate_degradation(
            initial_results['tests']['mixed_rw']['bandwidth_mib_s'],
            degraded_results['tests']['mixed_rw']['bandwidth_mib_s']
        ),
        'avg_write_degradation_percent': calculate_degradation(
            initial_results['summary']['avg_write_bandwidth_mib_s'],
            degraded_results['summary']['avg_write_bandwidth_mib_s']
        ),
        'avg_read_degradation_percent': calculate_degradation(
            initial_results['summary']['avg_read_bandwidth_mib_s'],
            degraded_results['summary']['avg_read_bandwidth_mib_s']
        )
    },
    'model_parameters': {
        'time_dependency': 'linear_interpolation_between_initial_and_degraded',
        'performance_prediction': 'based_on_device_usage_time',
        'applicable_workloads': ['fillrandom', 'compaction', 'mixed_workloads']
    }
}

# 결과 저장
with open('device_envelope_model.json', 'w') as f:
    json.dump(device_envelope_model, f, indent=2)

print("Device Envelope 모델 구축 완료:")
print("성능 열화 분석:")
print(f"  Sequential Write 열화: {device_envelope_model['degradation_analysis']['sequential_write_degradation_percent']:.2f}%")
print(f"  Random Write 열화: {device_envelope_model['degradation_analysis']['random_write_degradation_percent']:.2f}%")
print(f"  Sequential Read 열화: {device_envelope_model['degradation_analysis']['sequential_read_degradation_percent']:.2f}%")
print(f"  Random Read 열화: {device_envelope_model['degradation_analysis']['random_read_degradation_percent']:.2f}%")
print(f"  Mixed R/W 열화: {device_envelope_model['degradation_analysis']['mixed_rw_degradation_percent']:.2f}%")
print(f"  평균 Write 열화: {device_envelope_model['degradation_analysis']['avg_write_degradation_percent']:.2f}%")
print(f"  평균 Read 열화: {device_envelope_model['degradation_analysis']['avg_read_degradation_percent']:.2f}%")
PY

# 4. 결과 디렉토리로 이동
echo "4. 결과를 data 디렉토리로 이동..." | tee -a phase_a_degraded.log
mv *.json *.log data/

# 5. 완료 메시지
echo "=== Phase-A 열화 상태 측정 및 Device Envelope 모델 구축 완료 ===" | tee -a data/phase_a_degraded.log
echo "완료 시간: $(date)" | tee -a data/phase_a_degraded.log
echo "결과 파일:" | tee -a data/phase_a_degraded.log
ls -la data/ | tee -a data/phase_a_degraded.log
echo "" | tee -a data/phase_a_degraded.log
echo "Device Envelope 모델이 구축되었습니다!" | tee -a data/phase_a_degraded.log
echo "주요 결과 파일:" | tee -a data/phase_a_degraded.log
echo "  - initial_state_results.json: 초기 상태 성능" | tee -a data/phase_a_degraded.log
echo "  - degraded_state_results.json: 열화 상태 성능" | tee -a data/phase_a_degraded.log
echo "  - device_envelope_model.json: Device Envelope 모델" | tee -a data/phase_a_degraded.log
