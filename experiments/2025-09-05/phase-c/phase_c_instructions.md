# Phase-C: Per-Level WAF 분석 실행 가이드

**실행 일시**: 2025-09-05  
**목적**: RocksDB LOG에서 Per-Level Write Amplification 분석  

## 🎯 Phase-C 목표

1. **Per-Level WAF 계산**: 각 레벨별 쓰기 앰플리피케이션 분석
2. **Mass Balance 검증**: 이론적 예측과 실제 측정값 비교
3. **Read Amplification (RA_c) 계산**: 읽기 앰플리피케이션 분석

## 📋 사전 준비사항

### 1. LOG 파일 확인
```bash
# LOG 파일 위치 확인
ls -la ./log/LOG

# LOG 파일 크기 확인
du -h ./log/LOG

# LOG 파일 내용 미리보기
head -20 ./log/LOG
```

### 2. 필요한 스크립트 확인
```bash
# WAF 분석기 확인
ls -la scripts/waf_analyzer.py

# 실행 권한 확인
chmod +x scripts/waf_analyzer.py
```

## 🚀 Phase-C 실행 단계

### 1. WAF 분석 실행
```bash
# 기본 WAF 분석
python3 scripts/waf_analyzer.py --log ./log/LOG \
  --user-mb 1000 --out-dir phase-c-results --plot

# 결과 확인
ls -la phase-c-results/
cat phase-c-results/summary.json
```

### 2. Per-Level Breakdown 실행
```bash
# 레벨별 I/O 분해
python3 scripts/per_level_breakdown.py --log ./log/LOG \
  --output-dir phase-c-results
```

### 3. 결과 분석
```bash
# 생성된 파일들 확인
ls -la phase-c-results/

# CSV 데이터 확인
head -10 phase-c-results/waf_per_level.csv

# 그래프 확인
ls -la phase-c-results/*.png
```

## 📊 예상 결과

### Per-Level WAF 테이블
```
Level                Read(MiB/s)   Write(MiB/s)   %ReadBW  %WriteBW
-------------------------------------------------------------------
L0 (flush)               ___.__        ___.__      __._%      __._%
L1                      ___.__        ___.__      __._%      __._%
L2                      ___.__        ___.__      __._%      __._%
L3                      ___.__        ___.__      __._%      __._%
L4                      ___.__        ___.__      __._%      __._%
L5                      ___.__        ___.__      __._%      __._%
L6                      ___.__        ___.__      __._%      __._%
WAL                       ___.__        ___.__      __._%      __._%
-------------------------------------------------------------------
TOTAL                    ___.__        ___.__      __._%      __._%
```

### Mass Balance 검증
- **예상 총 쓰기**: ___ MB
- **실제 총 쓰기**: ___ MB  
- **오류율**: ___% (≤10% 목표)
- **검증 상태**: [ ] 통과 [ ] 실패

## 🔍 분석 포인트

### 1. 레벨별 특성
- **L0 (Flush)**: Memtable에서의 직접 쓰기
- **L1-L6 (Compaction)**: 레벨별 Compaction 쓰기
- **WAL**: Write-Ahead Log 쓰기

### 2. 병목 지점 식별
- 가장 높은 Write 부하가 있는 레벨
- 가장 높은 Read 부하가 있는 레벨
- 총 I/O 대역폭 사용률

### 3. 예상 vs 실제 비교
- Phase-B에서 측정된 WA (1.02)와 비교
- 모델 가정값과의 차이 분석

## 📁 결과 파일

### 생성될 파일들
- `waf_per_level.csv`: 레벨별 WAF 데이터
- `waf_per_level.png`: 레벨별 WAF 막대 그래프
- `summary.json`: 분석 요약 (JSON 형식)
- `per_level_breakdown.csv`: 레벨별 상세 분석

### 결과 저장 위치
```
experiments/2025-09-05/phase-c/
├── phase_c_instructions.md    # 이 파일
├── phase-c-results/           # 분석 결과
│   ├── waf_per_level.csv
│   ├── waf_per_level.png
│   ├── summary.json
│   └── per_level_breakdown.csv
└── phase_c_summary.md         # 분석 요약 (완료 후 생성)
```

## 🎯 성공 기준

### 정량적 기준
- [ ] Mass Balance 오류율 ≤ 10%
- [ ] Per-Level WAF 데이터 정상 생성
- [ ] 그래프 및 시각화 완료

### 정성적 기준
- [ ] 레벨별 특성 명확히 파악
- [ ] 병목 지점 식별 완료
- [ ] Phase-D 모델 검증을 위한 데이터 준비

## 🚀 다음 단계

Phase-C 완료 후:
1. **Phase-D**: 모델 검증 (S_max 계산 및 검증)
2. **Phase-A**: 디바이스 캘리브레이션 (필요시)
3. **Phase-E**: 민감도 분석 (선택사항)

---
**시작일**: 2025-09-05  
**상태**: [ ] 진행중 [ ] 완료  
**예상 소요시간**: 30-60분
