"""
Walk-Forward Optimizer for Ultron Strategy - KitaTrader Version
Implements rolling window optimization with grid search
"""

import json
import numpy as np
from datetime import datetime, timedelta
from itertools import product
import multiprocessing as mp
from functools import partial

# Import KitaTrader components
from Api.KitaApiEnums import *
from Robots.Ultron import Ultron


class WalkForwardOptimizer:
    def __init__(self, config_file='optimizer_config.json',
                 train_days=None, test_days=None, anchor=None, num_cores=None):
        """
        Initialize Walk-Forward Optimizer for KitaTrader
        
        Args:
            config_file: Path to optimizer configuration JSON
            train_days: Override training period from config
            test_days: Override testing period from config
            anchor: Override anchor mode from config
            num_cores: Override CPU core count from config
        """
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        # Optimization settings
        opt_config = self.config['optimization']
        self.train_days = train_days if train_days is not None else opt_config.get('train_days', 6)
        self.test_days = test_days if test_days is not None else opt_config.get('test_days', 2)
        self.anchor = anchor if anchor is not None else opt_config.get('anchor', False)
        
        # CPU cores
        cpu_percent = opt_config.get('cpu_cores_percent', 0.5)
        total_cores = mp.cpu_count()
        default_cores = int(total_cores * cpu_percent)
        self.num_cores = num_cores if num_cores is not None else default_cores
        
        # Parameter bounds
        self.param_bounds = self.config['parameter_bounds']
        
        # Data configuration
        data_config = self.config['data']
        self.symbol = data_config['symbol']
        
        print("="*70)
        print("ULTRON STRATEGY - WALK-FORWARD OPTIMIZER (KitaTrader)")
        print("="*70)
        print(f"Loaded configuration from: {config_file}")
        print(f"Using {self.num_cores} of {total_cores} CPU cores ({cpu_percent*100:.0f}%)")
        print(f"(Using {cpu_percent*100:.0f}% to prevent memory overflow - configurable in optimizer_config.json)")
        print("="*70)
    
    def generate_param_grid(self):
        """Generate parameter grid from config bounds"""
        param_grid = {}
        
        for param_name, bounds in self.param_bounds.items():
            if bounds['type'] == 'int':
                param_grid[param_name] = list(range(
                    bounds['min'],
                    bounds['max'] + 1,
                    bounds['step']
                ))
            elif bounds['type'] == 'float':
                values = []
                current = bounds['min']
                while current <= bounds['max']:
                    values.append(round(current, 10))
                    current += bounds['step']
                param_grid[param_name] = values
        
        return param_grid
    
    def generate_windows(self, start_date, end_date):
        """Generate train/test windows"""
        windows = []
        anchor_start = start_date
        current_start = start_date
        
        while current_start < end_date:
            # Training window
            if self.anchor:
                train_start = anchor_start  # Anchored - always start from beginning
            else:
                train_start = current_start  # Rolling - moves forward
            
            train_end = current_start + timedelta(days=self.train_days)
            
            # Testing window
            test_start = train_end
            test_end = test_start + timedelta(days=self.test_days)
            
            # Check if we have enough data
            if test_end > end_date:
                break
            
            windows.append({
                'train_start': train_start,
                'train_end': train_end,
                'test_start': test_start,
                'test_end': test_end
            })
            
            # Move to next window
            current_start = test_start  # Rolling forward
        
        return windows
    
    def run_backtest(self, params, start_date, end_date, verbose=False):
        """
        Run single backtest with given parameters
        
        Args:
            params: Dictionary of parameter values
            start_date: Backtest start date
            end_date: Backtest end date
            verbose: Print trade details
        
        Returns:
            Dictionary of performance metrics
        """
        robot = Ultron()
        
        # Set parameters
        robot.period1 = params['period1']
        robot.period2 = params['period2']
        robot.period3 = params['period3']
        robot.period4 = params['period4']
        robot.ma1_ma2_min_val = params['ma1_ma2_min_val']
        robot.ma1_ma2_max_val = params['ma1_ma2_max_val']
        robot.ma3_ma4_diff_max_val = params['ma3_ma4_diff_max_val']
        robot.take_profit_ticks = params['take_profit_ticks']
        robot.stop_loss_ticks = params['stop_loss_ticks']
        
        # Configure backtest
        robot.AllDataStartUtc = start_date
        robot.BacktestStartUtc = start_date
        robot.BacktestEndUtc = end_date
        robot.RunningMode = RunMode.SilentBacktesting
        robot.DataPath = "$(OneDrive)/KitaData/cfd"
        robot.DataMode = DataMode.Preload
        robot.AccountInitialBalance = 10000.0
        robot.AccountLeverage = 500
        robot.AccountCurrency = "EUR"
        
        try:
            # Run backtest
            robot.do_init()
            robot.do_start()
            
            while not robot.do_tick():
                pass
            
            robot.do_stop()
            
            # Calculate metrics
            net_profit = robot.account.balance - robot.AccountInitialBalance
            max_dd = robot.max_equity_drawdown_value
            num_trades = len(robot.history)
            
            winning_trades = len([x for x in robot.history if x.net_profit >= 0])
            losing_trades = len([x for x in robot.history if x.net_profit < 0])
            
            # Calculate Calmar Ratio
            if max_dd == 0:
                calmar = 0
            else:
                calmar = net_profit / max_dd
            
            return {
                'balance': robot.account.balance,
                'pnl': net_profit,
                'pnl_pct': (net_profit / robot.AccountInitialBalance) * 100,
                'max_drawdown': max_dd,
                'calmar': calmar,
                'trades': num_trades,
                'wins': winning_trades,
                'losses': losing_trades,
                'win_rate': (winning_trades / num_trades * 100) if num_trades > 0 else 0
            }
        
        except Exception as e:
            print(f"Error in backtest: {e}")
            return {
                'balance': 10000.0,
                'pnl': 0,
                'pnl_pct': 0,
                'max_drawdown': 0,
                'calmar': -1000,
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0
            }
    
    def optimize_window(self, train_start, train_end, test_start, test_end, param_grid, window_num):
        """Optimize parameters for one walk-forward window"""
        print("\n" + "="*70)
        print(f"Window {window_num}: Optimizing")
        print(f"Training: {train_start.strftime('%Y-%m-%d')} to {train_end.strftime('%Y-%m-%d')}")
        print(f"Testing:  {test_start.strftime('%Y-%m-%d')} to {test_end.strftime('%Y-%m-%d')}")
        print("="*70)
        
        # Generate all parameter combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))
        
        print(f"Testing {len(combinations):,} parameter combinations...")
        print("="*70)
        
        # Convert to list of param dicts
        param_dicts = []
        for combo in combinations:
            param_dict = dict(zip(param_names, combo))
            param_dicts.append(param_dict)
        
        # Run parallel optimization
        backtest_func = partial(self.run_backtest, 
                               start_date=train_start, 
                               end_date=train_end, 
                               verbose=False)
        
        with mp.Pool(processes=self.num_cores) as pool:
            results = pool.map(backtest_func, param_dicts)
        
        # Find best parameters based on Calmar Ratio
        best_idx = max(range(len(results)), key=lambda i: results[i]['calmar'])
        best_params = param_dicts[best_idx]
        best_result = results[best_idx]
        
        print("\n" + "="*70)
        print("Best Training Parameters:")
        print("="*70)
        for key, value in best_params.items():
            print(f"  {key}: {value}")
        print(f"\nTraining Performance:")
        print(f"  P&L: ${best_result['pnl']:.2f} ({best_result['pnl_pct']:+.2f}%)")
        print(f"  Calmar: {best_result['calmar']:.3f}")
        print(f"  Max DD: ${best_result['max_drawdown']:.2f}")
        print(f"  Trades: {best_result['trades']}")
        print(f"  Win Rate: {best_result['win_rate']:.1f}%")
        print("="*70)
        
        # Test on out-of-sample data
        print("\nTesting on out-of-sample data...")
        test_result = self.run_backtest(best_params, test_start, test_end, verbose=False)
        
        print("\n" + "="*70)
        print("Out-of-Sample Performance:")
        print("="*70)
        print(f"  P&L: ${test_result['pnl']:.2f} ({test_result['pnl_pct']:+.2f}%)")
        print(f"  Calmar: {test_result['calmar']:.3f}")
        print(f"  Max DD: ${test_result['max_drawdown']:.2f}")
        print(f"  Trades: {test_result['trades']}")
        print(f"  Win Rate: {test_result['win_rate']:.1f}%")
        print("="*70)
        
        return {
            'window': window_num,
            'train_start': train_start.strftime('%Y-%m-%d'),
            'train_end': train_end.strftime('%Y-%m-%d'),
            'test_start': test_start.strftime('%Y-%m-%d'),
            'test_end': test_end.strftime('%Y-%m-%d'),
            'best_params': best_params,
            'train_result': best_result,
            'test_result': test_result
        }
    
    def run(self):
        """Run walk-forward optimization"""
        # Get date range from config
        data_config = self.config['data']
        start_date = datetime.strptime(data_config['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(data_config['end_date'], '%Y-%m-%d')
        
        # Generate parameter grid
        param_grid = self.generate_param_grid()
        
        # Generate windows
        windows = self.generate_windows(start_date, end_date)
        
        print("\n" + "="*70)
        print("WALK-FORWARD OPTIMIZATION")
        print("="*70)
        print(f"Training Period: {self.train_days} days")
        print(f"Testing Period: {self.test_days} days")
        print(f"Method: {'Anchored' if self.anchor else 'Rolling'}")
        print(f"Generated {len(windows)} walk-forward windows")
        
        # Print parameter grid info
        print("\nParameter ranges loaded from config:")
        for param_name, values in param_grid.items():
            print(f"  {param_name}: {len(values)} values ({min(values)} to {max(values)})")
        
        total_combinations = np.prod([len(v) for v in param_grid.values()])
        print(f"Parameter grid size: {total_combinations:,} combinations")
        print("="*70)
        
        # Optimize each window
        all_results = []
        for i, window in enumerate(windows, 1):
            result = self.optimize_window(
                window['train_start'],
                window['train_end'],
                window['test_start'],
                window['test_end'],
                param_grid,
                i
            )
            all_results.append(result)
        
        # Aggregate results
        print("\n" + "="*70)
        print("WALK-FORWARD ANALYSIS SUMMARY")
        print("="*70)
        
        test_pnls = [r['test_result']['pnl'] for r in all_results]
        test_calmars = [r['test_result']['calmar'] for r in all_results]
        test_trades = [r['test_result']['trades'] for r in all_results]
        test_win_rates = [r['test_result']['win_rate'] for r in all_results]
        
        print(f"Out-of-Sample Performance (Combined):")
        print(f"  Total P&L: ${sum(test_pnls):.2f}")
        print(f"  Average P&L: ${np.mean(test_pnls):.2f}")
        print(f"  Average Calmar: {np.mean(test_calmars):.3f}")
        print(f"  Total Trades: {sum(test_trades)}")
        print(f"  Average Win Rate: {np.mean(test_win_rates):.1f}%")
        print("="*70)
        
        # Parameter stability analysis
        print("\n" + "="*70)
        print("PARAMETER STABILITY ANALYSIS")
        print("="*70)
        
        all_params = {}
        for result in all_results:
            for key, value in result['best_params'].items():
                if key not in all_params:
                    all_params[key] = []
                all_params[key].append(value)
        
        print("Most Common Parameter Values:")
        for param_name, values in all_params.items():
            unique, counts = np.unique(values, return_counts=True)
            sorted_idx = np.argsort(-counts)
            
            print(f"  {param_name}:")
            for idx in sorted_idx[:3]:  # Top 3
                pct = (counts[idx] / len(values)) * 100
                print(f"    {unique[idx]}: {counts[idx]} times ({pct:.0f}%)")
        print("="*70)
        
        # Save results
        results_dict = {
            'windows': all_results,
            'summary': {
                'total_pnl': float(sum(test_pnls)),
                'average_pnl': float(np.mean(test_pnls)),
                'average_calmar': float(np.mean(test_calmars)),
                'total_trades': int(sum(test_trades)),
                'average_win_rate': float(np.mean(test_win_rates))
            },
            'parameter_stability': {
                param_name: {
                    'values': [float(v) if isinstance(v, (float, np.floating)) else int(v) 
                              for v in values],
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values))
                }
                for param_name, values in all_params.items()
            },
            'optimization_settings': {
                'train_days': self.train_days,
                'test_days': self.test_days,
                'anchor': self.anchor,
                'num_windows': len(windows)
            }
        }
        
        with open('walk_forward_results.json', 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        print("\n" + "="*70)
        print("Results saved to: walk_forward_results.json")
        print("="*70)
        
        return results_dict


def main():
    """Run walk-forward optimization"""
    config_file = 'optimizer_config.json'
    
    optimizer = WalkForwardOptimizer(
        config_file=config_file
        # All other parameters come from config file
    )
    
    results = optimizer.run()
    
    print("\n" + "="*70)
    print("OPTIMIZATION COMPLETE!")
    print("="*70)


if __name__ == '__main__':
    main()

# End of file

