# LOG-based Phase Analysis - Detailed Report

## Analysis Time
2025-09-19 11:37:40

## Overview
This report provides a detailed analysis of RocksDB performance phases based on LOG data.

## Phase Analysis Results

### Initial Phase

**Basic Statistics:**
- Duration: 32.2 hours
- Sample Count: 11,592
- Start Time: 2025-09-12 10:16:04.958286
- End Time: 2025-09-13 18:28:08.810658

**Performance Statistics:**
- Average Rate: 17.1 MB/s
- Maximum Rate: 280.2 MB/s
- Minimum Rate: 13.8 MB/s
- Standard Deviation: 6.1 MB/s
- Coefficient of Variation: 0.356
- Median Rate: 15.1 MB/s
- Q25 Rate: 14.3 MB/s
- Q75 Rate: 17.6 MB/s

**Performance Trend:**
- Trend Slope: -0.001131
- Trend R²: 0.385
- Performance Change: -95.1%

**Compaction Statistics:**
- Total Compactions: 0
- Compaction Rate: 0.0 per hour

**Flush Statistics:**
- Total Flushes: 53053
- Flush Rate: 1647.6 per hour
- Flush by Type: {'finish': 26527, 'start': 26526}

**Phase Characteristics:**
- Stability: low
- Trend: stable
- Performance Level: medium
- Activity Level: medium

---

### Middle Phase

**Basic Statistics:**
- Duration: 32.2 hours
- Sample Count: 11,591
- Start Time: 2025-09-13 18:28:18.812315
- End Time: 2025-09-15 02:40:21.239054

**Performance Statistics:**
- Average Rate: 13.2 MB/s
- Maximum Rate: 13.8 MB/s
- Minimum Rate: 12.6 MB/s
- Standard Deviation: 0.4 MB/s
- Coefficient of Variation: 0.027
- Median Rate: 13.2 MB/s
- Q25 Rate: 12.9 MB/s
- Q75 Rate: 13.5 MB/s

**Performance Trend:**
- Trend Slope: -0.000108
- Trend R²: 0.997
- Performance Change: -8.7%

**Compaction Statistics:**
- Total Compactions: 0
- Compaction Rate: 0.0 per hour

**Flush Statistics:**
- Total Flushes: 43796
- Flush Rate: 1360.1 per hour
- Flush by Type: {'start': 21898, 'finish': 21898}

**Phase Characteristics:**
- Stability: high
- Trend: stable
- Performance Level: low
- Activity Level: low

---

### Final Phase

**Basic Statistics:**
- Duration: 32.2 hours
- Sample Count: 11,590
- Start Time: 2025-09-15 02:40:31.241258
- End Time: 2025-09-16 10:52:31.138360

**Performance Statistics:**
- Average Rate: 12.3 MB/s
- Maximum Rate: 12.6 MB/s
- Minimum Rate: 12.1 MB/s
- Standard Deviation: 0.2 MB/s
- Coefficient of Variation: 0.013
- Median Rate: 12.3 MB/s
- Q25 Rate: 12.2 MB/s
- Q75 Rate: 12.4 MB/s

**Performance Trend:**
- Trend Slope: -0.000048
- Trend R²: 0.993
- Performance Change: -4.5%

**Compaction Statistics:**
- Total Compactions: 0
- Compaction Rate: 0.0 per hour

**Flush Statistics:**
- Total Flushes: 41960
- Flush Rate: 1303.1 per hour
- Flush by Type: {'start': 20980, 'finish': 20980}

**Phase Characteristics:**
- Stability: high
- Trend: stable
- Performance Level: low
- Activity Level: low

---

## Key Insights

### Phase Progression Pattern
The analysis reveals a clear progression pattern across the three phases:

1. **Initial Phase**: High variability, decreasing performance
2. **Middle Phase**: Stabilizing performance, moderate activity
3. **Final Phase**: Stable performance, low activity

### Performance Characteristics
- **Initial**: medium performance, low stability
- **Middle**: low performance, high stability
- **Final**: low performance, high stability

### Activity Patterns
- **Initial**: medium activity level
- **Middle**: low activity level
- **Final**: low activity level

## Analysis Time
2025-09-19 11:37:40

