# Phase-E: Sensitivity Analysis (2025-09-08)

## 목적
v4 모델의 각 파라미터가 예측 정확도에 미치는 영향을 분석하여 모델의 안정성과 신뢰성을 평가합니다.

## 분석 방법
- **One-at-a-time (OAT)**: 단일 파라미터 변화 분석
- **Correlation Analysis**: 파라미터 간 상관관계 분석
- **Impact Ranking**: 파라미터 영향도 순위 분석

## 분석 파라미터

### 1. 디바이스 파라미터
- **B_w (Write Bandwidth)**: 쓰기 대역폭
- **B_r (Read Bandwidth)**: 읽기 대역폭
- **B_eff (Effective Bandwidth)**: 혼합 I/O 대역폭

### 2. LSM-tree 파라미터
- **WA (Write Amplification)**: 쓰기 증폭
- **CR (Compression Ratio)**: 압축률
- **RA (Read Amplification)**: 읽기 증폭

### 3. 동적 파라미터
- **p_stall**: Stall 확률
- **rho_r**: 읽기 비율
- **concurrency_factor**: 동시성 계수

## 분석 절차

### 1. 파라미터 범위 설정
```python
# 각 파라미터의 변화 범위 설정
parameter_ranges = {
    'B_w': [1000, 2000],      # MiB/s
    'B_r': [2000, 3000],      # MiB/s
    'WA': [1.5, 4.0],         # 배수
    'CR': [0.3, 0.7],         # 비율
    'p_stall': [0.0, 0.5]     # 확률
}
```

### 2. 민감도 분석 실행
```python
# v4 시뮬레이터를 사용한 민감도 분석
from experiments.phase_e.sensitivity_analysis import SensitivityAnalyzer

analyzer = SensitivityAnalyzer(v4_simulator)
sensitivity_results = analyzer.analyze_all_parameters()
```

### 3. 상관관계 분석
```python
# 파라미터 간 상관관계 분석
correlation_matrix = analyzer.calculate_correlations()
```

### 4. 영향도 순위 분석
```python
# 파라미터 영향도 순위 계산
impact_ranking = analyzer.rank_parameter_impact()
```

## 분석 결과

### 1. 민감도 지수
- **높음**: > 0.5 (파라미터 변화가 큰 영향)
- **중간**: 0.1-0.5 (적당한 영향)
- **낮음**: < 0.1 (작은 영향)

### 2. 상관관계
- **강한 상관관계**: |r| > 0.7
- **중간 상관관계**: 0.3 < |r| < 0.7
- **약한 상관관계**: |r| < 0.3

### 3. 영향도 순위
- **1순위**: 가장 영향이 큰 파라미터
- **2순위**: 두 번째로 영향이 큰 파라미터
- **기타**: 나머지 파라미터들

## 시각화

### 1. 민감도 히트맵
- **파라미터별 민감도**: 색상으로 표현
- **변화 범위**: X축으로 표현

### 2. 상관관계 매트릭스
- **파라미터 간 상관관계**: 색상과 숫자로 표현
- **상관관계 강도**: 색상 농도로 표현

### 3. 영향도 차트
- **파라미터별 영향도**: 막대 그래프
- **순위**: 높이 순으로 정렬

## 예상 결과
- **v4 모델 안정성**: 높은 안정성 예상
- **주요 파라미터**: B_w, WA, p_stall
- **상관관계**: B_w와 B_eff 간 강한 상관관계

## 상태
- [ ] 파라미터 범위 설정
- [ ] 민감도 분석 실행
- [ ] 상관관계 분석
- [ ] 영향도 순위 분석
- [ ] 시각화 생성
- [ ] 결과 분석 및 보고서 작성
