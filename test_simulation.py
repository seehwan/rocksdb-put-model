import sys
import os

# Ensure the current directory is in the path so we can import rl_env
sys.path.append(os.getcwd())

from rl_env.rocksdb_env import RocksDBFluidEnv
import numpy as np

def test_hockey_stick_behavior():
    print("Testing 'Hockey Stick' Behavior (Stall Dynamics)...")
    env = RocksDBFluidEnv()
    obs, _ = env.reset()
    
    print(f"Initial State: L0={obs[0]}, WA={obs[1]}")
    
    # Run with MAX RATE to force a stall
    action = np.array([400.0], dtype=np.float32) # 400 MB/s (Above max bandwidth 350)
    
    stall_occurred = False
    for i in range(100):
        obs, reward, terminated, truncated, info = env.step(action)
        l0_files = pos = obs[0]
        wa = obs[1]
        is_stalled = info['is_stalled']
        
        if i % 10 == 0:
            print(f"Step {i}: L0={l0_files:.2f}, WA={wa:.2f}, Stalled={is_stalled}, Reward={reward:.2f}")
            
        if is_stalled:
            print(f"!!! STALL DETECTED at Step {i} !!!")
            stall_occurred = True
            break
            
    if stall_occurred:
        print("PASS: System correctly stalled under high load.")
    else:
        print("FAIL: System did not stall despite overload.")

def test_mass_conservation():
    print("\nTesting Mass Conservation...")
    from rl_env.fluid_dynamics import RocksDBFluidDynamics
    # Custom config for test
    TEST_DEVICE = {'max_bandwidth_mb': 100.0, 'latency_ms': 0.1}
    sim = RocksDBFluidDynamics(l0_file_size_mb=10.0, device_config=TEST_DEVICE)
    
    # Step 1: Inflow=200, BW=100.
    # New Logic: WA is dynamic based on Total Input.
    # We verify the Continuity Equation: dL = (Inflow * WA - BW) / FileSize
    
    state = sim.step(inflow_rate_mb=200.0, dt=1.0)
    
    wa = state['wa']
    expected_load = 200.0 * wa
    expected_net_flow = expected_load - 100.0
    expected_l0 = expected_net_flow / 10.0
    
    print(f"Step 1: Inflow=200, BW=100, WA={wa:.2f}. Expected L0: {expected_l0:.2f}. Actual L0: {state['l0_files']:.2f}")
    
    assert abs(state['l0_files'] - expected_l0) < 0.01, f"Mass conservation failed! Expected {expected_l0}, got {state['l0_files']}"
    print("PASS: Mass conservation verified.")

def test_wa_growth_fanout():
    print("\nTesting WA Growth with Fan-out...")
    from rl_env.fluid_dynamics import RocksDBFluidDynamics
    # L0 = 10MB, FanOut=10
    # Level 1 fills at 100MB. Level 2 at 1000MB.
    TEST_DEVICE = {'max_bandwidth_mb': 350.0, 'latency_ms': 0.1}
    sim = RocksDBFluidDynamics(l0_file_size_mb=10.0, fan_out=10.0, base_wa=1.0, device_config=TEST_DEVICE)
    
    # 1. Initial State
    state0 = sim._get_state()
    print(f"Initial WA: {state0['wa']:.2f}")
    assert abs(state0['wa'] - 1.0) < 0.1
    
    # 2. Add 100MB (Fills up to Level 1)
    # expected_levels = 1.0
    # New WA = 1.0 + 1.0 * (10/2) = 6.0
    sim.step(inflow_rate_mb=100.0, dt=1.0)
    state1 = sim._get_state()
    print(f"After 100MB WA: {state1['wa']:.2f} (Expected ~6.0)")
    assert state1['wa'] >= 5.0, "WA should reflect Fan-out cost!"
    
    # 3. Add 900MB (Total 1000MB -> Fills Level 2)
    # expected_levels = 2.0
    # New WA = 1.0 + 2.0 * 5.0 = 11.0
    sim.step(inflow_rate_mb=900.0, dt=1.0)
    state2 = sim._get_state()
    print(f"After 1000MB WA: {state2['wa']:.2f} (Expected ~11.0)")
    assert state2['wa'] >= 10.0, "WA should reflect deeper levels with full fan-out cost!"
    
    print("PASS: Fan-out WA growth verified.")

def test_baseline_performance():
    print("\nTesting Baseline Performance (Standard RocksDB Simulation)...")
    print("Scenario: User pushes constant 64 MB/s (fillrandom).")
    from rl_env.fluid_dynamics import RocksDBFluidDynamics
    import numpy as np
    
    # Config similar to real environment (SATA SSD Default)
    sim = RocksDBFluidDynamics(
        max_l0_files=20, stall_threshold=20, 
        base_wa=1.0, 
        fan_out=10.0
    )
    
    inflow_request = 64.0 # User tries to push 64 MB/s
    total_steps = 50000 # Run longer (approx 14 hours simul time) to fill DB
    effective_throughputs = []
    wa_history = []
    
    print(f"Running long duration baseline test ({total_steps} steps)...")
    
    stall_count = 0
    for i in range(total_steps):
        state = sim.step(inflow_rate_mb=inflow_request, dt=1.0)
        
        effective_throughputs.append(state['effective_inflow'])
        wa_history.append(state['wa'])
        
        if state['is_stalled']:
            stall_count += 1
            
        if i % 5000 == 0:
            print(f"Step {i}: WA={state['wa']:.2f}, Eff_Rate={state['effective_inflow']:.2f}, Stalled={state['is_stalled']}")

    avg_throughput = np.mean(effective_throughputs)
    final_wa = wa_history[-1]
    
    print(f"\nSimulation Result over {total_steps} seconds:")
    print(f"  - Request Rate: {inflow_request} MB/s")
    print(f"  - Final WA: {final_wa:.2f}")
    print(f"  - Stall Count: {stall_count} / {total_steps} steps")
    print(f"  - Avg Effective Throughput: {avg_throughput:.2f} MB/s")
    
    if avg_throughput < inflow_request * 0.5:
        print("OBSERVATION: Performance degraded significantly due to Stalls/WA, matching real-world behavior.")
    else:
        print("OBSERVATION: Performance maintained (System capacity > Load).")

def test_overload_performance():
    print("\nTesting Overload Performance (500 MB/s)...")
    print("Scenario: User tries to push 500 MB/s (Above Max Bandwidth 350).")
    from rl_env.fluid_dynamics import RocksDBFluidDynamics
    import numpy as np
    
    sim = RocksDBFluidDynamics(
        max_l0_files=20, stall_threshold=20, 
        base_wa=1.0, 
        fan_out=10.0
    )
    
    inflow_request = 500.0
    total_steps = 10000 
    effective_throughputs = []
    wa_history = []
    
    stall_count = 0
    for i in range(total_steps):
        state = sim.step(inflow_rate_mb=inflow_request, dt=1.0)
        
        effective_throughputs.append(state['effective_inflow'])
        wa_history.append(state['wa'])
        
        if state['is_stalled']:
            stall_count += 1
            
        if i % 2000 == 0:
            print(f"Step {i}: WA={state['wa']:.2f}, Eff_Rate={state['effective_inflow']:.2f}, Stalled={state['is_stalled']}, L0={state['l0_files']:.2f}")

    avg_throughput = np.mean(effective_throughputs)
    final_wa = wa_history[-1]
    
    print(f"\nSimulation Result over {total_steps} seconds:")
    print(f"  - Request Rate: {inflow_request} MB/s")
    print(f"  - Final WA: {final_wa:.2f}")
    print(f"  - Stall Count: {stall_count} / {total_steps} steps ({(stall_count/total_steps)*100:.1f}%)")
    print(f"  - Avg Effective Throughput: {avg_throughput:.2f} MB/s")
    
    # Theoretical Limiting Speed = Bandwidth / WA
    theoretical_limit = 350.0 / final_wa
    print(f"  - Theoretical Limit (at Final WA): {350.0} / {final_wa:.2f} = {theoretical_limit:.2f} MB/s")

if __name__ == "__main__":
    # test_mass_conservation()
    # test_hockey_stick_behavior()
    # test_wa_growth_fanout()
    # test_baseline_performance()
    test_overload_performance()
