# RocksDB Put-Rate Model

RocksDB의 쓰기 경로(put, flush, compaction)를 정량 모델로 기술하고, steady state에서 가능한 지속 put rate와 레벨별 I/O 대역폭을 계산하는 방법을 정리합니다.

## Repo Layout

```
rocksdb-put-model/
├── README.md                    # 이 파일 (사용법, 요구사항, 빠른 시작)
├── PutModel.md                  # 전체 모델, 수식, 시뮬레이션 코드
├── PutModel.html                # HTML 버전 (MathJax 수식 렌더링)
├── styles.css                   # HTML 스타일시트
├── md_to_html_converter.py     # Markdown → HTML 변환기
├── section_validator.py         # HTML 섹션별 파싱 에러 검증 도구
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

### 0) Generate HTML version with MathJax
```bash
python3 md_to_html_converter.py
```
- `PutModel.md`를 읽어서 `PutModel.html` 생성
- LaTeX 수식을 MathJax로 렌더링 가능하게 변환
- 코드 블록과 테이블을 올바르게 처리

### 1) Validate HTML sections
```bash
python3 section_validator.py
```
- HTML 파일을 섹션별로 분할하여 파싱 에러 검증
- 각 섹션의 코드 태그, 리스트 구조, 수식 태그 문제 식별
- 수정 우선순위 제안

### 2) Run experiments
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

### 3) View results
- **HTML**: `PutModel.html`을 브라우저에서 열기
- **그래프**: `figs/` 폴더의 PNG 파일들
- **수치**: 각 스크립트의 콘솔 출력

## Requirements

- Python 3.8+
- matplotlib
- BeautifulSoup4 (HTML 검증용)

## Installation

```bash
# 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate  # macOS/Linux
# 또는
.venv\Scripts\activate     # Windows

# 의존성 설치
pip install matplotlib beautifulsoup4
```

## HTML Validation Tools

### section_validator.py
HTML 파일을 섹션별로 분할하고 각 섹션의 파싱 에러를 체계적으로 검증합니다.

**주요 기능:**
- HTML 파일을 h2 태그 기준으로 섹션별 분할
- 각 섹션별 코드 태그, 리스트 구조, 수식 태그 검증
- 에러 현황 및 수정 우선순위 제안

**사용법:**
```bash
python3 section_validator.py
```

**출력 예시:**
```
🔍 HTML 파일 섹션별 파싱 에러 검증 시작
📋 총 8개 섹션 발견:
  1. Header
  2. 0) 요약 (Key Takeaways)
  3. 1) 시스템 모델과 기호
  ...

🔍 섹션 검증: 0) 요약 (Key Takeaways)
❌ 4개의 파싱 에러 발견:
  1. 잘못된 코드 태그 순서: </code>...<code> 패턴 발견
  2. 코드 태그가 적절한 부모 요소에 없음
  ...

📊 전체 검증 결과 요약
⚠️  총 15개의 파싱 에러가 발견되었습니다.
```

### md_to_html_converter.py
Markdown 파일을 HTML로 변환하고 기본적인 파싱 에러를 자동으로 수정합니다.

**주요 기능:**
- 코드 태그 중첩 방지
- 연속적인 코드 태그를 div로 분리
- 수식 표현을 $$로 통일
- 리스트 구조 문제 자동 수정

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
- [ ] HTML 검증 도구로 정기적인 파싱 에러 점검
- [ ] 섹션별 수정 우선순위에 따른 체계적 개선

## License

MIT — `LICENSE` 참조.
