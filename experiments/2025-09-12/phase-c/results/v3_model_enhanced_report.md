# Enhanced v3 Model Analysis Report

## Overview
This report presents the enhanced v3 model analysis using RocksDB LOG data for improved accuracy.

## Model Enhancement
- **Base Model**: v3 (Dynamic Compaction-Aware Model)
- **Enhancement**: RocksDB LOG integration
- **Enhancement Factors**: Compaction intensity, Stall analysis, I/O contention, Write amplification

## Results
- **Predicted S_max**: 4.82 ops/sec
- **Actual QPS Mean**: 172.00 ops/sec
- **Error Rate**: 3471.43%
- **Validation Status**: Poor

## Enhancement Factors
- **p_stall_enhanced**: 0.500
- **B_read_enhanced**: 95.200
- **B_write_enhanced**: 96.600
- **compaction_factor**: 0.800
- **stall_factor**: 0.700
- **wa_factor**: 0.482
- **io_contention_factor**: 0.700

## RocksDB LOG Statistics
- **flush_frequency**: 69426.00
- **compaction_frequency**: 143942.50
- **stall_frequency**: 348495.00
- **avg_flush_size**: 60.74
- **avg_compaction_size**: 0.00
- **write_amplification**: 2.07
- **memtable_pressure**: 5.00
- **compaction_intensity**: 1.00
- **stall_duration**: 1.00
- **io_contention**: 1.00

## Visualization
![Enhanced v3 Model Analysis](v3_model_enhanced_analysis.png)

## Analysis Time
2025-09-17 04:26:37
