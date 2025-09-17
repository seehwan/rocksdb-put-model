"""
PutModel v4: Dynamic Simulation Framework

This module implements the v4 dynamic simulator for RocksDB put-rate prediction.
It incorporates Device Envelope Modeling, Closed Ledger Accounting, and dynamic simulation.

Key Features:
- Dynamic simulation with time-varying parameters
- Device envelope integration
- Per-level capacity modeling
- Backlog dynamics simulation
- Comprehensive logging and analysis
"""

import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import argparse
import yaml
from datetime import datetime

try:
    from .envelope import EnvelopeModel
    from .closed_ledger import ClosedLedger
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from envelope import EnvelopeModel
    from closed_ledger import ClosedLedger


class V4Simulator:
    """
    v4 Dynamic Simulator for RocksDB put-rate prediction.
    
    This class implements the complete v4 simulation framework including
    device envelope modeling, per-level capacity constraints, and backlog dynamics.
    """
    
    def __init__(self, envelope_model: EnvelopeModel, config: Dict):
        """
        Initialize the v4 simulator.
        
        Args:
            envelope_model: Device envelope model instance
            config: Simulation configuration dictionary
        """
        self.envelope = envelope_model
        self.config = config
        
        # Extract configuration
        self.levels = config.get('levels', [0, 1, 2, 3])
        self.dt = config.get('dt', 1.0)  # Time step in seconds
        self.max_steps = config.get('max_steps', 1000)
        
        # Device parameters
        self.device_config = config.get('device', {})
        self.qd = self.device_config.get('iodepth', 16)
        self.numjobs = self.device_config.get('numjobs', 2)
        self.bs_k = self.device_config.get('bs_k', 64)
        self.Br = self.device_config.get('Br', 1500)  # Read bandwidth MiB/s
        self.Bw = self.device_config.get('Bw', 2000)  # Write bandwidth MiB/s
        
        # DB parameters
        self.db_config = config.get('database', {})
        self.compression_ratio = self.db_config.get('compression_ratio', 0.54)
        self.wal_factor = self.db_config.get('wal_factor', 1.0)
        
        # Per-level parameters
        self.level_params = config.get('level_params', {})
        self._initialize_level_parameters()
        
        # Simulation state
        self.Q = {level: 0.0 for level in self.levels}  # Backlog queues (GiB)
        self.N_L0 = 0  # L0 file count
        self.t = 0.0  # Current time
        
        # Results storage
        self.results = []
        
    def _initialize_level_parameters(self):
        """Initialize per-level parameters from configuration."""
        # Default parameters for each level
        default_params = {
            'mu': 1.0,  # Scheduler efficiency
            'k': 1.0,   # Codec/block size factor
            'eta': 1.0, # Time-varying efficiency
            'capacity_factor': 1.0  # Capacity scaling factor
        }
        
        for level in self.levels:
            if level not in self.level_params:
                self.level_params[level] = default_params.copy()
    
    def _estimate_rho_r(self) -> float:
        """
        Estimate read ratio based on current system state.
        
        This is a heuristic implementation. In practice, this would be
        learned from LOG data or other sources.
        
        Returns:
            Estimated read ratio (0.0 to 1.0)
        """
        # Simple heuristic: higher L0 file count increases read ratio
        if self.N_L0 > 0:
            # Logistic function for smooth transition
            rho_r = 1.0 / (1.0 + np.exp(-0.1 * (self.N_L0 - 10)))
        else:
            rho_r = 0.0
        
        return min(rho_r, 0.5)  # Cap at 50% for stability
    
    def _calculate_stall_probability(self) -> float:
        """
        Calculate stall probability based on L0 file count.
        
        Returns:
            Stall probability (0.0 to 1.0)
        """
        # Logistic function for smooth stall transition
        threshold = self.config.get('stall_threshold', 8)
        steepness = self.config.get('stall_steepness', 0.5)
        
        p_stall = 1.0 / (1.0 + np.exp(-steepness * (self.N_L0 - threshold)))
        return min(p_stall, 0.9)  # Cap at 90% for stability
    
    def _calculate_level_capacity(self, level: int, rho_r: float) -> float:
        """
        Calculate per-level capacity using the envelope model.
        
        Args:
            level: LSM level
            rho_r: Read ratio
            
        Returns:
            Level capacity in MiB/s
        """
        # Get level parameters
        params = self.level_params[level]
        mu = params['mu']
        k = params['k']
        eta = params['eta']
        capacity_factor = params['capacity_factor']
        
        # Query envelope model for effective bandwidth
        Beff = self.envelope.query(
            rho_r=rho_r,
            qd=self.qd,
            numjobs=self.numjobs,
            bs_k=self.bs_k,
            Br=self.Br,
            Bw=self.Bw,
            clamp_to_physical=True
        )
        
        # Calculate level capacity
        C_level = mu * k * eta * capacity_factor * Beff
        
        return C_level
    
    def _calculate_workload_demands(self, S_put: float) -> Dict[int, float]:
        """
        Calculate per-level workload demands.
        
        Args:
            S_put: Put rate in MiB/s
            
        Returns:
            Dictionary mapping level to demand in MiB/s
        """
        demands = {}
        
        # L0: Flush demand
        demands[0] = S_put * self.compression_ratio
        
        # L1+: Compaction demands (simplified)
        for level in self.levels[1:]:
            # Simplified compaction demand calculation
            # In practice, this would be more sophisticated
            if level == 1:
                demands[level] = S_put * self.compression_ratio * 0.5
            else:
                demands[level] = S_put * self.compression_ratio * 0.1
        
        return demands
    
    def _update_backlog(self, demands: Dict[int, float], capacities: Dict[int, float]):
        """
        Update backlog queues based on demands and capacities.
        
        Args:
            demands: Per-level demands in MiB/s
            capacities: Per-level capacities in MiB/s
        """
        for level in self.levels:
            demand = demands.get(level, 0.0)
            capacity = capacities.get(level, 0.0)
            
            # Calculate net inflow/outflow
            net_flow = demand - capacity
            
            # Update backlog (convert MiB/s to GiB for storage)
            self.Q[level] += net_flow * self.dt / 1024  # Convert to GiB
            self.Q[level] = max(0.0, self.Q[level])  # Non-negative constraint
    
    def _update_l0_file_count(self, S_put: float, capacities: Dict[int, float]):
        """
        Update L0 file count based on put rate and L0 capacity.
        
        Args:
            S_put: Put rate in MiB/s
            capacities: Per-level capacities in MiB/s
        """
        # File size assumption (configurable)
        file_size_mb = self.config.get('l0_file_size_mb', 64)
        
        # Calculate file creation and consumption rates
        file_creation_rate = S_put / file_size_mb  # files per second
        file_consumption_rate = capacities.get(0, 0) / file_size_mb  # files per second
        
        # Update L0 file count
        net_file_rate = file_creation_rate - file_consumption_rate
        self.N_L0 += net_file_rate * self.dt
        self.N_L0 = max(0.0, self.N_L0)
    
    def simulate(self, steps: Optional[int] = None, dt: Optional[float] = None) -> pd.DataFrame:
        """
        Run the dynamic simulation.
        
        Args:
            steps: Number of simulation steps (optional)
            dt: Time step in seconds (optional)
            
        Returns:
            pandas DataFrame with simulation results
        """
        if steps is not None:
            self.max_steps = steps
        if dt is not None:
            self.dt = dt
        
        print(f"Starting v4 simulation: {self.max_steps} steps, dt={self.dt}s")
        
        # Reset simulation state
        self.Q = {level: 0.0 for level in self.levels}
        self.N_L0 = 0
        self.t = 0.0
        self.results = []
        
        # Target put rate (configurable)
        target_put_rate = self.config.get('target_put_rate', 200)  # MiB/s
        
        for step in range(self.max_steps):
            # Calculate stall probability
            p_stall = self._calculate_stall_probability()
            
            # Calculate actual put rate (reduced by stalls)
            S_put = target_put_rate * (1.0 - p_stall)
            
            # Estimate read ratio
            rho_r = self._estimate_rho_r()
            
            # Calculate per-level capacities
            capacities = {}
            for level in self.levels:
                capacities[level] = self._calculate_level_capacity(level, rho_r)
            
            # Calculate workload demands
            demands = self._calculate_workload_demands(S_put)
            
            # Update backlog queues
            self._update_backlog(demands, capacities)
            
            # Update L0 file count
            self._update_l0_file_count(S_put, capacities)
            
            # Store results
            result = {
                'step': step,
                'time': self.t,
                'S_put': S_put,
                'p_stall': p_stall,
                'rho_r': rho_r,
                'N_L0': self.N_L0,
                'Q_L0': self.Q[0],
                'Q_L1': self.Q[1],
                'Q_L2': self.Q[2],
                'Q_L3': self.Q[3],
                'C_L0': capacities[0],
                'C_L1': capacities[1],
                'C_L2': capacities[2],
                'C_L3': capacities[3],
                'D_L0': demands[0],
                'D_L1': demands[1],
                'D_L2': demands[2],
                'D_L3': demands[3]
            }
            self.results.append(result)
            
            # Update time
            self.t += self.dt
            
            # Progress reporting
            if step % 100 == 0:
                print(f"  Step {step}/{self.max_steps}: S_put={S_put:.1f} MiB/s, "
                      f"p_stall={p_stall:.3f}, N_L0={self.N_L0:.1f}")
        
        print("Simulation completed!")
        
        # Convert results to DataFrame
        df = pd.DataFrame(self.results)
        return df
    
    def save_results(self, df: pd.DataFrame, output_path: str):
        """
        Save simulation results to CSV file.
        
        Args:
            df: Simulation results DataFrame
            output_path: Output CSV file path
        """
        df.to_csv(output_path, index=False)
        print(f"Simulation results saved to: {output_path}")
    
    def analyze_results(self, df: pd.DataFrame) -> Dict:
        """
        Analyze simulation results and return summary statistics.
        
        Args:
            df: Simulation results DataFrame
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            'steady_state': {},
            'performance_metrics': {},
            'bottleneck_analysis': {}
        }
        
        # Steady-state analysis (last 20% of simulation)
        steady_start = int(0.8 * len(df))
        steady_df = df.iloc[steady_start:]
        
        analysis['steady_state'] = {
            'avg_put_rate': steady_df['S_put'].mean(),
            'avg_stall_prob': steady_df['p_stall'].mean(),
            'avg_read_ratio': steady_df['rho_r'].mean(),
            'avg_l0_files': steady_df['N_L0'].mean(),
            'avg_backlog': {f'L{level}': steady_df[f'Q_L{level}'].mean() 
                           for level in self.levels}
        }
        
        # Performance metrics
        analysis['performance_metrics'] = {
            'throughput_efficiency': steady_df['S_put'].mean() / self.config.get('target_put_rate', 200),
            'stall_percentage': steady_df['p_stall'].mean() * 100,
            'read_write_ratio': steady_df['rho_r'].mean(),
            'l0_file_stability': steady_df['N_L0'].std() / steady_df['N_L0'].mean() if steady_df['N_L0'].mean() > 0 else 0
        }
        
        # Bottleneck analysis
        avg_capacities = {f'L{level}': steady_df[f'C_L{level}'].mean() for level in self.levels}
        avg_demands = {f'L{level}': steady_df[f'D_L{level}'].mean() for level in self.levels}
        
        bottlenecks = []
        for level in self.levels:
            capacity = avg_capacities[f'L{level}']
            demand = avg_demands[f'L{level}']
            utilization = demand / capacity if capacity > 0 else 0
            bottlenecks.append({
                'level': level,
                'utilization': utilization,
                'capacity': capacity,
                'demand': demand
            })
        
        analysis['bottleneck_analysis'] = {
            'bottlenecks': sorted(bottlenecks, key=lambda x: x['utilization'], reverse=True),
            'max_utilization': max(b['utilization'] for b in bottlenecks),
            'bottleneck_level': max(bottlenecks, key=lambda x: x['utilization'])['level']
        }
        
        return analysis


def load_config(config_path: str) -> Dict:
    """
    Load simulation configuration from YAML file.
    
    Args:
        config_path: Path to configuration YAML file
        
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='v4 Dynamic Simulator')
    parser.add_argument('--envelope_json', required=True, help='Path to envelope model JSON file')
    parser.add_argument('--config_yaml', required=True, help='Path to configuration YAML file')
    parser.add_argument('--out_csv', default='sim_out.csv', help='Output CSV file path')
    parser.add_argument('--steps', type=int, default=1000, help='Number of simulation steps')
    parser.add_argument('--dt', type=float, default=1.0, help='Time step in seconds')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config_yaml)
    
    # Load envelope model
    envelope = EnvelopeModel.from_json_path(args.envelope_json)
    
    # Create simulator
    simulator = V4Simulator(envelope, config)
    
    # Run simulation
    results_df = simulator.simulate(steps=args.steps, dt=args.dt)
    
    # Save results
    simulator.save_results(results_df, args.out_csv)
    
    # Analyze results
    analysis = simulator.analyze_results(results_df)
    
    # Print analysis
    print("\nSimulation Analysis:")
    print(f"  Steady-state put rate: {analysis['steady_state']['avg_put_rate']:.1f} MiB/s")
    print(f"  Stall percentage: {analysis['performance_metrics']['stall_percentage']:.1f}%")
    print(f"  Read/write ratio: {analysis['steady_state']['avg_read_ratio']:.3f}")
    print(f"  Bottleneck level: L{analysis['bottleneck_analysis']['bottleneck_level']}")
    print(f"  Max utilization: {analysis['bottleneck_analysis']['max_utilization']:.1%}")


if __name__ == "__main__":
    main()
