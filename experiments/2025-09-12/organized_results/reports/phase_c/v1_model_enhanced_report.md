# Enhanced v1 Model Analysis Report

## Overview
This report presents the enhanced v1 model analysis using RocksDB LOG data for improved accuracy.

## Model Enhancement
- **Base Model**: v1 (Basic bandwidth-based model)
- **Enhancement**: RocksDB LOG integration
- **Enhancement Factors**: Flush, Stall, Write Amplification, Memtable pressure

## Results
- **Predicted S_max**: 4166.57 ops/sec
- **Actual QPS Mean**: 172.00 ops/sec
- **Error Rate**: -95.87%
- **Validation Status**: Poor

## Enhancement Factors
- **Flush Factor**: 0.500
- **Stall Factor**: 0.300
- **Write Amplification Factor**: 0.482
- **Memtable Factor**: 0.600
- **LOG Adjustment**: 0.700

## RocksDB LOG Statistics

- **Flush Frequency**: 69426.00
- **Compaction Frequency**: 143942.50
- **Stall Frequency**: 348495.00
- **Average Flush Size**: 60.74 MB
- **Write Amplification**: 2.07

## Visualization
![Enhanced v1 Model Analysis](v1_model_enhanced_analysis.png)

## Analysis Time
2025-09-17 05:03:38
