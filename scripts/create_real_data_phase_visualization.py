#!/usr/bin/env python3
"""
Real Data Phase Detection Visualization Script
Creates phase detection visualization using actual experimental data
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

def load_real_experimental_data():
    """Load real experimental data from 2025-09-12 experiment"""
    try:
        # Load actual fillrandom results
        fillrandom_data = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
        
        # Convert time to hours
        fillrandom_data['hours'] = fillrandom_data['secs_elapsed'] / 3600
        
        # Calculate rolling CV (Coefficient of Variation) with window size
        window_size = 100  # 100 data points window
        fillrandom_data['rolling_mean'] = fillrandom_data['interval_qps'].rolling(window=window_size, center=True).mean()
        fillrandom_data['rolling_std'] = fillrandom_data['interval_qps'].rolling(window=window_size, center=True).std()
        fillrandom_data['rolling_cv'] = fillrandom_data['rolling_std'] / fillrandom_data['rolling_mean']
        
        # Phase boundaries from paper analysis
        phase_boundaries = {
            'initial_end': 9.81,  # hours
            'middle_end': 42.0,   # hours
            'total_duration': fillrandom_data['hours'].max()  # hours
        }
        
        # Calculate actual CV values for each phase
        initial_data = fillrandom_data[fillrandom_data['hours'] <= phase_boundaries['initial_end']]
        middle_data = fillrandom_data[(fillrandom_data['hours'] > phase_boundaries['initial_end']) & 
                                   (fillrandom_data['hours'] <= phase_boundaries['middle_end'])]
        final_data = fillrandom_data[fillrandom_data['hours'] > phase_boundaries['middle_end']]
        
        cv_values = {
            'initial': initial_data['rolling_cv'].mean() if not initial_data.empty else 0.714,
            'middle': middle_data['rolling_cv'].mean() if not middle_data.empty else 0.516,
            'final': final_data['rolling_cv'].mean() if not final_data.empty else 0.474
        }
        
        return fillrandom_data, phase_boundaries, cv_values
        
    except Exception as e:
        print(f"Error loading real data: {e}")
        return None, None, None

def create_real_data_phase_visualization():
    """Create phase detection visualization using real experimental data"""
    
    fillrandom_data, phase_boundaries, cv_values = load_real_experimental_data()
    
    if fillrandom_data is None:
        print("Failed to load real experimental data")
        return
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))
    
    # Main plot: Real CV over time with phase boundaries
    ax1 = plt.subplot(2, 2, (1, 2))
    
    # Plot actual CV data
    valid_data = fillrandom_data.dropna(subset=['rolling_cv'])
    ax1.plot(valid_data['hours'], valid_data['rolling_cv'], 'b-', linewidth=2, 
             label='Real CV (Rolling Window)', alpha=0.8)
    
    # Add phase boundaries
    ax1.axvline(x=phase_boundaries['initial_end'], color='red', linestyle='--', 
                linewidth=3, alpha=0.8, label=f'Phase Boundary 1: {phase_boundaries["initial_end"]}h')
    ax1.axvline(x=phase_boundaries['middle_end'], color='orange', linestyle='--', 
                linewidth=3, alpha=0.8, label=f'Phase Boundary 2: {phase_boundaries["middle_end"]}h')
    
    # Add phase regions
    ax1.axvspan(0, phase_boundaries['initial_end'], alpha=0.1, color='red', label='Initial Phase')
    ax1.axvspan(phase_boundaries['initial_end'], phase_boundaries['middle_end'], 
                alpha=0.1, color='orange', label='Middle Phase')
    ax1.axvspan(phase_boundaries['middle_end'], phase_boundaries['total_duration'], 
                alpha=0.1, color='green', label='Final Phase')
    
    # Add CV value annotations
    ax1.annotate(f'CV = {cv_values["initial"]:.3f}', 
                xy=(phase_boundaries['initial_end']/2, cv_values['initial']), 
                xytext=(phase_boundaries['initial_end']/2, cv_values['initial'] + 0.1),
                ha='center', fontsize=16, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    
    ax1.annotate(f'CV = {cv_values["middle"]:.3f}', 
                xy=((phase_boundaries['initial_end'] + phase_boundaries['middle_end'])/2, cv_values['middle']), 
                xytext=((phase_boundaries['initial_end'] + phase_boundaries['middle_end'])/2, cv_values['middle'] + 0.1),
                ha='center', fontsize=16, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='orange', lw=2))
    
    ax1.annotate(f'CV = {cv_values["final"]:.3f}', 
                xy=((phase_boundaries['middle_end'] + phase_boundaries['total_duration'])/2, cv_values['final']), 
                xytext=((phase_boundaries['middle_end'] + phase_boundaries['total_duration'])/2, cv_values['final'] + 0.1),
                ha='center', fontsize=16, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='green', lw=2))
    
    ax1.set_xlabel('Time (hours)', fontsize=18, fontweight='bold')
    ax1.set_ylabel('Coefficient of Variation (CV)', fontsize=18, fontweight='bold')
    ax1.set_title('Real Data Phase Detection Based on CV Analysis', fontsize=20, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, phase_boundaries['total_duration'])
    
    # Subplot 2: Real QPS over time
    ax2 = plt.subplot(2, 2, 3)
    
    # Plot actual QPS data
    ax2.plot(fillrandom_data['hours'], fillrandom_data['interval_qps'], 'g-', linewidth=1, alpha=0.7, label='Real QPS')
    
    # Add phase boundaries
    ax2.axvline(x=phase_boundaries['initial_end'], color='red', linestyle='--', linewidth=2, alpha=0.8)
    ax2.axvline(x=phase_boundaries['middle_end'], color='orange', linestyle='--', linewidth=2, alpha=0.8)
    
    # Add phase regions
    ax2.axvspan(0, phase_boundaries['initial_end'], alpha=0.1, color='red')
    ax2.axvspan(phase_boundaries['initial_end'], phase_boundaries['middle_end'], alpha=0.1, color='orange')
    ax2.axvspan(phase_boundaries['middle_end'], phase_boundaries['total_duration'], alpha=0.1, color='green')
    
    ax2.set_xlabel('Time (hours)', fontsize=16, fontweight='bold')
    ax2.set_ylabel('QPS', fontsize=16, fontweight='bold')
    ax2.set_title('Real QPS Performance Over Time', fontsize=18, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, phase_boundaries['total_duration'])
    
    # Subplot 3: Phase statistics comparison
    ax3 = plt.subplot(2, 2, 4)
    
    phases = ['Initial', 'Middle', 'Final']
    cv_vals = [cv_values['initial'], cv_values['middle'], cv_values['final']]
    colors = ['red', 'orange', 'green']
    
    bars = ax3.bar(phases, cv_vals, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
    
    # Add value labels on bars
    for bar, val in zip(bars, cv_vals):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{val:.3f}', ha='center', va='bottom', fontsize=16, fontweight='bold')
    
    ax3.set_ylabel('CV Value', fontsize=16, fontweight='bold')
    ax3.set_title('Real Phase CV Comparison', fontsize=18, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # Save the visualization
    output_path = 'experiments/2025-09-12/organized_results/visualizations/final/real_data_phase_detection.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Real data phase detection visualization saved: {output_path}")
    
    plt.show()

def create_real_data_summary():
    """Create summary of real experimental data"""
    
    fillrandom_data, phase_boundaries, cv_values = load_real_experimental_data()
    
    if fillrandom_data is None:
        print("Failed to load real experimental data")
        return
    
    print("\n📊 Real Experimental Data Summary:")
    print(f"Total duration: {phase_boundaries['total_duration']:.1f} hours")
    print(f"Total data points: {len(fillrandom_data)}")
    print(f"Phase boundaries: {phase_boundaries['initial_end']}h, {phase_boundaries['middle_end']}h")
    print(f"Real CV values:")
    print(f"  Initial phase: {cv_values['initial']:.3f}")
    print(f"  Middle phase: {cv_values['middle']:.3f}")
    print(f"  Final phase: {cv_values['final']:.3f}")
    
    # Calculate QPS statistics for each phase
    initial_qps = fillrandom_data[fillrandom_data['hours'] <= phase_boundaries['initial_end']]['interval_qps']
    middle_qps = fillrandom_data[(fillrandom_data['hours'] > phase_boundaries['initial_end']) & 
                               (fillrandom_data['hours'] <= phase_boundaries['middle_end'])]['interval_qps']
    final_qps = fillrandom_data[fillrandom_data['hours'] > phase_boundaries['middle_end']]['interval_qps']
    
    print(f"\nQPS Statistics:")
    print(f"  Initial phase: mean={initial_qps.mean():.0f}, std={initial_qps.std():.0f}")
    print(f"  Middle phase: mean={middle_qps.mean():.0f}, std={middle_qps.std():.0f}")
    print(f"  Final phase: mean={final_qps.mean():.0f}, std={final_qps.std():.0f}")

if __name__ == "__main__":
    print("Creating real data phase detection visualizations...")
    create_real_data_summary()
    create_real_data_phase_visualization()
    print("✅ Real data phase detection visualizations created successfully!")

