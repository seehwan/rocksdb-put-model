#!/usr/bin/env python3
"""
Time-based S_max Visualization Script
Creates visualization showing S_max values over time from experimental data
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
from datetime import datetime, timedelta
import seaborn as sns

# Set style for publication quality
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.family': 'Times New Roman',
    'font.size': 18,
    'axes.titlesize': 20,
    'axes.labelsize': 18,
    'xtick.labelsize': 16,
    'ytick.labelsize': 16,
    'legend.fontsize': 16,
    'figure.titlesize': 22,
    'lines.linewidth': 2.5,
    'axes.linewidth': 1.5,
    'grid.linewidth': 1.0,
    'grid.alpha': 0.3
})

def load_experimental_data():
    """Load experimental data and calculate S_max values"""
    try:
        # Load actual fillrandom results
        fillrandom_data = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
        
        # Convert time to hours
        fillrandom_data['hours'] = fillrandom_data['secs_elapsed'] / 3600
        
        # Calculate S_max using the model formula
        # S_max = (B_w * U * μ_eff * B_eff * (1 - p_stall)) / (WA * CR)
        
        # Model parameters from paper
        B_w = 1484  # MiB/s (device write bandwidth)
        WA = 2.5     # Write Amplification
        CR = 1.2     # Compaction Ratio
        
        # Phase-specific parameters
        phase_boundaries = {
            'initial_end': 9.81,
            'middle_end': 42.0
        }
        
        def get_phase_params(hours):
            if hours <= phase_boundaries['initial_end']:
                # Initial phase
                U = 0.85
                μ_eff = 0.92
                B_eff = 0.78
                p_stall = 0.12
            elif hours <= phase_boundaries['middle_end']:
                # Middle phase
                U = 0.80
                μ_eff = 0.88
                B_eff = 0.75
                p_stall = 0.15
            else:
                # Final phase
                U = 0.90
                μ_eff = 0.95
                B_eff = 0.82
                p_stall = 0.08
            
            return U, μ_eff, B_eff, p_stall
        
        # Calculate S_max for each time point
        s_max_values = []
        for _, row in fillrandom_data.iterrows():
            hours = row['hours']
            U, μ_eff, B_eff, p_stall = get_phase_params(hours)
            
            # Calculate S_max
            s_max = (B_w * U * μ_eff * B_eff * (1 - p_stall)) / (WA * CR)
            s_max_values.append(s_max)
        
        fillrandom_data['s_max'] = s_max_values
        
        return fillrandom_data, phase_boundaries
        
    except Exception as e:
        print(f"Error loading experimental data: {e}")
        return None, None

def create_smax_time_visualization():
    """Create S_max over time visualization"""
    
    fillrandom_data, phase_boundaries = load_experimental_data()
    
    if fillrandom_data is None:
        print("Failed to load experimental data")
        return
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # Top plot: S_max over time
    ax1.plot(fillrandom_data['hours'], fillrandom_data['s_max'], 'b-', linewidth=2, 
             label='S_max (Maximum Sustainable Put Rate)', alpha=0.8)
    
    # Add phase boundaries
    ax1.axvline(x=phase_boundaries['initial_end'], color='red', linestyle='--', 
                linewidth=3, alpha=0.8, label=f'Phase Boundary 1: {phase_boundaries["initial_end"]}h')
    ax1.axvline(x=phase_boundaries['middle_end'], color='orange', linestyle='--', 
                linewidth=3, alpha=0.8, label=f'Phase Boundary 2: {phase_boundaries["middle_end"]}h')
    
    # Add phase regions
    ax1.axvspan(0, phase_boundaries['initial_end'], alpha=0.1, color='red', label='Initial Phase')
    ax1.axvspan(phase_boundaries['initial_end'], phase_boundaries['middle_end'], 
                alpha=0.1, color='orange', label='Middle Phase')
    ax1.axvspan(phase_boundaries['middle_end'], fillrandom_data['hours'].max(), 
                alpha=0.1, color='green', label='Final Phase')
    
    # Calculate phase averages
    initial_data = fillrandom_data[fillrandom_data['hours'] <= phase_boundaries['initial_end']]
    middle_data = fillrandom_data[(fillrandom_data['hours'] > phase_boundaries['initial_end']) & 
                                (fillrandom_data['hours'] <= phase_boundaries['middle_end'])]
    final_data = fillrandom_data[fillrandom_data['hours'] > phase_boundaries['middle_end']]
    
    initial_avg = initial_data['s_max'].mean()
    middle_avg = middle_data['s_max'].mean()
    final_avg = final_data['s_max'].mean()
    
    # Add average lines
    ax1.axhline(y=initial_avg, color='red', linestyle=':', linewidth=2, alpha=0.7, 
                label=f'Initial Avg: {initial_avg:.1f} MiB/s')
    ax1.axhline(y=middle_avg, color='orange', linestyle=':', linewidth=2, alpha=0.7, 
                label=f'Middle Avg: {middle_avg:.1f} MiB/s')
    ax1.axhline(y=final_avg, color='green', linestyle=':', linewidth=2, alpha=0.7, 
                label=f'Final Avg: {final_avg:.1f} MiB/s')
    
    ax1.set_xlabel('Time (hours)', fontsize=18, fontweight='bold')
    ax1.set_ylabel('S_max (MiB/s)', fontsize=18, fontweight='bold')
    ax1.set_title('Maximum Sustainable Put Rate (S_max) Over Time', fontsize=20, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, fillrandom_data['hours'].max())
    
    # Bottom plot: S_max vs Actual QPS comparison
    ax2.plot(fillrandom_data['hours'], fillrandom_data['s_max'], 'b-', linewidth=2, 
             label='S_max (Model Prediction)', alpha=0.8)
    ax2.plot(fillrandom_data['hours'], fillrandom_data['interval_qps'] / 1024 / 1024, 'g-', 
             linewidth=1, alpha=0.7, label='Actual QPS (MiB/s)')
    
    # Add phase boundaries
    ax2.axvline(x=phase_boundaries['initial_end'], color='red', linestyle='--', 
                linewidth=2, alpha=0.8)
    ax2.axvline(x=phase_boundaries['middle_end'], color='orange', linestyle='--', 
                linewidth=2, alpha=0.8)
    
    # Add phase regions
    ax2.axvspan(0, phase_boundaries['initial_end'], alpha=0.1, color='red')
    ax2.axvspan(phase_boundaries['initial_end'], phase_boundaries['middle_end'], 
                alpha=0.1, color='orange')
    ax2.axvspan(phase_boundaries['middle_end'], fillrandom_data['hours'].max(), 
                alpha=0.1, color='green')
    
    ax2.set_xlabel('Time (hours)', fontsize=18, fontweight='bold')
    ax2.set_ylabel('Throughput (MiB/s)', fontsize=18, fontweight='bold')
    ax2.set_title('S_max vs Actual Performance Comparison', fontsize=20, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=14)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, fillrandom_data['hours'].max())
    
    plt.tight_layout()
    
    # Save the visualization
    output_path = 'experiments/2025-09-12/organized_results/visualizations/final/smax_over_time.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ S_max over time visualization saved: {output_path}")
    
    plt.show()

def create_smax_phase_analysis():
    """Create detailed S_max phase analysis"""
    
    fillrandom_data, phase_boundaries = load_experimental_data()
    
    if fillrandom_data is None:
        print("Failed to load experimental data")
        return
    
    # Create figure
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Calculate phase data
    initial_data = fillrandom_data[fillrandom_data['hours'] <= phase_boundaries['initial_end']]
    middle_data = fillrandom_data[(fillrandom_data['hours'] > phase_boundaries['initial_end']) & 
                                (fillrandom_data['hours'] <= phase_boundaries['middle_end'])]
    final_data = fillrandom_data[fillrandom_data['hours'] > phase_boundaries['middle_end']]
    
    # Plot 1: S_max distribution by phase
    phases = ['Initial', 'Middle', 'Final']
    smax_means = [initial_data['s_max'].mean(), middle_data['s_max'].mean(), final_data['s_max'].mean()]
    smax_stds = [initial_data['s_max'].std(), middle_data['s_max'].std(), final_data['s_max'].std()]
    colors = ['red', 'orange', 'green']
    
    bars = ax1.bar(phases, smax_means, yerr=smax_stds, color=colors, alpha=0.7, 
                   edgecolor='black', linewidth=2, capsize=5)
    
    # Add value labels
    for bar, mean, std in zip(bars, smax_means, smax_stds):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + std + 10,
                f'{mean:.1f}±{std:.1f}', ha='center', va='bottom', 
                fontsize=14, fontweight='bold')
    
    ax1.set_ylabel('S_max (MiB/s)', fontsize=16, fontweight='bold')
    ax1.set_title('S_max Distribution by Phase', fontsize=18, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: S_max trend over time (smoothed)
    window_size = 1000  # Smoothing window
    fillrandom_data['smax_smooth'] = fillrandom_data['s_max'].rolling(window=window_size, center=True).mean()
    
    ax2.plot(fillrandom_data['hours'], fillrandom_data['smax_smooth'], 'b-', linewidth=3, 
             label='Smoothed S_max')
    
    # Add phase boundaries
    ax2.axvline(x=phase_boundaries['initial_end'], color='red', linestyle='--', linewidth=2)
    ax2.axvline(x=phase_boundaries['middle_end'], color='orange', linestyle='--', linewidth=2)
    
    ax2.set_xlabel('Time (hours)', fontsize=16, fontweight='bold')
    ax2.set_ylabel('S_max (MiB/s)', fontsize=16, fontweight='bold')
    ax2.set_title('Smoothed S_max Trend', fontsize=18, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=14)
    
    # Plot 3: S_max vs QPS scatter plot
    ax3.scatter(fillrandom_data['interval_qps'] / 1024 / 1024, fillrandom_data['s_max'], 
               alpha=0.6, s=1, c=fillrandom_data['hours'], cmap='viridis')
    
    # Add correlation line
    z = np.polyfit(fillrandom_data['interval_qps'] / 1024 / 1024, fillrandom_data['s_max'], 1)
    p = np.poly1d(z)
    ax3.plot(fillrandom_data['interval_qps'] / 1024 / 1024, p(fillrandom_data['interval_qps'] / 1024 / 1024), 
             "r--", alpha=0.8, linewidth=2, label=f'Trend: y={z[0]:.2f}x+{z[1]:.1f}')
    
    ax3.set_xlabel('Actual QPS (MiB/s)', fontsize=16, fontweight='bold')
    ax3.set_ylabel('S_max (MiB/s)', fontsize=16, fontweight='bold')
    ax3.set_title('S_max vs Actual QPS Correlation', fontsize=18, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=14)
    
    # Add colorbar
    cbar = plt.colorbar(ax3.collections[0], ax=ax3)
    cbar.set_label('Time (hours)', fontsize=14, fontweight='bold')
    
    # Plot 4: S_max efficiency over time
    fillrandom_data['efficiency'] = (fillrandom_data['interval_qps'] / 1024 / 1024) / fillrandom_data['s_max']
    fillrandom_data['efficiency_smooth'] = fillrandom_data['efficiency'].rolling(window=window_size, center=True).mean()
    
    ax4.plot(fillrandom_data['hours'], fillrandom_data['efficiency_smooth'], 'purple', linewidth=3, 
             label='S_max Utilization Efficiency')
    
    # Add phase boundaries
    ax4.axvline(x=phase_boundaries['initial_end'], color='red', linestyle='--', linewidth=2)
    ax4.axvline(x=phase_boundaries['middle_end'], color='orange', linestyle='--', linewidth=2)
    
    ax4.set_xlabel('Time (hours)', fontsize=16, fontweight='bold')
    ax4.set_ylabel('Efficiency Ratio', fontsize=16, fontweight='bold')
    ax4.set_title('S_max Utilization Efficiency Over Time', fontsize=18, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(fontsize=14)
    ax4.set_ylim(0, 1)
    
    plt.tight_layout()
    
    # Save the visualization
    output_path = 'experiments/2025-09-12/organized_results/visualizations/final/smax_phase_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ S_max phase analysis saved: {output_path}")
    
    plt.show()

def print_smax_statistics():
    """Print S_max statistics"""
    
    fillrandom_data, phase_boundaries = load_experimental_data()
    
    if fillrandom_data is None:
        print("Failed to load experimental data")
        return
    
    # Calculate efficiency first
    fillrandom_data['efficiency'] = (fillrandom_data['interval_qps'] / 1024 / 1024) / fillrandom_data['s_max']
    
    # Calculate phase data
    initial_data = fillrandom_data[fillrandom_data['hours'] <= phase_boundaries['initial_end']]
    middle_data = fillrandom_data[(fillrandom_data['hours'] > phase_boundaries['initial_end']) & 
                                (fillrandom_data['hours'] <= phase_boundaries['middle_end'])]
    final_data = fillrandom_data[fillrandom_data['hours'] > phase_boundaries['middle_end']]
    
    print("\n📊 S_max Statistics:")
    print(f"Overall S_max: mean={fillrandom_data['s_max'].mean():.1f} MiB/s, std={fillrandom_data['s_max'].std():.1f} MiB/s")
    print(f"Initial phase: mean={initial_data['s_max'].mean():.1f} MiB/s, std={initial_data['s_max'].std():.1f} MiB/s")
    print(f"Middle phase: mean={middle_data['s_max'].mean():.1f} MiB/s, std={middle_data['s_max'].std():.1f} MiB/s")
    print(f"Final phase: mean={final_data['s_max'].mean():.1f} MiB/s, std={final_data['s_max'].std():.1f} MiB/s")
    
    print(f"\nS_max Utilization Efficiency:")
    print(f"Overall: {fillrandom_data['efficiency'].mean():.3f}")
    print(f"Initial: {initial_data['efficiency'].mean():.3f}")
    print(f"Middle: {middle_data['efficiency'].mean():.3f}")
    print(f"Final: {final_data['efficiency'].mean():.3f}")

if __name__ == "__main__":
    print("Creating S_max time-based visualizations...")
    print_smax_statistics()
    create_smax_time_visualization()
    create_smax_phase_analysis()
    print("✅ S_max visualizations created successfully!")
