import numpy as np

class RocksDBFluidDynamics:
    """
    Simulates RocksDB internal state using Fluid Dynamics analogies.
    Based on the theoretical model in DATA_FLUID_DYNAMICS_ANALYSIS.md.
    
    Model:
    - Tank: L0 SSTables
    - Inflow: User Write Rate
    - Outflow: Compaction Rate
    - Safety Valve: Write Stall
    """
    
    # Device Specifications
    DEVICE_SATA_SSD = {
        'max_bandwidth_mb': 350.0,
        'latency_ms': 0.1
    }
    
    DEVICE_NVME_SSD = {
        'max_bandwidth_mb': 2000.0,
        'latency_ms': 0.02
    }

    def __init__(self, max_l0_files=20, stall_threshold=20, 
                 base_wa=1.0, 
                 device_config=DEVICE_SATA_SSD,
                 l0_file_size_mb=64.0, fan_out=10.0):
        """
        Args:
            max_l0_files: Physical limit
            stall_threshold: L0 count where Write Stall triggers
            base_wa: Minimum Write Amplification
            device_config: Dict containing 'max_bandwidth_mb'
            l0_file_size_mb: Size of one L0 SSTable
            fan_out: Compaction fan-out factor (typically 10)
        """
        # System Constants
        self.STALL_THRESHOLD = stall_threshold
        self.BASE_WA = base_wa
        self.MAX_BANDWIDTH = device_config['max_bandwidth_mb']
        self.FILE_SIZE_MB = l0_file_size_mb
        self.FAN_OUT = fan_out
        
        # State Variables
        self.l0_files = 0.0
        self.total_input_mb = 0.0 # Track total data to simulate "Level Filling"
        self.current_wa = base_wa
        self.is_stalled = False
        self.overlap_factor = 0.0 # [NEW] Track key range overlap probability
        self.aging_factor = 1.0   # [NEW] SSD Aging (1.0 -> 0.3)
        
    def step(self, inflow_rate_mb, dt=1.0):
        """
        Physics step for one time unit.
        Equation: dL/dt = k * ( Inflow * WA - Max_Bandwidth )
        """
        if self.l0_files >= self.STALL_THRESHOLD:
            self.is_stalled = True
        elif self.l0_files < self.STALL_THRESHOLD * 0.8: # Hysteresis
            self.is_stalled = False
            
        # Effective Inflow: If stalled, traffic is blocked
        if self.is_stalled:
            effective_inflow = 0.0
        else:
            effective_inflow = inflow_rate_mb

        # Update pseudo-time
        self.total_input_mb += effective_inflow * dt
        
        # 1. Update Write Amplification with Fan-out Logic
        estimated_levels = np.log(max(1.0, self.total_input_mb / self.FILE_SIZE_MB)) / np.log(self.FAN_OUT)
        estimated_levels = max(0.0, estimated_levels)
        
        # Leveled Compaction Cost:
        fanout_cost_per_level = self.FAN_OUT / 2.0 
        depth_component = estimated_levels * fanout_cost_per_level
        turbulence_component = self.l0_files * 0.15
        
        # [NEW] Compaction Storm Logic (L0-L1 Overlap)
        # As L0 files accumulate, the probability of them overlapping with the entire L1 range increases.
        # Simple Model: overlap_factor increases with L0 count.
        # If overlap_factor > threshold, a "Storm" triggers, causing WA to spike (External Merge Sort).
        
        # Increase overlap factor (probabilistic)
        if self.l0_files > 4:
            self.overlap_factor += 0.05 * (self.l0_files / 10.0)
        else:
             self.overlap_factor = max(0.0, self.overlap_factor - 0.1)
             
        # Trigger Storm
        storm_wa = 0.0
        if self.overlap_factor > 1.0:
            # Storm lasts for some time or clears up?
            # Let's say it's an impulse spike that clears after "processing".
            # We assume the storm clears when L0 drops significantly, but here we model the *instantaneous* cost.
            # WA adds a massive penalty: merging L0 (N files) + L1 (M files). M >> N usually.
            # Let's add a spike component proportional to accumulated data.
            storm_wa = 20.0  # Big penalty
            # Decay overlap factor to simulate "working through" the overlap
            self.overlap_factor = max(0.0, self.overlap_factor - 0.2) 
            
        self.current_wa = self.BASE_WA + depth_component + turbulence_component + storm_wa
        
        
        # [NEW] SSD Aging Logic
        # As total written bytes increase, SSD performance degrades (GC overhead, wear).
        # Simple Model: Bandwidth decays exponentially or linearly.
        # Let's say it degrades to 50% over 100GB (100,000 MB) of writes for this simulation scale.
        # aging_factor = exp(-k * total_input)
        
        # For simulation speed, let's make it degrade faster: 50% after 20,000 MB.
        # 0.5 = exp(-k * 20000) -> ln(0.5) = -k * 20000 -> k = -ln(0.5)/20000 approx 3.46e-5
        
        aging_decay_rate = 3.5e-5
        self.aging_factor = np.exp(-aging_decay_rate * self.total_input_mb)
        
        # Lower bound: Don't let it go below 30%
        self.aging_factor = max(0.3, self.aging_factor)
        
        current_bandwidth = self.MAX_BANDWIDTH * self.aging_factor
        
        # 2. Calculate Continuity Equation
        total_io_load = effective_inflow * self.current_wa
        
        # Net Flow
        # Even if inflow is 0, we have Outflow capacity (Compaction), so L0 can drain.
        # Drain Rate = Current Bandwidth (affected by aging)
        # Actually dL/dt = Input*WA - Bandwidth.
        net_flow_mb = total_io_load - current_bandwidth
        
        # Update Level
        dl_files = (net_flow_mb * dt) / self.FILE_SIZE_MB
        self.l0_files += dl_files
        self.l0_files = max(0.0, self.l0_files) 
        
        return {
            'l0_files': self.l0_files,
            'wa': self.current_wa,
            'is_stalled': self.is_stalled,
            'total_load': total_io_load,
            'net_flow': net_flow_mb,
            'effective_inflow': effective_inflow,
            'overlap_factor': self.overlap_factor,
            'aging_factor': self.aging_factor,
            'current_bandwidth': self.MAX_BANDWIDTH * self.aging_factor
        }
    
    def reset(self):
        self.l0_files = 0.0
        self.current_wa = self.BASE_WA
        self.is_stalled = False
        self.overlap_factor = 0.0
        self.aging_factor = 1.0
        return self._get_state()

    def _get_state(self):
        return {
            'l0_files': self.l0_files,
            'wa': self.current_wa,
            'is_stalled': self.is_stalled,
            'total_load': 0.0,
            'net_flow': 0.0,
            'effective_inflow': 0.0,
            'overlap_factor': self.overlap_factor,
            'aging_factor': self.aging_factor,
            'current_bandwidth': self.MAX_BANDWIDTH * self.aging_factor
        }
