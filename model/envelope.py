"""
PutModel v4: Device Envelope Modeling

This module implements the Device Envelope model for mixed I/O bandwidth prediction.
It replaces the Harmonic Mean assumption with empirical measurements from fio grid sweeps.

Key Features:
- 4D grid interpolation (ρr, iodepth, numjobs, bs)
- Linear interpolation with optional clamping
- Support for multiple device types
- Extrapolation warnings for out-of-grid queries
"""

import json
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from typing import Dict, List, Optional, Tuple, Union
import warnings


class EnvelopeModel:
    """
    Device Envelope Model for mixed I/O bandwidth prediction.
    
    This class implements a 4D interpolation model based on fio grid sweep results.
    It provides accurate bandwidth predictions for mixed read/write workloads.
    """
    
    def __init__(self, grid_data: Dict):
        """
        Initialize the envelope model from grid data.
        
        Args:
            grid_data: Dictionary containing grid axes and bandwidth measurements
                - rho_r_axis: List of read ratios [0.0, 0.25, 0.5, 0.75, 1.0]
                - iodepth_axis: List of queue depths [1, 4, 16, 64]
                - numjobs_axis: List of parallel jobs [1, 2, 4]
                - bs_axis: List of block sizes in KiB [4, 64, 1024]
                - bandwidth_grid: 4D numpy array of bandwidth measurements
        """
        self.rho_r_axis = np.array(grid_data['rho_r_axis'])
        self.iodepth_axis = np.array(grid_data['iodepth_axis'])
        self.numjobs_axis = np.array(grid_data['numjobs_axis'])
        self.bs_axis = np.array(grid_data['bs_axis'])
        self.bandwidth_grid = np.array(grid_data['bandwidth_grid'])
        
        # Validate grid dimensions
        expected_shape = (len(self.rho_r_axis), len(self.iodepth_axis), 
                         len(self.numjobs_axis), len(self.bs_axis))
        if self.bandwidth_grid.shape != expected_shape:
            raise ValueError(f"Grid shape mismatch: expected {expected_shape}, got {self.bandwidth_grid.shape}")
        
        # Create interpolator
        self.interpolator = RegularGridInterpolator(
            (self.rho_r_axis, self.iodepth_axis, self.numjobs_axis, self.bs_axis),
            self.bandwidth_grid,
            method='linear',
            bounds_error=False,
            fill_value=None
        )
        
        # Store metadata
        self.metadata = grid_data.get('metadata', {})
        
    @classmethod
    def from_json_path(cls, path: str) -> "EnvelopeModel":
        """
        Load envelope model from JSON file.
        
        Args:
            path: Path to JSON file containing grid data
            
        Returns:
            EnvelopeModel instance
        """
        with open(path, 'r') as f:
            grid_data = json.load(f)
        return cls(grid_data)
    
    def query(self, rho_r: float, qd: int, numjobs: int, bs_k: int,
              Br: Optional[float] = None, Bw: Optional[float] = None,
              clamp_to_physical: bool = True) -> float:
        """
        Query the envelope model for effective bandwidth.
        
        Args:
            rho_r: Read ratio (0.0 to 1.0)
            qd: Queue depth
            numjobs: Number of parallel jobs
            bs_k: Block size in KiB
            Br: Read bandwidth for physical clamping (optional)
            Bw: Write bandwidth for physical clamping (optional)
            clamp_to_physical: Whether to apply physical constraints
            
        Returns:
            Effective bandwidth in MiB/s
            
        Raises:
            ValueError: If parameters are out of valid ranges
        """
        # Validate inputs
        if not 0.0 <= rho_r <= 1.0:
            raise ValueError(f"rho_r must be between 0.0 and 1.0, got {rho_r}")
        if qd <= 0:
            raise ValueError(f"Queue depth must be positive, got {qd}")
        if numjobs <= 0:
            raise ValueError(f"Number of jobs must be positive, got {numjobs}")
        if bs_k <= 0:
            raise ValueError(f"Block size must be positive, got {bs_k}")
        
        # Check for extrapolation
        self._check_extrapolation(rho_r, qd, numjobs, bs_k)
        
        # Query interpolator
        point = np.array([rho_r, qd, numjobs, bs_k])
        Beff = float(self.interpolator(point))
        
        # Apply physical clamping if requested
        if clamp_to_physical and Br is not None and Bw is not None:
            Beff = min(Beff, min(Br, Bw))
        
        return Beff
    
    def _check_extrapolation(self, rho_r: float, qd: int, numjobs: int, bs_k: int):
        """Check if query point requires extrapolation and issue warning if needed."""
        extrapolation_needed = False
        
        if rho_r < self.rho_r_axis.min() or rho_r > self.rho_r_axis.max():
            extrapolation_needed = True
        if qd < self.iodepth_axis.min() or qd > self.iodepth_axis.max():
            extrapolation_needed = True
        if numjobs < self.numjobs_axis.min() or numjobs > self.numjobs_axis.max():
            extrapolation_needed = True
        if bs_k < self.bs_axis.min() or bs_k > self.bs_axis.max():
            extrapolation_needed = True
        
        if extrapolation_needed:
            warnings.warn(
                f"Query point ({rho_r}, {qd}, {numjobs}, {bs_k}) requires extrapolation. "
                f"Grid ranges: rho_r=[{self.rho_r_axis.min()}, {self.rho_r_axis.max()}], "
                f"iodepth=[{self.iodepth_axis.min()}, {self.iodepth_axis.max()}], "
                f"numjobs=[{self.numjobs_axis.min()}, {self.numjobs_axis.max()}], "
                f"bs=[{self.bs_axis.min()}, {self.bs_axis.max()}]",
                UserWarning
            )
    
    def get_grid_info(self) -> Dict:
        """Get information about the grid dimensions and ranges."""
        return {
            'rho_r_range': [float(self.rho_r_axis.min()), float(self.rho_r_axis.max())],
            'iodepth_range': [int(self.iodepth_axis.min()), int(self.iodepth_axis.max())],
            'numjobs_range': [int(self.numjobs_axis.min()), int(self.numjobs_axis.max())],
            'bs_range': [int(self.bs_axis.min()), int(self.bs_axis.max())],
            'grid_shape': self.bandwidth_grid.shape,
            'total_points': self.bandwidth_grid.size,
            'metadata': self.metadata
        }
    
    def validate_physical_constraints(self, Br: float, Bw: float) -> Dict:
        """
        Validate that the envelope model respects physical constraints.
        
        Args:
            Br: Read bandwidth in MiB/s
            Bw: Write bandwidth in MiB/s
            
        Returns:
            Dictionary with validation results
        """
        violations = []
        max_violation = 0.0
        
        # Check all grid points
        for i, rho_r in enumerate(self.rho_r_axis):
            for j, qd in enumerate(self.iodepth_axis):
                for k, numjobs in enumerate(self.numjobs_axis):
                    for l, bs_k in enumerate(self.bs_axis):
                        Beff = self.bandwidth_grid[i, j, k, l]
                        physical_limit = min(Br, Bw)
                        
                        if Beff > physical_limit:
                            violation = (Beff - physical_limit) / physical_limit * 100
                            violations.append({
                                'point': (rho_r, qd, numjobs, bs_k),
                                'Beff': Beff,
                                'limit': physical_limit,
                                'violation_pct': violation
                            })
                            max_violation = max(max_violation, violation)
        
        return {
            'total_violations': len(violations),
            'max_violation_pct': max_violation,
            'violations': violations,
            'is_valid': len(violations) == 0
        }


def create_sample_envelope_model() -> EnvelopeModel:
    """
    Create a sample envelope model for testing.
    
    This creates a synthetic model with realistic characteristics.
    """
    # Define grid axes
    rho_r_axis = [0.0, 0.25, 0.5, 0.75, 1.0]
    iodepth_axis = [1, 4, 16, 64]
    numjobs_axis = [1, 2, 4]
    bs_axis = [4, 64, 1024]
    
    # Create synthetic bandwidth grid
    # Higher read ratios and more parallel jobs generally reduce effective bandwidth
    bandwidth_grid = np.zeros((len(rho_r_axis), len(iodepth_axis), len(numjobs_axis), len(bs_axis)))
    
    for i, rho_r in enumerate(rho_r_axis):
        for j, qd in enumerate(iodepth_axis):
            for k, numjobs in enumerate(numjobs_axis):
                for l, bs_k in enumerate(bs_axis):
                    # Base bandwidth decreases with read ratio and parallel jobs
                    base_bandwidth = 2000 * (1 - rho_r * 0.3) * (1 - (numjobs - 1) * 0.1)
                    
                    # Queue depth effect (diminishing returns)
                    qd_factor = 1 + 0.5 * np.log(qd) / np.log(64)
                    
                    # Block size effect (larger blocks are more efficient)
                    bs_factor = 1 + 0.2 * np.log(bs_k / 4) / np.log(1024 / 4)
                    
                    bandwidth_grid[i, j, k, l] = base_bandwidth * qd_factor * bs_factor
    
    grid_data = {
        'rho_r_axis': rho_r_axis,
        'iodepth_axis': iodepth_axis,
        'numjobs_axis': numjobs_axis,
        'bs_axis': bs_axis,
        'bandwidth_grid': bandwidth_grid.tolist(),
        'metadata': {
            'created_by': 'PutModel v4',
            'version': '1.0',
            'description': 'Sample synthetic envelope model for testing'
        }
    }
    
    return EnvelopeModel(grid_data)


if __name__ == "__main__":
    # Test the envelope model
    print("Creating sample envelope model...")
    model = create_sample_envelope_model()
    
    print("Grid info:")
    info = model.get_grid_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print("\nTesting queries:")
    test_cases = [
        (0.5, 16, 2, 64),  # 50% read, qd=16, 2 jobs, 64KiB blocks
        (0.25, 4, 1, 1024),  # 25% read, qd=4, 1 job, 1024KiB blocks
        (0.75, 64, 4, 4),  # 75% read, qd=64, 4 jobs, 4KiB blocks
    ]
    
    for rho_r, qd, numjobs, bs_k in test_cases:
        Beff = model.query(rho_r, qd, numjobs, bs_k)
        print(f"  ρr={rho_r}, qd={qd}, jobs={numjobs}, bs={bs_k}KiB → Beff={Beff:.1f} MiB/s")
    
    print("\nTesting physical constraints:")
    validation = model.validate_physical_constraints(Br=1500, Bw=2000)
    print(f"  Valid: {validation['is_valid']}")
    print(f"  Violations: {validation['total_violations']}")
    print(f"  Max violation: {validation['max_violation_pct']:.1f}%")