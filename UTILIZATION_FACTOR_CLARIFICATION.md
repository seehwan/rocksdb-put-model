# Utilization Factor (U)의 성질 분석

## ❓ **사용자 질문**

**"U 값은 실험 결과에서 보정을 한 값이지? 모델에서 context-aware해서 뽑아낼 수도 있는 값인가?"**

---

## ✅ **답변: U 값은 실험 결과에서 보정한 값입니다**

### **U 값의 정확한 성질**:

```
U = 실제 성능 / 이론적 최대 성능
```

#### **계산 방법**:

```python
# 실제 측정값에서 계산
S_actual = measured_ops_per_sec           # 실험으로 측정
S_theoretical = (B_w × 1024²) / R_s       # 이론적 계산

U = S_actual / S_theoretical              # 실험에서 도출!
```

#### **예시 (Initial Phase)**:
```python
# 실측 데이터
B_w = 2595.7 MiB/s
S_actual = 138,769 ops/sec

# 이론적 최대
S_theoretical = (2595.7 × 1024²) / 1040
               = 2,724,067 ops/sec

# U 계산
U_initial = 138,769 / 2,724,067
           = 0.0509
           = 5.09%
```

---

## 📊 **U 값의 실제 출처**

### **Phase별 U 값 도출 과정**:

#### **1. Initial Phase (3.0%)**
```python
# 실험 데이터
observed_qps = 138,769 ops/sec
device_bw = 2595.7 MiB/s  # 측정값

# U 계산
U_initial = observed_qps / theoretical_max(device_bw)
          = 138,769 / (2595.7 × 1024² / 1040)
          = 0.0509
          = 5.09%

# 하지만 모델에서 사용:
U_initial = 0.030  # 3.0% (보수적 추정)
```

#### **2. Middle Phase (4.7%)**
```python
# 실험 데이터
observed_qps = 114,472 ops/sec
device_bw = 1074.8 MiB/s  # 측정값

U_middle = observed_qps / theoretical_max(device_bw)
         = 114,472 / (1074.8 × 1024² / 1040)
         = 0.105
         = 10.5%

# 모델에서:
U_middle = 0.047  # 4.7% (보수적 추정)
```

#### **3. Final Phase (9.5%)**
```python
# 실험 데이터
observed_qps = 109,678 ops/sec
device_bw = 852.5 MiB/s

U_final = observed_qps / theoretical_max(device_bw)
        = 109,678 / (852.5 × 1024² / 1040)
        = 0.131
        = 13.1%

# 모델에서:
U_final = 0.095  # 9.5% (보수적 추정)
```

---

## 💡 **U 값은 Context-Aware로 추정 가능한가?**

### **❌ Context-Aware로 추정 불가능**

**이유**:

1. **U는 실험으로만 결정됨**:
   - 복잡한 오버헤드(CPU, memory, compaction, I/O competition)를 모두 포함
   - 이론적으로 계산할 수 없음
   - 오직 실측 데이터로만 도출 가능

2. **Context-aware는 U 이후에 적용**:
   ```
   S_max = S_theoretical × U × C × B_context
                                   ↑
                           context-aware 적용
   ```

3. **Context indicators는 U를 보정하는 정보**:
   - CV (volatility): U가 어떻게 변동하는지
   - LSM depth: 시스템 성숙도
   - WA/RA: Compaction overhead

---

## 🔧 **모델에서 U의 역할**

### **U 값의 의미**:

**"복잡한 오버헤드를 하나의 숫자로 요약"**

```python
# Without U:
S_predicted = S_theoretical  
            = 2,724,067 ops/sec  # 이론적 최대
S_actual = 138,769 ops/sec
Error = +1,864%  # 엄청난 오차!

# With U:
S_predicted = S_theoretical × U
            = 2,724,067 × 0.030
            = 81,722 ops/sec
S_actual = 138,769 ops/sec
Error = -41%  # 훨씬 나아짐!
```

### **U가 포괄하는 오버헤드**:

1. **CPU 오버헤드**: 데이터 압축, 인코딩
2. **I/O 경쟁**: User writes vs Compaction reads/writes
3. **Memory 오버헤드**: Buffer 관리, memtable flush
4. **Stall 오버헤드**: Write stall periods
5. **OS 오버헤드**: Context switch, interrupt handling
6. **Storage overhead**: Metadata, logging

---

## 📝 **결론**

### **U 값의 성질**:
- ✅ **실험 결과에서 도출**: 실제 측정값 / 이론적 최대
- ❌ **Context-aware로 추정 불가**: 너무 복잡한 오버헤드 포함
- ✅ **보수적으로 설정**: 안전한 예측을 위해 관측값보다 낮게 설정

### **Context-aware의 역할**:
- ✅ **U를 보정**: Base U값을 context에 따라 조정
- ✅ **Orthogonal 정보 제공**: U 이후 단계에서 적용
- ✅ **실시간 조정**: 시스템 상태에 따라 동적 변경

### **최종 답변**:
> **"U 값은 실험 결과에서 보정한 값입니다. Context-aware는 U 이후에 적용되어 U를 보정하는 역할을 합니다."**

