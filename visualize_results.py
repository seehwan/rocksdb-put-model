import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import PPO

# Add current directory to path
sys.path.append(os.getcwd())

from rl_env.fluid_dynamics import RocksDBFluidDynamics
from rl_env.rocksdb_env import RocksDBFluidEnv

def run_scenario(name, sim_duration_steps=2000, input_mode='constant', constant_rate=0.0, agent=None):
    """
    Runs a simulation scenario and returns output data.
    
    Args:
        name: Name of scenario
        sim_duration_steps: Number of steps
        input_mode: 'constant' or 'agent'
        constant_rate: Rate for constant mode (MB/s)
        agent: Loaded PPO agent for agent mode
    """
    print(f"Running Scenario: {name}...")
    
    # Init Simulator
    # Use SATA SSD config (350 MB/s)
    sim = RocksDBFluidDynamics(
        fan_out=10.0,
        device_config={'max_bandwidth_mb': 350.0, 'latency_ms': 0.1}
    )
    
    # If Agent mode, we need the gym env wrapper logic to normalize observations/actions
    env = None
    if input_mode == 'agent':
        env = RocksDBFluidEnv()
        # Ensure env sim uses same config if possible, but rocksdb_env creates its own sim.
        # Let's inject our configured sim into the env to be safe
        env.sim = sim 
        env.reset()
        
    data = {
        'steps': [],
        'rate_in': [],
        'rate_effective': [],
        'wa': [],
        'l0': [],
        'overlap': [],
        'aging': [],
        'cumulative_writes': [],
        'put_latency': [],
        'stalled': []
    }
    
    obs, _ = env.reset() if env else (None, None)
    
    for i in range(sim_duration_steps):
        target_rate = 0.0
        
        if input_mode == 'constant':
            target_rate = constant_rate
            state = sim.step(inflow_rate_mb=target_rate, dt=1.0)
            
        elif input_mode == 'heuristic':
             # Aggressive Controller: Aim for 5% Stall Tolerance
             # Strategy: Push hard (150 MB/s) until L0 is dangerously high (19), then back off slightly?
             # Or simply Bang-Bang: 200 MB/s if L0 < 20, else 0. This guarantees stalls.
             current_l0 = sim.l0_files
             if current_l0 >= 20.0:
                 target_rate = 0.0 # Forced Stop
             elif current_l0 >= 18.0:
                 target_rate = 100.0 # Slow down near cliff
             else:
                 target_rate = 200.0 # Aggressive Push
             
             state = sim.step(inflow_rate_mb=target_rate, dt=1.0)

        elif input_mode == 'agent':
            # PPO Agent
            action, _ = agent.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            
            # Map action back to rate for logging (Gym env does this internally)
            # We can get actual rate from info or just infer it
            # From env code: target_rate = ((normalized_action + 1.0) / 2.0) * max_action_rate
            normalized_action = np.clip(action[0], -1.0, 1.0)
            target_rate = ((normalized_action + 1.0) / 2.0) * env.max_action_rate
            
            state = info

        # Log Data
        data['steps'].append(i)
        data['rate_in'].append(target_rate)
        data['rate_effective'].append(state['effective_inflow'])
        data['wa'].append(state['wa'])
        data['l0'].append(state['l0_files'])
        data['overlap'].append(state.get('overlap_factor', 0.0))
        data['aging'].append(state.get('aging_factor', 1.0))
        # Cumulative
        prev_cumulative = data['cumulative_writes'][-1] if data['cumulative_writes'] else 0.0
        new_cumulative = prev_cumulative + state['effective_inflow']
        data['cumulative_writes'].append(new_cumulative)
        
        # Est. Put Latency
        # If L0 < 20: Memtable write (~0.1 ms)
        # If L0 >= 20: Write Stall (~1000 ms penalty)
        if state['l0_files'] >= 20.0:
            lat = 1000.0
        else:
            lat = 0.1
        data['put_latency'].append(lat)
        
    return data

def plot_results(scenarios):
    fig, axes = plt.subplots(6, 1, figsize=(10, 22), sharex=True)
    
    # 1. Throughput
    ax = axes[0]
    ax.set_title("Effective Throughput (MB/s)")
    for name, data in scenarios.items():
        # Rolling average for smoothness
        window = 50
        y_smooth = np.convolve(data['rate_effective'], np.ones(window)/window, mode='valid')
        x_smooth = data['steps'][:len(y_smooth)]
        ax.plot(x_smooth, y_smooth, label=name)
    ax.set_ylabel("MB/s")
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # 2. Write Amplification (WA)
    ax = axes[1]
    ax.set_title("Write Amplification (WA)")
    for name, data in scenarios.items():
        ax.plot(data['steps'], data['wa'], label=name)
    ax.set_ylabel("WA Factor")
    ax.grid(True, alpha=0.3)
    
    # 3. L0 Files (Backlog)
    ax = axes[2]
    ax.set_title("L0 File Count (Backlog)")
    for name, data in scenarios.items():
        ax.plot(data['steps'], data['l0'], label=name)
    ax.set_ylabel("Count")
    ax.axhline(y=20, color='r', linestyle='--', label='Stall Threshold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # 4. Environment Factors
    ax = axes[3]
    ax.set_title("Environment Factors")
    for name, data in scenarios.items():
        if 'overlap' in data:
             ax.plot(data['steps'], data['overlap'], label=f"{name} (Overlap)", linestyle='--')
        if 'aging' in data:
             ax.plot(data['steps'], data['aging'], label=f"{name} (Aging Factor)", linewidth=2)
    ax.set_ylabel("Factor")
    ax.grid(True, alpha=0.3)
    
    # 5. Put Latency (New)
    ax = axes[4]
    ax.set_title("Estimated Put Latency (ms)")
    for name, data in scenarios.items():
        ax.plot(data['steps'], data['put_latency'], label=name)
    ax.set_ylabel("Latency (ms)")
    ax.grid(True, alpha=0.3)
    # Log scale might be better to see the jump
    ax.set_yscale('log')

    # 6. Cumulative Writes
    ax = axes[5]
    ax.set_title("Result: Cumulative Data Written (MB)")
    for name, data in scenarios.items():
        ax.plot(data['steps'], data['cumulative_writes'], label=name, linewidth=2)
    ax.set_ylabel("Total MB")
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.xlabel("Simulation Steps (Seconds)")
    plt.tight_layout()
    plt.savefig("simulation_comparison_chart.png")
    print("Chart saved to simulation_comparison_chart.png")

if __name__ == "__main__":
    # Load Agent
    model_path = "rocksdb_ppo_agent"
    agent = None
    if os.path.exists(model_path + ".zip"):
        print("Loading PPO Agent...")
        agent = PPO.load(model_path)
    else:
        print("Warning: RL Agent model not found. Skipping RL scenario.")
        
    sim_steps = 5000
    
    results = {}
    
    # 1. Baseline (64 MB/s)
    results['Baseline (64 MB/s)'] = run_scenario(
        "Baseline", sim_steps, 'constant', constant_rate=64.0
    )
    
    # 2. Overload (500 MB/s)
    results['Overload (500 MB/s)'] = run_scenario(
        "Overload", sim_steps, 'constant', constant_rate=500.0
    )

    # 3. Aggressive (Heuristic)
    results['Aggressive (Aim 5% Stall)'] = run_scenario(
        "Aggressive", sim_steps, 'heuristic'
    )
    
    # 3. RL Agent
    if agent:
        results['RL Agent'] = run_scenario(
            "RL Agent", sim_steps, 'agent', agent=agent
        )
        
    plot_results(results)
