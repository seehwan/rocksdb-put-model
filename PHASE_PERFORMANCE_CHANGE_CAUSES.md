# RocksDB Phase별 성능 변화 원인 분석

## 개요

논문에서 관찰된 세 가지 operational phase (Initial, Middle, Final)에서 성능이 변경되는 근본 원인을 분석합니다.

---

## 📊 Phase별 성능 특성 요약

| Phase | 시간 범위 | CV | 주요 특징 | 평균 QPS |
|-------|----------|-----|-----------|----------|
| **Initial** | 0-9.81h | 0.714 | 고변동성, 높은 volatility | 168,047 |
| **Middle** | 9.81-42.0h | 0.516 | 안정화 진행, compaction-intensive | 124,767 |
| **Final** | 42.0h+ | 0.474 | 성숙한 steady-state | 110,280 |

---

## 🔍 성능 변화의 핵심 원인

### **0. Compaction과 Flush의 시간에 따른 증폭 효과 (근본 원인) ⭐**

**LSM-tree의 핵심 특성**: 시간이 지날수록 compaction workload가 **지수적으로 증폭**됩니다.

#### **증폭 메커니즘**

**1. Level 크기의 지수적 성장**
```
Size_i = Size_0 × T^i  (T = 10, typical size ratio)

L0:  1×
L1:  10×
L2:  100×
L3:  1,000×
L4:  10,000×
L5:  100,000×
L6:  1,000,000×
```

**2. Cascading Compaction Chains (연쇄 compaction)**
- **Initial**: L0→L1만 존재, chain length = 1
- **Middle**: L0→L1→L2→L3, chain length = 3-4
- **Final**: L0→L1→L2→...→L6, chain length = 6-7

단일 L0 flush가 여러 level을 거치며 compaction을 연쇄적으로 트리거합니다.

**3. Compaction Workload 누적**
```
Initial:  Workload ∝ Size_0 × Frequency_0  (최소)
Middle:   Workload ∝ Σ(Size_i × Frequency_i) for i=0..3
Final:    Workload ∝ Σ(Size_i × Frequency_i) for i=0..6
```

**4. Flush 빈도의 진화**
- **Initial**: 매우 빈번한 flush (53,053회 in 9.81h), 각 flush가 bandwidth 경쟁
- **Middle**: Flush 빈도 안정화, 하지만 각 flush가 multi-level chain 트리거
- **Final**: Flush 빈도 예측 가능, 하지만 각 flush가 최대 compaction workload 트리거

#### **Time-Dependent Write Amplification**
```
WA(t) = WA_base + α × Σ(T^i × Active(i, t))
```
- $L(t)$: 시간 t에서 활성화된 level 수
- Initial: L(0) ≈ 1-2 → WA ≈ 1.02
- Middle: L(9.81h) ≈ 3-4 → WA ≈ 2.87
- Final: L(42h+) ≈ 6-7 → WA ≈ 4.45

**이것이 phase별 성능 변화의 근본 원인입니다!**

---

### **1. LSM-Tree 구조의 성장과 성숙 (증폭 효과의 결과)**

#### **Initial Phase (0-9.81h)**
- **LSM 구조**: 최소 구조 (L0만, 또는 L0-L1)
- **특징**:
  - 빈 DB에서 시작하여 첫 SST 파일 형성
  - Memtable → L0 flush가 빈번하게 발생
  - 단순한 L0→L1 compaction만 수행
  - Multi-level compaction chain 없음

- **성능 영향**:
  - LSM-tree depth가 얕아서 Write Amplification이 낮음 (WA ≈ 1.02)
  - Read Amplification도 매우 낮음 (RA ≈ 0.1)
  - 구조가 단순해 보이지만, 불안정함

#### **Middle Phase (9.81-42.0h)**
- **LSM 구조**: 확장 중 (L0-L3까지 형성)
- **특징**:
  - Multiple levels가 활성화됨
  - L0→L1→L2→L3 compaction chain 형성
  - 각 level의 크기가 기하급수적으로 증가
  - Compaction workload가 급격히 증가

- **성능 영향**:
  - Write Amplification 급증 (WA ≈ 2.87)
  - Read Amplification 증가 (RA ≈ 4.40)
  - Compaction overhead가 주요 bottleneck이 됨

#### **Final Phase (42.0h+)**
- **LSM 구조**: 성숙한 구조 (L0-L6, 완전한 7-level 구조)
- **특징**:
  - 모든 level이 안정적으로 형성됨
  - Compaction 패턴이 최적화되고 예측 가능
  - 데이터 분포가 안정적 (95%는 L4-L6에, 5%는 L0-L3)

- **성능 영향**:
  - Write Amplification 최대 (WA ≈ 4.45)
  - 하지만 compaction 패턴이 최적화되어 효율적
  - 구조적 안정성으로 예측 가능한 성능

---

### **2. Compaction 패턴의 진화**

#### **Initial Phase: 단순하지만 불안정**
```
Compaction 특징:
- Memtable flush → L0: 매우 빈번 (53,053회)
- L0 → L1: 단순한 single-level compaction
- Chain compaction 없음
- Concurrent compaction 최소
```

**문제점**:
- Flush가 경쟁적으로 발생하여 device bandwidth를 불규칙하게 점유
- 순간적으로 throughput이 폭등하거나 급락
- **Chain compaction risk 높음**: 여러 level이 동시에 compact할 위험

#### **Middle Phase: 복잡해지며 안정화**
```
Compaction 특징:
- Multi-level compaction chain: L0→L1→L2→L3
- Compaction-intensive: 배경 프로세스가 주요 I/O 소비
- Concurrent compaction 증가
- Scheduling complexity 증가
```

**특징**:
- Compaction이 본격적으로 시작
- User write와 compaction I/O의 경쟁이 심화
- **Compaction overhead가 성능 제약의 주요 원인**

#### **Final Phase: 최적화된 패턴**
```
Compaction 특징:
- Multi-level chains: L0→L1→L2→...→L6
- 최적화된 scheduling: 우선순위 기반 compaction
- 예측 가능한 패턴: 규칙적이고 안정적
- Resource coordination 완성
```

**장점**:
- Compaction 패턴이 최적화되어 효율적
- I/O 경쟁은 있지만 예측 가능
- 시스템이 mature steady-state에 도달

---

### **3. Write/Read Amplification (WA/RA)의 변화**

논문의 실험 결과에 따르면:

| Phase | WA | RA | Overhead Impact |
|-------|----|----|-----------------|
| Initial | 1.02 | 0.1 | 최소 (거의 없음) |
| Middle | 2.87 | 4.40 | **최대** (compaction-intensive) |
| Final | 4.45 | 4.40 | 높지만 최적화됨 |

#### **Initial Phase: WA/RA가 낮은 이유**
- LSM-tree depth가 얕아서 데이터 재작성 횟수가 적음
- Compaction이 거의 없어서 추가 I/O 최소

#### **Middle Phase: WA/RA가 급증하는 이유**
- Multiple levels 형성으로 데이터가 여러 번 재작성됨
- Compaction이 본격화되어 read amplification 급증
- **Compaction overhead가 성능의 주요 제약**

#### **Final Phase: WA가 높지만 효율적인 이유**
- WA는 최대이지만 (4.45), compaction 패턴이 최적화됨
- 시스템이 mature하여 overhead를 효율적으로 관리
- **구조적 안정성으로 예측 가능**

---

### **4. Volatility (변동성, CV)의 감소**

| Phase | CV | 해석 |
|-------|----|------|
| Initial | 0.714 | 매우 높은 변동성 |
| Middle | 0.516 | 중간 변동성 (안정화 중) |
| Final | 0.474 | 낮은 변동성 (안정적) |

#### **CV가 감소하는 이유**

**Initial Phase의 높은 CV (0.714) 원인**:
1. **시스템 초기화**: RocksDB 내부 구조가 형성 중
2. **메모리 할당 패턴**: 동적 메모리 관리가 불안정
3. **OS 캐시 워밍업**: 파일 시스템 캐시가 비어있음
4. **빈번한 flush**: 53,053회 flush가 불규칙하게 발생
5. **Chain compaction risk**: 여러 level이 동시 compact할 위험
6. **측정 노이즈**: 초기 단계에서 상대적 노이즈 영향 큼

**Middle Phase의 CV 감소 (0.516) 원인**:
1. **LSM 구조 안정화**: Multiple levels가 형성되어 구조 안정
2. **Compaction 패턴 예측 가능**: 규칙적인 compaction 패턴
3. **시스템 리소스 안정화**: 메모리, 캐시가 안정화됨
4. **Device 성능 안정화**: SSD controller가 최적화됨

**Final Phase의 낮은 CV (0.474) 원인**:
1. **완전한 시스템 성숙**: 모든 내부 구조 완성
2. **예측 가능한 패턴**: Compaction, flush 모두 일정한 패턴
3. **Thermal equilibrium**: 하드웨어가 steady state 도달
4. **알고리즘 수렴**: RocksDB 알고리즘이 workload에 최적화됨

---

### **5. I/O 경쟁 패턴의 변화**

#### **Initial Phase: User write 중심**
```
I/O 분포:
- User Writes: 92%
- Compaction I/O: 8%
- Read I/O: <1%
```

**특징**:
- Compaction이 거의 없어서 User write가 대부분
- Device bandwidth가 User write에 집중
- **단순하지만 불안정**: Flush가 경쟁적으로 발생

#### **Middle Phase: Compaction-intensive**
```
I/O 분포 (추정):
- User Writes: ~60%
- Compaction Writes: ~25%
- Compaction Reads: ~15%
```

**특징**:
- Compaction I/O가 급격히 증가
- User write와 compaction이 device bandwidth 경쟁
- **Compaction overhead가 주요 제약**

#### **Final Phase: 균형잡힌 경쟁**
```
I/O 분포 (추정):
- User Writes: ~45%
- Compaction Writes: ~35%
- Compaction Reads: ~20%
```

**특징**:
- I/O 경쟁은 있지만 예측 가능
- Compaction이 최적화되어 효율적
- **균형잡힌 리소스 사용**

---

### **6. Context-Aware Correction Factor의 변화**

논문의 모델에서 $C_{\text{ctx}}$ 값이 phase별로 다르게 설정되는 이유:

| Phase | $C_{\text{ctx}}$ | 의미 |
|-------|------------------|------|
| Initial | 0.789 | 효율성 감소 (불안정) |
| Middle | 0.880 | 안정화 진행 중 |
| Final | 1.735 | 최적 효율 (mature) |

#### **Initial Phase ($C_{\text{ctx}} = 0.789)**
- **원인**: Cache warmup, 빈번한 flush, chain compaction events
- **결과**: 시스템이 LSM-tree 구조를 형성 중이라 리소스 활용이 비효율적

#### **Middle Phase ($C_{\text{ctx}} = 0.880)**
- **원인**: Compaction 패턴이 예측 가능해지지만, LSM 구조가 계속 진화
- **결과**: Initial보다 효율적이지만, 아직 최적화되지 않음

#### **Final Phase ($C_{\text{ctx}} = 1.735)**
- **원인**: LSM-tree 구조가 안정적, compaction 패턴 최적화, 시스템 peak efficiency
- **결과**: **$> 1$ 값은 mature 시스템이 base efficiency보다 더 좋은 성능을 낼 수 있음을 의미**

---

## 🔗 원인들의 상호작용

### **연쇄 반응 (Chain Reaction)**

```
1. LSM-Tree 구조 성장
   ↓
2. Multiple levels 활성화
   ↓
3. Compaction pattern 복잡화
   ↓
4. WA/RA 증가
   ↓
5. Compaction overhead 증가
   ↓
6. I/O 경쟁 심화
   ↓
7. 하지만 시스템이 mature하면 최적화됨
   ↓
8. Final phase에서 안정적이면서도 효율적
```

### **Trade-off 관계**

- **Initial**: 구조는 단순하지만 **불안정** (높은 CV)
- **Middle**: 구조가 복잡해지고 **compaction-intensive** (최대 overhead)
- **Final**: 구조는 복잡하지만 **최적화되고 안정적** (낮은 CV, 효율적 compaction)

---

## 📈 성능 변화의 정량적 측정

### **실험 데이터 (논문 기준)**

| Metric | Initial | Middle | Final |
|--------|---------|--------|-------|
| **Average QPS** | 168,047 | 124,767 | 110,280 |
| **CV** | 0.714 | 0.516 | 0.474 |
| **WA** | 1.02 | 2.87 | 4.45 |
| **RA** | 0.1 | 4.40 | 4.40 |
| **$C_{\text{ctx}}$** | 0.789 | 0.880 | 1.735 |
| **$S_{\text{cv}}$** (Initial) | 0.16 | - | - |

### **성능 저하의 원인 분석**

**Initial → Middle QPS 감소** (168,047 → 124,767, **-25.7%**):
- **주요 원인**: Compaction overhead 급증 (WA 1.02 → 2.87, RA 0.1 → 4.40)
- **부수 원인**: I/O 경쟁 심화, LSM 구조 복잡화

**Middle → Final QPS 감소** (124,767 → 110,280, **-11.6%**):
- **주요 원인**: WA 증가 (2.87 → 4.45)
- **하지만**: 시스템이 mature하여 $C_{\text{ctx}}$가 1.735로 증가하여 일부 상쇄
- **결과**: 감소폭이 Middle transition보다 작음

---

## 💡 핵심 통찰

### **1. 구조의 복잡성 vs. 안정성**
- Initial: 구조는 단순하지만 **불안정** (높은 CV)
- Final: 구조는 복잡하지만 **안정적** (낮은 CV)

### **2. Compaction Overhead의 최적화**
- Middle: Compaction이 시작되어 overhead 최대
- Final: Compaction이 최적화되어 overhead를 효율적으로 관리

### **3. 성능 예측 가능성**
- Initial: 높은 변동성으로 예측 어려움 (CV = 0.714)
- Final: 낮은 변동성으로 예측 가능 (CV = 0.474)

### **4. 시스템 성숙도 (Maturity)**
- Initial: 시스템이 형성 중 ($C_{\text{ctx}} = 0.789$)
- Final: 시스템이 성숙 ($C_{\text{ctx}} = 1.735$, $> 1$ = 최적화된 효율)

---

## 🎯 결론

RocksDB의 성능이 phase별로 변경되는 **근본 원인**:

1. **LSM-Tree 구조의 성장**: 단순한 구조에서 복잡한 7-level 구조로 성장
2. **Compaction 패턴의 진화**: 단순 flush에서 최적화된 multi-level compaction으로
3. **WA/RA의 변화**: 낮은 amplification에서 높지만 최적화된 amplification으로
4. **Volatility 감소**: 높은 변동성에서 안정적인 성능으로
5. **I/O 경쟁 패턴**: User write 중심에서 균형잡힌 경쟁으로
6. **시스템 성숙도**: 초기 형성에서 mature steady-state로

**핵심 통찰**: 
- **Initial phase**는 구조가 단순하지만 **불안정**
- **Middle phase**는 구조가 복잡해지며 **compaction-intensive** (overhead 최대)
- **Final phase**는 구조가 복잡하지만 **최적화되고 안정적** (mature steady-state)

이러한 변화는 **LSM-tree의 자연스러운 진화 과정**이며, 논문의 phase-optimized model이 이를 정확히 포착하고 있습니다.

