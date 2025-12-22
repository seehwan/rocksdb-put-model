import gymnasium as gym
from gymnasium import spaces
import numpy as np
from .fluid_dynamics import RocksDBFluidDynamics

class RocksDBFluidEnv(gym.Env):
    """
    Gym Environment for controlling RocksDB Write Rate.
    Observations: [L0_Files, Write_Amplification]
    Actions: [Target_Write_Rate] (MB/s)
    """
    metadata = {"render_modes": ["human", "ansi"]}

    def __init__(self):
        super(RocksDBFluidEnv, self).__init__()
        
        # Default to SATA SSD
        self.sim = RocksDBFluidDynamics()
        self.max_action_rate = 500.0 # Max Rate Limiter setting (MB/s)
        
        # Action: Target Write Rate (continuous)
        # Normalized action [-1, 1] is standard for PPO.
        self.action_space = spaces.Box(
            low=-1.0, 
            high=1.0, 
            shape=(1,), 
            dtype=np.float32
        )
        
        # Observation: 
        # 0: L0 File Count (0 ~ 50+)
        # 1: Current WA (1.0 ~ 10.0+)
        # 2: Overlap Factor (0.0 ~ 1.0+)
        self.observation_space = spaces.Box(
            low=np.array([0.0, 1.0, 0.0]), 
            high=np.array([100.0, 20.0, 5.0]), # Overlap can go > 1.0 before storm triggers
            dtype=np.float32
        )
        
        self.step_count = 0
        self.max_steps = 1000 # Episode length
        
    def step(self, action):
        self.step_count += 1
        
        # Map Action [-1, 1] -> [0, MAX]
        # rate = ((action + 1) / 2) * max_rate
        normalized_action = float(action[0])
        # Clip to be safe
        normalized_action = np.clip(normalized_action, -1.0, 1.0)
        
        target_rate = ((normalized_action + 1.0) / 2.0) * self.max_action_rate
        
        # Step Physics
        state = self.sim.step(target_rate, dt=1.0)
        
        # Calculate Reward
        # Goal: Maximize Throughput WITHOUT Stalling.
        # Now that simulation blocks inflow on stall, effective_inflow becomes 0.
        # This naturally penalizes Stalls (Reward becomes 0).
        
        effective_inflow = state['effective_inflow']
        throughput_reward = effective_inflow / self.max_action_rate # Normalize 0~1
        
        # We can add a small penalty for being in "Stalled State" to encourage getting out,
        # but the 0 throughput is the main driver.
        stall_penalty = 0.0
        if state['is_stalled']:
             stall_penalty = 0.1 # Small extra penalty to avoid staying at limit
            
        reward = throughput_reward - stall_penalty
        
        # Check termination
        terminated = False
        truncated = False
        if self.step_count >= self.max_steps:
            truncated = True
            
        # Clip observations to prevent NaN in Neural Net
        # L0 shouldn't explode now due to blocking, but good to keep clip.
        l0_clipped = np.clip(state['l0_files'], 0.0, 2000.0)
        wa_clipped = np.clip(state['wa'], 1.0, 500.0)
        overlap_clipped = np.clip(state['overlap_factor'], 0.0, 10.0)

        obs = np.array([l0_clipped, wa_clipped, overlap_clipped], dtype=np.float32)
        info = state
        
        return obs, reward, terminated, truncated, info
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        state_dict = self.sim.reset()
        self.step_count = 0
        
        obs = np.array([state_dict['l0_files'], state_dict['wa'], state_dict['overlap_factor']], dtype=np.float32)
        return obs, {}
