"""
PutModel v4: Closed Ledger Accounting

This module implements the Closed Ledger Accounting system for RocksDB performance analysis.
It provides physical verification of write amplification and read amplification calculations.

Key Features:
- Standardized accounting definitions for WA/RA
- Physical verification of ledger closure
- Per-level I/O breakdown
- Support for multiple data sources (LOG, statistics, iostat)
"""

import json
import re
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import warnings


class ClosedLedger:
    """
    Closed Ledger Accounting system for RocksDB performance analysis.
    
    This class implements standardized accounting definitions and verifies
    that the ledger closes within acceptable tolerances.
    """
    
    def __init__(self):
        """Initialize the closed ledger system."""
        self.ledger_data = {}
        self.verification_results = {}
        
    def parse_rocksdb_log(self, log_path: str) -> Dict:
        """
        Parse RocksDB LOG file to extract I/O statistics.
        
        Args:
            log_path: Path to RocksDB LOG file
            
        Returns:
            Dictionary with parsed I/O statistics
        """
        log_data = {
            'wal_bytes': 0,
            'flush_bytes': 0,
            'compaction_read_bytes': 0,
            'compaction_write_bytes': 0,
            'user_write_bytes': 0,
            'device_read_bytes': 0,
            'device_write_bytes': 0,
            'per_level_stats': {}
        }
        
        with open(log_path, 'r') as f:
            for line in f:
                # Parse WAL writes
                if 'WAL write' in line:
                    match = re.search(r'(\d+) bytes', line)
                    if match:
                        log_data['wal_bytes'] += int(match.group(1))
                
                # Parse flush operations
                elif 'flush' in line.lower() and 'bytes' in line:
                    match = re.search(r'(\d+) bytes', line)
                    if match:
                        log_data['flush_bytes'] += int(match.group(1))
                
                # Parse compaction operations
                elif 'compaction' in line.lower() and 'bytes' in line:
                    # Extract read bytes
                    read_match = re.search(r'(\d+) bytes read', line)
                    if read_match:
                        log_data['compaction_read_bytes'] += int(read_match.group(1))
                    
                    # Extract write bytes
                    write_match = re.search(r'(\d+) bytes written', line)
                    if write_match:
                        log_data['compaction_write_bytes'] += int(write_match.group(1))
                
                # Parse user writes
                elif 'user write' in line.lower() and 'bytes' in line:
                    match = re.search(r'(\d+) bytes', line)
                    if match:
                        log_data['user_write_bytes'] += int(match.group(1))
        
        return log_data
    
    def parse_statistics_json(self, stats_path: str) -> Dict:
        """
        Parse RocksDB statistics JSON file.
        
        Args:
            stats_path: Path to statistics JSON file
            
        Returns:
            Dictionary with parsed statistics
        """
        with open(stats_path, 'r') as f:
            stats = json.load(f)
        
        # Extract relevant statistics
        stats_data = {
            'wal_bytes': stats.get('WAL_BYTES_WRITTEN', 0),
            'flush_bytes': stats.get('FLUSH_BYTES_WRITTEN', 0),
            'compaction_read_bytes': stats.get('COMPACT_READ_BYTES', 0),
            'compaction_write_bytes': stats.get('COMPACT_WRITE_BYTES', 0),
            'user_write_bytes': stats.get('USER_WRITE_BYTES', 0),
            'per_level_stats': {}
        }
        
        # Extract per-level statistics
        for key, value in stats.items():
            if 'LEVEL' in key and 'BYTES' in key:
                level_match = re.search(r'LEVEL(\d+)', key)
                if level_match:
                    level = int(level_match.group(1))
                    if level not in stats_data['per_level_stats']:
                        stats_data['per_level_stats'][level] = {}
                    
                    if 'READ' in key:
                        stats_data['per_level_stats'][level]['read_bytes'] = value
                    elif 'WRITE' in key:
                        stats_data['per_level_stats'][level]['write_bytes'] = value
        
        return stats_data
    
    def calculate_wa_ra(self, data: Dict) -> Dict:
        """
        Calculate Write Amplification and Read Amplification.
        
        Args:
            data: Dictionary with I/O statistics
            
        Returns:
            Dictionary with WA/RA calculations
        """
        # Extract data
        wal_bytes = data.get('wal_bytes', 0)
        flush_bytes = data.get('flush_bytes', 0)
        compaction_read_bytes = data.get('compaction_read_bytes', 0)
        compaction_write_bytes = data.get('compaction_write_bytes', 0)
        user_write_bytes = data.get('user_write_bytes', 0)
        device_read_bytes = data.get('device_read_bytes', 0)
        device_write_bytes = data.get('device_write_bytes', 0)
        
        # Calculate WA (Write Amplification)
        wa_stat = (wal_bytes + flush_bytes + compaction_write_bytes) / user_write_bytes if user_write_bytes > 0 else 0
        wa_device = device_write_bytes / user_write_bytes if user_write_bytes > 0 else 0
        
        # Calculate RA (Read Amplification)
        ra_comp = compaction_read_bytes / user_write_bytes if user_write_bytes > 0 else 0
        ra_runtime = device_read_bytes / user_write_bytes if user_write_bytes > 0 else 0
        
        return {
            'wa_stat': wa_stat,
            'wa_device': wa_device,
            'ra_comp': ra_comp,
            'ra_runtime': ra_runtime,
            'user_write_bytes': user_write_bytes,
            'wal_bytes': wal_bytes,
            'flush_bytes': flush_bytes,
            'compaction_read_bytes': compaction_read_bytes,
            'compaction_write_bytes': compaction_write_bytes,
            'device_read_bytes': device_read_bytes,
            'device_write_bytes': device_write_bytes
        }
    
    def verify_ledger_closure(self, wa_ra_data: Dict, tolerance: float = 0.1) -> Dict:
        """
        Verify that the ledger closes within acceptable tolerances.
        
        Args:
            wa_ra_data: Dictionary with WA/RA calculations
            tolerance: Acceptable tolerance for closure verification (default: 10%)
            
        Returns:
            Dictionary with verification results
        """
        wa_stat = wa_ra_data['wa_stat']
        wa_device = wa_ra_data['wa_device']
        
        # Calculate closure error
        closure_error = abs(wa_stat - wa_device) / max(wa_stat, wa_device) if max(wa_stat, wa_device) > 0 else 0
        
        # Check if ledger closes
        is_closed = closure_error <= tolerance
        
        verification = {
            'is_closed': is_closed,
            'closure_error': closure_error,
            'tolerance': tolerance,
            'wa_stat': wa_stat,
            'wa_device': wa_device,
            'difference': abs(wa_stat - wa_device),
            'relative_difference': closure_error * 100  # Convert to percentage
        }
        
        if not is_closed:
            warnings.warn(
                f"Ledger does not close within tolerance. "
                f"Error: {closure_error:.1%}, Tolerance: {tolerance:.1%}"
            )
        
        return verification
    
    def create_ledger_summary(self, data: Dict, wa_ra_data: Dict, verification: Dict) -> pd.DataFrame:
        """
        Create a comprehensive ledger summary DataFrame.
        
        Args:
            data: Raw I/O statistics
            wa_ra_data: WA/RA calculations
            verification: Verification results
            
        Returns:
            pandas DataFrame with ledger summary
        """
        summary_data = {
            'Metric': [
                'User Write (GB)',
                'WAL Write (GB)',
                'Flush Write (GB)',
                'Compaction Read (GB)',
                'Compaction Write (GB)',
                'Device Read (GB)',
                'Device Write (GB)',
                'WA (Statistics)',
                'WA (Device)',
                'RA (Compaction)',
                'RA (Runtime)',
                'Ledger Closure Error (%)',
                'Ledger Closed'
            ],
            'Value': [
                wa_ra_data['user_write_bytes'] / (1024**3),
                wa_ra_data['wal_bytes'] / (1024**3),
                wa_ra_data['flush_bytes'] / (1024**3),
                wa_ra_data['compaction_read_bytes'] / (1024**3),
                wa_ra_data['compaction_write_bytes'] / (1024**3),
                wa_ra_data['device_read_bytes'] / (1024**3),
                wa_ra_data['device_write_bytes'] / (1024**3),
                wa_ra_data['wa_stat'],
                wa_ra_data['wa_device'],
                wa_ra_data['ra_comp'],
                wa_ra_data['ra_runtime'],
                verification['relative_difference'],
                verification['is_closed']
            ]
        }
        
        return pd.DataFrame(summary_data)
    
    def process_rocksdb_data(self, log_path: str, stats_path: Optional[str] = None, 
                           iostat_path: Optional[str] = None) -> Dict:
        """
        Process RocksDB data from multiple sources and create ledger.
        
        Args:
            log_path: Path to RocksDB LOG file
            stats_path: Path to statistics JSON file (optional)
            iostat_path: Path to iostat data file (optional)
            
        Returns:
            Dictionary with complete ledger analysis
        """
        # Parse LOG file
        log_data = self.parse_rocksdb_log(log_path)
        
        # Parse statistics if available
        if stats_path and Path(stats_path).exists():
            stats_data = self.parse_statistics_json(stats_path)
            # Merge statistics data
            for key, value in stats_data.items():
                if key != 'per_level_stats':
                    log_data[key] = max(log_data.get(key, 0), value)
        
        # Parse iostat data if available
        if iostat_path and Path(iostat_path).exists():
            iostat_data = self.parse_iostat_data(iostat_path)
            log_data.update(iostat_data)
        
        # Calculate WA/RA
        wa_ra_data = self.calculate_wa_ra(log_data)
        
        # Verify ledger closure
        verification = self.verify_ledger_closure(wa_ra_data)
        
        # Create summary
        summary_df = self.create_ledger_summary(log_data, wa_ra_data, verification)
        
        return {
            'raw_data': log_data,
            'wa_ra_data': wa_ra_data,
            'verification': verification,
            'summary': summary_df
        }
    
    def parse_iostat_data(self, iostat_path: str) -> Dict:
        """
        Parse iostat data file.
        
        Args:
            iostat_path: Path to iostat data file
            
        Returns:
            Dictionary with device I/O statistics
        """
        # This is a placeholder implementation
        # In practice, you would parse iostat output to extract device read/write bytes
        return {
            'device_read_bytes': 0,
            'device_write_bytes': 0
        }
    
    def save_ledger_csv(self, ledger_data: Dict, output_path: str):
        """
        Save ledger data to CSV file.
        
        Args:
            ledger_data: Complete ledger analysis data
            output_path: Output CSV file path
        """
        ledger_data['summary'].to_csv(output_path, index=False)
        print(f"Ledger summary saved to: {output_path}")


def main():
    """Example usage of the ClosedLedger class."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process RocksDB data for closed ledger accounting')
    parser.add_argument('log_path', help='Path to RocksDB LOG file')
    parser.add_argument('--stats', help='Path to statistics JSON file')
    parser.add_argument('--iostat', help='Path to iostat data file')
    parser.add_argument('--output', '-o', default='ledger_summary.csv', 
                       help='Output CSV file path')
    
    args = parser.parse_args()
    
    # Create ledger instance
    ledger = ClosedLedger()
    
    # Process data
    print("Processing RocksDB data...")
    ledger_data = ledger.process_rocksdb_data(
        log_path=args.log_path,
        stats_path=args.stats,
        iostat_path=args.iostat
    )
    
    # Print summary
    print("\nLedger Summary:")
    print(ledger_data['summary'].to_string(index=False))
    
    # Print verification results
    verification = ledger_data['verification']
    print(f"\nLedger Closure Verification:")
    print(f"  Closed: {verification['is_closed']}")
    print(f"  Error: {verification['relative_difference']:.2f}%")
    print(f"  Tolerance: {verification['tolerance']:.1%}")
    
    # Save to CSV
    ledger.save_ledger_csv(ledger_data, args.output)


if __name__ == "__main__":
    main()
