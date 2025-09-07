# Phase-E: v2.1 모델 민감도 분석 가이드

**실행 일시**: 2025-09-05  
**모델 버전**: v2.1  
**목표**: 파라미터 변화가 S_max에 미치는 영향 분석  

## 🎯 민감도 분석 목표

v2.1 모델의 주요 파라미터들이 S_max 예측에 미치는 영향을 정량적으로 분석하여:
1. **핵심 파라미터 식별**: S_max에 가장 큰 영향을 미치는 파라미터
2. **튜닝 가이드 제공**: 성능 최적화를 위한 파라미터 조정 방향
3. **모델 안정성 평가**: 파라미터 변화에 대한 모델의 견고성

## 📊 분석 대상 파라미터

### 1. Stall 관련 파라미터
- **p_stall**: Stall 확률 (0.0 ~ 0.8)
- **영향**: S_max = (1 - p_stall) × S_max_basic

### 2. Mixed I/O 파라미터
- **ρ_r**: 읽기 비율 (0.1 ~ 0.9)
- **ρ_w**: 쓰기 비율 (0.1 ~ 0.9)
- **제약**: ρ_r + ρ_w = 1

### 3. 압축 및 증폭 파라미터
- **WA_device**: 디바이스 쓰기 증폭 (1.0 ~ 5.0)
- **CR**: 압축률 (0.3 ~ 0.8)

### 4. Per-Level 파라미터
- **share_L2**: L2 레벨 공유율 (0.2 ~ 0.6)
- **read_to_write_L2**: L2 읽기/쓰기 비율 (0.0 ~ 1.0)

## 🧮 민감도 분석 스크립트

### 1. 기본 설정
```python
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# 기본 파라미터 (Phase-B 결과 기반)
B_w = 1484  # MiB/s
B_r = 2368  # MiB/s
CR = 0.5406
WA_device = 2.87
p_stall = 0.45
rho_r = 0.45
rho_w = 0.55
```

### 2. Stall 민감도 분석
```python
def stall_sensitivity_analysis():
    """Stall 확률 변화에 따른 S_max 분석"""
    p_stall_range = np.linspace(0.0, 0.8, 50)
    S_max_values = []
    
    for p_stall in p_stall_range:
        B_eff = 1 / (rho_r / B_r + rho_w / B_w)
        S_max_basic = B_eff / (WA_device * (1 + 1/CR))
        S_max_final = (1 - p_stall) * S_max_basic
        S_max_values.append(S_max_final)
    
    return p_stall_range, S_max_values

# 실행 및 시각화
p_stall_range, s_max_stall = stall_sensitivity_analysis()
plt.figure(figsize=(10, 6))
plt.plot(p_stall_range, s_max_stall, 'b-', linewidth=2)
plt.xlabel('Stall Probability (p_stall)')
plt.ylabel('S_max (MiB/s)')
plt.title('S_max vs Stall Probability')
plt.grid(True)
plt.show()
```

### 3. Mixed I/O 민감도 분석
```python
def mixed_io_sensitivity_analysis():
    """읽기/쓰기 비율 변화에 따른 S_max 분석"""
    rho_r_range = np.linspace(0.1, 0.9, 50)
    S_max_values = []
    
    for rho_r in rho_r_range:
        rho_w = 1 - rho_r
        B_eff = 1 / (rho_r / B_r + rho_w / B_w)
        S_max_basic = B_eff / (WA_device * (1 + 1/CR))
        S_max_final = (1 - p_stall) * S_max_basic
        S_max_values.append(S_max_final)
    
    return rho_r_range, S_max_values

# 실행 및 시각화
rho_r_range, s_max_mixed = mixed_io_sensitivity_analysis()
plt.figure(figsize=(10, 6))
plt.plot(rho_r_range, s_max_mixed, 'g-', linewidth=2)
plt.xlabel('Read Ratio (ρ_r)')
plt.ylabel('S_max (MiB/s)')
plt.title('S_max vs Read/Write Mix Ratio')
plt.grid(True)
plt.show()
```

### 4. WA 민감도 분석
```python
def wa_sensitivity_analysis():
    """Write Amplification 변화에 따른 S_max 분석"""
    wa_range = np.linspace(1.0, 5.0, 50)
    S_max_values = []
    
    for wa in wa_range:
        B_eff = 1 / (rho_r / B_r + rho_w / B_w)
        S_max_basic = B_eff / (wa * (1 + 1/CR))
        S_max_final = (1 - p_stall) * S_max_basic
        S_max_values.append(S_max_final)
    
    return wa_range, S_max_values

# 실행 및 시각화
wa_range, s_max_wa = wa_sensitivity_analysis()
plt.figure(figsize=(10, 6))
plt.plot(wa_range, s_max_wa, 'r-', linewidth=2)
plt.xlabel('Write Amplification (WA)')
plt.ylabel('S_max (MiB/s)')
plt.title('S_max vs Write Amplification')
plt.grid(True)
plt.show()
```

## 📈 민감도 지수 계산

### 1. 탄성계수 (Elasticity)
```python
def calculate_elasticity(x_values, y_values, base_x, base_y):
    """파라미터 변화에 대한 S_max의 탄성계수 계산"""
    # 기본값에서의 인덱스 찾기
    base_idx = np.argmin(np.abs(x_values - base_x))
    
    # 1% 변화에 대한 반응 계산
    delta_x = base_x * 0.01
    delta_y = y_values[base_idx + 1] - y_values[base_idx]
    
    elasticity = (delta_y / base_y) / (delta_x / base_x)
    return elasticity

# 각 파라미터별 탄성계수 계산
stall_elasticity = calculate_elasticity(p_stall_range, s_max_stall, 0.45, s_max_stall[22])
mixed_elasticity = calculate_elasticity(rho_r_range, s_max_mixed, 0.45, s_max_mixed[22])
wa_elasticity = calculate_elasticity(wa_range, s_max_wa, 2.87, s_max_wa[22])

print(f"Stall 탄성계수: {stall_elasticity:.2f}")
print(f"Mixed I/O 탄성계수: {mixed_elasticity:.2f}")
print(f"WA 탄성계수: {wa_elasticity:.2f}")
```

### 2. 민감도 순위
```python
def rank_sensitivity():
    """파라미터별 민감도 순위"""
    sensitivities = {
        'Stall': abs(stall_elasticity),
        'Mixed I/O': abs(mixed_elasticity),
        'WA': abs(wa_elasticity)
    }
    
    sorted_sens = sorted(sensitivities.items(), key=lambda x: x[1], reverse=True)
    
    print("민감도 순위:")
    for i, (param, sens) in enumerate(sorted_sens, 1):
        print(f"{i}. {param}: {sens:.2f}")
    
    return sorted_sens

sensitivity_ranking = rank_sensitivity()
```

## 🎯 튜닝 가이드 생성

### 1. 성능 최적화 우선순위
```python
def generate_tuning_guide():
    """민감도 분석 결과를 바탕으로 한 튜닝 가이드"""
    print("=== v2.1 모델 기반 튜닝 가이드 ===\n")
    
    # Stall 최적화
    if abs(stall_elasticity) > 1.0:
        print("1. Stall 최적화 (높은 민감도)")
        print("   - L0 score 조정: level0_file_num_compaction_trigger 감소")
        print("   - Background jobs 증가: max_background_jobs 증가")
        print("   - Subcompactions 조정: max_subcompactions 증가")
        print()
    
    # WA 최적화
    if abs(wa_elasticity) > 0.5:
        print("2. Write Amplification 최적화")
        print("   - Compaction 전략 조정: leveled → universal 고려")
        print("   - Target file size 조정: target_file_size_base 감소")
        print("   - Level multiplier 조정: max_bytes_for_level_multiplier 감소")
        print()
    
    # Mixed I/O 최적화
    if abs(mixed_elasticity) > 0.3:
        print("3. Mixed I/O 최적화")
        print("   - Read/Write 비율 모니터링")
        print("   - Compaction 시점 조정")
        print("   - Cache 크기 조정")
        print()

generate_tuning_guide()
```

### 2. 파라미터 조정 시뮬레이션
```python
def simulate_parameter_adjustment():
    """파라미터 조정 시뮬레이션"""
    print("=== 파라미터 조정 시뮬레이션 ===\n")
    
    # 현재 설정
    current_p_stall = 0.45
    current_wa = 2.87
    current_rho_r = 0.45
    
    # 최적화 시나리오
    scenarios = [
        ("Stall 50% 감소", {"p_stall": current_p_stall * 0.5}),
        ("WA 20% 감소", {"WA_device": current_wa * 0.8}),
        ("Read 비율 30% 증가", {"rho_r": min(0.9, current_rho_r * 1.3)}),
    ]
    
    for scenario_name, params in scenarios:
        # 시뮬레이션 실행
        B_eff = 1 / (params.get("rho_r", current_rho_r) / B_r + 
                    (1 - params.get("rho_r", current_rho_r)) / B_w)
        WA_sim = params.get("WA_device", current_wa)
        p_stall_sim = params.get("p_stall", current_p_stall)
        
        S_max_basic = B_eff / (WA_sim * (1 + 1/CR))
        S_max_final = (1 - p_stall_sim) * S_max_basic
        
        improvement = (S_max_final - 187.1) / 187.1 * 100
        
        print(f"{scenario_name}:")
        print(f"  S_max: {S_max_final:.1f} MiB/s")
        print(f"  개선율: {improvement:+.1f}%")
        print()

simulate_parameter_adjustment()
```

## 📊 결과 시각화

### 1. 종합 민감도 대시보드
```python
def create_sensitivity_dashboard():
    """민감도 분석 결과 대시보드 생성"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Stall 민감도
    axes[0, 0].plot(p_stall_range, s_max_stall, 'b-', linewidth=2)
    axes[0, 0].set_title('Stall 민감도')
    axes[0, 0].set_xlabel('p_stall')
    axes[0, 0].set_ylabel('S_max (MiB/s)')
    axes[0, 0].grid(True)
    
    # Mixed I/O 민감도
    axes[0, 1].plot(rho_r_range, s_max_mixed, 'g-', linewidth=2)
    axes[0, 1].set_title('Mixed I/O 민감도')
    axes[0, 1].set_xlabel('ρ_r')
    axes[0, 1].set_ylabel('S_max (MiB/s)')
    axes[0, 1].grid(True)
    
    # WA 민감도
    axes[1, 0].plot(wa_range, s_max_wa, 'r-', linewidth=2)
    axes[1, 0].set_title('WA 민감도')
    axes[1, 0].set_xlabel('WA')
    axes[1, 0].set_ylabel('S_max (MiB/s)')
    axes[1, 0].grid(True)
    
    # 민감도 순위
    params = [item[0] for item in sensitivity_ranking]
    values = [item[1] for item in sensitivity_ranking]
    axes[1, 1].bar(params, values, color=['red', 'green', 'blue'])
    axes[1, 1].set_title('민감도 순위')
    axes[1, 1].set_ylabel('탄성계수')
    axes[1, 1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('sensitivity_dashboard.png', dpi=300, bbox_inches='tight')
    plt.show()

create_sensitivity_dashboard()
```

## 📋 실행 체크리스트

### Phase-E 실행 단계
- [ ] **환경 설정**: Python 분석 환경 준비
- [ ] **데이터 로드**: Phase-A, B, C 결과 로드
- [ ] **Stall 민감도**: p_stall 0.0~0.8 범위 분석
- [ ] **Mixed I/O 민감도**: ρ_r 0.1~0.9 범위 분석
- [ ] **WA 민감도**: WA 1.0~5.0 범위 분석
- [ ] **탄성계수 계산**: 각 파라미터별 민감도 정량화
- [ ] **튜닝 가이드**: 최적화 우선순위 제시
- [ ] **시뮬레이션**: 파라미터 조정 효과 예측
- [ ] **시각화**: 민감도 대시보드 생성
- [ ] **보고서**: 결과 문서화

## 🎯 기대 결과

### 1. 정량적 인사이트
- **핵심 파라미터 식별**: S_max에 가장 큰 영향을 미치는 파라미터
- **최적화 방향**: 성능 향상을 위한 구체적 조정 방향
- **모델 한계**: 현재 모델의 한계점과 개선 필요사항

### 2. 실용적 가이드
- **튜닝 우선순위**: RocksDB 설정 조정 우선순위
- **성능 예측**: 파라미터 변경 시 예상 성능 변화
- **모니터링 포인트**: 지속적 성능 관리 시 중점 관찰 항목

---

**참고**: 이 가이드는 `putmodel_v2_1.html`의 v2.1 모델을 기반으로 작성되었습니다.
