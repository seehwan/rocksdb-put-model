#!/usr/bin/env python3
"""
Generate WA/RA Sensitivity Visualization

WA/RA 파라미터 변화에 따른 utilization factor sensitivity 분석:
1. WA 변화에 따른 sensitivity
2. RA 변화에 따른 sensitivity  
3. Combined WA/RA sensitivity
4. Utilization factor adjustment 시각화
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Font setup
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['axes.unicode_minus'] = False

def calculate_utilization_adjustment(wa, ra, phase):
    """WA/RA에 따른 utilization factor adjustment 계산"""
    
    # Base utilization by phase
    base_util = {
        'initial': 0.030,
        'middle': 0.047,
        'final': 0.095
    }
    
    # Nominal WA/RA by phase
    nominal_wa = {
        'initial': 1.02,
        'middle': 2.87,
        'final': 4.45
    }
    
    nominal_ra = {
        'initial': 0.1,
        'middle': 4.40,
        'final': 4.40
    }
    
    # Calculate adjustment factors
    wa_ratio = wa / nominal_wa[phase]
    ra_ratio = ra / nominal_ra[phase]
    
    # WA adjustment (higher WA → lower utilization due to overhead)
    wa_penalty = np.maximum(0.85, 1.0 - (wa_ratio - 1.0) * 0.15)
    
    # RA adjustment (higher RA → lower utilization due to read overhead)
    ra_penalty = np.maximum(0.85, 1.0 - (ra_ratio - 1.0) * 0.10)
    
    # Combined adjustment
    adjustment = wa_penalty * ra_penalty
    
    adjusted_util = base_util[phase] * adjustment
    
    return adjusted_util, wa_penalty, ra_penalty

def generate_wa_ra_sensitivity_visualizations():
    """WA/RA sensitivity 시각화 생성"""
    
    # Figure 1: WA Impact on Utilization
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    phases = ['initial', 'middle', 'final']
    
    for i, phase in enumerate(phases):
        # WA sweep
        wa_range = np.linspace(0.5, 6.0, 100)
        ra_fixed = {'initial': 0.1, 'middle': 4.40, 'final': 4.40}[phase]
        
        util_values = []
        wa_penalty_values = []
        
        for wa in wa_range:
            adj_util, wa_pen, _ = calculate_utilization_adjustment(wa, ra_fixed, phase)
            util_values.append(adj_util)
            wa_penalty_values.append(wa_pen)
        
        ax = axes[0, i]
        ax2 = ax.twinx()
        
        line1 = ax.plot(wa_range, util_values, 'b-', linewidth=3, label='Adjusted Utilization')
        line2 = ax2.plot(wa_range, np.array(wa_penalty_values) * 100, 'r--', linewidth=2, 
                         alpha=0.7, label='WA Penalty (%)')
        
        # Highlight nominal
        nominal_wa = {'initial': 1.02, 'middle': 2.87, 'final': 4.45}[phase]
        ax.axvline(x=nominal_wa, color='orange', linestyle='--', linewidth=2, alpha=0.5)
        
        base_util = {'initial': 0.030, 'middle': 0.047, 'final': 0.095}[phase]
        ax.axhline(y=base_util, color='gray', linestyle='--', linewidth=2, alpha=0.5, 
                  label='Base Utilization')
        
        ax.set_xlabel('WA', fontsize=12, fontweight='bold')
        ax.set_ylabel('Utilization Factor', fontsize=12, fontweight='bold', color='b')
        ax2.set_ylabel('Penalty (%)', fontsize=12, fontweight='bold', color='r')
        ax.set_title(f'{phase.capitalize()} Phase', fontsize=14, fontweight='bold')
        
        ax.tick_params(axis='y', labelcolor='b')
        ax2.tick_params(axis='y', labelcolor='r')
        ax.grid(True, alpha=0.3)
        
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, fontsize=9, loc='upper right')
    
    # RA Impact on Utilization
    for i, phase in enumerate(phases):
        # RA sweep
        ra_range = np.linspace(0.0, 8.0, 100)
        wa_fixed = {'initial': 1.02, 'middle': 2.87, 'final': 4.45}[phase]
        
        util_values = []
        ra_penalty_values = []
        
        for ra in ra_range:
            adj_util, _, ra_pen = calculate_utilization_adjustment(wa_fixed, ra, phase)
            util_values.append(adj_util)
            ra_penalty_values.append(ra_pen)
        
        ax = axes[1, i]
        ax2 = ax.twinx()
        
        line1 = ax.plot(ra_range, util_values, 'g-', linewidth=3, label='Adjusted Utilization')
        line2 = ax2.plot(ra_range, np.array(ra_penalty_values) * 100, 'r--', linewidth=2,
                         alpha=0.7, label='RA Penalty (%)')
        
        # Highlight nominal
        nominal_ra = {'initial': 0.1, 'middle': 4.40, 'final': 4.40}[phase]
        ax.axvline(x=nominal_ra, color='orange', linestyle='--', linewidth=2, alpha=0.5)
        
        base_util = {'initial': 0.030, 'middle': 0.047, 'final': 0.095}[phase]
        ax.axhline(y=base_util, color='gray', linestyle='--', linewidth=2, alpha=0.5,
                  label='Base Utilization')
        
        ax.set_xlabel('RA', fontsize=12, fontweight='bold')
        ax.set_ylabel('Utilization Factor', fontsize=12, fontweight='bold', color='g')
        ax2.set_ylabel('Penalty (%)', fontsize=12, fontweight='bold', color='r')
        ax.set_title(f'{phase.capitalize()} Phase', fontsize=14, fontweight='bold')
        
        ax.tick_params(axis='y', labelcolor='g')
        ax2.tick_params(axis='y', labelcolor='r')
        ax.grid(True, alpha=0.3)
        
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, fontsize=9, loc='upper right')
    
    plt.tight_layout()
    plt.savefig('figs/wa_ra_utilization_sensitivity.png', dpi=300, bbox_inches='tight')
    print("✅ Generated: figs/wa_ra_utilization_sensitivity.png")
    
    # Figure 2: Combined WA/RA Sensitivity (2D Contour)
    fig = plt.figure(figsize=(16, 5))
    
    for i, phase in enumerate(phases):
        ax = fig.add_subplot(1, 3, i+1)
        
        wa_grid = np.linspace(0.5, 6.0, 50)
        ra_grid = np.linspace(0.0, 8.0, 50)
        WA, RA = np.meshgrid(wa_grid, ra_grid)
        
        util_grid = np.zeros_like(WA)
        for idx in range(len(wa_grid)):
            for jdx in range(len(ra_grid)):
                adj_util, _, _ = calculate_utilization_adjustment(WA[jdx, idx], RA[jdx, idx], phase)
                util_grid[jdx, idx] = adj_util
        
        contour = ax.contourf(WA, RA, util_grid, levels=20, cmap='viridis', alpha=0.7)
        ax.contour(WA, RA, util_grid, levels=10, colors='black', alpha=0.3, linewidths=0.5)
        
        # Highlight nominal
        nominal_wa = {'initial': 1.02, 'middle': 2.87, 'final': 4.45}[phase]
        nominal_ra = {'initial': 0.1, 'middle': 4.40, 'final': 4.40}[phase]
        ax.plot(nominal_wa, nominal_ra, 'r*', markersize=15, label='Nominal')
        
        ax.set_xlabel('WA', fontsize=12, fontweight='bold')
        ax.set_ylabel('RA', fontsize=12, fontweight='bold')
        ax.set_title(f'{phase.capitalize()} Phase', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        
        plt.colorbar(contour, ax=ax, label='Utilization Factor')
    
    plt.tight_layout()
    plt.savefig('figs/wa_ra_combined_sensitivity.png', dpi=300, bbox_inches='tight')
    print("✅ Generated: figs/wa_ra_combined_sensitivity.png")
    
    # Figure 3: Sensitivity Comparison
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Range for each parameter
    wa_range = np.linspace(0.5, 6.0, 50)
    ra_range = np.linspace(0.0, 8.0, 50)
    
    # Calculate sensitivity for each phase
    for phase_idx, phase in enumerate(phases):
        util_wa = []
        util_ra = []
        
        # Fixed RA for WA sensitivity
        ra_fixed = {'initial': 0.1, 'middle': 4.40, 'final': 4.40}[phase]
        for wa in wa_range:
            adj, _, _ = calculate_utilization_adjustment(wa, ra_fixed, phase)
            util_wa.append(adj)
        
        # Fixed WA for RA sensitivity
        wa_fixed = {'initial': 1.02, 'middle': 2.87, 'final': 4.45}[phase]
        for ra in ra_range:
            adj, _, _ = calculate_utilization_adjustment(wa_fixed, ra, phase)
            util_ra.append(adj)
        
        # Normalize for comparison
        util_wa = np.array(util_wa)
        util_ra = np.array(util_ra)
        
        base_util = {'initial': 0.030, 'middle': 0.047, 'final': 0.095}[phase]
        
        # Plot WA sensitivity
        ax.plot(wa_range, (util_wa - base_util) / base_util * 100, 
               linewidth=3, marker='o', markersize=4,
               label=f'{phase.capitalize()} Phase (WA)')
        
        # Plot RA sensitivity
        ax.plot(ra_range / 8 * 6 + 0.5, (util_ra - base_util) / base_util * 100,
               '--', linewidth=3, marker='s', markersize=4,
               label=f'{phase.capitalize()} Phase (RA)')
    
    ax.set_xlabel('Parameter Value (WA: 0.5-6.0, RA: 0.0-8.0)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Utilization Factor Change (%)', fontsize=12, fontweight='bold')
    ax.set_title('WA/RA Sensitivity Comparison', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10, ncol=2)
    
    plt.tight_layout()
    plt.savefig('figs/wa_ra_sensitivity_comparison.png', dpi=300, bbox_inches='tight')
    print("✅ Generated: figs/wa_ra_sensitivity_comparison.png")
    
    plt.close('all')
    
    print("\n" + "=" * 80)
    print("✅ All WA/RA Sensitivity Visualizations Generated!")
    print("=" * 80)


if __name__ == "__main__":
    generate_wa_ra_sensitivity_visualizations()

