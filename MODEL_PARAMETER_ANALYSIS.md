# 모델 파라미터 분석: 현재 논문의 문제

## ❌ **발견된 문제**

### **Section 4의 모델이 V5.3가 아님!**

**현재 Section 4 "Phase-Optimized Put-Rate Model"**:
- Line 451-498: V3 Dynamic Model의 "Model Simulation Algorithm"
- 수식이 V5.3과 다름!

**실제 V5.3 공식**:
```latex
S_max = (B_w × 1024² / R_s) × U_phase × C_phase × B_context
```

**현재 논문의 수식들**:
- Line 348-350: Per-User Device Requirements (W3의 WA/CR 기반)
- Line 366: Harmonic Mean for Mixed I/O (V3)
- Line 383: Per-Level Capacity Constraints (V3)
- Line 399: Dynamic Stall Function (V3)
- Line 416: Non-linear Concurrency Scaling (V3)
- Line 434-436: Backlog Dynamics (V3)
- Line 457-498: Dynamic Simulation Algorithm (V3)

**→ V5.3 공식이 없음!**

---

## 🔍 **파라미터 분석**

### **논문에서 정의된 파라미터들** (Line 298-343):

#### **System Parameters**:
- `S_max`, `B_w`, `B_r`, `B_eff`, `CR`, `WA`, `w_wal`

#### **Level-Specific Parameters**:
- `ℓ`, `C_ℓ`, `k_ℓ`, `μ_eff,ℓ`, `μ_min,ℓ`, `μ_max,ℓ`, `γ_ℓ`, `k_s`, `k_0,ℓ`

#### **Workload Parameters**:
- `ρ_r`, `ρ_w`, `D^W_ℓ`, `D^R_ℓ`, `A^W_ℓ`, `A^R_ℓ`, `Q^W_ℓ`, `Q^R_ℓ`

#### **Stall Parameters**:
- `p_stall`, `N_L0`, `τ_slow`, `a`, `σ`, `Δ`, `T`

**→ 총 35개 파라미터 정의됨**

---

## ❌ **V5.3에서 실제 사용되는 파라미터**

**V5.3 공식**:
```
S_max = (B_w × 1024² / R_s) × U_phase × C_phase × B_context
```

**필요한 파라미터** (5개만!):
1. `B_w`: Write bandwidth (MB/s)
2. `R_s`: Record size (1040 bytes)
3. `U_phase`: Phase-specific utilization (0.030, 0.047, 0.095)
4. `C_phase`: Phase-specific calibration (1.579, 1.0, 2.065)
5. `B_context`: Context bonus factors

**Context bonuses (initial phase)**:
- `B_vol`: Volatility bonus (1.20, 1.10, 1.0)
- `B_warm`: Warmup bonus (1.15, 1.0)
- `B_pot`: Potential bonus (1.12, 1.0)

**Context bonuses (final phase)**:
- `B_stab`: Stability bonus (1.15, 1.0)
- `B_mat`: Maturity bonus (1.10, 1.0)
- `B_eff`: Efficiency bonus (1.05, 1.0)

**→ 총 11개 파라미터만 사용**

---

## 📊 **불필요한 파라미터들** (24개)

**V3/V4 모델에서 왔지만 V5.3에서는 안 쓰이는 것들**:
1. ❌ `B_r` (Read bandwidth) - V5.3는 write-only
2. ❌ `B_eff` (Mixed I/O) - V5.3는 mixed I/O 고려 안 함
3. ❌ `C_ℓ` (Per-level capacity) - V5.3는 level 구분 안 함
4. ❌ `k_ℓ` (Capacity factor) - V5.3는 level 구분 안 함
5. ❌ `μ_eff,ℓ` - Concurrency modeling 안 함
6. ❌ `ρ_r`, `ρ_w` - Mixed I/O 안 함
7. ❌ `D^W_ℓ`, `D^R_ℓ` - Level demands 안 함
8. ❌ `A^W_ℓ`, `A^R_ℓ` - Allocation 안 함
9. ❌ `Q^W_ℓ`, `Q^R_ℓ` - Backlog tracking 안 함
10. ❌ `p_stall`, `N_L0`, `τ_slow`, `a` - Stall modeling 안 함
11. ❌ 등등... 총 24개 불필요

---

## ✅ **필요한 파라미터만 추가**

**V5.3 핵심 공식이 빠져있음!**

**추가해야 할 것**:
```latex
\subsubsection{Core Prediction Formula}

\begin{equation}
S_{\max} = \frac{B_w \times 1024^2}{R_s} \times U_{\text{phase}} \times C_{\text{phase}} \times B_{\text{context}}
\label{eq:phase_optimized_core}
\end{equation}

where:
\begin{itemize}
    \item $S_{\max}$: Maximum sustainable put rate (ops/sec)
    \item $B_w$: Measured available write bandwidth (MB/s)
    \item $R_s$: Record size (1040 bytes)
    \item $U_{\text{phase}}$: Phase-specific utilization (0.030, 0.047, 0.095)
    \item $C_{\text{phase}}$: Phase-specific calibration (1.579, 1.0, 2.065)
    \item $B_{\text{context}}$: Context bonuses (phase-specific)
\end{itemize}
```

---

## 🎯 **문제의 핵심**

**현재 논문**:
- V3 Dynamic Model 수식만 있음
- V5.3 Phase-Optimized 수식 없음
- 불필요한 파라미터 24개 정의됨

**해결책**:
- V5.3 핵심 공식 추가
- V3 수식들은 별도 섹션으로 이동 또는 제거

