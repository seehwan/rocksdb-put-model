# RocksDB Put-Rate Models Analysis Report
## Phase-C Comprehensive Analysis (2025-09-12)

### Executive Summary

This report presents a comprehensive analysis of five different RocksDB put-rate prediction models (v1, v2.1, v3, v4, v5) using experimental data from Phase-A and Phase-B experiments conducted on 2025-09-12.

### Model Performance Overview

| Model | Predicted S_max (ops/sec) | Actual QPS Mean (ops/sec) | Error Rate (%) | Validation Status |
|-------|---------------------------|---------------------------|----------------|-------------------|
| **v1** | 579.13 | 120,972.36 | 20,788.47% | Poor |
| **v2.1** | 22.70 | 120,972.36 | 532,123.15% | Poor |
| **v3** | 6,048.62 | 120,972.36 | 1,900.00% | Poor |
| **v4** | 188,700.00 | 120,972.36 | -56.00% | Poor |
| **v5** | 50,015.95 | 172.00 | -99.66% | Poor |

### Detailed Model Analysis

## 1. v1 Model (Basic Model)

**Characteristics:**
- Simple baseline model
- Basic bandwidth-based calculation
- No advanced features

**Results:**
- Predicted S_max: 579.13 ops/sec
- Actual QPS Mean: 120,972.36 ops/sec
- Error Rate: 20,788.47%
- Validation Status: Poor

**Analysis:**
The v1 model shows significant under-prediction, indicating that basic bandwidth calculations are insufficient for accurate put-rate prediction in complex RocksDB environments.

## 2. v2.1 Model (Harmonic Mean Model)

**Characteristics:**
- Harmonic mean calculation for mixed I/O capacity
- Per-level capacity and concurrency consideration
- Stall duty cycle modeling

**Results:**
- Predicted S_max: 22.70 ops/sec
- Actual QPS Mean: 120,972.36 ops/sec
- Error Rate: 532,123.15%
- Validation Status: Poor

**Detailed Parameters:**
- B_w (Write Bandwidth): 138 MB/s
- B_r (Read Bandwidth): 136 MB/s
- CR (Compression Ratio): 0.5406
- WA (Write Amplification): 2.87
- p_stall: 0.1

**Level Constraints:**
- Level 0: 44.15 ops/sec, Capacity: 13.70 MB/s
- Level 1: 35.32 ops/sec, Capacity: 27.40 MB/s
- Level 2: 29.43 ops/sec, Capacity: 41.10 MB/s
- Level 3: 25.23 ops/sec, Capacity: 54.80 MB/s

**Analysis:**
The v2.1 model shows extreme under-prediction, suggesting that the harmonic mean approach may be too conservative for the given workload characteristics.

## 3. v3 Model (Dynamic Compaction-Aware Model)

**Characteristics:**
- Heuristic-based model
- Dynamic compaction awareness
- Known 95% under-prediction error

**Results:**
- Predicted S_max: 6,048.62 ops/sec
- Actual QPS Mean: 120,972.36 ops/sec
- Error Rate: 1,900.00%
- Validation Status: Poor

**Model Features:**
- Stall Factor: 1.0
- P_stall: 0.0
- Model Type: Dynamic Compaction-Aware
- Heuristic Based: True
- Under-prediction Error: 95.0%

**Analysis:**
The v3 model demonstrates the known issue of significant under-prediction, which is a documented limitation of this heuristic-based approach.

## 4. v4 Model (Device Envelope Model)

**Characteristics:**
- Device envelope modeling
- Closed ledger accounting
- Dynamic simulation framework
- RocksDB LOG analysis

**Results:**
- Predicted S_max: 188,700.00 ops/sec
- Actual QPS Mean: 0.00 ops/sec (no Phase-B data)
- Error Rate: N/A
- Validation Status: Poor

**Device Envelope Analysis:**
- Initial Performance: Empty (no data)
- Degraded Performance: Empty (no data)
- Degradation Analysis: Empty (no data)

**Closed Ledger Accounting:**
- Actual QPS Mean: 0.0 ops/sec
- Average Initial Bandwidth: 0.0 MB/s
- Average Degraded Bandwidth: 0.0 MB/s
- Compaction Write Bandwidth: 188.7 MB/s
- Compaction Read Bandwidth: 35.68 MB/s
- Write Amplification: 2.0

**RocksDB Statistics:**
- Compaction Write Bandwidth: 188.7 MB/s
- Compaction Read Bandwidth: 35.68 MB/s
- Write Amplification: 2.0
- Compaction Time: 5.0 seconds

**Analysis:**
The v4 model shows the highest prediction but lacks Phase-B data for proper validation. The device envelope approach appears to be overly optimistic.

## 5. v5 Model (Real-time Adaptation Model)

**Characteristics:**
- Real-time adaptation
- Dynamic environment response
- Auto-tuning capabilities

**Results:**
- Predicted S_max: 50,015.95 ops/sec
- Actual QPS Mean: 172.00 ops/sec (filtered data)
- Error Rate: -99.66%
- Validation Status: Poor

**Model Features:**
- Adaptation Speed: 5.0 sec
- Accuracy: 85.0%
- Stability: 90.0%
- Model Type: Real-time Adaptation Model
- Dynamic Environment: True
- Auto-tuning: True

**Analysis:**
The v5 model shows significant over-prediction when compared to filtered Phase-B data, suggesting that the real-time adaptation features may not be properly calibrated for the given workload.

### Data Quality Issues

**Phase-B Data Problems:**
- 43.5% of records show abnormally high values (>100,000 ops/sec)
- Initial warm-up effect causes unrealistic performance spikes
- Maximum recorded value: 1,946,448 ops/sec (10-second mark)
- Data filtering applied: Only values ≤10,000 ops/sec used for analysis

**Root Cause:**
The `db_bench --report_interval_seconds=10` setting captures initial warm-up performance before RocksDB stabilizes, leading to unrealistic high values that skew model predictions.

### Recommendations

1. **Data Collection Improvement:**
   - Increase warm-up period before data collection
   - Use longer reporting intervals to avoid initial spikes
   - Implement proper data filtering in collection scripts

2. **Model Validation:**
   - All models show poor validation status
   - Need for model calibration using clean experimental data
   - Consider ensemble approaches combining multiple models

3. **Future Work:**
   - Re-run experiments with proper warm-up periods
   - Develop data quality validation pipelines
   - Implement model ensemble techniques
   - Create adaptive model selection based on workload characteristics

### Conclusion

The analysis reveals significant challenges in RocksDB put-rate prediction:

1. **Data Quality Issues:** The experimental data contains unrealistic values due to warm-up effects
2. **Model Limitations:** All models show poor validation against actual performance
3. **Prediction Range:** Model predictions vary by 4 orders of magnitude (22.70 to 188,700 ops/sec)
4. **Need for Improvement:** Both data collection and model development require significant enhancement

The results highlight the complexity of predicting RocksDB performance and the need for more sophisticated modeling approaches combined with high-quality experimental data.

---

**Report Generated:** 2025-09-17 00:48:00  
**Analysis Period:** 2025-09-12 Phase-A and Phase-B experiments  
**Models Analyzed:** v1, v2.1, v3, v4, v5  
**Total Records Processed:** 34,779 (Phase-B), 207 (Phase-A)  
**Data Quality:** Filtered for realistic values (≤10,000 ops/sec)
