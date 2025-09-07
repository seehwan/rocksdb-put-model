# Phase-A: Device Calibration (2025-09-08)

## 목적
디바이스 I/O 성능을 정확히 측정하여 v4 모델의 Device Envelope Modeling에 필요한 파라미터를 확보합니다.

## 실험 설정
- **디바이스**: `/dev/nvme1n1p1`
- **테스트 도구**: `fio`
- **블록 크기**: 128k
- **I/O Depth**: 32
- **작업 수**: 1
- **실행 시간**: 60초

## 테스트 항목

### 1. Write Test
```bash
fio --name=w --filename=/dev/nvme1n1p1 --rw=write --bs=128k --iodepth=32 --numjobs=1 --time_based=1 --runtime=60
```
- **목적**: 순수 쓰기 성능 측정
- **측정값**: B_w (Write Bandwidth)

### 2. Read Test
```bash
fio --name=r --filename=/dev/nvme1n1p1 --rw=read --bs=128k --iodepth=32 --numjobs=1 --time_based=1 --runtime=60
```
- **목적**: 순수 읽기 성능 측정
- **측정값**: B_r (Read Bandwidth)

### 3. Mixed Test
```bash
fio --name=rw --filename=/dev/nvme1n1p1 --rw=rw --rwmixread=50 --bs=128k --iodepth=32 --numjobs=1 --time_based=1 --runtime=60
```
- **목적**: 혼합 I/O 성능 측정
- **측정값**: B_eff (Effective Bandwidth)

## 예상 결과
- **B_w**: ~1500 MiB/s
- **B_r**: ~2400 MiB/s  
- **B_eff**: ~2200 MiB/s

## 상태
- [ ] Write Test 실행
- [ ] Read Test 실행
- [ ] Mixed Test 실행
- [ ] 결과 분석 및 저장
