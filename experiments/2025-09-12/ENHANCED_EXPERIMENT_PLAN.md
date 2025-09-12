# 2025-09-12 향상된 실험 계획서

## 🎯 실험 목표

**SSD 장치 상태 변화와 시간대별 컴팩션 동작을 관찰하여 RocksDB 안정화 가능성 및 안정적 Put 속도 구하기**

### 핵심 연구 질문
1. **초기화된 SSD에서 시작한 RocksDB가 안정화될 수 있는가?**
2. **안정화된다면 안정적으로 처리할 수 있는 Put 속도는?**
3. **시간에 따른 컴팩션 동작과 레벨별 성능 변화는 어떻게 나타나는가?**
4. **장치 열화가 FillRandom 성능에 미치는 영향은?**

## 📊 실험 설계

### 1. SSD 장치 상태 관리

#### 1.1 초기화 상태 설정
- **완전 초기화**: `umount`, `blkdiscard`, `mkfs.f2fs`
- **초기 성능 측정**: 초기화 직후 장치 성능 측정
- **기준선 설정**: 초기 상태를 기준선으로 설정

#### 1.2 열화 상태 모니터링
- **실시간 모니터링**: 실험 진행 중 장치 성능 지속 모니터링
- **주기적 측정**: 1시간 간격으로 장치 성능 측정
- **열화 지표**: 쓰기 성능, 읽기 성능, 지연시간 변화 추적

### 2. FillRandom 워크로드 설계

#### 2.1 키 분포 실험
- **Uniform Random**: 균등 분포 키 생성
- **Zipfian Random**: 지프 분포 키 생성 (s=0.99)
- **비교 분석**: 두 분포에서의 성능 차이 분석

#### 2.2 실험 설정
- **키 크기**: 16 bytes (기본)
- **값 크기**: 1024 bytes (1KB)
- **데이터 크기**: 100GB (충분한 데이터로 장기간 실험)
- **동시성**: 16 threads (적절한 동시성)

### 3. 시간대별 컴팩션 동작 분석

#### 3.1 컴팩션 상태 추적
- **L0 → L1 컴팩션**: MemTable flush 및 L0 컴팩션
- **L1 → L2 컴팩션**: L1에서 L2로의 컴팩션
- **L2+ 컴팩션**: L2 이상 레벨의 컴팩션
- **컴팩션 주기**: 각 레벨별 컴팩션 주기 측정

#### 3.2 성능 지표 모니터링
- **WAF (Write Amplification Factor)**: 시간에 따른 WAF 변화
- **RA (Read Amplification)**: 읽기 증폭 변화
- **I/O 분포**: 레벨별 I/O 사용량 분포
- **지연시간**: 컴팩션으로 인한 지연시간

### 4. 레벨별 FillRandom 성능 변화

#### 4.1 레벨별 성능 측정
- **L0 성능**: MemTable flush 성능
- **L1 성능**: L1 컴팩션 성능
- **L2 성능**: L2 컴팩션 성능 (주요 병목)
- **L3+ 성능**: 상위 레벨 컴팩션 성능

#### 4.2 성능 변화 패턴
- **초기 성능**: 실험 시작 직후 성능
- **전환 성능**: 레벨 전환 시 성능
- **안정 성능**: 안정화된 상태에서의 성능

## 🔧 실험 환경 및 설정

### 하드웨어 환경
- **CPU**: Intel i9-12900K (16 cores, 24 threads)
- **Memory**: 64GB DDR4-3200
- **Storage**: Samsung 980 PRO 2TB NVMe SSD
- **OS**: Ubuntu 22.04 LTS

### RocksDB 설정
```bash
# 기본 설정
--db=/rocksdb/data
--num=1000000000  # 10억 키
--value_size=1024
--key_size=16
--threads=16

# 컴팩션 설정
--level0_file_num_compaction_trigger=4
--max_bytes_for_level_base=268435456  # 256MB
--max_bytes_for_level_multiplier=10
--max_background_compactions=4
--max_background_flushes=2

# 로깅 설정
--log_file_time_to_roll=3600  # 1시간마다 로그 롤링
--max_log_file_size=10485760  # 10MB
```

### 모니터링 설정
- **시스템 모니터링**: CPU, 메모리, I/O 사용률
- **RocksDB 모니터링**: 컴팩션 상태, 레벨별 통계
- **장치 모니터링**: SSD 성능, 온도, 마모도

## 📋 실험 절차

### Phase 1: 초기 설정 및 기준선 측정 (Day 1)

#### 1.1 SSD 완전 초기화
```bash
# 1. 언마운트
sudo umount /dev/nvme0n1p1

# 2. 블록 디스카드 (완전 초기화)
sudo blkdiscard /dev/nvme0n1p1

# 3. 파일시스템 재생성
sudo mkfs.f2fs /dev/nvme0n1p1

# 4. 마운트
sudo mount /dev/nvme0n1p1 /rocksdb
```

#### 1.2 초기 장치 성능 측정
```bash
# fio 벤치마크로 초기 성능 측정
fio --name=initial_write --rw=write --bs=4k --size=10g --numjobs=16
fio --name=initial_read --rw=read --bs=4k --size=10g --numjobs=16
```

#### 1.3 실험 환경 준비
- RocksDB 빌드 및 설치
- 모니터링 도구 설정
- 실험 스크립트 준비

### Phase 2: FillRandom 실험 실행 (Day 2-4)

#### 2.1 Uniform Random 실험
```bash
# Uniform Random FillRandom 실행
./db_bench --benchmarks=fillrandom \
  --db=/rocksdb/data \
  --num=1000000000 \
  --value_size=1024 \
  --key_size=16 \
  --threads=16 \
  --distribution=uniform \
  --stats_interval=1000000 \
  --stats_interval_seconds=60 \
  --report_interval_seconds=60
```

#### 2.2 Zipfian Random 실험
```bash
# Zipfian Random FillRandom 실행
./db_bench --benchmarks=fillrandom \
  --db=/rocksdb/data \
  --num=1000000000 \
  --value_size=1024 \
  --key_size=16 \
  --threads=16 \
  --distribution=zipfian \
  --zipfian_alpha=0.99 \
  --stats_interval=1000000 \
  --stats_interval_seconds=60 \
  --report_interval_seconds=60
```

#### 2.3 실시간 모니터링
- 1시간 간격 성능 측정
- 컴팩션 상태 추적
- 장치 성능 모니터링

### Phase 3: 컴팩션 완료 대기 (Day 5)

#### 3.1 남은 컴팩션 완료 대기
```bash
# 컴팩션 상태 확인
./db_bench --benchmarks=compact --db=/rocksdb/data

# 컴팩션 완료까지 대기
while [ $(./db_bench --benchmarks=compact --db=/rocksdb/data | grep "Compaction" | wc -l) -gt 0 ]; do
  echo "Waiting for compaction to complete..."
  sleep 60
done
```

#### 3.2 최종 상태 측정
- 최종 장치 성능 측정
- 최종 RocksDB 상태 측정
- 안정화 여부 판단

### Phase 4: 데이터 분석 및 모델링 (Day 6-7)

#### 4.1 로그 분석
- LOG 파일 분석
- 컴팩션 패턴 분석
- 성능 변화 패턴 분석

#### 4.2 모델 개발
- v4 모델 기반 분석
- v5 모델 개발 (필요시)
- 안정화 모델 개발

## 📊 데이터 수집 및 관리

### 로그 파일 관리
```bash
# LOG 파일을 실험 디렉토리로 복사
cp /rocksdb/data/LOG /home/sslab/rocksdb-put-model/experiments/2025-09-12/logs/
cp /rocksdb/data/LOG.old.* /home/sslab/rocksdb-put-model/experiments/2025-09-12/logs/
```

### 수집 데이터
- **LOG 파일**: RocksDB 실행 로그
- **성능 지표**: ops/sec, MiB/s, 지연시간
- **컴팩션 통계**: 레벨별 컴팩션 정보
- **장치 성능**: fio 벤치마크 결과
- **시스템 리소스**: CPU, 메모리, I/O 사용률

## 🎯 예상 결과

### 1. SSD 장치 상태 변화
- **초기 성능**: 최고 성능 상태
- **열화 성능**: 사용 시간에 따른 성능 저하
- **열화 패턴**: 성능 저하 패턴 및 원인

### 2. 컴팩션 동작 패턴
- **초기 컴팩션**: 빠른 컴팩션 (빈 레벨)
- **전환 컴팩션**: 레벨 전환 시 컴팩션 패턴
- **안정 컴팩션**: 안정화된 상태에서의 컴팩션

### 3. 안정화 가능성
- **안정화 조건**: 안정화에 필요한 조건
- **안정화 시간**: 안정화까지 소요 시간
- **안정화 지표**: 안정화를 판단할 수 있는 지표

### 4. 안정적 Put 속도
- **최대 처리 속도**: 안정화된 상태에서의 최대 속도
- **지속 가능 속도**: 장기간 유지 가능한 속도
- **성능 예측**: 다양한 조건에서의 성능 예측

## 🚀 모델링 접근법

### v4 모델 활용
- 기존 v4 모델의 Device Envelope Modeling 활용
- 4D Grid Interpolation 기반 장치 성능 모델링
- Dynamic Simulation Framework 활용

### v5 모델 개발 (필요시)
- 시간 의존적 성능 변화 모델
- 레벨별 컴팩션 모델
- 안정화 모델

### 핵심 모델 파라미터
- **장치 상태**: 초기화/열화 상태
- **시간**: 실험 진행 시간
- **컴팩션 상태**: 레벨별 컴팩션 상태
- **성능 지표**: WAF, RA, I/O 분포

## 📁 출력 파일 구조

```
2025-09-12/
├── logs/                          # 로그 파일
│   ├── LOG                        # 메인 로그 파일
│   ├── LOG.old.*                  # 롤링된 로그 파일
│   └── system_logs/               # 시스템 로그
├── data/                          # 실험 데이터
│   ├── device_performance/        # 장치 성능 데이터
│   ├── rocksdb_performance/       # RocksDB 성능 데이터
│   ├── compaction_stats/          # 컴팩션 통계
│   └── system_stats/              # 시스템 통계
├── results/                       # 실험 결과
│   ├── analysis/                  # 분석 결과
│   ├── models/                    # 모델 파일
│   └── visualizations/            # 시각화 결과
└── scripts/                       # 실험 스크립트
    ├── run_experiment.py          # 메인 실험 스크립트
    ├── monitor_device.py          # 장치 모니터링 스크립트
    ├── analyze_logs.py            # 로그 분석 스크립트
    └── generate_model.py          # 모델 생성 스크립트
```

---

**실험 시작일**: 2025-09-12  
**예상 완료일**: 2025-09-18  
**총 기간**: 7일  
**주요 목표**: SSD 장치 상태 변화 및 RocksDB 안정화 가능성 분석
