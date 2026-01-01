"""
Ultron Trading Environment for Reinforcement Learning
Uses Gymnasium (maintained replacement for OpenAI Gym)
Compatible with stable-baselines3 (PPO, A2C, DQN, etc.)
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import json
from datetime import datetime

# Import KitaTrader components
from Api.KitaApiEnums import *
from Robots.Ultron import Ultron


class UltronEnv(gym.Env):
    """
    Gymnasium environment for training Ultron strategy parameters via RL
    
    Action Space: Discrete parameters for the strategy
        - period1: 2-15
        - period2: 2-15
        - period3: 30-70
        - period4: 2-15
        - take_profit_ticks: 50-2000
        - stop_loss_ticks: 50-2000
    
    Observation Space: Market state + indicators + position info
        - MA1, MA2, MA3, MA4 values
        - MA differences
        - Current price, bid, ask
        - Position status (open/closed)
        - Account balance, equity, drawdown
        - Recent performance metrics
    
    Reward: Calmar Ratio (risk-adjusted return)
    """
    
    metadata = {"render.modes": ["human"]}
    
    def __init__(self, start_date, end_date, config_file='optimizer_config.json'):
        """
        Initialize Ultron RL Environment
        
        Args:
            start_date: Start date for training/testing
            end_date: End date for training/testing
            config_file: Path to optimizer configuration
        """
        super(UltronEnv, self).__init__()
        
        self.start_date = start_date
        self.end_date = end_date
        
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.param_bounds = self.config['parameter_bounds']
        
        # Define action space (discrete parameters)
        # Using MultiDiscrete for each parameter range
        self.action_space = spaces.MultiDiscrete([
            (self.param_bounds['period1']['max'] - self.param_bounds['period1']['min']) // self.param_bounds['period1']['step'] + 1,
            (self.param_bounds['period2']['max'] - self.param_bounds['period2']['min']) // self.param_bounds['period2']['step'] + 1,
            (self.param_bounds['period3']['max'] - self.param_bounds['period3']['min']) // self.param_bounds['period3']['step'] + 1,
            (self.param_bounds['period4']['max'] - self.param_bounds['period4']['min']) // self.param_bounds['period4']['step'] + 1,
            (self.param_bounds['take_profit_ticks']['max'] - self.param_bounds['take_profit_ticks']['min']) // self.param_bounds['take_profit_ticks']['step'] + 1,
            (self.param_bounds['stop_loss_ticks']['max'] - self.param_bounds['stop_loss_ticks']['min']) // self.param_bounds['stop_loss_ticks']['step'] + 1,
        ])
        
        # Define observation space
        # Features: [MA1, MA2, MA3, MA4, MA1-MA2, MA3-MA4, bid, ask, spread,
        #           balance, equity, drawdown, position_size, unrealized_pnl,
        #           num_trades, win_rate, calmar]
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(17,),
            dtype=np.float32
        )
        
        # Robot instance
        self.robot = None
        self.current_step = 0
        self.max_steps = 100000  # Safety limit
    
    def reset(self, seed=None, **kwargs):
        """Reset environment to initial state"""
        super().reset(seed=seed)
        np.random.seed(seed)
        
        # Create new robot instance
        self.robot = Ultron()
        
        # Configure robot
        self.robot.AllDataStartUtc = self.start_date
        self.robot.BacktestStartUtc = self.start_date
        self.robot.BacktestEndUtc = self.end_date
        self.robot.RunningMode = RunMode.SilentBacktesting
        self.robot.DataPath = "$(OneDrive)/KitaData/cfd"
        self.robot.DataMode = DataMode.Preload
        self.robot.AccountInitialBalance = 10000.0
        self.robot.AccountLeverage = 500
        self.robot.AccountCurrency = "EUR"
        
        # Initialize and start
        self.robot.do_init()
        self.robot.do_start()
        
        self.current_step = 0
        
        # Get initial observation
        obs = self._get_observation()
        
        return obs, {}
    
    def step(self, action):
        """
        Execute one step with given action (parameter set)
        
        Args:
            action: Array of discrete parameter indices
        
        Returns:
            observation, reward, terminated, truncated, info
        """
        # Convert discrete action indices to actual parameter values
        self.robot.period1 = self.param_bounds['period1']['min'] + action[0] * self.param_bounds['period1']['step']
        self.robot.period2 = self.param_bounds['period2']['min'] + action[1] * self.param_bounds['period2']['step']
        self.robot.period3 = self.param_bounds['period3']['min'] + action[2] * self.param_bounds['period3']['step']
        self.robot.period4 = self.param_bounds['period4']['min'] + action[3] * self.param_bounds['period4']['step']
        self.robot.take_profit_ticks = self.param_bounds['take_profit_ticks']['min'] + action[4] * self.param_bounds['take_profit_ticks']['step']
        self.robot.stop_loss_ticks = self.param_bounds['stop_loss_ticks']['min'] + action[5] * self.param_bounds['stop_loss_ticks']['step']
        
        # Execute one tick
        terminated = self.robot.do_tick()
        
        # Calculate reward (Calmar Ratio)
        reward = self._calculate_reward()
        
        # Get observation
        obs = self._get_observation()
        
        # Info dict
        info = {
            'balance': self.robot.account.balance,
            'trades': len(self.robot.history),
            'drawdown': self.robot.max_equity_drawdown_value
        }
        
        self.current_step += 1
        truncated = self.current_step >= self.max_steps
        
        return obs, reward, terminated, truncated, info
    
    def _get_observation(self):
        """
        Get current observation (market state)
        
        Returns:
            np.array of shape (17,) with current market features
        """
        try:
            # Get indicator values
            ma1 = self.robot.ma1.Current.Value if hasattr(self.robot, 'ma1') else 0
            ma2 = self.robot.ma2.Current.Value if hasattr(self.robot, 'ma2') else 0
            ma3 = self.robot.ma3.Current.Value if hasattr(self.robot, 'ma3') else 0
            ma4 = self.robot.ma4.Current.Value if hasattr(self.robot, 'ma4') else 0
            
            # Calculate MA differences
            ma1_ma2 = abs(ma1 - ma2)
            ma3_ma4 = abs(ma3 - ma4)
            
            # Get current prices
            symbol = self.robot.symbol
            bid = symbol.bid
            ask = symbol.ask
            spread = ask - bid
            
            # Account info
            balance = self.robot.account.balance
            equity = self.robot.account.equity
            drawdown = self.robot.max_equity_drawdown_value
            
            # Position info
            position_size = sum(p.volume_in_units for p in self.robot.positions)
            unrealized_pnl = sum(p.net_profit for p in self.robot.positions)
            
            # Performance metrics
            num_trades = len(self.robot.history)
            winning_trades = len([x for x in self.robot.history if x.net_profit >= 0])
            win_rate = (winning_trades / num_trades) if num_trades > 0 else 0
            
            net_profit = balance - self.robot.AccountInitialBalance
            calmar = (net_profit / drawdown) if drawdown != 0 else 0
            
            # Construct observation vector
            obs = np.array([
                ma1, ma2, ma3, ma4,
                ma1_ma2, ma3_ma4,
                bid, ask, spread,
                balance, equity, drawdown,
                position_size, unrealized_pnl,
                num_trades, win_rate, calmar
            ], dtype=np.float32)
            
            return obs
            
        except Exception as e:
            # Return zero observation on error
            return np.zeros(17, dtype=np.float32)
    
    def _calculate_reward(self):
        """
        Calculate reward based on Calmar Ratio
        
        Returns:
            float: Calmar Ratio (risk-adjusted return)
        """
        net_profit = self.robot.account.balance - self.robot.AccountInitialBalance
        max_dd = self.robot.max_equity_drawdown_value
        
        if max_dd == 0:
            # No drawdown - check if profitable
            if net_profit > 0:
                return 10.0  # Good - making money without risk
            else:
                return -1.0  # Bad - no trades or flat
        
        # Calmar Ratio as reward
        calmar = net_profit / max_dd
        return calmar
    
    def render(self, mode='human'):
        """Render environment state (optional)"""
        if mode == 'human':
            print(f"Step: {self.current_step}")
            print(f"Balance: ${self.robot.account.balance:.2f}")
            print(f"Trades: {len(self.robot.history)}")
            print(f"Drawdown: ${self.robot.max_equity_drawdown_value:.2f}")


def train_ultron_with_rl(train_start, train_end, test_start, test_end, 
                         total_timesteps=10000, model_name='ultron_ppo'):
    """
    Train Ultron strategy using PPO reinforcement learning
    
    Args:
        train_start: Training start date
        train_end: Training end date
        test_start: Testing start date
        test_end: Testing end date
        total_timesteps: Number of training steps
        model_name: Name for saving the model
    
    Returns:
        Trained model and test results
    """
    from stable_baselines3 import PPO
    
    # Create training environment
    train_env = UltronEnv(train_start, train_end)
    
    print("\n" + "="*70)
    print("TRAINING ULTRON WITH PPO REINFORCEMENT LEARNING")
    print("="*70)
    print(f"Training Period: {train_start} to {train_end}")
    print(f"Total Timesteps: {total_timesteps:,}")
    print("="*70 + "\n")
    
    # Create PPO model
    model = PPO(
        "MlpPolicy",
        train_env,
        verbose=1,
        learning_rate=0.0003,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        batch_size=64,
        n_steps=2048
    )
    
    # Train model
    model.learn(total_timesteps=total_timesteps)
    
    # Save model
    model.save(model_name)
    print(f"\nModel saved to: {model_name}.zip")
    
    # Test on out-of-sample data
    print("\n" + "="*70)
    print("TESTING ON OUT-OF-SAMPLE DATA")
    print("="*70)
    
    test_env = UltronEnv(test_start, test_end)
    obs, _ = test_env.reset()
    
    total_reward = 0
    terminated = False
    
    while not terminated:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = test_env.step(action)
        total_reward += reward
        
        if terminated or truncated:
            break
    
    print(f"\nTest Results:")
    print(f"  Final Balance: ${info['balance']:.2f}")
    print(f"  Total Trades: {info['trades']}")
    print(f"  Max Drawdown: ${info['drawdown']:.2f}")
    print(f"  Total Reward: {total_reward:.2f}")
    print("="*70)
    
    return model, info


if __name__ == '__main__':
    # Example usage
    train_start = datetime(2025, 1, 1)
    train_end = datetime(2025, 1, 31)
    test_start = datetime(2025, 2, 1)
    test_end = datetime(2025, 2, 28)
    
    model, test_results = train_ultron_with_rl(
        train_start, train_end,
        test_start, test_end,
        total_timesteps=10000
    )
    
    print("\nTraining complete! Model saved.")

# End of file

