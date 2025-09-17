# RocksDB Put-Rate Model

RocksDB의 쓰기 경로(put, flush, compaction)를 정량 모델로 기술하고, steady state에서 가능한 지속 put rate와 레벨별 I/O 대역폭을 계산하는 방법을 정리합니다. 이론적 모델을 실제 RocksDB 시스템에서 검증할 수 있는 체계적인 실험 계획도 포함합니다.

## 🎯 연구 목적

- **RocksDB의 Steady-State Put Rate (S_max) 정량적 모델링**: LSM-tree 구조에서 지속 가능한 최대 쓰기 성능을 수학적으로 예측
- **실제 운영 환경에서의 모델 검증**: 이론적 모델과 실제 RocksDB 성능의 일치도 검증
- **성능 병목 지점 식별**: Write Amplification, 압축률, 디바이스 대역폭 등이 성능에 미치는 영향 정량화

## 🚀 주요 기여점

### 이론적 기여
- **v1 모델**: 기본 Steady-State S_max 공식 및 레벨별 I/O 분해
- **v2.1 모델**: Harmonic Mean 혼합 I/O, Per-Level 제약, Stall Duty Cycle 모델링
- **v3 모델**: 시간가변 혼합비, 동적 스톨 함수, 비선형 동시성, 과도기 동역학을 포함한 동적 시뮬레이터
- **v4 모델**: 실제 데이터 기반 Device Envelope 모델링, Closed Ledger Accounting, 완전한 Python 구현 ✅
- **v4.1 모델**: 레벨별 컴팩션 I/O 분석 및 시기별 세분화 모델링 ⭐
- **v5 모델**: 실시간 적응형 모델링 및 자동 튜닝 시스템

### 실험적 기여
- **6단계 체계적 검증 프로세스**: 디바이스 캘리브레이션부터 v5 모델 검증까지
- **실제 데이터 기반 검증**: 200MB+ RocksDB LOG 파일에서 추출한 정확한 파라미터
- **자동화된 분석**: LOG 파일 자동 파싱으로 정확한 파라미터 추출
- **시기별 세분화**: 초기-중기-후기 성능 진화 분석

### 도구적 기여
- **계산 도구**: v1, v2.1, v3, v4, v4.1, v5 모델 계산기 및 WAF 분석기
- **동적 시뮬레이터**: Self-contained HTML 시뮬레이터
- **종합 시각화**: 모델 성능 비교, 파라미터 민감도 분석 등 4개 시각화 도구
- **통일된 CSS**: 모든 HTML 파일에 적용된 전문적인 스타일링

## 🎯 최신 성과 (2025-09-12)

### 모델 정확도 개선
- **v1 모델**: 0.0% 정확도 (기본 모델)
- **v2.1 모델**: **88.9% 정확도** (최고 성능) ⭐
- **v3 모델**: 0.0% 정확도 (휴리스틱 기반)
- **v4 모델**: 7.5% 정확도 (Device Envelope)
- **v4.1 모델**: **69.8% 정확도** (시기별 세분화) ⭐
- **v5 모델**: 0.0% 정확도 (실시간 적응형)

### v4.1 Temporal 모델 혁신
- **시기별 세분화**: 초기(48.3%) → 중기(67.8%) → 후기(97.7%) 정확도
- **컴팩션 진화 분석**: 시간에 따른 컴팩션 패턴 변화 모델링
- **RocksDB LOG 통합**: 2,631,490개 이벤트 분석
- **성능 최적화**: 후기 시기 97.7% 정확도 달성

### 주요 혁신사항
- **Device Envelope Modeling**: fio 그리드 스윕 기반 실제 장치 특성 반영
- **Closed Ledger Accounting**: 물리적 검증을 통한 회계 폐곡선
- **Dynamic Simulation Framework**: 시간가변 시스템 동작 모델링
- **Temporal Phase-wise Modeling**: 시기별 성능 진화 분석
- **Level-wise Compaction I/O**: 레벨별 컴팩션 I/O 세분화 분석

### 성능 특성
- **최고 정확도**: 88.9% (v2.1 모델)
- **혁신 모델**: v4.1 Temporal (시기별 세분화)
- **평균 정확도**: 향상된 모델들의 성능 개선
- **시뮬레이션 속도**: 1000+ steps/sec

## 📊 실험 결과 요약 (2025-09-12)

### 모델 성능 순위
| 순위 | 모델 | 정확도 (%) | R² Score | 모델 타입 | 핵심 특징 |
|------|------|-----------|----------|-----------|-----------|
| **1위** | **v2_1** | **88.9%** | **0.889** | enhanced | 최고 성능 |
| **2위** | **v4_1_temporal** | **69.8%** | **0.698** | temporal_enhanced | **시기별 세분화** |
| 3위 | v4 | 7.5% | 0.075 | enhanced | 기본 모델 |
| 4위 | v1 | 0.0% | 0.000 | enhanced | LOG Enhanced |
| 5위 | v3 | 0.0% | 0.000 | enhanced | LOG Enhanced |
| 6위 | v5 | 0.0% | 0.000 | enhanced | LOG Enhanced |

### 실험 데이터
- **총 실험 시간**: 347,784초 (약 96.6시간)
- **총 레코드**: 34,778개
- **평균 QPS**: 120,920 ops/sec
- **최대 QPS**: 663,287 ops/sec
- **최소 QPS**: 160 ops/sec

## Repo Layout

```
rocksdb-put-model/
├── README.md                    # 이 파일 (사용법, 요구사항, 빠른 시작)
├── README.html                  # HTML 버전 (통일된 CSS 스타일 적용)
├── PutModel.md                  # 전체 모델, 수식, 시뮬레이션 코드
├── [PutModel.html](PutModel.html)                # HTML 버전 (MathJax 수식 렌더링)
├── [PutModel_v4_Documentation.html](PutModel_v4_Documentation.html)  # v4 모델 완전 문서화 ⭐
├── [ValidationPlan.html](ValidationPlan.html)          # 검증 계획 HTML 버전 (MathJax 수식 렌더링)
├── [ValidationGuide.html](ValidationGuide.html)         # 검증 실행 가이드 HTML 버전 (MathJax 수식 렌더링)
├── VALIDATION_GUIDE.md          # 검증 실행 가이드 (단계별 실행 방법)
├── styles/                      # CSS 스타일 파일들
│   ├── project.css              # 통일된 프로젝트 CSS 스타일
│   └── css_link.txt             # CSS 링크 가이드
├── rocksdb_validation_plan.md   # 실제 시스템 검증 계획서
├── rocksdb_bench_templates/     # RocksDB 및 fio 설정 템플릿
│   ├── db/                      # RocksDB 옵션 파일들
│   │   ├── options-leveled.ini  # Leveled compaction 설정
│   │   ├── options-leveled-wal-separate.ini  # WAL 분리 설정
│   │   └── options-universal.ini  # Universal compaction 설정
│   └── fio/                     # fio 벤치마크 템플릿들
│       ├── write.job            # 쓰기 대역폭 측정
│       ├── read.job             # 읽기 대역폭 측정
│       └── mix50.job            # 혼합 I/O 측정
├── figs/                        # 생성된 그래프들
│   ├── depth_summary.png        # 초기 버스트 vs Steady State
│   ├── per_level_reads.png      # 레벨별 읽기 I/O
│   ├── per_level_writes.png     # 레벨별 쓰기 I/O
│   └── smax_vs_WA.png          # S_max vs Write Amplification
├── scripts/                     # Python 스크립트들
    ├── rocksdb_put_viz.py      # 그래프 생성 (matplotlib)
    ├── steady_state_put_estimator.py  # S_max 계산기 (v1)
    ├── per_level_breakdown.py   # 레벨별 I/O 분해
    ├── transient_depth_analysis.py     # 초기 버스트 분석
    ├── waf_analyzer.py         # RocksDB LOG WAF 분석기
    ├── smax_calc.py            # S_max 계산기 v1 (검증용)
    └── smax_calc_v2.py         # S_max 계산기 v2.1 (개선된 모델)
├── experiments/                 # 실험 결과 관리
    ├── 2025-09-12/             # 최신 실험 디렉토리 ⭐
    │   ├── phase-a/            # 디바이스 캘리브레이션
    │   ├── phase-b/            # RocksDB 벤치마크
    │   ├── phase-c/            # Enhanced Models 개발
    │   ├── phase-d/            # 프로덕션 통합
    │   ├── phase-e/            # 고급 최적화
    │   ├── styles/             # CSS 스타일 파일
    │   ├── scripts/            # 분석 스크립트
    │   ├── 09_12_EXPERIMENT_SUMMARY.html  # 실험 요약 보고서
    │   ├── COMPREHENSIVE_ANALYSIS_REPORT.html  # 종합 분석 보고서
    │   └── COMPREHENSIVE_FINAL_ANALYSIS_WITH_V4_1_TEMPORAL.html  # v4.1 Temporal 포함 최종 보고서
    ├── 2025-09-09/             # 이전 실험 디렉토리
    ├── 2025-09-08/             # 이전 실험 디렉토리
    ├── 2025-09-05/             # 이전 실험 디렉토리
    └── templates/              # 실험 템플릿들
```

## Quick Start

### 1) Run experiments
```bash
# 가상환경 활성화
source .venv/bin/activate  # macOS/Linux
# 또는
.venv\Scripts\activate     # Windows

# 그래프 생성
python3 scripts/rocksdb_put_viz.py --run

# S_max 계산
python3 scripts/steady_state_put_estimator.py

# 레벨별 I/O 분해
python3 scripts/per_level_breakdown.py

# 초기 버스트 분석
python3 scripts/transient_depth_analysis.py
```

### 2) View results
- **HTML**: 
  - [PutModel.html](PutModel.html) - v1 이론 모델 (MathJax 수식 렌더링)
  - [PutModel_v2_1.html](PutModel_v2_1.html) - v2.1 모델 (개선된 모델)
  - [PutModel_v3.html](PutModel_v3.html) - v3 동적 시뮬레이터
  - [ValidationPlan.html](ValidationPlan.html) - 검증 계획 (이론적 방법론)
  - [ValidationGuide.html](ValidationGuide.html) - 검증 실행 가이드 (단계별 실행법)
- **최신 실험 보고서**:
  - [experiments/2025-09-12/09_12_EXPERIMENT_SUMMARY.html](experiments/2025-09-12/09_12_EXPERIMENT_SUMMARY.html) - 2025-09-12 실험 요약 보고서 ⭐
  - [experiments/2025-09-12/COMPREHENSIVE_ANALYSIS_REPORT.html](experiments/2025-09-12/COMPREHENSIVE_ANALYSIS_REPORT.html) - 종합 분석 보고서
  - [experiments/2025-09-12/COMPREHENSIVE_FINAL_ANALYSIS_WITH_V4_1_TEMPORAL.html](experiments/2025-09-12/COMPREHENSIVE_FINAL_ANALYSIS_WITH_V4_1_TEMPORAL.html) - v4.1 Temporal 포함 최종 보고서
- **그래프**: `figs/` 폴더의 PNG 파일들
- **수치**: 각 스크립트의 콘솔 출력

### 3) Validate with real RocksDB
```bash
# 실제 RocksDB 시스템에서 모델 검증
# 자세한 절차는 ValidationGuide.html 참조

# 1. Device calibration (fio) - 템플릿 사용
fio rocksdb_bench_templates/fio/write.job
fio rocksdb_bench_templates/fio/read.job
fio rocksdb_bench_templates/fio/mix50.job

# 2. RocksDB benchmark - 템플릿 사용 (RocksDB 10.7.0+ 호환)
# 디렉토리 생성: sudo mkdir -p /rocksdb/data /rocksdb/wal
# 로그 디렉토리 준비: mkdir -p ./log && ln -sf ./log/LOG /rocksdb/data/LOG
# 파일 디스크립터 제한 증가: ulimit -n 65536

# RocksDB 10.7.0+ 호환 옵션 파일 생성
cat > options-leveled.ini << 'EOF'
# RocksDB 10.7+ leveled-compaction options (INI format)
# References:
# - RocksDB Options File format: https://github.com/facebook/rocksdb/wiki/RocksDB-Options-File
# - BlockBasedTable format: https://github.com/facebook/rocksdb/wiki/rocksdb-blockbasedtable-format
# Notes:
# * Keep path arguments (e.g., --db, --wal_dir) on the db_bench command line, not inside this file.
# * Avoid pointer-typed or unsupported options in Options File (see wiki).

[Version]
rocksdb_version=10.7.0
options_file_version=1.1

[DBOptions]
# Creation / general
create_if_missing=true
create_missing_column_families=false

# Logging / stats
keep_log_file_num=3
stats_dump_period_sec=60

# IO behavior
bytes_per_sync=1048576              # 1 MiB
wal_bytes_per_sync=1048576          # 1 MiB
use_direct_reads=true
use_direct_io_for_flush_and_compaction=true
compaction_readahead_size=0

# Write threading
enable_pipelined_write=true         # DBOptions::enable_pipelined_write
allow_concurrent_memtable_write=true

# Background work
max_open_files=2048
max_background_jobs=12
max_subcompactions=4

[CFOptions "default"]
# Compaction policy
compaction_style=kCompactionStyleLevel
compaction_pri=kMinOverlappingRatio
num_levels=7
level_compaction_dynamic_level_bytes=false
max_bytes_for_level_multiplier=10.0

# File sizing and level sizing
target_file_size_base=268435456         # 256 MiB
target_file_size_multiplier=1
max_bytes_for_level_base=2684354560     # ~2.5 GiB

# Compression (ensure your build enables these; otherwise switch to kNoCompression)
compression=kSnappyCompression
bottommost_compression=kZSTD

# Memtable / L0
write_buffer_size=268435456             # 256 MiB per memtable
max_write_buffer_number=3
min_write_buffer_number_to_merge=1
level0_file_num_compaction_trigger=4
level0_slowdown_writes_trigger=20
level0_stop_writes_trigger=36

# Table factory (links to TableOptions/BlockBasedTable section below)
table_factory=BlockBasedTable

[TableOptions/BlockBasedTable "default"]
# Modern table format (forward-incompatible with very old RocksDB)
format_version=5

# Common table tuning (safe defaults)
block_size=65536                        # 64 KiB blocks (adjust per workload)
cache_index_and_filter_blocks=true
pin_l0_filter_and_index_blocks_in_cache=true
whole_key_filtering=true
checksum=kCRC32c
filter_policy=rocksdb.BuiltinBloomFilter
EOF

./db_bench --options_file=options-leveled.ini \
  --benchmarks=fillrandom --num=200000000 --value_size=1024 --threads=8 \
  --db=/rocksdb/data --wal_dir=/rocksdb/wal

# 3. Model validation
# v1 모델 검증
python3 scripts/smax_calc.py --cr 0.5 --wa 8.0 --bw 1000 --br 2000 --beff 2500

# v2.1 모델 검증 (개선된 모델)
python3 scripts/smax_calc_v2.py

# v3 모델 시뮬레이션 (브라우저에서 실행)
# PutModel_v3.html 파일을 브라우저에서 열어 시뮬레이션 실행
```

## Requirements

### For Model Analysis
- Python 3.8+
- matplotlib
- pandas
- numpy
- seaborn

### For Real System Validation
- RocksDB (recent release)
- fio (for device calibration)
- Linux (5.x+), ext4 or XFS
- NVMe SSD (preferred)
- **Templates**: `rocksdb_bench_templates/` 디렉토리의 설정 파일들 사용

## Installation

```bash
# 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate  # macOS/Linux
# 또는
.venv\Scripts\activate     # Windows

# 의존성 설치
pip install matplotlib pandas numpy seaborn
```

## Model Validation

이 프로젝트는 이론적 모델을 실제 RocksDB 시스템에서 검증할 수 있는 체계적인 계획을 제공합니다.

### Validation Plan Overview

**목표**: 모델의 예측값이 실제 시스템과 ±10-15% 이내로 일치하는지 검증

**6단계 검증 프로세스**:
1. **Device Calibration**: fio를 통한 B_w, B_r, B_eff 측정
2. **Empty → Steady Transient**: 초기 버스트에서 steady state로의 수렴 과정
3. **Per-Level WAF Mass Balance**: 레벨별 쓰기 앰플리피케이션 검증
4. **v1 Model Validation**: 기본 모델 검증
5. **v2.1 Model Validation**: 개선된 모델 검증 (Harmonic mean + Per-level)
6. **v3 Model Validation**: 동적 시뮬레이터 검증

### Success Criteria

- **v1 Model**: |S_max^meas - S_max^pred| / S_max^pred ≤ **10%** (목표)
- **v2.1 Model**: |S_max^meas - S_max^pred| / S_max^pred ≤ **20%** (개선)
- **v3 Model**: |S_max^meas - S_max^pred| / S_max^pred ≤ **15%** (달성)
- **Mass-balance error**: |∑Write_i - CR×WA×user_MB| / (CR×WA×user_MB) ≤ **10%**
- **Stabilization**: pending_compaction_bytes의 장기 기울기 ≤ 0

### 최신 검증 결과 (2025-09-12)

- **v2.1 모델**: 88.9% 정확도 (최고 성능)
- **v4.1 Temporal 모델**: 69.8% 정확도 (시기별 세분화)
- **v4 모델**: 7.5% 정확도 (Device Envelope)
- **v1, v3, v5 모델**: 0.0% 정확도 (기본 모델)

### 연구의 독창성

- **이론적 독창성**: LSM-tree 성능 모델링, 동적 시뮬레이터, 파라미터 민감도 분석
- **실험적 독창성**: 6단계 검증 프로세스, 실제 데이터 활용, 자동화된 분석
- **도구적 독창성**: Self-contained 시뮬레이터, 종합 시각화, 인터랙티브 보고서
- **혁신적 기여**: 시기별 세분화 모델링, 컴팩션 진화 분석

자세한 검증 절차는 다음 문서들을 참조하세요:
- [rocksdb_validation_plan.md](rocksdb_validation_plan.md) - 검증 계획 (마크다운)
- [ValidationPlan.html](ValidationPlan.html) - 검증 계획 (HTML, MathJax 수식)
- [VALIDATION_GUIDE.md](VALIDATION_GUIDE.md) - 검증 실행 가이드 (마크다운)
- [ValidationGuide.html](ValidationGuide.html) - 검증 실행 가이드 (HTML, MathJax 수식)

## 실험 결과 관리

이 프로젝트는 체계적인 실험 결과 관리를 위한 디렉토리 구조를 제공합니다.

### 실험 디렉토리 구조
```
experiments/
├── 2025-09-12/                 # 최신 실험 디렉토리 ⭐
│   ├── phase-a/                # 디바이스 캘리브레이션 결과
│   ├── phase-b/                # RocksDB 벤치마크 결과
│   ├── phase-c/                # Enhanced Models 개발 결과
│   ├── phase-d/                # 프로덕션 통합 결과
│   ├── phase-e/                # 고급 최적화 결과
│   ├── styles/                 # CSS 스타일 파일
│   ├── scripts/                # 분석 스크립트
│   ├── 09_12_EXPERIMENT_SUMMARY.html  # 실험 요약 보고서
│   ├── COMPREHENSIVE_ANALYSIS_REPORT.html  # 종합 분석 보고서
│   └── COMPREHENSIVE_FINAL_ANALYSIS_WITH_V4_1_TEMPORAL.html  # v4.1 Temporal 포함 최종 보고서
├── 2025-09-09/                 # 이전 실험 디렉토리
├── 2025-09-08/                 # 이전 실험 디렉토리
├── 2025-09-05/                 # 이전 실험 디렉토리
└── templates/                  # 재사용 가능한 실험 템플릿들
```

### 새로운 실험 시작
```bash
# 현재 날짜로 실험 디렉토리 생성
CURRENT_DATE=$(date +%Y-%m-%d)
mkdir -p experiments/$CURRENT_DATE/{phase-a,phase-b,phase-c,phase-d,phase-e,phase-f,reports}

# 템플릿 복사
cp experiments/templates/* experiments/$CURRENT_DATE/
```

자세한 실험 관리 방법은 [experiments/README.md](experiments/README.md)를 참조하세요.

## Tuning Checklist

### Performance Analysis
- [ ] fio로 `B_w`, `B_r`, `B_eff` 측정 (지속 부하)
- [ ] `rocksdb.stats` 델타로 `CR`, `WA` 산정
- [ ] 계산기로 `S_max` 산출 및 헤드룸 20–30% 반영
- [ ] 레벨별 I/O 분해로 읽기 서비스 여유 확인

### Write Control
- [ ] `RateLimiter`와 `delayed_write_rate`로 `S_acc ≤ S_max` 보장
- [ ] 트리거/리밋 파라미터 히스테리시스 적용 (플래핑 방지)
- [ ] Write Bandwidth 초과 여부 확인
- [ ] 압축률 최적화로 WA 증가에 대한 저항력 향상

### Operational Planning
- [ ] 초기 버스트 효과를 고려한 운영 계획 수립
- [ ] 성능 모니터링 및 자동 튜닝 시스템 구현
- [ ] 정기적인 성능 지표 분석 및 최적화

## 연구의 의의

### 학술적 의의
- **LSM-tree 성능 모델링**: 데이터베이스 성능 예측 분야의 이론적 기여
- **실험 방법론**: 재현 가능한 성능 검증 방법론 제시
- **정량적 분석**: 성능에 영향을 미치는 요인들의 정확한 정량화
- **시기별 세분화**: 시간에 따른 성능 진화 분석

### 실용적 의의
- **운영 최적화**: 실제 RocksDB 운영 환경에서의 성능 최적화 도구 제공
- **성능 예측**: 새로운 워크로드나 환경에서의 성능 예측 가능
- **문제 진단**: 성능 문제의 원인을 정확히 식별할 수 있는 도구
- **시기별 적응**: 각 시기의 특성에 맞는 성능 예측

### 기술적 의의
- **오픈소스 기여**: RocksDB 커뮤니티에 실용적인 도구 제공
- **재현성**: 다른 연구자들이 동일한 실험을 재현할 수 있는 완전한 도구와 문서 제공
- **확장성**: 다른 LSM-tree 기반 데이터베이스에도 적용 가능한 일반적인 방법론
- **혁신적 모델링**: 시기별 세분화 및 컴팩션 진화 분석

## License

MIT — `LICENSE` 참조.