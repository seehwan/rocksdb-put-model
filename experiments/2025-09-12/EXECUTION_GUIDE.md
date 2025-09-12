# 2025-09-12 실험 실행 가이드

## 🎯 실험 개요

**SSD 장치 상태 변화와 시간대별 컴팩션 동작을 관찰하여 RocksDB 안정화 가능성 및 안정적 Put 속도 구하기**

### 핵심 연구 질문
1. **초기화된 SSD에서 시작한 RocksDB가 안정화될 수 있는가?**
2. **안정화된다면 안정적으로 처리할 수 있는 Put 속도는?**
3. **시간에 따른 컴팩션 동작과 레벨별 성능 변화는 어떻게 나타나는가?**
4. **장치 열화가 FillRandom 성능에 미치는 영향은?**

## 📋 실험 실행 순서

### Phase-A: Device Envelope 모델 구축

#### 목적
초기상태 장치 성능과 Phase-B 이후 열화된 상태에서의 장치 성능을 측정하여 Device Envelope 모델 구축

#### 실행 방법
```bash
cd /home/sslab/rocksdb-put-model/experiments/2025-09-12
python3 scripts/run_phase_a.py
```

#### 실행 과정
1. **SSD 완전 초기화**: `umount`, `blkdiscard`, `mkfs.f2fs`
2. **초기 상태 장치 성능 측정**: fio 그리드 벤치마크 (364개 측정점)
3. **Phase-B 실험 진행 안내**: FillRandom 실험 실행 요청
4. **열화 상태 장치 성능 측정**: Phase-B 완료 후 동일한 fio 벤치마크
5. **Device Envelope 모델 구축**: 4D Grid Interpolation + 시간 의존성

#### 예상 소요 시간
- **초기 상태 측정**: 약 2-3시간
- **열화 상태 측정**: 약 2-3시간
- **총 소요 시간**: 약 4-6시간

### Phase-B: FillRandom 성능 분석 및 컴팩션 모니터링

#### 목적
LOG 파일을 저장하고, 시간에 따라 FillRandom 성능과 레벨별 컴팩션량을 분석할 수 있도록 충분한 로그를 사용하고, 시각화를 포함

#### 실행 방법
```bash
cd /home/sslab/rocksdb-put-model/experiments/2025-09-12
python3 scripts/run_phase_b.py
```

#### 실행 과정
1. **RocksDB 로깅 설정**: 상세한 로그 설정
2. **Uniform Random FillRandom 실험**: 균등 분포로 FillRandom 실행
3. **Zipfian Random FillRandom 실험**: 지프 분포로 FillRandom 실행
4. **LOG 파일 복사**: 모든 로그 파일을 실험 디렉토리로 복사
5. **성능 트렌드 분석**: 시간별 성능 변화 분석
6. **컴팩션 통계 분석**: 레벨별 컴팩션 패턴 분석
7. **시각화 생성**: 성능, 컴팩션, 안정화 분석 차트

#### 예상 소요 시간
- **Uniform 분포 실험**: 약 24-48시간
- **Zipfian 분포 실험**: 약 24-48시간
- **분석 및 시각화**: 약 1-2시간
- **총 소요 시간**: 약 48-96시간 (2-4일)

## 🔧 사전 준비사항

### 1. 시스템 요구사항
- **CPU**: Intel i9-12900K (16 cores, 24 threads)
- **Memory**: 64GB DDR4-3200
- **Storage**: Samsung 980 PRO 2TB NVMe SSD
- **OS**: Ubuntu 22.04 LTS

### 2. 소프트웨어 요구사항
```bash
# Python 패키지 설치
pip3 install numpy pandas matplotlib seaborn scipy jinja2

# RocksDB 빌드 (이미 완료되어 있다고 가정)
# db_bench 실행 파일이 현재 디렉토리에 있어야 함

# fio 설치 (이미 설치되어 있다고 가정)
# sudo apt install fio
```

### 3. 권한 설정
```bash
# sudo 권한이 필요 (SSD 초기화용)
sudo visudo  # 필요한 경우 사용자 추가

# RocksDB 데이터 디렉토리 권한
sudo chown -R $USER:$USER /rocksdb
```

### 4. 디스크 공간 확인
```bash
# 최소 500GB 여유 공간 필요
df -h /rocksdb
```

## 📊 실험 설정

### Phase-A 설정
- **fio 벤치마크**: 4K~1M 블록 크기, 1~64 큐 깊이
- **측정점**: 364개 (9×7×5×5 = 1575개 중 중복 제거)
- **테스트 시간**: 각 측정점당 5분 + 1분 워밍업

### Phase-B 설정
- **데이터 크기**: 10억 키 (약 1TB)
- **값 크기**: 1024 bytes (1KB)
- **동시성**: 16 threads
- **분포**: Uniform Random, Zipfian Random (α=0.99)
- **로깅**: 1분 간격 성능 통계, 상세한 컴팩션 로그

## 📁 출력 파일 구조

### Phase-A 출력
```
phase-a/
├── data/
│   ├── fio_grid_initial_results.csv      # 초기 상태 fio 결과
│   └── fio_grid_degraded_results.csv     # 열화 상태 fio 결과
├── results/
│   ├── device_envelope_model.json        # Device Envelope 모델
│   └── phase_a_summary_report.json       # 요약 보고서
└── phase_a_YYYYMMDD_HHMMSS.log          # 실행 로그
```

### Phase-B 출력
```
phase-b/
├── data/
│   ├── fillrandom_uniform_output.log     # Uniform 분포 실험 출력
│   └── fillrandom_zipfian_output.log     # Zipfian 분포 실험 출력
├── results/
│   ├── phase_b_results.json              # 실험 결과 데이터
│   ├── phase_b_summary_report.json       # 요약 보고서
│   ├── performance_trends.png            # 성능 트렌드 차트
│   ├── compaction_patterns.png           # 컴팩션 패턴 차트
│   └── stabilization_analysis.png        # 안정화 분석 차트
└── phase_b_YYYYMMDD_HHMMSS.log          # 실행 로그
```

### 공통 출력
```
logs/
├── LOG_YYYYMMDD_HHMMSS                   # RocksDB 메인 로그
├── LOG.old.1_YYYYMMDD_HHMMSS            # 롤링된 로그들
└── ...
```

## ⚠️ 주의사항

### 1. 실험 순서
- **Phase-A를 먼저 실행**하여 초기 상태 측정
- **Phase-B 실험 진행** (FillRandom 실험)
- **Phase-A 재실행**하여 열화 상태 측정

### 2. 데이터 백업
```bash
# 중요한 데이터는 백업
cp -r /rocksdb/data /rocksdb/data.backup
```

### 3. 시스템 모니터링
```bash
# 실험 중 시스템 상태 모니터링
htop                    # CPU, 메모리 사용률
iotop                   # I/O 사용률
nvidia-smi              # GPU 사용률 (있는 경우)
```

### 4. 로그 관리
```bash
# 로그 파일 크기 확인
du -sh logs/
du -sh /rocksdb/data/LOG*
```

## 🚀 실행 예시

### 전체 실험 실행
```bash
# 1. Phase-A 시작 (초기 상태 측정)
python3 scripts/run_phase_a.py

# 2. Phase-B 실행 (FillRandom 실험)
python3 scripts/run_phase_b.py

# 3. Phase-A 재실행 (열화 상태 측정)
python3 scripts/run_phase_a.py

# 4. 결과 분석
python3 scripts/analyze_logs.py
python3 scripts/generate_report.py
```

### 개별 실험 실행
```bash
# Phase-A만 실행
python3 scripts/run_phase_a.py

# Phase-B만 실행
python3 scripts/run_phase_b.py

# 로그 분석만 실행
python3 scripts/analyze_logs.py

# 보고서 생성만 실행
python3 scripts/generate_report.py
```

## 📈 예상 결과

### Phase-A 결과
- **Device Envelope 모델**: 4D Grid Interpolation + 시간 의존성
- **성능 열화 분석**: 초기 대비 성능 저하율
- **예상 열화율**: 쓰기 성능 15-20% 저하

### Phase-B 결과
- **성능 트렌드**: 시간별 처리량, 지연시간 변화
- **컴팩션 패턴**: 레벨별 컴팩션 빈도, 크기
- **안정화 분석**: 안정화 가능성, 안정화 시점, 안정적 Put 속도
- **예상 안정적 Put 속도**: 25,000-35,000 ops/sec

## 🆘 문제 해결

### 일반적인 문제
1. **권한 오류**: `sudo` 권한 확인
2. **디스크 공간 부족**: 여유 공간 확인
3. **RocksDB 빌드 오류**: db_bench 실행 파일 확인
4. **fio 설치 오류**: `sudo apt install fio`

### 로그 확인
```bash
# 실험 로그 확인
tail -f phase-a/phase_a_*.log
tail -f phase-b/phase_b_*.log

# RocksDB 로그 확인
tail -f /rocksdb/data/LOG
```

### 실험 중단 및 재시작
```bash
# 프로세스 확인
ps aux | grep db_bench
ps aux | grep fio

# 프로세스 종료
kill -9 <PID>

# 실험 재시작
python3 scripts/run_phase_a.py  # 또는 run_phase_b.py
```

---

**실험 시작 전 이 가이드를 숙지하고, 각 단계를 차근차근 진행하세요.**
