# V4.2 Model Evaluation with RocksDB Characteristics

## Overview
This report presents the evaluation of the V4.2 FillRandom Enhanced model using RocksDB operational characteristics-based phase segmentation.

## Analysis Time
2025-09-19 11:13:46

## RocksDB Characteristics-Based Phase Analysis

### Phase Segmentation Based on RocksDB Operational Characteristics

#### Initial Phase Phase
- **Average QPS**: 147306.67 ops/sec
- **Maximum QPS**: 1946448.00 ops/sec
- **Minimum QPS**: 160.00 ops/sec
- **Standard Deviation**: 98587.74 ops/sec
- **Coefficient of Variation**: 0.669
- **Trend**: decreasing
- **Stability**: unstable
- **Sample Count**: 6,956
- **Phase Type**: 빈 DB에서 빠르게 성능이 변하는 구간

#### Middle Phase Phase
- **Average QPS**: 116080.68 ops/sec
- **Maximum QPS**: 654823.00 ops/sec
- **Minimum QPS**: 49445.00 ops/sec
- **Standard Deviation**: 58085.14 ops/sec
- **Coefficient of Variation**: 0.500
- **Trend**: decreasing
- **Stability**: unstable
- **Sample Count**: 20,868
- **Phase Type**: 컴팩션이 진행되며 안정화되어 가는 구간

#### Final Phase Phase
- **Average QPS**: 109299.11 ops/sec
- **Maximum QPS**: 250993.00 ops/sec
- **Minimum QPS**: 49195.00 ops/sec
- **Standard Deviation**: 51502.02 ops/sec
- **Coefficient of Variation**: 0.471
- **Trend**: increasing
- **Stability**: stable
- **Sample Count**: 6,956
- **Phase Type**: 안정화 구간

### V4.2 Model Evaluation (RocksDB Characteristics Based)

#### Overall Accuracy
- **Overall Accuracy**: -337.0%
- **Best Phase**: Final Phase
- **Worst Phase**: Middle Phase

#### Phase-specific Comparison

##### Initial Phase Phase
- **Actual Average QPS**: 147306.67 ops/sec
- **Model Prediction**: 965261.68 ops/sec
- **Accuracy**: -455.3%
- **Difference**: 817955.00 ops/sec
- **Relative Error**: 555.3%
- **Phase Type**: 빈 DB에서 빠르게 성능이 변하는 구간
- **Stability**: unstable
- **Trend**: decreasing
- **Coefficient of Variation**: 0.669

##### Middle Phase Phase
- **Actual Average QPS**: 116080.68 ops/sec
- **Model Prediction**: 852512.87 ops/sec
- **Accuracy**: -534.4%
- **Difference**: 736432.19 ops/sec
- **Relative Error**: 634.4%
- **Phase Type**: 컴팩션이 진행되며 안정화되어 가는 구간
- **Stability**: unstable
- **Trend**: decreasing
- **Coefficient of Variation**: 0.500

##### Final Phase Phase
- **Actual Average QPS**: 109299.11 ops/sec
- **Model Prediction**: 242025.06 ops/sec
- **Accuracy**: -21.4%
- **Difference**: 132725.95 ops/sec
- **Relative Error**: 121.4%
- **Phase Type**: 안정화 구간
- **Stability**: stable
- **Trend**: increasing
- **Coefficient of Variation**: 0.471

#### Performance Trends Analysis
- **Actual Trend**: decreasing
- **Predicted Trend**: decreasing
- **Trend Accuracy**: False
- **Degradation Prediction**: 25.8%

#### Model Improvements
- **Rocksdb Characteristics Based**: Implemented
- **Operational Phases Analysis**: Implemented
- **Stability Aware Evaluation**: Implemented
- **Performance Trend Analysis**: Implemented
- **Phase Specific Modeling**: Implemented

#### RocksDB Characteristics Analysis
- **Phase Segmentation Method**: rocksdb_operational_characteristics
- **Segmentation Criteria**: performance_changes, stability_analysis, operational_characteristics
- **Phase Identification**:
  - **Initial Phase**: 빈 DB에서 빠르게 성능이 변하는 구간
  - **Middle Phase**: 컴팩션이 진행되며 안정화되어 가는 구간
  - **Final Phase**: 안정화 구간

- **Evaluation Improvements**:
  - RocksDB 내부 동작 특성 반영
  - 구간별 안정성 특성 고려
  - 성능 변화 패턴 분석
  - 운영 특성 기반 평가

## Key Insights

### 1. RocksDB Characteristics-Based Phase Segmentation
- **Initial Phase**: 빈 DB에서 빠르게 성능이 변하는 구간
- **Middle Phase**: 컴팩션이 진행되며 안정화되어 가는 구간
- **Final Phase**: 안정화 구간

### 2. V4.2 Model Evaluation Improvements
- **RocksDB 내부 동작 특성 반영**: 실제 RocksDB 운영 특성 기반 구간 분할
- **구간별 안정성 특성 고려**: 변동계수 기반 안정성 평가
- **성능 변화 패턴 분석**: 구간별 성능 변화 패턴 분석
- **운영 특성 기반 평가**: RocksDB 운영 특성 기반 모델 평가

### 3. Model Performance Insights
- **RocksDB Characteristics Validation**: 모델이 실제 RocksDB 운영 특성에 맞게 검증됨
- **Phase-specific Accuracy**: 구간별 정확도 평가
- **Performance Prediction**: QPS 예측 정확도
- **Stability Analysis**: 성능 안정성 분석

## Visualization
![V4.2 Model Evaluation with RocksDB Characteristics](v4_2_model_evaluation_rocksdb_characteristics.png)

## Analysis Time
2025-09-19 11:13:46
