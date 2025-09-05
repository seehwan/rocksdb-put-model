# Phase-C: Per-Level WAF 분석

**실험 일시**: ___  
**LOG 파일**: ___  
**분석 도구**: waf_analyzer.py  

## 🔍 WAF 분석 실행

### 1. WAF 분석 스크립트 실행
```bash
# WAF 분석 실행
python3 scripts/waf_analyzer.py --log ./log/LOG \
  --user-mb 1000 --out-dir validation_results --plot

# 결과 확인
ls -la validation_results/
cat validation_results/summary.json
```

### 2. Per-Level Breakdown 실행
```bash
# 레벨별 I/O 분해
python3 scripts/per_level_breakdown.py --log ./log/LOG \
  --output-dir validation_results
```

## 📊 분석 결과

### Per-Level WAF 결과
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

### 생성된 그래프
- [ ] `waf_per_level.png` - 레벨별 WAF 막대 그래프
- [ ] `waf_per_level.csv` - 레벨별 WAF 데이터
- [ ] `summary.json` - 분석 요약

## 📈 상세 분석

### 레벨별 특성 분석
- **L0 (Flush)**: Write=___, Read=___
- **L1-L6 (Compaction)**: 평균 Write=___, 평균 Read=___
- **WAL**: Write=___, Read=___

### 병목 지점 식별
- **가장 높은 Write 부하**: Level ___
- **가장 높은 Read 부하**: Level ___
- **총 I/O 대역폭 사용률**: ___%

### 예상 vs 실제 비교
- **예상 WA**: ___ (모델 가정값)
- **실제 WA**: ___ (측정값)
- **차이**: ___%

## 🎯 다음 단계

- [ ] Per-Level WAF 분석 완료
- [ ] Mass Balance 검증 완료
- [ ] 그래프 생성 완료
- [ ] Phase-D: 모델 검증

---

**완료일**: ___  
**상태**: [ ] 진행중 [ ] 완료
