#!/usr/bin/env python3
"""
Generate Rate Control Visualization

생성할 그래프:
1. CV vs Rate Reduction
2. Accuracy vs Rate Reduction
3. Trade-off 비교
4. 3D Surface plot (CV, Accuracy, Throughput)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['axes.unicode_minus'] = False

def generate_rate_control_visualizations():
    """Rate control 시각화 생성"""
    
    # 데이터
    reductions = np.arange(0, 11)
    cv_values = 0.538 * (1 - reductions / 100 * 0.70)
    acc_values = 75.0 + (0.538 - cv_values) / 0.538 * 10
    throughput = 100 - reductions
    
    # Figure 1: CV vs Rate Reduction
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. CV vs Rate Reduction
    ax1 = axes[0, 0]
    ax1.plot(reductions, cv_values, 'b-', linewidth=3, marker='o', markersize=8)
    ax1.axhline(y=0.538, color='r', linestyle='--', linewidth=2, label='Original CV')
    ax1.axhline(y=0.50, color='g', linestyle='--', linewidth=2, label='Target CV')
    ax1.fill_between(reductions, cv_values, 0.538, alpha=0.2, color='blue')
    ax1.set_xlabel('Rate Reduction (%)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('CV (Coefficient of Variation)', fontsize=14, fontweight='bold')
    ax1.set_title('CV vs Rate Reduction', fontsize=16, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=12)
    
    # Highlight 8%
    ax1.axvline(x=8, color='orange', linestyle='--', linewidth=2, alpha=0.5)
    ax1.plot(8, cv_values[8], 'ro', markersize=12, label='Recommended (8%)')
    ax1.text(8, cv_values[8] + 0.01, '8%', fontsize=12, fontweight='bold', 
             ha='center', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    
    # 2. Accuracy vs Rate Reduction
    ax2 = axes[0, 1]
    ax2.plot(reductions, acc_values, 'g-', linewidth=3, marker='s', markersize=8)
    ax2.axhline(y=75.0, color='r', linestyle='--', linewidth=2, label='Baseline')
    ax2.axhline(y=75.6, color='b', linestyle='--', linewidth=2, label='8% target')
    ax2.fill_between(reductions, acc_values, 75.0, alpha=0.2, color='green')
    ax2.set_xlabel('Rate Reduction (%)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax2.set_title('Accuracy vs Rate Reduction', fontsize=16, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=12)
    
    # Highlight 8%
    ax2.axvline(x=8, color='orange', linestyle='--', linewidth=2, alpha=0.5)
    ax2.plot(8, acc_values[8], 'ro', markersize=12)
    ax2.text(8, acc_values[8] + 0.2, '8%', fontsize=12, fontweight='bold',
             ha='center', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    
    # 3. Trade-off Analysis
    ax3 = axes[1, 0]
    ax3_twin = ax3.twinx()
    
    line1 = ax3.plot(reductions, acc_values, 'g-', linewidth=3, marker='o', 
                     markersize=8, label='Accuracy')
    line2 = ax3_twin.plot(reductions, throughput, 'b-', linewidth=3, marker='s',
                         markersize=8, label='Throughput')
    
    ax3.set_xlabel('Rate Reduction (%)', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold', color='g')
    ax3_twin.set_ylabel('Throughput (%)', fontsize=14, fontweight='bold', color='b')
    ax3.set_title('Trade-off: Accuracy vs Throughput', fontsize=16, fontweight='bold')
    
    ax3.tick_params(axis='y', labelcolor='g')
    ax3_twin.tick_params(axis='y', labelcolor='b')
    
    # Highlight 8%
    ax3.axvline(x=8, color='orange', linestyle='--', linewidth=2, alpha=0.5)
    ax3.plot(8, acc_values[8], 'ro', markersize=12)
    ax3.text(8, acc_values[8] + 0.5, '8%', fontsize=12, fontweight='bold',
             ha='center', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    
    # 4. Efficiency Analysis
    ax4 = axes[1, 1]
    efficiency = acc_values / reductions
    efficiency[0] = 0
    
    ax4.bar(reductions, efficiency, width=0.8, color='purple', alpha=0.7, edgecolor='black', linewidth=1.5)
    ax4.axhline(y=0.07, color='r', linestyle='--', linewidth=3, label='Constant (0.07)')
    ax4.set_xlabel('Rate Reduction (%)', fontsize=14, fontweight='bold')
    ax4.set_ylabel('Efficiency (Acc / Reduction)', fontsize=14, fontweight='bold')
    ax4.set_title('Efficiency Analysis', fontsize=16, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.legend(fontsize=12)
    
    # Highlight 8%
    rect = Rectangle((7.6, 0), 0.8, 0.08, linewidth=3, edgecolor='orange', 
                    facecolor='none', alpha=0.7)
    ax4.add_patch(rect)
    ax4.text(8, 0.075, '8%', fontsize=12, fontweight='bold',
             ha='center', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('figs/rate_control_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Generated: figs/rate_control_analysis.png")
    
    # Figure 2: 3D Surface Plot
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')
    
    # Create mesh
    reduction_range = np.arange(0, 11)
    acc_range = acc_values
    cv_range = cv_values
    
    ax.scatter(reduction_range, acc_range, cv_range, c=cv_range, cmap='viridis', 
              s=100, alpha=0.7, edgecolors='black', linewidth=2)
    
    ax.set_xlabel('Rate Reduction (%)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_zlabel('CV', fontsize=14, fontweight='bold')
    ax.set_title('Rate Control 3D Analysis', fontsize=16, fontweight='bold')
    
    # Highlight 8%
    idx_8 = 8
    ax.scatter([8], [acc_values[idx_8]], [cv_values[idx_8]], 
               c='red', s=200, marker='*', label='8% Recommended')
    
    plt.colorbar(ax.scatter(reduction_range, acc_range, cv_range, c=cv_range, cmap='viridis'),
                 ax=ax, label='CV', pad=0.15)
    ax.legend(fontsize=12)
    
    plt.savefig('figs/rate_control_3d.png', dpi=300, bbox_inches='tight')
    print("✅ Generated: figs/rate_control_3d.png")
    
    # Figure 3: Comparative Analysis
    fig, ax = plt.subplots(figsize=(14, 8))
    
    x = np.arange(len(reductions))
    width = 0.35
    
    # Normalize values for comparison
    cv_norm = (cv_values - cv_values.min()) / (cv_values.max() - cv_values.min()) * 100
    acc_norm = acc_values
    
    bars1 = ax.bar(x - width/2, cv_norm, width, label='CV (Normalized)', color='blue', alpha=0.7)
    bars2 = ax.bar(x + width/2, acc_norm, width, label='Accuracy', color='green', alpha=0.7)
    
    ax.set_xlabel('Rate Reduction (%)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Normalized Value (%)', fontsize=14, fontweight='bold')
    ax.set_title('Comparative Analysis: CV vs Accuracy', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(reductions)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Highlight 8%
    ax.axvline(x=8, color='orange', linestyle='--', linewidth=2, alpha=0.5)
    ax.text(8, max(cv_norm.max(), acc_norm.max()) * 1.05, '8% Recommended',
            fontsize=12, fontweight='bold', ha='center',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('figs/rate_control_comparative.png', dpi=300, bbox_inches='tight')
    print("✅ Generated: figs/rate_control_comparative.png")
    
    plt.close('all')
    
    print("\n" + "=" * 80)
    print("✅ All Rate Control Visualizations Generated!")
    print("=" * 80)


if __name__ == "__main__":
    generate_rate_control_visualizations()

