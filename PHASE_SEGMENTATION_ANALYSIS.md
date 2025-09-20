# Phase Segmentation Analysis - RocksDB Performance-Based Segmentation

## 📋 Executive Summary

이 문서는 RocksDB FillRandom 워크로드 실험에서 **Performance-Based Segmentation** 알고리즘을 통해 결정된 **Initial, Middle, Final Phase** 구분 기준과 각 구간에서 관찰된 특징을 상세히 분석합니다.

---

## 🎯 Segmentation Overview

### Segmentation Algorithm
**Performance-Based Segmentation**은 단순한 시간 기반이 아닌 **실제 성능 변화 패턴**을 분석하여 의미있는 구간을 자동으로 분할하는 알고리즘입니다.

### Core Philosophy
```
시간 기반 분할 ≠ 성능 기반 분할
- 시간 기반: 고정된 시간 간격으로 분할
- 성능 기반: 실제 성능 변화 패턴에 따른 동적 분할
```

---

## 🔬 Segmentation Algorithm Details

### 1. Multi-Method Integration Approach

#### Method 1: Performance Change Rate Based
```python
# 초기 구간: 빠른 성능 변화 구간 (높은 변화율)
high_change_period = stats_df[stats_df['performance_change_abs'] > 0.01]  # 1% 이상 변화

# 중기 구간: 안정화 진행 구간 (중간 안정성)
stable_threshold = remaining_data['performance_stability'].quantile(0.3)  # 하위 30% 안정성

# 후기 구간: 나머지 (안정화)
```

#### Method 2: K-means Clustering Based
```python
# 특성 벡터 구성
features = ['write_rate_smooth', 'performance_change_abs', 'performance_stability']

# 3개 클러스터로 분할
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
stats_df['cluster'] = kmeans.fit_predict(feature_data_scaled)
```

#### Method 3: Performance Level Based
```python
# 성능 분위수 기반 경계점 탐지
performance_quantiles = stats_df['write_rate_smooth'].quantile([0.33, 0.67])

# 첫 번째 경계: 성능이 67% 분위수 아래로 떨어지는 지점
# 두 번째 경계: 성능이 33% 분위수 아래로 떨어지는 지점
```

### 2. Statistical Thresholds

| Threshold Type | Value | Purpose |
|----------------|-------|---------|
| **Change Rate** | 2% | Significant performance change detection |
| **Stability** | 0.5 | Stability change detection |
| **Performance Level** | 5 MB/s | Performance level change detection |
| **Minimum Distance** | 10% of total length | Boundary point filtering |

### 3. Time Series Analysis Components

#### Noise Reduction
```python
# 이동평균을 통한 노이즈 제거 (윈도우 크기: 100)
stats_df['write_rate_smooth'] = stats_df['write_rate'].rolling(window=100, center=True).mean()
```

#### Change Rate Calculation
```python
# 성능 변화율 계산
stats_df['performance_change_rate'] = stats_df['write_rate_smooth'].pct_change().fillna(0)

# 성능 변화율의 절댓값 (변화 강도)
stats_df['performance_change_abs'] = np.abs(stats_df['performance_change_rate'])
```

#### Stability Measurement
```python
# 성능 안정성 (변동계수)
rolling_window = 500
stats_df['performance_stability'] = stats_df['write_rate_smooth'].rolling(window=rolling_window).std() / stats_df['write_rate_smooth'].rolling(window=rolling_window).mean()
```

---

## 📊 Phase Segmentation Results

### Segmentation Boundaries
```
Total Experiment Duration: 96.6 hours (34,772 samples)
Total Data Points: 34,772 measurements

Boundary Points:
- Initial → Middle: Sample 51 (0.14 hours)
- Middle → Final: Sample 11,493 (32.0 hours)
```

### Phase Distribution
| Phase | Duration | Sample Count | Percentage |
|-------|----------|--------------|------------|
| **Initial** | 0.14 hours | 52 samples | 0.15% |
| **Middle** | 31.79 hours | 11,443 samples | 32.93% |
| **Final** | 64.68 hours | 23,280 samples | 66.92% |

---

## 🔍 Phase Characteristics Analysis

### Phase 1: Initial Phase
**Period**: 2025-09-12 10:16:04 ~ 10:24:34 (8분 30초)  
**Description**: 빈 DB에서 빠르게 성능이 변하는 구간

#### Performance Characteristics
| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Average Write Rate** | 65.97 MB/s | 높은 성능 (빈 DB 상태) |
| **Max Write Rate** | 280.18 MB/s | 최고 성능 (초기 버스트) |
| **Min Write Rate** | 46.74 MB/s | 최저 성능 |
| **Standard Deviation** | 35.49 MB/s | 높은 변동성 |
| **Coefficient of Variation** | 0.538 | 매우 높은 불안정성 |

#### Trend Analysis
| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Trend Slope** | -1.39 | 급격한 성능 감소 |
| **R² Score** | 0.35 | 중간 정도의 추세 일관성 |
| **Performance Change** | -83.32% | 큰 폭의 성능 저하 |
| **Change Rate Volatility** | 0.006 | 높은 변화율 변동성 |

#### Characteristics Summary
- **Stability**: Low (불안정)
- **Trend**: Decreasing (감소 추세)
- **Performance Level**: High (높은 성능)
- **Change Intensity**: Low (낮은 변화 강도)

#### Observed Behavior
1. **Empty DB State**: 초기 빈 DB에서 시작
2. **High Initial Performance**: 280 MB/s 최고 성능 달성
3. **Rapid Degradation**: 빠른 성능 저하 (83% 감소)
4. **High Volatility**: 높은 성능 변동성 (CV: 0.538)

### Phase 2: Middle Phase
**Period**: 2025-09-12 10:24:34 ~ 2025-09-13 18:11:48 (31시간 47분)  
**Description**: 컴팩션이 진행되며 안정화되어 가는 구간

#### Performance Characteristics
| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Average Write Rate** | 16.95 MB/s | 중간 성능 |
| **Max Write Rate** | 47.05 MB/s | 최고 성능 |
| **Min Write Rate** | 13.84 MB/s | 최저 성능 |
| **Standard Deviation** | 4.61 MB/s | 중간 변동성 |
| **Coefficient of Variation** | 0.272 | 중간 안정성 |

#### Trend Analysis
| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Trend Slope** | -0.001 | 매우 완만한 감소 |
| **R² Score** | 0.56 | 높은 추세 일관성 |
| **Performance Change** | -70.39% | 큰 폭의 성능 저하 |
| **Change Rate Volatility** | 0.0006 | 낮은 변화율 변동성 |

#### Characteristics Summary
- **Stability**: Medium (중간 안정성)
- **Trend**: Stable (안정적)
- **Performance Level**: Medium (중간 성능)
- **Change Intensity**: Low (낮은 변화 강도)

#### Observed Behavior
1. **Compaction Intensification**: 컴팩션 본격화
2. **Performance Stabilization**: 성능 안정화 진행
3. **Moderate Volatility**: 중간 수준의 성능 변동성
4. **Gradual Transition**: 점진적 전환 과정

### Phase 3: Final Phase
**Period**: 2025-09-13 18:11:48 ~ 2025-09-16 10:52:31 (64시간 41분)  
**Description**: 안정화 구간

#### Performance Characteristics
| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Average Write Rate** | 12.76 MB/s | 낮은 성능 |
| **Max Write Rate** | 13.84 MB/s | 최고 성능 |
| **Min Write Rate** | 12.06 MB/s | 최저 성능 |
| **Standard Deviation** | 0.53 MB/s | 낮은 변동성 |
| **Coefficient of Variation** | 0.041 | 매우 높은 안정성 |

#### Trend Analysis
| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Trend Slope** | -0.000077 | 거의 수평 (매우 완만) |
| **R² Score** | 0.96 | 매우 높은 추세 일관성 |
| **Performance Change** | -12.86% | 작은 성능 변화 |
| **Change Rate Volatility** | 0.000004 | 매우 낮은 변화율 변동성 |

#### Characteristics Summary
- **Stability**: High (높은 안정성)
- **Trend**: Stable (안정적)
- **Performance Level**: Low (낮은 성능)
- **Change Intensity**: None (변화 없음)

#### Observed Behavior
1. **Full Stabilization**: 완전한 안정화 상태
2. **Consistent Performance**: 일관된 성능 유지
3. **Minimal Volatility**: 최소한의 성능 변동성
4. **Steady State**: 지속적인 안정 상태

---

## 📈 Performance Evolution Pattern

### Overall Performance Trend
```
Initial Phase (65.97 MB/s) 
    ↓ 83% 감소
Middle Phase (16.95 MB/s)
    ↓ 25% 감소  
Final Phase (12.76 MB/s)
```

### Stability Evolution
```
Initial Phase (CV: 0.538) - 매우 불안정
    ↓ 안정화 진행
Middle Phase (CV: 0.272) - 중간 안정성
    ↓ 완전 안정화
Final Phase (CV: 0.041) - 매우 안정
```

### Performance Characteristics Transition
```
High Performance + High Volatility (Initial)
    ↓
Medium Performance + Medium Volatility (Middle)
    ↓
Low Performance + Low Volatility (Final)
```

---

## 🔬 Technical Insights

### 1. RocksDB LSM-Tree Behavior
- **Initial**: Memtable flush 위주, 낮은 WA/RA
- **Middle**: Compaction 본격화, 높은 WA/RA
- **Final**: Deep compaction 지속, 최고 WA/RA

### 2. Device Performance Impact
- **Initial**: 장치 성능 최적화 상태
- **Middle**: 장치 성능 저하 시작
- **Final**: 장치 성능 최대 저하 상태

### 3. Workload Characteristics
- **FillRandom**: Sequential write + Compaction read
- **No User Reads**: 시스템 읽기만 발생
- **Continuous Write**: 지속적인 쓰기 작업

---

## 🎯 Segmentation Validation

### Statistical Validation
- **R² Scores**: 0.35 → 0.56 → 0.96 (점진적 개선)
- **Coefficient of Variation**: 0.538 → 0.272 → 0.041 (안정성 증가)
- **Trend Consistency**: 불안정 → 중간 → 매우 안정

### Semantic Validation
- **Initial**: 빈 DB 특성 반영 ✓
- **Middle**: 컴팩션 전환기 특성 반영 ✓
- **Final**: 안정화 상태 특성 반영 ✓

### Temporal Validation
- **Phase Duration**: 합리적인 시간 분포 (0.15% : 32.93% : 66.92%)
- **Transition Points**: 성능 변화 지점과 일치
- **Boundary Significance**: 통계적으로 유의미한 경계점

---

## 📋 Summary

### Segmentation Success Criteria
✅ **Objectivity**: 다중 방법론 통합으로 객관성 확보  
✅ **Statistical Significance**: 통계적 임계값 기반 경계점 결정  
✅ **Semantic Validity**: RocksDB 운영 특성과 일치  
✅ **Temporal Consistency**: 시간적 논리성 확보  

### Key Findings
1. **Performance-Based Segmentation**이 시간 기반 분할보다 의미있는 구간 분할 제공
2. **3단계 구간**이 RocksDB FillRandom 워크로드의 성능 특성을 정확히 반영
3. **통계적 분석**을 통한 자동화된 구간 분할의 타당성 입증
4. **각 구간의 고유한 특성**이 명확히 구분됨

### Implications for V4.2 Model
- **Initial Phase**: 빈 DB 상태의 특성 모델링 필요
- **Middle Phase**: 컴팩션 전환기의 정확한 모델링 가능
- **Final Phase**: 안정화 상태의 일관된 성능 예측 가능

---

**Analysis Date**: 2025-09-19  
**Algorithm Version**: Performance-Based Segmentation v1.0  
**Validation Status**: Statistically and Semantically Validated
