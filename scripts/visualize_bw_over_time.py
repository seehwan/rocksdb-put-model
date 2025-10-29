#!/usr/bin/env python3
"""
Visualize compaction and flush bandwidth over time
Y-axis: bandwidth (MB/s or MB/hour)
X-axis: time
"""

import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import pandas as pd

def parse_sizes(s):
    """Parse file sizes from input/output lists"""
    sizes = []
    matches = re.findall(r'(\d+)\(([\d.]+)(\w+)\)', s)
    for match in matches:
        size = float(match[1])
        unit = match[2]
        
        if unit == 'KB':
            size /= 1000
        elif unit == 'GB':
            size *= 1000
        elif unit == 'MB':
            pass
        else:
            continue
        
        sizes.append(size)
    return sizes

def parse_log_file(log_path):
    """Parse compaction and flush events with sizes and timestamps"""
    
    compaction_pattern = re.compile(
        r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)'
        r'.*?Compaction start summary.*?Base level (\d+),'
        r'\s+inputs:\s+\[([^\]]+)\],?\s*\[?([^\]]*)\]?'
    )
    
    flush_pattern = re.compile(
        r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)'
        r'.*?Level-0 flush table.*?(\d+)\s+bytes'
    )
    
    compactions = []
    flushes = []
    
    print("Parsing LOG file...")
    line_count = 0
    
    with open(log_path, 'r') as f:
        for line in f:
            line_count += 1
            if line_count % 500000 == 0:
                print(f"  Processed {line_count:,} lines...")
            
            # Parse compaction
            m = compaction_pattern.search(line)
            if m:
                timestamp_str = m.group(1)
                level = int(m.group(2))
                inputs_str = m.group(3)
                outputs_str = m.group(4) if len(m.groups()) > 3 and m.group(4) else ""
                
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y/%m/%d-%H:%M:%S.%f')
                    
                    input_sizes = parse_sizes(inputs_str)
                    output_sizes = parse_sizes(outputs_str)
                    
                    input_total = sum(input_sizes)
                    output_total = sum(output_sizes) if output_sizes else 0
                    
                    compactions.append({
                        'time': timestamp,
                        'level': level,
                        'size_mb': input_total + output_total
                    })
                except Exception as e:
                    pass
            
            # Parse flush
            m = flush_pattern.search(line)
            if m:
                timestamp_str = m.group(1)
                size_bytes = int(m.group(2))
                size_mb = size_bytes / (1024 * 1024)
                
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y/%m/%d-%H:%M:%S.%f')
                    
                    flushes.append({
                        'time': timestamp,
                        'size_mb': size_mb
                    })
                except:
                    pass
    
    return compactions, flushes

def calculate_hourly_bandwidth(events, start_time):
    """Calculate bandwidth over 1-hour windows"""
    
    if not events:
        return [], []
    
    # Create DataFrame for easier aggregation
    df = pd.DataFrame(events)
    df['time_hours'] = [(t - start_time).total_seconds() / 3600 for t in df['time']]
    
    # Group by hour
    df['hour'] = df['time_hours'].astype(int)
    
    hourly = df.groupby('hour').agg({
        'size_mb': ['sum', 'count']
    }).reset_index()
    
    hourly.columns = ['hour', 'total_mb', 'count']
    hourly['bandwidth_mb_per_hour'] = hourly['total_mb']
    
    return hourly['hour'].values, hourly['bandwidth_mb_per_hour'].values

def create_visualization(compactions, flushes, phase_boundaries, output_path):
    """Create visualization of bandwidth over time"""
    
    if not compactions or not flushes:
        print("No data to visualize")
        return
    
    # Separate by phase
    start_time = compactions[0]['time']
    
    initial_end, middle_end = phase_boundaries
    
    # Add time_hours column
    for c in compactions:
        c['time_hours'] = (c['time'] - start_time).total_seconds() / 3600
    for f in flushes:
        f['time_hours'] = (f['time'] - start_time).total_seconds() / 3600
    
    initial_comp = [c for c in compactions if c['time_hours'] < initial_end]
    middle_comp = [c for c in compactions if initial_end <= c['time_hours'] < middle_end]
    final_comp = [c for c in compactions if c['time_hours'] >= middle_end]
    
    initial_flush = [f for f in flushes if f['time_hours'] < initial_end]
    middle_flush = [f for f in flushes if initial_end <= f['time_hours'] < middle_end]
    final_flush = [f for f in flushes if f['time_hours'] >= middle_end]
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Compaction bandwidth over time (scatter)
    ax = axes[0, 0]
    
    for phase_data, label, color in [
        (initial_comp, 'Initial', 'red'),
        (middle_comp, 'Middle', 'blue'),
        (final_comp, 'Final', 'green')
    ]:
        if phase_data:
            times = [c['time_hours'] for c in phase_data]
            sizes = [c['size_mb'] for c in phase_data]
            ax.scatter(times, sizes, label=label, alpha=0.3, s=5, c=color)
    
    ax.axvline(x=9.81, color='r', linestyle='--', linewidth=2, alpha=0.5)
    ax.axvline(x=42.0, color='r', linestyle='--', linewidth=2, alpha=0.5)
    ax.set_xlabel('Time (hours)', fontsize=20, family='Times New Roman')
    ax.set_ylabel('Compaction Size (MB)', fontsize=20, family='Times New Roman')
    ax.set_title('Compaction Size Over Time', fontsize=22, family='Times New Roman')
    ax.legend(fontsize=16)
    ax.tick_params(labelsize=18)
    ax.grid(True, alpha=0.3)
    
    # 2. Flush bandwidth over time (scatter)
    ax = axes[0, 1]
    
    for phase_data, label, color in [
        (initial_flush, 'Initial', 'red'),
        (middle_flush, 'Middle', 'blue'),
        (final_flush, 'Final', 'green')
    ]:
        if phase_data:
            times = [f['time_hours'] for f in phase_data]
            sizes = [f['size_mb'] for f in phase_data]
            ax.scatter(times, sizes, label=label, alpha=0.3, s=5, c=color)
    
    ax.axvline(x=9.81, color='r', linestyle='--', linewidth=2, alpha=0.5)
    ax.axvline(x=42.0, color='r', linestyle='--', linewidth=2, alpha=0.5)
    ax.set_xlabel('Time (hours)', fontsize=20, family='Times New Roman')
    ax.set_ylabel('Flush Size (MB)', fontsize=20, family='Times New Roman')
    ax.set_title('Flush Size Over Time', fontsize=22, family='Times New Roman')
    ax.legend(fontsize=16)
    ax.tick_params(labelsize=18)
    ax.grid(True, alpha=0.3)
    
    # 3. Hourly bandwidth for compaction (MB/s)
    ax = axes[1, 0]
    
    # Calculate hourly bandwidth
    df_comp = pd.DataFrame(compactions)
    df_comp['hour'] = df_comp['time_hours'].astype(int)
    hourly_comp = df_comp.groupby('hour')['size_mb'].sum().reset_index()
    
    # Convert MB/hour to MB/s by dividing by 3600
    hourly_comp['size_mb_per_s'] = hourly_comp['size_mb'] / 3600
    
    ax.plot(hourly_comp['hour'], hourly_comp['size_mb_per_s'], 
            linewidth=3, c='blue', alpha=0.7, label='Total Compaction BW')
    ax.fill_between(hourly_comp['hour'], 0, hourly_comp['size_mb_per_s'], alpha=0.3)
    
    ax.axvline(x=9.81, color='r', linestyle='--', linewidth=2, alpha=0.5)
    ax.axvline(x=42.0, color='r', linestyle='--', linewidth=2, alpha=0.5)
    ax.set_xlabel('Time (hours)', fontsize=20, family='Times New Roman')
    ax.set_ylabel('Bandwidth (MB/s)', fontsize=20, family='Times New Roman')
    ax.set_title('Compaction Bandwidth (MB/s)', fontsize=22, family='Times New Roman')
    ax.legend(fontsize=16)
    ax.tick_params(labelsize=18)
    ax.grid(True, alpha=0.3)
    
    # 4. Hourly bandwidth for flush (MB/s)
    ax = axes[1, 1]
    
    df_flush = pd.DataFrame(flushes)
    df_flush['hour'] = df_flush['time_hours'].astype(int)
    hourly_flush = df_flush.groupby('hour')['size_mb'].sum().reset_index()
    
    # Convert MB/hour to MB/s by dividing by 3600
    hourly_flush['size_mb_per_s'] = hourly_flush['size_mb'] / 3600
    
    ax.plot(hourly_flush['hour'], hourly_flush['size_mb_per_s'],
            linewidth=3, c='orange', alpha=0.7, label='Total Flush BW')
    ax.fill_between(hourly_flush['hour'], 0, hourly_flush['size_mb_per_s'], alpha=0.3)
    
    ax.axvline(x=9.81, color='r', linestyle='--', linewidth=2, alpha=0.5)
    ax.axvline(x=42.0, color='r', linestyle='--', linewidth=2, alpha=0.5)
    ax.set_xlabel('Time (hours)', fontsize=20, family='Times New Roman')
    ax.set_ylabel('Bandwidth (MB/s)', fontsize=20, family='Times New Roman')
    ax.set_title('Flush Bandwidth (MB/s)', fontsize=22, family='Times New Roman')
    ax.legend(fontsize=16)
    ax.tick_params(labelsize=18)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nVisualization saved: {output_path}")

def main():
    log_path = 'experiments/2025-09-12/rocksdb_log_phase_b.log'
    output_path = 'figs/bw_over_time.png'
    
    print("=" * 60)
    print("Analyzing Bandwidth Over Time")
    print("=" * 60)
    
    # Parse LOG file
    compactions, flushes = parse_log_file(log_path)
    
    print(f"\nExtracted events:")
    print(f"  Compactions: {len(compactions)}")
    print(f"  Flushes: {len(flushes)}")
    
    if compactions:
        print(f"  Avg compaction size: {np.mean([c['size_mb'] for c in compactions]):.1f} MB")
        total_comp_mb = sum([c['size_mb'] for c in compactions])
        print(f"  Total compaction data: {total_comp_mb/1000:.1f} GB")
    
    if flushes:
        print(f"  Avg flush size: {np.mean([f['size_mb'] for f in flushes]):.1f} MB")
        total_flush_mb = sum([f['size_mb'] for f in flushes])
        print(f"  Total flush data: {total_flush_mb/1000:.1f} GB")
    
    # Create visualization
    create_visualization(compactions, flushes, (9.81, 42.0), output_path)
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()

