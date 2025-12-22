import sys
import os
import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor

# Add current directory to path
sys.path.append(os.getcwd())

from rl_env.rocksdb_env import RocksDBFluidEnv

def train_agent():
    print("Setting up Environment...")
    env = RocksDBFluidEnv()
    
    # Sanity check
    check_env(env)
    
    # Wrap in Monitor for logging
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    env = Monitor(env, log_dir)
    
    print("Initializing PPO Agent...")
    # Using MlpPolicy because observations are simple vectors
    model = PPO("MlpPolicy", env, verbose=1, 
                learning_rate=0.0003,
                n_steps=2048,
                batch_size=64,
                n_epochs=10,
                gamma=0.99,
                gae_lambda=0.95,
                clip_range=0.2,
                ent_coef=0.01)
    
    print("Starting Training...")
    model.learn(total_timesteps=50000)
    print("Training Complete.")
    
    model.save("rocksdb_ppo_agent")
    print("Model Saved.")
    
    return model

def evaluate_dynamic_equilibrium(model):
    print("\nEVALUATION: Tracking Dynamic Equilibrium")
    env = RocksDBFluidEnv()
    obs, _ = env.reset()
    
    # We want to see if the agent decreases rate as WA increases (due to Fan-out)
    # Simulator config: L0=64MB, FanOut=10
    
    states = []
    actions = []
    rewards = []
    wa_values = []
    
    print("Running episode...")
    terminated = False
    truncated = False
    
    step = 0
    while not (terminated or truncated):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        
        states.append(obs[0]) # L0
        wa_values.append(obs[1]) # WA
        actions.append(action[0]) # Rate
        rewards.append(reward)
        
        if step % 100 == 0:
            print(f"Step {step}: WA={obs[1]:.2f}, L0={obs[0]:.2f}, Overlap={obs[2]:.2f}, Rate={action[0]:.2f}")
        step += 1
        
    # Analysis
    # As WA went from 1.0 -> 3.0+, did Action go down?
    initial_rate = np.mean(actions[:50])
    final_rate = np.mean(actions[-50:])
    initial_wa = wa_values[0]
    final_wa = wa_values[-1]
    
    print(f"\nSummary:")
    print(f"Initial WA: {initial_wa:.2f} -> Rate: {initial_rate:.2f}")
    print(f"Final WA:   {final_wa:.2f} -> Rate: {final_rate:.2f}")
    
    if final_rate < initial_rate and final_wa > initial_wa:
        print("SUCCESS: Agent correctly reduced rate to match increased WA (Dynamic Equilibrium).")
    else:
        print("WARNING: Equilibrium logic not clearly observed. Agent might be suboptimal or WA didn't grow enough.")

if __name__ == "__main__":
    trained_model = train_agent()
    evaluate_dynamic_equilibrium(trained_model)
