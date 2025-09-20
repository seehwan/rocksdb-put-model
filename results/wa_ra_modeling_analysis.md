# WA/RA Modeling Analysis

## 🎯 Analysis Focus

이 분석은 각 모델(v4, v4.1, v4.2)에서 **WA(Write Amplification)**와 **RA(Read Amplification)**가 어떻게 고려되고 모델링되었는지를 평가합니다.

## 📊 Observed WA/RA Characteristics (Phase-B)

### FillRandom Workload Characteristics
- **Write Pattern**: Sequential Write Only
- **Read Pattern**: Compaction Read Only
- **User Reads**: 0 (No user reads)
- **System Reads**: Background Compaction Only

### Observed WA/RA Evolution
| Phase | Estimated WA | Estimated RA | Compaction Intensity |
|-------|--------------|--------------|---------------------|
| Initial Phase | 1.2 | 0.1 | low |
| Middle Phase | 2.5 | 0.8 | high |
| Final Phase | 3.2 | 1.1 | sustained_high |

## 🔍 Model WA/RA Approaches

### V4.MODEL
**Model Type**: Device Envelope Model

**Approach Type**: Implicit/Indirect

#### WA Modeling
- **Method**: Device I/O Envelope에 암묵적으로 포함
- **Explicit Calculation**: ❌
- **Consideration Level**: low
- **Implementation**: I/O 대역폭 제약에 WA 영향이 간접적으로 반영

#### RA Modeling
- **Method**: Device I/O Envelope에 암묵적으로 포함
- **Explicit Calculation**: ❌
- **Consideration Level**: low
- **Implementation**: Read I/O 대역폭 제약에 RA 영향이 간접적으로 반영

**Level Awareness**: ❌
**Temporal Awareness**: ❌

### V4.1.TEMPORAL
**Model Type**: Temporal Enhanced Model

**Approach Type**: Temporal Implicit

#### WA Modeling
- **Method**: 시기별 성능 인자에 WA 변화 간접 반영
- **Explicit Calculation**: ❌
- **Consideration Level**: medium
- **Implementation**: 시기별 cost_factor와 write_amplification 인자 사용

#### RA Modeling
- **Method**: 시기별 성능 인자에 RA 변화 간접 반영
- **Explicit Calculation**: ❌
- **Consideration Level**: medium
- **Implementation**: 시기별 read bandwidth adjustment 사용

**Level Awareness**: ❌
**Temporal Awareness**: ✅

### V4.2
**Model Type**: Level-wise Temporal Enhanced Model

**Approach Type**: Explicit Level-wise Temporal

#### WA Modeling
- **Method**: 레벨별 시기별 명시적 WA 모델링
- **Explicit Calculation**: ✅
- **Consideration Level**: very_high
- **Implementation**: 각 레벨(L0-L6)별 시기별 WA 값 명시적 계산

#### RA Modeling
- **Method**: 레벨별 시기별 명시적 RA 모델링
- **Explicit Calculation**: ✅
- **Consideration Level**: very_high
- **Implementation**: 각 레벨(L0-L6)별 시기별 RA 값 명시적 계산

**Level Awareness**: ✅
**Temporal Awareness**: ✅

## 📈 WA/RA Modeling Accuracy

| Model | Overall WA/RA Score | Sophistication Score | WA Accuracy | RA Accuracy |
|-------|---------------------|---------------------|-------------|-------------|
| v4.model | 0.534 | 0.00 | 51.5% | 55.3% |
| v4.1.temporal | 0.532 | 0.20 | 53.8% | 52.7% |
| v4.2 | 0.813 | 1.00 | 95.9% | 66.7% |

## 🔬 Detailed WA/RA Predictions

### V4.MODEL
| Phase | Actual WA | Predicted WA | WA Error | Actual RA | Predicted RA | RA Error |
|-------|-----------|--------------|----------|-----------|--------------|----------|
| Initial Phase | 1.2 | 1.0 | 16.7% | 0.1 | 1.0 | 900.0% |
| Middle Phase | 2.5 | 1.0 | 60.0% | 0.8 | 1.0 | 25.0% |
| Final Phase | 3.2 | 1.0 | 68.8% | 1.1 | 1.0 | 9.1% |

### V4.1.TEMPORAL
| Phase | Actual WA | Predicted WA | WA Error | Actual RA | Predicted RA | RA Error |
|-------|-----------|--------------|----------|-----------|--------------|----------|
| Initial Phase | 1.2 | 1.5 | 25.0% | 0.1 | 1.0 | 900.0% |
| Middle Phase | 2.5 | 1.3 | 48.0% | 0.8 | 1.1 | 37.5% |
| Final Phase | 3.2 | 1.1 | 65.6% | 1.1 | 1.1 | 4.5% |

### V4.2
| Phase | Actual WA | Predicted WA | WA Error | Actual RA | Predicted RA | RA Error |
|-------|-----------|--------------|----------|-----------|--------------|----------|
| Initial Phase | 1.2 | 1.3 | 8.3% | 0.1 | 0.2 | 100.0% |
| Middle Phase | 2.5 | 2.4 | 4.0% | 0.8 | 0.8 | 0.0% |
| Final Phase | 3.2 | 3.2 | 0.0% | 1.1 | 1.1 | 0.0% |

## 💡 Key Findings

### Sophistication Ranking
1. **V4.2**: 1.00
2. **V4.1.TEMPORAL**: 0.20
3. **V4.MODEL**: 0.00

### Accuracy Ranking
1. **V4.2**: 0.813
2. **V4.MODEL**: 0.534
3. **V4.1.TEMPORAL**: 0.532

### Critical Insights
- v4.2만 WA/RA를 명시적으로 모델링하지만 성능 예측 정확도는 최하위
- v4는 WA/RA를 전혀 고려하지 않지만 트렌드 추적 능력은 최고
- WA/RA 모델링의 정교함이 반드시 성능 예측 정확도로 이어지지 않음
- FillRandom 워크로드에서는 WA/RA보다 다른 요인이 더 중요할 수 있음

## 🎯 Conclusion

**WA/RA 모델링의 정교함**이 반드시 **성능 예측 정확도**로 이어지지 않습니다. v4.2는 가장 정교한 Level-wise WA/RA 모델링을 수행하지만, 실제 성능 예측에서는 가장 낮은 정확도를 보입니다.

이는 **FillRandom 워크로드의 특성상 WA/RA보다 다른 요인들**(장치 성능, I/O 패턴, 시간적 변화 등)이 더 중요할 수 있음을 시사합니다.
