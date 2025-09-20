# V4.2 Model Analysis Report

## Model Version: v4.2
## Analysis Time: 2025-09-19 11:45:09

## Model Description
V4.2 model incorporates device degradation and FillRandom workload characteristics:

### Key Features:
1. **Device Degradation Model**: Based on Phase-A actual degradation data
2. **FillRandom Workload Characteristics**: Sequential write only, compaction read only
3. **Temporal Phase Analysis**: Initial, Middle, Final phases
4. **Multi-Model Integration**: Device Envelope, Closed Ledger, Dynamic Simulation

## Phase-A Device Degradation Data
- **Initial State**: Write 4116.6 MB/s, Read 5487.2 MB/s
- **Degraded State**: Write 1074.8 MB/s, Read 1166.1 MB/s

## FillRandom Workload Characteristics
- **Workload Type**: FillRandom
- **Write Pattern**: Sequential Write Only
- **Read Pattern**: Compaction Read Only
- **User Reads**: 0
- **System Reads**: Compaction Only

## Predicted S_max by Phase
- **Initial Phase**: 1209794.63 ops/sec
- **Middle Phase**: 767261.58 ops/sec
- **Final Phase**: 185014.72 ops/sec

## Analysis Time
2025-09-19 11:45:09

