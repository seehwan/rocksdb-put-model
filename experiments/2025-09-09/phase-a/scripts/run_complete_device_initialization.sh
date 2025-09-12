#!/bin/bash
# 완전한 장치 초기화 후 Phase-A 재실행 스크립트
# Phase-B와 동일한 초기화 과정을 거친 후 성능 측정

set -e  # 오류 발생시 스크립트 종료

echo "=== 완전한 장치 초기화 후 Phase-A 재실행 ==="
echo "시작 시간: $(date)"
echo ""

# 설정
DEVICE="/dev/nvme1n1"
PARTITION1="/dev/nvme1n1p1"
PARTITION2="/dev/nvme1n1p2"
WAL_MOUNT="/rocksdb/wal"
DATA_MOUNT="/rocksdb/data"
LOG_FILE="complete_initialization.log"

# 로그 파일 초기화
echo "=== 완전한 장치 초기화 시작 ===" > "$LOG_FILE"
echo "시작 시간: $(date)" >> "$LOG_FILE"

# 진행률 업데이트 함수
update_progress() {
    echo "$(date): $1" | tee -a "$LOG_FILE"
    echo "$1"
}

# 1. 기존 마운트 해제
update_progress "1. 기존 마운트 해제 시작"
echo "마운트 해제 시작: $(date)" >> "$LOG_FILE"

update_progress "  - WAL 파티션 마운트 해제 중..."
sudo umount "$WAL_MOUNT" 2>/dev/null || echo "    WAL 파티션이 이미 unmount 상태입니다."

update_progress "  - DATA 파티션 마운트 해제 중..."
sudo umount "$DATA_MOUNT" 2>/dev/null || echo "    DATA 파티션이 이미 unmount 상태입니다."

update_progress "  - 기타 마운트 확인..."
mount | grep nvme1n1 || echo "    추가 마운트 없음"

# 2. 블록 디스카드 (트림 실행)
update_progress "2. 블록 디스카드 실행 시작"
echo "블록 디스카드 시작: $(date)" >> "$LOG_FILE"

update_progress "  - 파티션 1 디스카드 중..."
sudo blkdiscard -f "$PARTITION1"

update_progress "  - 파티션 2 디스카드 중..."
sudo blkdiscard -f "$PARTITION2"

update_progress "  - 전체 장치 디스카드 중..."
sudo blkdiscard -f "$DEVICE"

# 3. 전체 장치 초기화를 위한 write
update_progress "3. 전체 장치 초기화 write 실행"
echo "전체 장치 write 시작: $(date)" >> "$LOG_FILE"

# 전체 장치에 0으로 덮어쓰기 (완전 초기화)
update_progress "  - 전체 장치를 0으로 덮어쓰는 중..."
echo "경고: 이 작업은 시간이 오래 걸릴 수 있습니다."
sudo dd if=/dev/zero of="$DEVICE" bs=1M status=progress 2>&1 | tee -a "$LOG_FILE"

# 4. 파티션 재생성 (필요시)
update_progress "4. 파티션 테이블 확인"
echo "파티션 확인: $(date)" >> "$LOG_FILE"

# 파티션 테이블 확인
sudo fdisk -l "$DEVICE" | tee -a "$LOG_FILE"

# 파티션이 없다면 재생성 (보통은 이미 존재함)
if ! sudo fdisk -l "$DEVICE" | grep -q "nvme1n1p1"; then
    update_progress "  - 파티션 테이블 재생성 중..."
    # GPT 파티션 테이블 생성
    echo "label: gpt" | sudo sfdisk "$DEVICE"
    # 파티션 생성 (첫 번째 파티션: 20GB, 두 번째 파티션: 나머지)
    echo "size=20G, type=linux" | sudo sfdisk "$DEVICE"
    echo "type=linux" | sudo sfdisk "$DEVICE"
else
    update_progress "  - 파티션 테이블이 이미 존재합니다."
fi

# 5. F2FS 포맷
update_progress "5. F2FS 포맷 실행"
echo "F2FS 포맷 시작: $(date)" >> "$LOG_FILE"

update_progress "  - 파티션 1 (WAL) F2FS 포맷 중..."
sudo mkfs.f2fs -f "$PARTITION1"

update_progress "  - 파티션 2 (DATA) F2FS 포맷 중..."
sudo mkfs.f2fs -f "$PARTITION2"

# 6. 포맷 확인
update_progress "6. 포맷 결과 확인"
echo "포맷 확인: $(date)" >> "$LOG_FILE"

sudo fdisk -l "$DEVICE" | tee -a "$LOG_FILE"

# 7. Phase-A 재실행
update_progress "7. Phase-A 재실행 시작"
echo "Phase-A 재실행 시작: $(date)" >> "$LOG_FILE"

# Phase-A 스크립트 실행
if [ -f "./run_phase_a_rerun.sh" ]; then
    update_progress "  - Phase-A 재실행 스크립트 실행 중..."
    chmod +x ./run_phase_a_rerun.sh
    ./run_phase_a_rerun.sh 2>&1 | tee -a "$LOG_FILE"
else
    update_progress "  - Phase-A 재실행 스크립트가 없습니다. 수동으로 fio 테스트를 실행합니다."
    
    # 수동으로 fio 테스트 실행
    update_progress "  - Sequential Write Test 실행 중..."
    sudo fio --name=seq_write_clean --filename="$PARTITION2" --rw=write --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > seq_write_clean.json 2>&1
    
    update_progress "  - Random Write Test 실행 중..."
    sudo fio --name=rand_write_clean --filename="$PARTITION2" --rw=randwrite --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > rand_write_clean.json 2>&1
    
    update_progress "  - Mixed R/W Test 실행 중..."
    sudo fio --name=mixed_rw_clean --filename="$PARTITION2" --rw=rw --rwmixread=50 --bs=128k --iodepth=32 --runtime=60 --time_based=1 --ioengine=libaio --direct=1 --group_reporting=1 --output-format=json > mixed_rw_clean.json 2>&1
fi

# 8. 결과 분석
update_progress "8. 결과 분석 시작"
echo "결과 분석 시작: $(date)" >> "$LOG_FILE"

# Python 스크립트로 결과 분석
python3 - << 'PY'
import json
import os

def extract_bandwidth(fio_file):
    try:
        with open(fio_file, 'r') as f:
            data = json.load(f)
        
        job = data['jobs'][0]
        write_bw = job.get('write', {}).get('bw', 0) / 1024  # KB/s to MiB/s
        read_bw = job.get('read', {}).get('bw', 0) / 1024   # KB/s to MiB/s
        
        return write_bw, read_bw
    except Exception as e:
        print(f"Error processing {fio_file}: {e}")
        return 0, 0

# 결과 파일들
files = [
    ('seq_write_clean.json', 'Sequential Write'),
    ('rand_write_clean.json', 'Random Write'),
    ('mixed_rw_clean.json', 'Mixed R/W')
]

print("=== 완전 초기화 후 성능 결과 ===")
print()

clean_results = {}
for filename, test_name in files:
    if os.path.exists(filename):
        write_bw, read_bw = extract_bandwidth(filename)
        clean_results[test_name] = {'write': write_bw, 'read': read_bw}
        print(f"{test_name}:")
        print(f"  Write: {write_bw:.1f} MiB/s")
        if read_bw > 0:
            print(f"  Read:  {read_bw:.1f} MiB/s")
        print()
    else:
        print(f"{test_name}: 파일 없음")

# 이전 결과와 비교
print("=== 이전 결과와 비교 ===")
print()

previous_results = {
    'Sequential Write': 1770.0,
    'Random Write': 1809.3,
    'Mixed R/W': {'write': 1220.1, 'read': 1221.3}
}

for test_name, clean_data in clean_results.items():
    if test_name in previous_results:
        if isinstance(previous_results[test_name], dict):
            prev_write = previous_results[test_name]['write']
            prev_read = previous_results[test_name]['read']
            curr_write = clean_data['write']
            curr_read = clean_data['read']
            
            write_diff = ((curr_write - prev_write) / prev_write) * 100
            read_diff = ((curr_read - prev_read) / prev_read) * 100
            
            print(f"{test_name}:")
            print(f"  Write: {prev_write:.1f} → {curr_write:.1f} MiB/s ({write_diff:+.1f}%)")
            print(f"  Read:  {prev_read:.1f} → {curr_read:.1f} MiB/s ({read_diff:+.1f}%)")
        else:
            prev_value = previous_results[test_name]
            curr_value = clean_data['write']
            diff = ((curr_value - prev_value) / prev_value) * 100
            
            print(f"{test_name}: {prev_value:.1f} → {curr_value:.1f} MiB/s ({diff:+.1f}%)")
        print()

# 결과 저장
result_data = {
    'timestamp': '$(date -Iseconds)',
    'initialization_type': 'complete_clean',
    'device': '/dev/nvme1n1p2',
    'results': clean_results,
    'comparison_with_previous': {
        'previous_results': previous_results,
        'improvement_analysis': 'See console output above'
    }
}

with open('complete_initialization_results.json', 'w') as f:
    json.dump(result_data, f, indent=2)

print("결과가 complete_initialization_results.json에 저장되었습니다.")
PY

# 9. 완료
update_progress "9. 완전한 장치 초기화 및 Phase-A 재실행 완료"
echo "완료 시간: $(date)" >> "$LOG_FILE"

echo ""
echo "=== 완전한 장치 초기화 후 Phase-A 재실행 완료 ==="
echo "완료 시간: $(date)"
echo ""
echo "📁 결과 파일들:"
echo "  - $LOG_FILE (전체 로그)"
echo "  - seq_write_clean.json"
echo "  - rand_write_clean.json" 
echo "  - mixed_rw_clean.json"
echo "  - complete_initialization_results.json"
echo ""
echo "🔍 결과 분석:"
echo "  python3 -c \"import json; data=json.load(open('complete_initialization_results.json')); print(json.dumps(data, indent=2))\""
