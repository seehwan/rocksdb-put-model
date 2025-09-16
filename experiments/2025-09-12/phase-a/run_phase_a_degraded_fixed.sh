#!/bin/bash
# Phase-A: 열화상태 장치 성능 측정 스크립트 (수정됨)
# 실행일: 2025-09-12
# 목적: Phase-B 완료 후 열화된 상태에서의 성능 측정

echo "=== Phase-A: 열화상태 장치 성능 측정 시작 (수정됨) ===" | tee phase_a_degraded_fixed.log
echo "시작 시간: $(date)" | tee -a phase_a_degraded_fixed.log
echo "장치: /dev/nvme1n1" | tee -a phase_a_degraded_fixed.log
echo "마운트 포인트: /rocksdb" | tee -a phase_a_degraded_fixed.log
echo "작업 디렉토리: /rocksdb" | tee -a phase_a_degraded_fixed.log
echo "주의: 이 스크립트는 Phase-B 완료 후에 실행해야 합니다!" | tee -a phase_a_degraded_fixed.log
echo "" | tee -a phase_a_degraded_fixed.log

# 작업 디렉토리를 /rocksdb로 변경
cd /rocksdb
echo "작업 디렉토리 변경: $(pwd)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log

# 초기 상태 결과 확인
if [ ! -f "/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/initial_state_results.json" ]; then
    echo "ERROR: 초기 상태 결과 파일이 없습니다!" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
    echo "먼저 ./run_phase_a_initial.sh 를 실행하세요." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
    exit 1
fi

echo "초기 상태 결과 파일 확인됨: /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/initial_state_results.json" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log

echo "1. 열화 상태 fio 벤치마크 실행 중..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
echo "  (초기 상태와 동일한 조건으로 재측정)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log

# Sequential Write Test
echo "  - Sequential Write Test..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
echo "    시작: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
fio --name=seq_write_degraded --filename=./seq_write_degraded_test --size=1G --rw=write --bs=64k --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=1 --output-format=json --output=seq_write_degraded.json
echo "    완료: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log

# Random Write Test
echo "  - Random Write Test..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
echo "    시작: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
fio --name=rand_write_degraded --filename=./rand_write_degraded_test --size=1G --rw=randwrite --bs=4k --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=1 --output-format=json --output=rand_write_degraded.json
echo "    완료: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log

# Sequential Read Test
echo "  - Sequential Read Test..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
echo "    시작: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
fio --name=seq_read_degraded --filename=./seq_read_degraded_test --size=1G --rw=read --bs=64k --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=1 --output-format=json --output=seq_read_degraded.json
echo "    완료: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log

# Random Read Test
echo "  - Random Read Test..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
echo "    시작: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
fio --name=rand_read_degraded --filename=./rand_read_degraded_test --size=1G --rw=randread --bs=4k --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=1 --output-format=json --output=rand_read_degraded.json
echo "    완료: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log

# Mixed Read/Write Test
echo "  - Mixed Read/Write Test..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
echo "    시작: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
fio --name=mixed_rw_degraded --filename=./mixed_rw_degraded_test --size=1G --rw=rw --bs=4k --direct=1 --runtime=30 --time_based=1 --ioengine=libaio --iodepth=1 --numjobs=1 --output-format=json --output=mixed_rw_degraded.json
echo "    완료: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log

echo "2. 열화 상태 결과 분석 중..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log

# 결과 분석 및 저장
python3 << 'PYTHON_EOF'
import json
import os

def analyze_fio_result(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        if 'jobs' in data and len(data['jobs']) > 0:
            job = data['jobs'][0]
            write_bw = job.get('write', {}).get('bw', 0) / 1024  # KiB/s to MiB/s
            read_bw = job.get('read', {}).get('bw', 0) / 1024   # KiB/s to MiB/s
            return write_bw, read_bw
        return 0, 0
    except Exception as e:
        print(f"Error analyzing {filename}: {e}")
        return 0, 0

# 결과 분석
results = {}
files = ['seq_write_degraded.json', 'rand_write_degraded.json', 'seq_read_degraded.json', 'rand_read_degraded.json', 'mixed_rw_degraded.json']

for filename in files:
    if os.path.exists(filename):
        write_bw, read_bw = analyze_fio_result(filename)
        results[filename.replace('.json', '')] = {
            'write_bandwidth_mib_s': write_bw,
            'read_bandwidth_mib_s': read_bw
        }
        print(f"Analyzed {filename}: Write={write_bw:.1f} MiB/s, Read={read_bw:.1f} MiB/s")
    else:
        print(f"File not found: {filename}")

# 요약 결과 생성
degraded_results = {
    "device": "/dev/nvme1n1",
    "mount_point": "/rocksdb",
    "test_date": "2025-09-12",
    "test_type": "degraded_state_measurement",
    "environment": "after_phase_b_fillrandom_experiment",
    "tests": results,
    "summary": {
        "max_write_bandwidth_mib_s": max([r['write_bandwidth_mib_s'] for r in results.values()]) if results else 0,
        "max_read_bandwidth_mib_s": max([r['read_bandwidth_mib_s'] for r in results.values()]) if results else 0,
        "avg_write_bandwidth_mib_s": sum([r['write_bandwidth_mib_s'] for r in results.values()]) / len(results) if results else 0,
        "avg_read_bandwidth_mib_s": sum([r['read_bandwidth_mib_s'] for r in results.values()]) / len(results) if results else 0,
        "mixed_bandwidth_mib_s": results.get('mixed_rw_degraded', {}).get('write_bandwidth_mib_s', 0) + results.get('mixed_rw_degraded', {}).get('read_bandwidth_mib_s', 0),
        "environmental_factor": "degraded_state"
    }
}

# 결과 저장
with open('degraded_state_results_fixed.json', 'w') as f:
    json.dump(degraded_results, f, indent=2)

print("열화 상태 측정 결과:")
print(f"  평균 Write: {degraded_results['summary']['avg_write_bandwidth_mib_s']:.1f} MiB/s")
print(f"  평균 Read: {degraded_results['summary']['avg_read_bandwidth_mib_s']:.1f} MiB/s")
print(f"  최대 Write: {degraded_results['summary']['max_write_bandwidth_mib_s']:.1f} MiB/s")
print(f"  최대 Read: {degraded_results['summary']['max_read_bandwidth_mib_s']:.1f} MiB/s")
PYTHON_EOF

echo "3. 결과를 data 디렉토리로 이동..." | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
mv degraded_state_results_fixed.json /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/
mv *.json /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/ 2>/dev/null || true

echo "=== Phase-A 열화 상태 측정 및 Device Envelope 모델 구축 완료 (수정됨) ===" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
echo "완료 시간: $(date)" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
echo "결과 파일:" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
ls -la /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/ | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log

echo "Device Envelope 모델이 구축되었습니다!" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
echo "주요 결과 파일:" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
echo "  - initial_state_results.json: 초기 상태 성능" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
echo "  - degraded_state_results_fixed.json: 열화 상태 성능" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
echo "  - device_envelope_model.json: Device Envelope 모델" | tee -a /home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/phase_a_degraded_fixed.log
