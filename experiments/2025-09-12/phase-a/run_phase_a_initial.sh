#!/bin/bash
# Phase-A: 초기상태 장치 성능 측정 스크립트
# 실행일: 2025-09-12
# 목적: SSD 완전 초기화 후 초기 성능 측정

echo "=== Phase-A: 초기상태 장치 성능 측정 시작 ===" | tee phase_a_initial.log
echo "시작 시간: $(date)" | tee -a phase_a_initial.log
echo "장치: /dev/nvme1n1" | tee -a phase_a_initial.log
echo "마운트 포인트: /rocksdb" | tee -a phase_a_initial.log
echo "" | tee -a phase_a_initial.log

# 1. SSD 완전 초기화
echo "1. SSD 완전 초기화 중..." | tee -a phase_a_initial.log
echo "  기존 파티션 언마운트..." | tee -a phase_a_initial.log
sudo umount /dev/nvme1n1p1 2>/dev/null || true
sudo umount /dev/nvme1n1p2 2>/dev/null || true
sudo umount /dev/nvme1n1 2>/dev/null || true
sleep 2

echo "  기존 파티션 테이블 삭제..." | tee -a phase_a_initial.log
sudo parted /dev/nvme1n1 mklabel gpt
sleep 2

echo "  블록 디스카드 (완전 초기화)..." | tee -a phase_a_initial.log
sudo blkdiscard /dev/nvme1n1
sleep 5

echo "  파일시스템 재생성..." | tee -a phase_a_initial.log
sudo mkfs.f2fs /dev/nvme1n1
sleep 3

echo "  마운트..." | tee -a phase_a_initial.log
sudo mount /dev/nvme1n1 /rocksdb
sleep 2

echo "  권한 설정..." | tee -a phase_a_initial.log
sudo chown -R $USER:$USER /rocksdb

echo "  초기화 완료: $(date)" | tee -a phase_a_initial.log

# 2. 초기 상태 fio 벤치마크 (핵심 테스트)
echo "2. 초기 상태 fio 벤치마크 실행 중..." | tee -a phase_a_initial.log

# 2.1 Sequential Write Test (RocksDB MemTable flush)
echo "  - Sequential Write Test..." | tee -a phase_a_initial.log
echo "    시작: $(date)" | tee -a phase_a_initial.log
sudo fio --name=seq_write_initial --filename=/dev/nvme1n1 --rw=write --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > seq_write_initial.json 2>&1
echo "    완료: $(date)" | tee -a phase_a_initial.log

# 2.2 Random Write Test (fillrandom workload)
echo "  - Random Write Test..." | tee -a phase_a_initial.log
echo "    시작: $(date)" | tee -a phase_a_initial.log
sudo fio --name=rand_write_initial --filename=/dev/nvme1n1 --rw=randwrite --bs=4k --iodepth=16 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > rand_write_initial.json 2>&1
echo "    완료: $(date)" | tee -a phase_a_initial.log

# 2.3 Sequential Read Test (compaction reads)
echo "  - Sequential Read Test..." | tee -a phase_a_initial.log
echo "    시작: $(date)" | tee -a phase_a_initial.log
sudo fio --name=seq_read_initial --filename=/dev/nvme1n1 --rw=read --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > seq_read_initial.json 2>&1
echo "    완료: $(date)" | tee -a phase_a_initial.log

# 2.4 Random Read Test
echo "  - Random Read Test..." | tee -a phase_a_initial.log
echo "    시작: $(date)" | tee -a phase_a_initial.log
sudo fio --name=rand_read_initial --filename=/dev/nvme1n1 --rw=randread --bs=4k --iodepth=16 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > rand_read_initial.json 2>&1
echo "    완료: $(date)" | tee -a phase_a_initial.log

# 2.5 Mixed Read/Write Test (실제 워크로드)
echo "  - Mixed Read/Write Test..." | tee -a phase_a_initial.log
echo "    시작: $(date)" | tee -a phase_a_initial.log
sudo fio --name=mixed_rw_initial --filename=/dev/nvme1n1 --rw=rw --rwmixread=50 --bs=4k --iodepth=16 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > mixed_rw_initial.json 2>&1
echo "    완료: $(date)" | tee -a phase_a_initial.log

# 3. 결과 분석
echo "3. 초기 상태 결과 분석 중..." | tee -a phase_a_initial.log
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
print("초기 상태 결과 분석 중...")
seq_write_results = analyze_fio_json('seq_write_initial.json')
rand_write_results = analyze_fio_json('rand_write_initial.json')
seq_read_results = analyze_fio_json('seq_read_initial.json')
rand_read_results = analyze_fio_json('rand_read_initial.json')
mixed_rw_results = analyze_fio_json('mixed_rw_initial.json')

# 초기 상태 결과 생성
initial_state_results = {
    'device': '/dev/nvme1n1',
    'mount_point': '/rocksdb',
    'test_date': '2025-09-12',
    'test_type': 'initial_state_measurement',
    'environment': 'fresh_initialized_ssd',
    'initialization': {
        'umount': True,
        'blkdiscard': True,
        'mkfs_f2fs': True,
        'mount': True
    },
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
        'environmental_factor': 'initial_state'
    }
}

# 평균 계산
write_tests = [seq_write_results, rand_write_results]
read_tests = [seq_read_results, rand_read_results]

if write_tests[0] and write_tests[1]:
    initial_state_results['summary']['avg_write_bandwidth_mib_s'] = (
        write_tests[0]['bandwidth_mib_s'] + write_tests[1]['bandwidth_mib_s']
    ) / 2

if read_tests[0] and read_tests[1]:
    initial_state_results['summary']['avg_read_bandwidth_mib_s'] = (
        read_tests[0]['bandwidth_mib_s'] + read_tests[1]['bandwidth_mib_s']
    ) / 2

# 결과 저장
with open('initial_state_results.json', 'w') as f:
    json.dump(initial_state_results, f, indent=2)

print("초기 상태 측정 결과:")
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

print(f"  평균 Write: {initial_state_results['summary']['avg_write_bandwidth_mib_s']:.1f} MiB/s")
print(f"  평균 Read: {initial_state_results['summary']['avg_read_bandwidth_mib_s']:.1f} MiB/s")
PY

# 4. 결과 디렉토리로 이동
echo "4. 결과를 data 디렉토리로 이동..." | tee -a phase_a_initial.log
mkdir -p data
mv *.json *.log data/

# 5. 완료 메시지
echo "=== Phase-A 초기 상태 측정 완료 ===" | tee -a data/phase_a_initial.log
echo "완료 시간: $(date)" | tee -a data/phase_a_initial.log
echo "결과 파일:" | tee -a data/phase_a_initial.log
ls -la data/ | tee -a data/phase_a_initial.log
echo "" | tee -a data/phase_a_initial.log
echo "다음 단계: Phase-B FillRandom 실험을 진행한 후 열화 상태 측정을 위해" | tee -a data/phase_a_initial.log
echo "  ./run_phase_a_degraded.sh 를 실행하세요." | tee -a data/phase_a_initial.log
