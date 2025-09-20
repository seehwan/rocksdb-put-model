# WA, RA, Device Envelope Relationship Analysis

## 🎯 Analysis Objective

이 분석은 **WA(Write Amplification)**, **RA(Read Amplification)**, **Device Envelope** 간의 관계와 이들이 **Put Rate** 결정에 미치는 상호작용을 분석합니다.

## 🔬 Theoretical Foundation

**기본 방정식**: S_max = f(Device_Envelope, WA, RA)
**상세 방정식**: S_max = min(Write_Constraint, Read_Constraint, Mixed_IO_Constraint)

### Constraint Equations
- **Write Constraint**: S_max_write = Device_Write_BW / (WA * Record_Size)
  - Write 대역폭 제약에 의한 Put Rate 한계
- **Read Constraint**: S_max_read = Device_Read_BW / (RA * Record_Size)
  - Read 대역폭 제약에 의한 Put Rate 한계 (FillRandom에서는 해당 없음)
- **Mixed Io Constraint**: S_max_mixed = Device_Envelope_Capacity / ((WA + RA) * Record_Size)
  - 혼합 I/O 대역폭 제약에 의한 Put Rate 한계

## 📊 Observed Relationships (Phase-B Data)

| Phase | WA | RA | User Write (MB/s) | System Write (MB/s) | System Read (MB/s) | Total I/O (MB/s) | Device Utilization |
|-------|----|----|-------------------|---------------------|-------------------|------------------|-------------------|
| Initial Phase | 1.2 | 0.1 | 65.97 | 79.16 | 6.60 | 85.76 | 18.00% |
| Middle Phase | 2.5 | 0.8 | 16.95 | 42.38 | 13.56 | 55.94 | 47.00% |
| Final Phase | 3.2 | 1.1 | 12.76 | 40.83 | 14.04 | 54.87 | 46.00% |

## 🔍 Constraint Analysis

| Phase | Write Constraint | Mixed I/O Constraint | Theoretical S_max | Actual QPS | Accuracy |
|-------|------------------|---------------------|-------------------|------------|----------|
| Initial Phase | 3,458,788 | 3,722,755 | 3,458,788 | 138,769 | -2292.5% |
| Middle Phase | 433,465 | 366,635 | 366,635 | 114,472 | -120.3% |
| Final Phase | 338,645 | 281,371 | 281,371 | 109,678 | -56.5% |

## 📈 Interaction Model Performance

| Model Type | Average Accuracy | Best Phase | Model Description |
|------------|------------------|------------|-------------------|
| Linear Model | -13.6% | Middle Phase (50.7%) | S_max = α * Envelope - β * WA - γ * RA |
| Multiplicative Model | -311.6% | Middle Phase (45.6%) | S_max = Envelope / (WA^α * RA^β) |
| Constrained Model | -860.0% | Final Phase (-108.8%) | S_max = min(Write_Constraint, Read_Constraint) |

## 💡 Key Findings

### Fundamental Relationships
- WA 증가 → Write I/O 요구량 증가 → S_max 감소
- RA 증가 → Read I/O 요구량 증가 → I/O 경합 → S_max 감소
- Device Envelope 감소 → 전체 I/O 용량 감소 → S_max 감소
- WA + RA 증가 → 전체 I/O 부담 증가 → S_max 감소

### Bottleneck Analysis
- **Initial Phase**: write_constraint (Capacity: 3,458,788 ops/sec)
- **Middle Phase**: mixed_io_constraint (Capacity: 366,635 ops/sec)
- **Final Phase**: mixed_io_constraint (Capacity: 281,371 ops/sec)

### Sensitivity Insights
- WA가 S_max에 가장 큰 영향을 미침 (Write 제약이 주요 병목)
- RA는 FillRandom 워크로드에서 간접적 영향만 있음
- Device Envelope 용량이 전체 성능의 상한선 결정
- WA + RA 조합이 실제 I/O 부담 결정

### Practical Implications
- FillRandom 워크로드에서는 Write 제약이 주요 병목
- RA 최적화보다 WA 최적화가 더 중요
- Device Envelope 개선이 근본적 성능 향상 방법
- 복잡한 WA/RA 모델링보다 Device 제약 이해가 중요

## 🎯 Conclusion

**WA, RA, Device Envelope의 관계**는 복잡한 상호작용을 보입니다. FillRandom 워크로드에서는 **Write 제약**이 주요 병목이며, **Device Envelope 용량**이 전체 성능의 상한선을 결정합니다.

**핵심 통찰**: 복잡한 WA/RA 모델링보다는 **실제 Device 제약 조건을 정확히 이해하고 반영**하는 것이 더 정확한 성능 예측으로 이어집니다.
