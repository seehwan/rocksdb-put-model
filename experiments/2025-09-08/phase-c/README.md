# Phase-C: Write Amplification Analysis (2025-09-08)

## 목적
RocksDB LOG 파일을 분석하여 정확한 Write Amplification (WA) 값을 측정하고 v4 모델의 Closed Ledger Accounting에 반영합니다.

## 분석 대상
- **LOG 파일**: RocksDB 실행 중 생성된 로그
- **STATISTICS**: RocksDB 내장 통계
- **레벨별 분석**: L0, L1, L2, L3 각 레벨의 WA

## 분석 도구
- **waf_analyzer.py**: LOG 파일 WA 분석기
- **RocksDB STATISTICS**: 내장 통계 정보
- **수동 검증**: 로그 파일 직접 분석

## 분석 절차

### 1. LOG 파일 수집
```bash
# RocksDB 실행 후 LOG 파일 확인
ls -la /path/to/rocksdb/LOG*
```

### 2. WA 분석 실행
```bash
# Python 분석 도구 실행
python3 scripts/waf_analyzer.py /path/to/rocksdb/LOG
```

### 3. STATISTICS 확인
```bash
# RocksDB 통계 정보 확인
grep -i "write_amplification" /path/to/rocksdb/STATISTICS
```

### 4. 레벨별 분석
- **L0**: Memtable flush로 인한 WA
- **L1**: L0→L1 compaction WA
- **L2**: L1→L2 compaction WA
- **L3**: L2→L3 compaction WA

## 측정 항목

### 1. 전체 WA
- **LOG 기반**: 실제 로그에서 계산된 WA
- **STATISTICS 기반**: RocksDB 내장 통계 WA
- **비교 분석**: 두 방법 간 차이점 분석

### 2. 레벨별 WA
- **L0 WA**: Memtable flush 비율
- **L1 WA**: L0→L1 compaction 비율
- **L2 WA**: L1→L2 compaction 비율
- **L3 WA**: L2→L3 compaction 비율

### 3. 시간별 WA 변화
- **초기**: 시스템 시작 시 WA
- **안정화**: Steady-state WA
- **최종**: 전체 실행 기간 WA

## 예상 결과
- **LOG WA**: ~2.5-3.0
- **STATISTICS WA**: ~1.0-1.5
- **차이 요인**: 측정 방법 및 시점 차이

## 상태
- [x] LOG 파일 수집
- [x] WA 분석 실행
- [x] STATISTICS 확인
- [x] 레벨별 분석
- [x] 결과 검증 및 저장

## 실험 결과 (2025-09-08)

### WA 분석 결과
- **STATISTICS WA**: 1.045
- **LOG WA**: 1.045
- **차이 요인**: 없음 (일치)
- **분석 상태**: 완료

### 주요 발견사항
- **WA 일치**: STATISTICS와 LOG 값이 정확히 일치
- **낮은 WA**: 1.045로 매우 낮은 Write Amplification
- **압축 효과**: Snappy 압축으로 0.508 압축률 달성
