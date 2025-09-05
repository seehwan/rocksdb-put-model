# RocksDB Put-Rate Model

RocksDB의 쓰기 경로(put, flush, compaction)를 정량 모델로 기술하고, steady state에서 가능한 지속 put rate와 레벨별 I/O 대역폭을 계산하는 방법을 정리합니다. 이론적 모델을 실제 RocksDB 시스템에서 검증할 수 있는 체계적인 실험 계획도 포함합니다.

## Repo Layout

```
rocksdb-put-model/
├── README.md                    # 이 파일 (사용법, 요구사항, 빠른 시작)
├── PutModel.md                  # 전체 모델, 수식, 시뮬레이션 코드
├── [PutModel.html](PutModel.html)                # HTML 버전 (MathJax 수식 렌더링)
├── [ValidationPlan.html](ValidationPlan.html)          # 검증 계획 HTML 버전 (MathJax 수식 렌더링)
├── [ValidationGuide.html](ValidationGuide.html)         # 검증 실행 가이드 HTML 버전 (MathJax 수식 렌더링)
├── VALIDATION_GUIDE.md          # 검증 실행 가이드 (단계별 실행 방법)
├── styles.css                   # HTML 스타일시트
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
└── scripts/                     # Python 스크립트들
    ├── rocksdb_put_viz.py      # 그래프 생성 (matplotlib)
    ├── steady_state_put_estimator.py  # S_max 계산기
    ├── per_level_breakdown.py   # 레벨별 I/O 분해
    ├── transient_depth_analysis.py     # 초기 버스트 분석
    ├── waf_analyzer.py         # RocksDB LOG WAF 분석기
    └── smax_calc.py            # S_max 계산기 (검증용)
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
  - [PutModel.html](PutModel.html) - 이론 모델 (MathJax 수식 렌더링)
  - [ValidationPlan.html](ValidationPlan.html) - 검증 계획 (이론적 방법론)
  - [ValidationGuide.html](ValidationGuide.html) - 검증 실행 가이드 (단계별 실행법)
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

# 2. RocksDB benchmark - 템플릿 사용
# 디렉토리 생성: sudo mkdir -p /rocksdb/data /rocksdb/wal
./db_bench --options_file=rocksdb_bench_templates/db/options-leveled.ini \
  --benchmarks=fillrandom --num=200000000 --value_size=1024 --threads=8

# 3. Model validation
python3 scripts/smax_calc.py --cr 0.5 --wa 8.0 --bw 1000 --br 2000 --beff 2500
```

## Requirements

### For Model Analysis
- Python 3.8+
- matplotlib

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
pip install matplotlib
```

## Model Validation

이 프로젝트는 이론적 모델을 실제 RocksDB 시스템에서 검증할 수 있는 체계적인 계획을 제공합니다.

### Validation Plan Overview

**목표**: 모델의 예측값이 실제 시스템과 ±10-15% 이내로 일치하는지 검증

**5단계 검증 프로세스**:
1. **Device Calibration**: fio를 통한 B_w, B_r, B_eff 측정
2. **Empty → Steady Transient**: 초기 버스트에서 steady state로의 수렴 과정
3. **Per-Level WAF Mass Balance**: 레벨별 쓰기 앰플리피케이션 검증
4. **Envelope Boundary S_max**: 최대 지속 가능한 put rate 검증
5. **Sensitivity Analysis**: 파라미터 변화에 따른 성능 영향 분석

### Success Criteria

- **Envelope error**: |S_max^meas - S_max^pred| / S_max^pred ≤ **10%** (목표)
- **Mass-balance error**: |∑Write_i - CR×WA×user_MB| / (CR×WA×user_MB) ≤ **10%**
- **Stabilization**: pending_compaction_bytes의 장기 기울기 ≤ 0

자세한 검증 절차는 다음 문서들을 참조하세요:
- [rocksdb_validation_plan.md](rocksdb_validation_plan.md) - 검증 계획 (마크다운)
- [ValidationPlan.html](ValidationPlan.html) - 검증 계획 (HTML, MathJax 수식)
- [VALIDATION_GUIDE.md](VALIDATION_GUIDE.md) - 검증 실행 가이드 (마크다운)
- [ValidationGuide.html](ValidationGuide.html) - 검증 실행 가이드 (HTML, MathJax 수식)

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

## License

MIT — `LICENSE` 참조.
