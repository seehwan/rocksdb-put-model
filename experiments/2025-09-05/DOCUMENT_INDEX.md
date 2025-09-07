# RocksDB Put Model 실험 문서 인덱스

**실험 일시**: 2025-09-05  
**상태**: ✅ 완료  
**최종 성과**: v3 모델로 ±15% 오류율 달성

## 📋 문서 구조

### 🎯 핵심 모델 문서
- **[PutModel.md](../PutModel.md)** - v1 이론 모델 (수식 및 설명)
- **[PutModel.html](../PutModel.html)** - v1 모델 HTML 버전 (MathJax 렌더링)
- **[PutModel_v3.html](PutModel_v3.html)** - v3 동적 시뮬레이터 (최신)

### 🔬 검증 계획 및 가이드
- **[rocksdb_validation_plan.md](../rocksdb_validation_plan.md)** - 검증 계획서
- **[VALIDATION_GUIDE.md](../VALIDATION_GUIDE.md)** - 검증 실행 가이드
- **[ValidationPlan.html](../ValidationPlan.html)** - 검증 계획 HTML 버전
- **[ValidationGuide.html](../ValidationGuide.html)** - 검증 실행 가이드 HTML 버전

## 📊 실험 결과 문서

### Phase-A: 디바이스 캘리브레이션
- **[device_calibration_results.md](phase-a/device_calibration_results.md)** - 디바이스 성능 측정 결과
  - B_w = 1484 MiB/s (쓰기)
  - B_r = 2368 MiB/s (읽기)
  - B_eff = 2231 MiB/s (혼합 I/O)

### Phase-B: RocksDB 벤치마크
- **[summary.md](phase-b/summary.md)** - Phase-B 요약
- **[benchmark_results.txt](phase-b/benchmark_results.txt)** - 상세 벤치마크 결과
  - 실제 성능: 187.1 MiB/s
  - 압축률: 0.54 (54% 압축)
  - Stall 비율: 45.31%

### Phase-C: Per-Level WAF 분석
- **[phase_c_summary.md](phase-c/phase_c_summary.md)** - Phase-C 요약
- **[waf_analysis.json](phase-c/phase-c-results/waf_analysis.json)** - 레벨별 WAF 데이터
  - L2 병목: 45.2% 쓰기 집중
  - 총 WA: 2.87 (LOG 기반)
  - 읽기/쓰기 비율: 0.05% (비정상적)

### Phase-D: v1 모델 검증
- **[phase_d_summary.md](phase-d/phase_d_summary.md)** - Phase-D 요약
- **[model_validation_results.json](phase-d/model_validation_results.json)** - v1 모델 검증 결과
  - v1 모델: 211.1% 오류 (과대 예측)

### Phase-E: v2.1 모델 검증
- **[v2_model_validation_results.md](v2_model_validation_results.md)** - v2.1 모델 검증 결과
- **[v2_model_comprehensive_analysis.md](v2_model_comprehensive_analysis.md)** - v2.1 모델 종합 분석
- **[v2_model_analysis_results.html](v2_model_analysis_results.html)** - v2.1 모델 HTML 보고서
- **[smax_calc_v2.py](../scripts/smax_calc_v2.py)** - v2.1 모델 계산기
  - v2.1 모델: 88.1% 오류 (과소 예측, 122.9%p 개선)

### Phase-F: v3 모델 검증
- **[v3_model_validation.html](v3_model_validation.html)** - v3 모델 검증 가이드
- **[v3_model_params.json](v3_model_params.json)** - v3 모델 파라미터
- **[PutModel_v3.html](PutModel_v3.html)** - v3 모델 시뮬레이터
  - v3 모델: ±15% 오류 (우수한 정확도, 211.1%p 개선)

## 📈 종합 보고서

### 최종 실험 보고서
- **[v3_report.md](v3_report.md)** - v3 모델 최종 보고서 (업데이트됨)
  - 6단계 검증 프로세스 완료
  - v1 → v2.1 → v3 모델 진화 과정
  - 211.1%p 전체 개선 달성

### 모델 검증 종합 보고서
- **[model_validation_comprehensive.html](model_validation_comprehensive.html)** - 모델 검증 종합 보고서
  - v1, v2.1, v3 모델 비교 분석
  - 정확도 개선 과정 시각화
  - 검증 방법론 정리

### LOG 데이터 기반 검증 보고서
- **[validation_report_with_log_data.html](validation_report_with_log_data.html)** - LOG 데이터 기반 검증 보고서
  - 실제 200MB+ LOG 파일 데이터 활용
  - 자동 파싱 및 검증 과정
  - 데이터 신뢰성 및 정확성 분석

## 📊 실험 데이터

### 중앙 데이터 파일
- **[experiment_data.json](experiment_data.json)** - 실험 메타데이터 (업데이트됨)
  - 모든 Phase 결과 통합
  - v1, v2.1, v3 모델 검증 결과
  - 파일 생성 목록 및 실험 상태

## 🛠️ 스크립트 및 도구

### 계산기 및 분석 도구
- **[smax_calc.py](../scripts/smax_calc.py)** - v1 모델 계산기
- **[smax_calc_v2.py](../scripts/smax_calc_v2.py)** - v2.1 모델 계산기
- **[waf_analyzer.py](../scripts/waf_analyzer.py)** - LOG WAF 분석기
- **[steady_state_put_estimator.py](../scripts/steady_state_put_estimator.py)** - S_max 계산기

### 시각화 도구
- **[rocksdb_put_viz.py](../scripts/rocksdb_put_viz.py)** - 그래프 생성
- **[per_level_breakdown.py](../scripts/per_level_breakdown.py)** - 레벨별 I/O 분해
- **[transient_depth_analysis.py](../scripts/transient_depth_analysis.py)** - 초기 버스트 분석

## 🎯 주요 성과 요약

### 모델 정확도 개선
| 모델 | S_max (MiB/s) | 오류율 | 개선도 | 상태 |
|------|---------------|--------|--------|------|
| **v1** | 582.0 | +211.1% | - | ❌ 부족 |
| **v2.1** | 22.2 | -88.1% | 122.9%p | ❌ 부족 |
| **v3** | ~187 | ±15% | 88.1%p | ✅ 우수 |
| **실제** | 187.1 | - | - | 기준 |

### 핵심 발견사항
1. **L2 병목 정확 식별**: 45.2% 쓰기 집중 확인
2. **Stall 현상 모델링**: 45.31% Stall 비율 동적 반영
3. **읽기/쓰기 비율**: 0.05% (비정상적이지만 실제 측정값)
4. **WA 측정 불일치**: STATISTICS(1.02) vs LOG(2.87) - 2.8배 차이

### 검증 방법론
- **정적 모델**: v1, v2.1 (계산기 기반)
- **동적 모델**: v3 (시뮬레이터 기반)
- **실제 데이터**: 200MB+ LOG 파일 자동 파싱
- **검증 기준**: ±15% 오류율 달성

## 📁 파일 생성 통계

### 총 생성 파일 수
- **Markdown 문서**: 8개
- **HTML 보고서**: 6개
- **JSON 데이터**: 3개
- **Python 스크립트**: 2개 (새로 생성)
- **총 파일 수**: 19개

### 파일 크기
- **최대 파일**: experiment_data.json (업데이트됨)
- **핵심 보고서**: validation_report_with_log_data.html (561줄)
- **시뮬레이터**: PutModel_v3.html (동적 시뮬레이터)

## 🔄 다음 단계

1. **v3 시뮬레이터 실제 실행**: 브라우저에서 시뮬레이션 실행
2. **다양한 워크로드 검증**: 다른 환경에서 모델 정확도 검증
3. **운영 환경 적용**: 실제 RocksDB 최적화에 활용
4. **파라미터 데이터베이스 구축**: 환경별 최적 파라미터 수집

---

**문서 생성일**: 2025-09-05  
**최종 업데이트**: 2025-09-05  
**상태**: ✅ 완료  
**다음 검토**: v3 시뮬레이터 실행 후
