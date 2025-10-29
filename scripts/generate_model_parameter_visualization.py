#!/usr/bin/env python3
"""
Generate Model Parameter Visualization

생성할 그래프:
1. Utilization factor에 따른 s_max 변화
2. Context bonuses 영향
3. Phase별 파라미터 민감도
4. 3D visualization
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Font setup
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['axes.unicode_minus'] = False

def calculate_s_max(device_bw, utilization, calibration, context_bonus):
    """s_max 계산"""
    theoretical_max = device_bw * 1024**2 / 1024  # ops/sec (assuming 1KB value)
    s_max = theoretical_max * utilization * calibration * context_bonus
    return s_max

def generate_model_parameter_visualizations():
    """Model parameter 시각화 생성"""
    
    # Phase-specific parameters
    phases = ['Initial', 'Middle', 'Final']
    u_values = [0.030, 0.047, 0.095]
    c_values = [1.579, 1.0, 2.065]
    
    device_bw = 4.0  # GB/s (example)
    
    # Visualization 1: Utilization Factor Impact
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Utilization factor sweep
    u_range = np.arange(0.01, 0.11, 0.001)
    base_s_max = np.array([calculate_s_max(device_bw, u, 1.0, 1.0) for u in u_range])
    
    ax1 = axes[0, 0]
    for i, (phase, u) in enumerate(zip(phases, u_values)):
        s_max_values = np.array([calculate_s_max(device_bw, u, 1.0, 1.0) for _ in u_range])
        ax1.plot(u_range, base_s_max, 'k--', linewidth=2, alpha=0.3)
        ax1.plot(u, calculate_s_max(device_bw, u, 1.0, 1.0), 
                'o', markersize=12, label=f'{phase} (U={u:.3f})', linewidth=2)
    
    ax1.set_xlabel('Utilization Factor', fontsize=14, fontweight='bold')
    ax1.set_ylabel('S_max (ops/sec)', fontsize=14, fontweight='bold')
    ax1.set_title('Utilization Factor Impact', fontsize=16, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=11)
    
    # 2. Calibration factor impact
    c_range = np.arange(1.0, 2.5, 0.01)
    base_s_max_c = np.array([calculate_s_max(device_bw, 0.047, c, 1.0) for c in c_range])
    
    ax2 = axes[0, 1]
    for i, (phase, u, c) in enumerate(zip(phases, u_values, c_values)):
        s_max = calculate_s_max(device_bw, u, c, 1.0)
        ax2.plot(c, s_max, 'o', markersize=12, label=f'{phase} (C={c:.3f})', linewidth=2)
    
    ax2.plot(c_range, base_s_max_c, 'b--', linewidth=2, alpha=0.5, label='Middle phase trend')
    ax2.set_xlabel('Calibration Factor', fontsize=14, fontweight='bold')
    ax2.set_ylabel('S_max (ops/sec)', fontsize=14, fontweight='bold')
    ax2.set_title('Calibration Factor Impact', fontsize=16, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=11)
    
    # 3. Context bonus impact
    bonus_range = np.arange(0.8, 1.5, 0.01)
    s_max_initial = np.array([calculate_s_max(device_bw, 0.030, 1.579, b) for b in bonus_range])
    s_max_final = np.array([calculate_s_max(device_bw, 0.095, 2.065, b) for b in bonus_range])
    
    ax3 = axes[1, 0]
    ax3.plot(bonus_range, s_max_initial, 'b-', linewidth=3, label='Initial (U=0.030, C=1.579)', marker='o', markersize=4)
    ax3.plot(bonus_range, s_max_final, 'r-', linewidth=3, label='Final (U=0.095, C=2.065)', marker='s', markersize=4)
    ax3.axvline(x=1.0, color='gray', linestyle='--', linewidth=2, alpha=0.5, label='No bonus')
    
    # Highlight specific bonuses
    bonuses_initial = [1.0, 1.15, 1.20]
    bonuses_final = [1.0, 1.05, 1.15]
    for b in bonuses_initial:
        y = calculate_s_max(device_bw, 0.030, 1.579, b)
        ax3.plot(b, y, 'bo', markersize=10)
    for b in bonuses_final:
        y = calculate_s_max(device_bw, 0.095, 2.065, b)
        ax3.plot(b, y, 'rs', markersize=10)
    
    ax3.set_xlabel('Context Bonus', fontsize=14, fontweight='bold')
    ax3.set_ylabel('S_max (ops/sec)', fontsize=14, fontweight='bold')
    ax3.set_title('Context Bonus Impact', fontsize=16, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=11)
    
    # 4. Combined impact (3D surface)
    ax4 = fig.add_subplot(224, projection='3d')
    
    u_mesh = np.linspace(0.02, 0.10, 20)
    c_mesh = np.linspace(1.0, 2.5, 20)
    U, C = np.meshgrid(u_mesh, c_mesh)
    
    S = calculate_s_max(device_bw, U, C, 1.0)
    surf = ax4.plot_surface(U, C, S, cmap='viridis', alpha=0.7)
    
    ax4.set_xlabel('Utilization', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Calibration', fontsize=12, fontweight='bold')
    ax4.set_zlabel('S_max', fontsize=12, fontweight='bold')
    ax4.set_title('3D Surface: U, C → S_max', fontsize=14, fontweight='bold')
    
    # Highlight phase points
    for u, c in zip(u_values, c_values):
        s = calculate_s_max(device_bw, u, c, 1.0)
        ax4.scatter([u], [c], [s], color='red', s=100)
    
    plt.colorbar(surf, ax=ax4, shrink=0.5, aspect=20)
    
    plt.tight_layout()
    plt.savefig('figs/model_parameter_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Generated: figs/model_parameter_analysis.png")
    
    # Visualization 2: Phase comparison
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Simulate different scenarios
    scenarios = ['Base', 'With Calibration', 'With Context Bonus', 'Full Model']
    
    # Calculate for each phase
    initial_values = [
        calculate_s_max(device_bw, 0.030, 1.0, 1.0),
        calculate_s_max(device_bw, 0.030, 1.579, 1.0),
        calculate_s_max(device_bw, 0.030, 1.579, 1.15),
        calculate_s_max(device_bw, 0.030, 1.579, 1.20)
    ]
    
    middle_values = [
        calculate_s_max(device_bw, 0.047, 1.0, 1.0),
        calculate_s_max(device_bw, 0.047, 1.0, 1.0),
        calculate_s_max(device_bw, 0.047, 1.0, 1.0),
        calculate_s_max(device_bw, 0.047, 1.0, 1.0)
    ]
    
    final_values = [
        calculate_s_max(device_bw, 0.095, 1.0, 1.0),
        calculate_s_max(device_bw, 0.095, 2.065, 1.0),
        calculate_s_max(device_bw, 0.095, 2.065, 1.05),
        calculate_s_max(device_bw, 0.095, 2.065, 1.15)
    ]
    
    x = np.arange(len(scenarios))
    width = 0.25
    
    bars1 = ax.bar(x - width, initial_values, width, label='Initial', color='blue', alpha=0.7)
    bars2 = ax.bar(x, middle_values, width, label='Middle', color='green', alpha=0.7)
    bars3 = ax.bar(x + width, final_values, width, label='Final', color='orange', alpha=0.7)
    
    ax.set_xlabel('Model Configuration', fontsize=14, fontweight='bold')
    ax.set_ylabel('S_max (ops/sec)', fontsize=14, fontweight='bold')
    ax.set_title('Phase-Specific Model Outputs', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.0f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('figs/model_phase_comparison.png', dpi=300, bbox_inches='tight')
    print("✅ Generated: figs/model_phase_comparison.png")
    
    # Visualization 3: Parameter sensitivity
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # Initial phase sensitivity
    ax = axes[0]
    param_range = np.linspace(-30, 30, 50)  # % change
    
    u_base = 0.030
    c_base = 1.579
    b_base = 1.20
    
    u_sensitivity = [calculate_s_max(device_bw, u_base * (1 + p/100), c_base, 1.0) for p in param_range]
    c_sensitivity = [calculate_s_max(device_bw, u_base, c_base * (1 + p/100), 1.0) for p in param_range]
    b_sensitivity = [calculate_s_max(device_bw, u_base, c_base, b_base * (1 + p/100)) for p in param_range]
    
    ax.plot(param_range, u_sensitivity, 'b-', linewidth=2, label='Utilization')
    ax.plot(param_range, c_sensitivity, 'g-', linewidth=2, label='Calibration')
    ax.plot(param_range, b_sensitivity, 'r-', linewidth=2, label='Context Bonus')
    ax.axvline(x=0, color='k', linestyle='--', linewidth=1, alpha=0.3)
    ax.set_xlabel('Parameter Change (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('S_max (ops/sec)', fontsize=12, fontweight='bold')
    ax.set_title('Initial Phase Sensitivity', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Middle phase sensitivity
    ax = axes[1]
    u_base_m = 0.047
    c_base_m = 1.0
    b_base_m = 1.0
    
    u_sensitivity = [calculate_s_max(device_bw, u_base_m * (1 + p/100), c_base_m, 1.0) for p in param_range]
    c_sensitivity = [calculate_s_max(device_bw, u_base_m, c_base_m * (1 + p/100), 1.0) for p in param_range]
    b_sensitivity = [calculate_s_max(device_bw, u_base_m, c_base_m, b_base_m * (1 + p/100)) for p in param_range]
    
    ax.plot(param_range, u_sensitivity, 'b-', linewidth=2, label='Utilization')
    ax.plot(param_range, c_sensitivity, 'g-', linewidth=2, label='Calibration')
    ax.plot(param_range, b_sensitivity, 'r-', linewidth=2, label='Context Bonus')
    ax.axvline(x=0, color='k', linestyle='--', linewidth=1, alpha=0.3)
    ax.set_xlabel('Parameter Change (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('S_max (ops/sec)', fontsize=12, fontweight='bold')
    ax.set_title('Middle Phase Sensitivity', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Final phase sensitivity
    ax = axes[2]
    u_base_f = 0.095
    c_base_f = 2.065
    b_base_f = 1.15
    
    u_sensitivity = [calculate_s_max(device_bw, u_base_f * (1 + p/100), c_base_f, 1.0) for p in param_range]
    c_sensitivity = [calculate_s_max(device_bw, u_base_f, c_base_f * (1 + p/100), 1.0) for p in param_range]
    b_sensitivity = [calculate_s_max(device_bw, u_base_f, c_base_f, b_base_f * (1 + p/100)) for p in param_range]
    
    ax.plot(param_range, u_sensitivity, 'b-', linewidth=2, label='Utilization')
    ax.plot(param_range, c_sensitivity, 'g-', linewidth=2, label='Calibration')
    ax.plot(param_range, b_sensitivity, 'r-', linewidth=2, label='Context Bonus')
    ax.axvline(x=0, color='k', linestyle='--', linewidth=1, alpha=0.3)
    ax.set_xlabel('Parameter Change (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('S_max (ops/sec)', fontsize=12, fontweight='bold')
    ax.set_title('Final Phase Sensitivity', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('figs/model_parameter_sensitivity.png', dpi=300, bbox_inches='tight')
    print("✅ Generated: figs/model_parameter_sensitivity.png")
    
    plt.close('all')
    
    print("\n" + "=" * 80)
    print("✅ All Model Parameter Visualizations Generated!")
    print("=" * 80)


if __name__ == "__main__":
    generate_model_parameter_visualizations()

