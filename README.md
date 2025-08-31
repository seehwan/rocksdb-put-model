# RocksDB Put-Rate Model

RocksDB의 쓰기 경로(put, flush, compaction)를 정량 모델로 기술하고, steady state에서 가능한 지속 put rate와 레벨별 I/O 대역폭을 계산하는 방법을 정리합니다.

## Repo Layout

```
rocksdb-put-model/
├── README.md                    # 이 파일 (사용법, 요구사항, 빠른 시작)
├── PutModel.md                  # 전체 모델, 수식, 시뮬레이션 코드
├── PutModel.html                # HTML 버전 (MathJax 수식 렌더링)
├── styles.css                   # HTML 스타일시트
├── figs/                        # 생성된 그래프들
│   ├── depth_summary.png        # 초기 버스트 vs Steady State
│   ├── per_level_reads.png      # 레벨별 읽기 I/O
│   ├── per_level_writes.png     # 레벨별 쓰기 I/O
│   └── smax_vs_WA.png          # S_max vs Write Amplification
└── scripts/                     # Python 스크립트들
    ├── rocksdb_put_viz.py      # 그래프 생성 (matplotlib)
    ├── steady_state_put_estimator.py  # S_max 계산기
    ├── per_level_breakdown.py   # 레벨별 I/O 분해
    └── transient_depth_analysis.py     # 초기 버스트 분석
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
- **HTML**: `PutModel.html`을 브라우저에서 열기
- **그래프**: `figs/` 폴더의 PNG 파일들
- **수치**: 각 스크립트의 콘솔 출력

## Requirements

- Python 3.8+
- matplotlib

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
