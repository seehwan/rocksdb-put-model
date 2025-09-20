# Performance-based Segmentation Analysis Report

## Analysis Time
2025-09-19 19:07:59

## Overview
This report presents the results of performance-based segmentation analysis using RocksDB LOG data.
Unlike time-based segmentation, this approach identifies phases based on actual performance change patterns.

## Segmentation Method
The segmentation is based on:
1. **Performance Change Rate Analysis**: Detecting significant performance transitions
2. **Performance Level Changes**: Identifying major performance drops
3. **Stability Analysis**: Detecting changes in performance variability
4. **Clustering Analysis**: Using K-means clustering on performance characteristics

## Phase Definitions
### Initial Phase
**Description**: 빈 DB에서 빠르게 성능이 변하는 구간

**Timing**:
- Start: 2025-09-12 10:16:04.958286
- End: 2025-09-12 10:24:34.990949
- Duration: 0.1 hours
- Sample Count: 52

**Performance Statistics**:
- Average Rate: 66.0 MB/s
- Performance Range: 46.7 - 280.2 MB/s
- Standard Deviation: 35.5 MB/s
- Coefficient of Variation: 0.538
- Median Rate: 56.7 MB/s

**Performance Trend**:
- Trend Slope: -1.385764
- R² Score: 0.350
- Overall Change: -83.3%
- Average Change Rate: -0.000844
- Change Rate Volatility: 0.006090

**Phase Characteristics**:
- Stability: low
- Trend: decreasing
- Performance Level: high
- Change Intensity: low

---

### Middle Phase
**Description**: 컴팩션이 진행되며 안정화되어 가는 구간

**Timing**:
- Start: 2025-09-12 10:24:34.990949
- End: 2025-09-13 18:11:48.642740
- Duration: 31.8 hours
- Sample Count: 11,443

**Performance Statistics**:
- Average Rate: 16.9 MB/s
- Performance Range: 13.8 - 47.0 MB/s
- Standard Deviation: 4.6 MB/s
- Coefficient of Variation: 0.272
- Median Rate: 15.1 MB/s

**Performance Trend**:
- Trend Slope: -0.001045
- R² Score: 0.562
- Overall Change: -70.4%
- Average Change Rate: -0.000120
- Change Rate Volatility: 0.000597

**Phase Characteristics**:
- Stability: medium
- Trend: stable
- Performance Level: medium
- Change Intensity: low

---

### Final Phase
**Description**: 안정화 구간

**Timing**:
- Start: 2025-09-13 18:11:48.642740
- End: 2025-09-16 10:52:31.138360
- Duration: 64.7 hours
- Sample Count: 23,280

**Performance Statistics**:
- Average Rate: 12.8 MB/s
- Performance Range: 12.1 - 13.8 MB/s
- Standard Deviation: 0.5 MB/s
- Coefficient of Variation: 0.041
- Median Rate: 12.6 MB/s

**Performance Trend**:
- Trend Slope: -0.000077
- R² Score: 0.962
- Overall Change: -12.9%
- Average Change Rate: -0.000006
- Change Rate Volatility: 0.000004

**Phase Characteristics**:
- Stability: high
- Trend: stable
- Performance Level: low
- Change Intensity: low

---

## Key Insights

### Performance-based vs Time-based Segmentation
- **Performance-based**: Segments based on actual performance change patterns
- **Advantage**: More meaningful phase boundaries that reflect actual system behavior
- **Result**: Variable phase durations based on performance characteristics

### Phase Progression Pattern
- **Initial**: high performance, low stability, decreasing trend (Avg: 66.0 MB/s)
- **Middle**: medium performance, medium stability, stable trend (Avg: 16.9 MB/s)
- **Final**: low performance, high stability, stable trend (Avg: 12.8 MB/s)

## Analysis Time
2025-09-19 19:07:59

