#!/usr/bin/env python3
"""
V5.3 Model Visualization Generator

Generates comprehensive visualizations for V5.3 Initial-Phase-Optimized Model
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.gridspec import GridSpec

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10

# V5.3 Model Data
phase_accuracy = {
    'Initial': 75.0,
    'Middle': 92.2,
    'Final': 86.4
}

predicted_values = {
    'Initial': 173495,
    'Middle': 116542,
    'Final': 124626
}

actual_values = {
    'Initial': 138769,
    'Middle': 114472,
    'Final': 109678
}

utilization_data = {
    'Initial': {'target': 3.0, 'actual': 3.34, 'calibration': 1.579},
    'Middle': {'target': 4.7, 'actual': 4.7, 'calibration': 1.0},
    'Final': {'target': 9.5, 'actual': 10.1, 'calibration': 2.065}
}

adjustment_factors = {
    'Initial': {
        'Calibration': 1.579,
        'Volatility': 1.20,
        'Warmup': 1.15,
        'Potential': 1.12,
        'Total': 2.440
    },
    'Final': {
        'Calibration': 2.065,
        'Stability': 1.15,
        'Maturity': 1.10,
        'Efficiency': 1.05,
        'Total': 2.743
    }
}


def create_phase_accuracy_chart():
    """Phase-wise accuracy comparison chart"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    phases = list(phase_accuracy.keys())
    accuracies = list(phase_accuracy.values())
    colors = ['#3498db', '#27ae60', '#f39c12']
    
    bars = ax.bar(phases, accuracies, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
    
    # Add value labels on bars
    for bar, acc in zip(bars, accuracies):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{acc:.1f}%',
                ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    # Add overall accuracy line
    overall = np.mean(accuracies)
    ax.axhline(y=overall, color='red', linestyle='--', linewidth=2, label=f'Overall: {overall:.1f}%')
    
    ax.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_title('V5.3 Model: Phase-Wise Accuracy', fontsize=16, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('v5_3_phase_accuracy.png', dpi=300, bbox_inches='tight')
    print("✅ Created: v5_3_phase_accuracy.png")
    plt.close()


def create_prediction_comparison():
    """Predicted vs Actual QPS comparison"""
    fig, ax = plt.subplots(figsize=(12, 7))
    
    phases = list(predicted_values.keys())
    predicted = list(predicted_values.values())
    actual = list(actual_values.values())
    
    x = np.arange(len(phases))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, predicted, width, label='Predicted', 
                   color='#3498db', alpha=0.8, edgecolor='black')
    bars2 = ax.bar(x + width/2, actual, width, label='Actual',
                   color='#27ae60', alpha=0.8, edgecolor='black')
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height/1000)}K',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_ylabel('QPS (ops/sec)', fontsize=14, fontweight='bold')
    ax.set_title('V5.3 Model: Predicted vs Actual Performance', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(phases)
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3)
    
    # Format y-axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000)}K'))
    
    plt.tight_layout()
    plt.savefig('v5_3_prediction_comparison.png', dpi=300, bbox_inches='tight')
    print("✅ Created: v5_3_prediction_comparison.png")
    plt.close()


def create_utilization_analysis():
    """Utilization factor analysis"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    phases = list(utilization_data.keys())
    target_util = [utilization_data[p]['target'] for p in phases]
    actual_util = [utilization_data[p]['actual'] for p in phases]
    
    x = np.arange(len(phases))
    width = 0.35
    
    # Left plot: Target vs Actual Utilization
    bars1 = ax1.bar(x - width/2, target_util, width, label='V5.3 Target',
                    color='#3498db', alpha=0.8, edgecolor='black')
    bars2 = ax1.bar(x + width/2, actual_util, width, label='Actual Observed',
                    color='#e74c3c', alpha=0.8, edgecolor='black')
    
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                     f'{height:.1f}%',
                     ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax1.set_ylabel('Utilization Factor (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Utilization Factor Comparison', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(phases)
    ax1.legend(fontsize=10)
    ax1.grid(axis='y', alpha=0.3)
    
    # Right plot: Calibration Factors
    calibration = [utilization_data[p]['calibration'] for p in phases]
    colors_cal = ['#3498db', '#27ae60', '#f39c12']
    
    bars = ax2.bar(phases, calibration, color=colors_cal, alpha=0.8, edgecolor='black')
    
    for bar, cal in zip(bars, calibration):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                 f'{cal:.3f}x',
                 ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax2.axhline(y=1.0, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Baseline (1.0x)')
    ax2.set_ylabel('Calibration Factor', fontsize=12, fontweight='bold')
    ax2.set_title('Phase Calibration Factors', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('v5_3_utilization_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Created: v5_3_utilization_analysis.png")
    plt.close()


def create_adjustment_breakdown():
    """Context-aware adjustment factors breakdown"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Initial Phase Adjustments
    initial_factors = adjustment_factors['Initial']
    components = ['Calibration', 'Volatility', 'Warmup', 'Potential']
    values = [initial_factors[c] for c in components]
    colors = ['#3498db', '#9b59b6', '#e67e22', '#1abc9c']
    
    bars1 = ax1.barh(components, values, color=colors, alpha=0.8, edgecolor='black')
    
    for bar, val in zip(bars1, values):
        width = bar.get_width()
        ax1.text(width, bar.get_y() + bar.get_height()/2.,
                 f' {val:.3f}x',
                 ha='left', va='center', fontsize=11, fontweight='bold')
    
    ax1.axvline(x=1.0, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Baseline')
    ax1.set_xlabel('Adjustment Factor', fontsize=12, fontweight='bold')
    ax1.set_title(f'Initial Phase Adjustments\nTotal: {initial_factors["Total"]:.3f}x',
                  fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(axis='x', alpha=0.3)
    
    # Final Phase Adjustments
    final_factors = adjustment_factors['Final']
    components = ['Calibration', 'Stability', 'Maturity', 'Efficiency']
    values = [final_factors[c] for c in components]
    colors = ['#f39c12', '#27ae60', '#3498db', '#e74c3c']
    
    bars2 = ax2.barh(components, values, color=colors, alpha=0.8, edgecolor='black')
    
    for bar, val in zip(bars2, values):
        width = bar.get_width()
        ax2.text(width, bar.get_y() + bar.get_height()/2.,
                 f' {val:.3f}x',
                 ha='left', va='center', fontsize=11, fontweight='bold')
    
    ax2.axvline(x=1.0, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Baseline')
    ax2.set_xlabel('Adjustment Factor', fontsize=12, fontweight='bold')
    ax2.set_title(f'Final Phase Adjustments\nTotal: {final_factors["Total"]:.3f}x',
                  fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('v5_3_adjustment_breakdown.png', dpi=300, bbox_inches='tight')
    print("✅ Created: v5_3_adjustment_breakdown.png")
    plt.close()


def create_architecture_flow():
    """V5.3 Architecture flow diagram"""
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Define colors
    color_input = '#3498db'
    color_router = '#9b59b6'
    color_phase = ['#3498db', '#27ae60', '#f39c12']
    color_output = '#e74c3c'
    
    # Input box
    input_box = mpatches.FancyBboxPatch((0.15, 0.85), 0.7, 0.08,
                                        boxstyle="round,pad=0.01",
                                        edgecolor=color_input, facecolor=color_input,
                                        alpha=0.3, linewidth=2)
    ax.add_patch(input_box)
    ax.text(0.5, 0.89, 'Input: device_write_bw, phase, context',
            ha='center', va='center', fontsize=12, fontweight='bold')
    
    # Router box
    router_box = mpatches.FancyBboxPatch((0.35, 0.72), 0.3, 0.08,
                                         boxstyle="round,pad=0.01",
                                         edgecolor=color_router, facecolor=color_router,
                                         alpha=0.3, linewidth=2)
    ax.add_patch(router_box)
    ax.text(0.5, 0.76, 'Phase Router',
            ha='center', va='center', fontsize=11, fontweight='bold')
    
    # Arrow input -> router
    ax.annotate('', xy=(0.5, 0.80), xytext=(0.5, 0.85),
                arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    # Phase boxes
    phase_positions = [(0.1, 0.55), (0.4, 0.55), (0.7, 0.55)]
    phase_names = ['Initial Phase', 'Middle Phase', 'Final Phase']
    
    for i, (pos, name, color) in enumerate(zip(phase_positions, phase_names, color_phase)):
        box = mpatches.FancyBboxPatch(pos, 0.25, 0.12,
                                      boxstyle="round,pad=0.01",
                                      edgecolor=color, facecolor=color,
                                      alpha=0.3, linewidth=2)
        ax.add_patch(box)
        ax.text(pos[0] + 0.125, pos[1] + 0.06, name,
                ha='center', va='center', fontsize=10, fontweight='bold')
        
        # Arrow router -> phase
        ax.annotate('', xy=(pos[0] + 0.125, 0.67), xytext=(0.5, 0.72),
                    arrowprops=dict(arrowstyle='->', lw=1.5, color='gray'))
    
    # Optimization boxes
    opt_positions = [(0.1, 0.35), (0.4, 0.35), (0.7, 0.35)]
    opt_labels = ['Base × 1.579\n+ Volatility\n+ Warmup\n+ Potential',
                  'Base × 1.0\nDirect\nOutput',
                  'Base × 2.065\n+ Stability\n+ Maturity\n+ Efficiency']
    
    for i, (pos, label, color) in enumerate(zip(opt_positions, opt_labels, color_phase)):
        box = mpatches.FancyBboxPatch(pos, 0.25, 0.15,
                                      boxstyle="round,pad=0.01",
                                      edgecolor=color, facecolor='white',
                                      alpha=0.8, linewidth=1.5)
        ax.add_patch(box)
        ax.text(pos[0] + 0.125, pos[1] + 0.075, label,
                ha='center', va='center', fontsize=8)
        
        # Arrow phase -> optimization
        ax.annotate('', xy=(pos[0] + 0.125, 0.50), xytext=(pos[0] + 0.125, 0.55),
                    arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
        
        # Arrow optimization -> output
        ax.annotate('', xy=(0.5, 0.20), xytext=(pos[0] + 0.125, 0.35),
                    arrowprops=dict(arrowstyle='->', lw=1.5, color='gray'))
    
    # Output box
    output_box = mpatches.FancyBboxPatch((0.25, 0.12), 0.5, 0.08,
                                         boxstyle="round,pad=0.01",
                                         edgecolor=color_output, facecolor=color_output,
                                         alpha=0.3, linewidth=2)
    ax.add_patch(output_box)
    ax.text(0.5, 0.16, 'Output: predicted S_max (ops/sec)',
            ha='center', va='center', fontsize=12, fontweight='bold')
    
    # Accuracy labels
    accuracies = ['75.0%', '92.2%', '86.4%']
    for i, (pos, acc) in enumerate(zip(opt_positions, accuracies)):
        ax.text(pos[0] + 0.125, pos[1] - 0.03, f'Accuracy: {acc}',
                ha='center', va='top', fontsize=9, fontweight='bold',
                color=color_phase[i])
    
    # Title
    ax.text(0.5, 0.97, 'V5.3 Model Architecture Flow',
            ha='center', va='top', fontsize=16, fontweight='bold')
    
    # Overall accuracy
    ax.text(0.5, 0.05, 'Overall Accuracy: 84.5%',
            ha='center', va='center', fontsize=14, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig('v5_3_architecture_flow.png', dpi=300, bbox_inches='tight')
    print("✅ Created: v5_3_architecture_flow.png")
    plt.close()


def create_consistency_analysis():
    """Model consistency analysis"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    phases = list(phase_accuracy.keys())
    accuracies = list(phase_accuracy.values())
    mean_acc = np.mean(accuracies)
    std_acc = np.std(accuracies)
    
    x = np.arange(len(phases))
    
    # Bar chart with error indication
    colors = ['#3498db', '#27ae60', '#f39c12']
    bars = ax.bar(x, accuracies, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
    
    # Add value labels
    for bar, acc in zip(bars, accuracies):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{acc:.1f}%',
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    # Mean line
    ax.axhline(y=mean_acc, color='red', linestyle='--', linewidth=2,
               label=f'Mean: {mean_acc:.1f}%')
    
    # Std deviation band
    ax.axhspan(mean_acc - std_acc, mean_acc + std_acc, alpha=0.2, color='red',
               label=f'Std Dev: ±{std_acc:.1f}%')
    
    ax.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Phase', fontsize=14, fontweight='bold')
    ax.set_title('V5.3 Model: Consistency Analysis\nσ = 7.2% (Excellent)',
                 fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(phases)
    ax.set_ylim(0, 100)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('v5_3_consistency_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ Created: v5_3_consistency_analysis.png")
    plt.close()


def create_comprehensive_dashboard():
    """Comprehensive V5.3 dashboard"""
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    # Top: Overall metrics
    ax1 = fig.add_subplot(gs[0, :])
    ax1.axis('off')
    
    metrics = [
        ('Overall\nAccuracy', '84.5%', '#27ae60'),
        ('Consistency\n(σ)', '7.2%', '#3498db'),
        ('Parameters', '4', '#9b59b6'),
        ('Status', 'Production\nReady', '#f39c12')
    ]
    
    for i, (label, value, color) in enumerate(metrics):
        x_pos = 0.15 + i * 0.2
        circle = plt.Circle((x_pos, 0.5), 0.08, color=color, alpha=0.3)
        ax1.add_patch(circle)
        ax1.text(x_pos, 0.5, value, ha='center', va='center',
                fontsize=16, fontweight='bold')
        ax1.text(x_pos, 0.25, label, ha='center', va='top',
                fontsize=10)
    
    ax1.text(0.5, 0.85, 'V5.3 Initial-Phase-Optimized Model - Complete Dashboard',
            ha='center', va='center', fontsize=18, fontweight='bold')
    
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    
    # Middle left: Phase accuracy
    ax2 = fig.add_subplot(gs[1, 0])
    phases = list(phase_accuracy.keys())
    accuracies = list(phase_accuracy.values())
    colors = ['#3498db', '#27ae60', '#f39c12']
    ax2.bar(phases, accuracies, color=colors, alpha=0.7, edgecolor='black')
    ax2.set_ylabel('Accuracy (%)')
    ax2.set_title('Phase Accuracy', fontweight='bold')
    ax2.set_ylim(0, 100)
    ax2.grid(axis='y', alpha=0.3)
    
    # Middle center: Predicted vs Actual
    ax3 = fig.add_subplot(gs[1, 1])
    x = np.arange(len(phases))
    width = 0.35
    predicted = [v/1000 for v in predicted_values.values()]
    actual = [v/1000 for v in actual_values.values()]
    ax3.bar(x - width/2, predicted, width, label='Predicted', color='#3498db', alpha=0.7)
    ax3.bar(x + width/2, actual, width, label='Actual', color='#27ae60', alpha=0.7)
    ax3.set_ylabel('QPS (K ops/sec)')
    ax3.set_title('Predicted vs Actual', fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(phases)
    ax3.legend(fontsize=8)
    ax3.grid(axis='y', alpha=0.3)
    
    # Middle right: Utilization
    ax4 = fig.add_subplot(gs[1, 2])
    target_util = [utilization_data[p]['target'] for p in phases]
    actual_util = [utilization_data[p]['actual'] for p in phases]
    ax4.bar(x - width/2, target_util, width, label='Target', color='#3498db', alpha=0.7)
    ax4.bar(x + width/2, actual_util, width, label='Actual', color='#e74c3c', alpha=0.7)
    ax4.set_ylabel('Utilization (%)')
    ax4.set_title('Utilization Factor', fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(phases)
    ax4.legend(fontsize=8)
    ax4.grid(axis='y', alpha=0.3)
    
    # Bottom left: Initial adjustments
    ax5 = fig.add_subplot(gs[2, 0])
    initial_factors = adjustment_factors['Initial']
    components = ['Calib', 'Vol', 'Warm', 'Pot']
    values = [initial_factors[c] for c in ['Calibration', 'Volatility', 'Warmup', 'Potential']]
    colors_adj = ['#3498db', '#9b59b6', '#e67e22', '#1abc9c']
    ax5.barh(components, values, color=colors_adj, alpha=0.7)
    ax5.axvline(x=1.0, color='red', linestyle='--', linewidth=1, alpha=0.5)
    ax5.set_xlabel('Factor')
    ax5.set_title(f'Initial Adjustments ({initial_factors["Total"]:.2f}x)', fontweight='bold', fontsize=10)
    ax5.grid(axis='x', alpha=0.3)
    
    # Bottom center: Final adjustments
    ax6 = fig.add_subplot(gs[2, 1])
    final_factors = adjustment_factors['Final']
    components = ['Calib', 'Stab', 'Mat', 'Eff']
    values = [final_factors[c] for c in ['Calibration', 'Stability', 'Maturity', 'Efficiency']]
    colors_adj = ['#f39c12', '#27ae60', '#3498db', '#e74c3c']
    ax6.barh(components, values, color=colors_adj, alpha=0.7)
    ax6.axvline(x=1.0, color='red', linestyle='--', linewidth=1, alpha=0.5)
    ax6.set_xlabel('Factor')
    ax6.set_title(f'Final Adjustments ({final_factors["Total"]:.2f}x)', fontweight='bold', fontsize=10)
    ax6.grid(axis='x', alpha=0.3)
    
    # Bottom right: Consistency
    ax7 = fig.add_subplot(gs[2, 2])
    mean_acc = np.mean(accuracies)
    std_acc = np.std(accuracies)
    ax7.bar(phases, accuracies, color=colors, alpha=0.7, edgecolor='black')
    ax7.axhline(y=mean_acc, color='red', linestyle='--', linewidth=2)
    ax7.axhspan(mean_acc - std_acc, mean_acc + std_acc, alpha=0.2, color='red')
    ax7.set_ylabel('Accuracy (%)')
    ax7.set_title(f'Consistency (σ={std_acc:.1f}%)', fontweight='bold', fontsize=10)
    ax7.set_ylim(0, 100)
    ax7.grid(axis='y', alpha=0.3)
    
    plt.savefig('v5_3_comprehensive_dashboard.png', dpi=300, bbox_inches='tight')
    print("✅ Created: v5_3_comprehensive_dashboard.png")
    plt.close()


def main():
    """Generate all visualizations"""
    print("🎨 Generating V5.3 Model Visualizations...")
    print()
    
    create_phase_accuracy_chart()
    create_prediction_comparison()
    create_utilization_analysis()
    create_adjustment_breakdown()
    create_architecture_flow()
    create_consistency_analysis()
    create_comprehensive_dashboard()
    
    print()
    print("=" * 60)
    print("✅ All V5.3 visualizations generated successfully!")
    print("=" * 60)
    print()
    print("Generated files:")
    print("  1. v5_3_phase_accuracy.png")
    print("  2. v5_3_prediction_comparison.png")
    print("  3. v5_3_utilization_analysis.png")
    print("  4. v5_3_adjustment_breakdown.png")
    print("  5. v5_3_architecture_flow.png")
    print("  6. v5_3_consistency_analysis.png")
    print("  7. v5_3_comprehensive_dashboard.png")
    print()


if __name__ == '__main__':
    main()

