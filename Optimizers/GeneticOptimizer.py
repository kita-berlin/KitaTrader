"""
Genetic Algorithm Optimizer for Ultron Strategy - KitaTrader Version
Uses DEAP (Distributed Evolutionary Algorithms in Python)
"""

import random
import numpy as np
import json
import os
from datetime import datetime, timedelta
from deap import base, creator, tools, algorithms
import multiprocessing as mp
from functools import partial

# Import KitaTrader components
from Api.KitaApiEnums import *
from Robots.Ultron import Ultron


class GeneticOptimizer:
    def __init__(self, config_file='optimizer_config.json', 
                 train_days=None, test_days=None, 
                 population_size=None, generations=None, num_cores=None):
        """
        Initialize Genetic Optimizer for KitaTrader
        
        Args:
            config_file: Path to optimizer configuration JSON
            train_days: Override training period from config
            test_days: Override testing period from config
            population_size: Override population size from config
            generations: Override number of generations from config
            num_cores: Override CPU core count from config
        """
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        # Optimization settings
        opt_config = self.config['optimization']
        self.train_days = train_days if train_days is not None else opt_config.get('train_days', 6)
        self.test_days = test_days if test_days is not None else opt_config.get('test_days', 2)
        self.population_size = population_size if population_size is not None else opt_config.get('population_size', 100)
        self.generations = generations if generations is not None else opt_config.get('generations', 30)
        
        # CPU cores
        cpu_percent = opt_config.get('cpu_cores_percent', 0.5)
        total_cores = mp.cpu_count()
        default_cores = int(total_cores * cpu_percent)
        self.num_cores = num_cores if num_cores is not None else default_cores
        
        # Parameter bounds
        self.param_bounds = self.config['parameter_bounds']
        
        # Fitness weights
        self.fitness_weights = self.config['fitness_weights']
        
        # Training/testing split
        data_config = self.config['data']
        start_date = datetime.strptime(data_config['start_date'], '%Y-%m-%d')
        
        self.train_start = start_date
        self.train_end = self.train_start + timedelta(days=self.train_days)
        self.test_start = self.train_end
        self.test_end = self.test_start + timedelta(days=self.test_days)
        
        print("="*70)
        print("ULTRON STRATEGY - GENETIC ALGORITHM OPTIMIZER (KitaTrader)")
        print("="*70)
        print(f"Loaded configuration from: {config_file}")
        print(f"Training: {self.train_start.strftime('%Y-%m-%d')} to {self.train_end.strftime('%Y-%m-%d')} ({self.train_days} days)")
        print(f"Testing:  {self.test_start.strftime('%Y-%m-%d')} to {self.test_end.strftime('%Y-%m-%d')} ({self.test_days} days)")
        print(f"Using {self.num_cores} of {total_cores} CPU cores ({cpu_percent*100:.0f}%)")
        print(f"(Using {cpu_percent*100:.0f}% to prevent memory overflow - configurable in optimizer_config.json)")
        print("="*70)
    
    def evaluate_individual(self, individual, train_start, train_end):
        """
        Evaluate a single individual (parameter set)
        
        Args:
            individual: List of parameter values [period1, period2, ...]
            train_start: Training start date
            train_end: Training end date
        
        Returns:
            Tuple of fitness value (Calmar Ratio)
        """
        # Create robot instance
        robot = Ultron()
        
        # Set parameters from individual
        robot.period1 = int(individual[0])
        robot.period2 = int(individual[1])
        robot.period3 = int(individual[2])
        robot.period4 = int(individual[3])
        robot.ma1_ma2_min_val = float(individual[4])
        robot.ma1_ma2_max_val = float(individual[5])
        robot.ma3_ma4_diff_max_val = float(individual[6])
        robot.take_profit_ticks = int(individual[7])
        robot.stop_loss_ticks = int(individual[8])
        
        # Configure backtest
        robot.AllDataStartUtc = train_start
        robot.BacktestStartUtc = train_start
        robot.BacktestEndUtc = train_end
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
            
            # Calculate fitness (Calmar Ratio)
            net_profit = robot.account.balance - robot.AccountInitialBalance
            max_dd = robot.max_equity_drawdown_value
            num_trades = len(robot.history)
            
            # Fitness calculation with penalties
            if max_dd == 0 or num_trades < self.fitness_weights['trades_min']:
                # No trades or no drawdown = bad
                fitness = -self.fitness_weights['inactive_penalty']
            else:
                # Calmar Ratio as primary fitness
                calmar = net_profit / max_dd
                fitness = calmar * self.fitness_weights['calmar_ratio']
                
                # Bonus for profitability
                if net_profit > 0:
                    fitness += self.fitness_weights['profit_bonus']
                
                # Penalty for too few trades
                if num_trades < self.fitness_weights['trades_good']:
                    fitness *= 0.5
            
            return (fitness,)
            
        except Exception as e:
            print(f"Error evaluating individual: {e}")
            return (-1000.0,)  # Penalty for failed evaluation
    
    def setup_deap(self):
        """Setup DEAP genetic algorithm framework"""
        # Create fitness and individual classes
        if hasattr(creator, "FitnessMax"):
            del creator.FitnessMax
        if hasattr(creator, "Individual"):
            del creator.Individual
        
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        
        toolbox = base.Toolbox()
        
        # Attribute generators for each parameter
        toolbox.register("period1", random.randint, 
                        self.param_bounds['period1']['min'],
                        self.param_bounds['period1']['max'])
        toolbox.register("period2", random.randint,
                        self.param_bounds['period2']['min'],
                        self.param_bounds['period2']['max'])
        toolbox.register("period3", random.randint,
                        self.param_bounds['period3']['min'],
                        self.param_bounds['period3']['max'])
        toolbox.register("period4", random.randint,
                        self.param_bounds['period4']['min'],
                        self.param_bounds['period4']['max'])
        toolbox.register("ma1_ma2_min", random.uniform,
                        self.param_bounds['ma1_ma2_min_val']['min'],
                        self.param_bounds['ma1_ma2_min_val']['max'])
        toolbox.register("ma1_ma2_max", random.uniform,
                        self.param_bounds['ma1_ma2_max_val']['min'],
                        self.param_bounds['ma1_ma2_max_val']['max'])
        toolbox.register("ma3_ma4_diff", random.uniform,
                        self.param_bounds['ma3_ma4_diff_max_val']['min'],
                        self.param_bounds['ma3_ma4_diff_max_val']['max'])
        toolbox.register("tp_ticks", random.randint,
                        self.param_bounds['take_profit_ticks']['min'],
                        self.param_bounds['take_profit_ticks']['max'])
        toolbox.register("sl_ticks", random.randint,
                        self.param_bounds['stop_loss_ticks']['min'],
                        self.param_bounds['stop_loss_ticks']['max'])
        
        # Individual and population
        toolbox.register("individual", tools.initCycle, creator.Individual,
                        (toolbox.period1, toolbox.period2, toolbox.period3, toolbox.period4,
                         toolbox.ma1_ma2_min, toolbox.ma1_ma2_max, toolbox.ma3_ma4_diff,
                         toolbox.tp_ticks, toolbox.sl_ticks), n=1)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        
        # Genetic operators
        toolbox.register("evaluate", partial(self.evaluate_individual, 
                                             train_start=self.train_start, 
                                             train_end=self.train_end))
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", tools.mutPolynomialBounded,
                        low=[self.param_bounds['period1']['min'],
                             self.param_bounds['period2']['min'],
                             self.param_bounds['period3']['min'],
                             self.param_bounds['period4']['min'],
                             self.param_bounds['ma1_ma2_min_val']['min'],
                             self.param_bounds['ma1_ma2_max_val']['min'],
                             self.param_bounds['ma3_ma4_diff_max_val']['min'],
                             self.param_bounds['take_profit_ticks']['min'],
                             self.param_bounds['stop_loss_ticks']['min']],
                        up=[self.param_bounds['period1']['max'],
                            self.param_bounds['period2']['max'],
                            self.param_bounds['period3']['max'],
                            self.param_bounds['period4']['max'],
                            self.param_bounds['ma1_ma2_min_val']['max'],
                            self.param_bounds['ma1_ma2_max_val']['max'],
                            self.param_bounds['ma3_ma4_diff_max_val']['max'],
                            self.param_bounds['take_profit_ticks']['max'],
                            self.param_bounds['stop_loss_ticks']['max']],
                        eta=20, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=3)
        
        return toolbox
    
    def run(self):
        """Run genetic algorithm optimization"""
        print("\n" + "="*70)
        print("GENETIC ALGORITHM OPTIMIZATION")
        print("="*70)
        print(f"Population Size: {self.population_size}")
        print(f"Generations: {self.generations}")
        print(f"Training Period: {self.train_days} days")
        print(f"Testing Period: {self.test_days} days")
        print("="*70 + "\n")
        
        # Setup DEAP
        toolbox = self.setup_deap()
        
        # Create initial population
        pop = toolbox.population(n=self.population_size)
        
        # Hall of Fame to store best individuals
        hof = tools.HallOfFame(1)
        
        # Statistics
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("std", np.std)
        stats.register("min", np.min)
        stats.register("max", np.max)
        
        # Run evolution with multiprocessing
        with mp.Pool(processes=self.num_cores) as pool:
            toolbox.register("map", pool.map)
            
            pop, log = algorithms.eaSimple(
                pop, toolbox,
                cxpb=0.5,      # Crossover probability
                mutpb=0.2,     # Mutation probability
                ngen=self.generations,
                stats=stats,
                halloffame=hof,
                verbose=True
            )
        
        # Get best parameters
        best_individual = hof[0]
        best_params = {
            'period1': int(best_individual[0]),
            'period2': int(best_individual[1]),
            'period3': int(best_individual[2]),
            'period4': int(best_individual[3]),
            'ma1_ma2_min_val': float(best_individual[4]),
            'ma1_ma2_max_val': float(best_individual[5]),
            'ma3_ma4_diff_max_val': float(best_individual[6]),
            'take_profit_ticks': int(best_individual[7]),
            'stop_loss_ticks': int(best_individual[8])
        }
        
        print("\n" + "="*70)
        print("BEST PARAMETERS (Training):")
        print("="*70)
        for key, value in best_params.items():
            print(f"  {key}: {value}")
        print("="*70)
        
        # Test on out-of-sample data
        print("\n" + "="*70)
        print("TESTING ON OUT-OF-SAMPLE DATA...")
        print("="*70)
        
        robot = Ultron()
        robot.period1 = best_params['period1']
        robot.period2 = best_params['period2']
        robot.period3 = best_params['period3']
        robot.period4 = best_params['period4']
        robot.ma1_ma2_min_val = best_params['ma1_ma2_min_val']
        robot.ma1_ma2_max_val = best_params['ma1_ma2_max_val']
        robot.ma3_ma4_diff_max_val = best_params['ma3_ma4_diff_max_val']
        robot.take_profit_ticks = best_params['take_profit_ticks']
        robot.stop_loss_ticks = best_params['stop_loss_ticks']
        
        robot.AllDataStartUtc = self.test_start
        robot.BacktestStartUtc = self.test_start
        robot.BacktestEndUtc = self.test_end
        robot.RunningMode = RunMode.SilentBacktesting
        robot.DataPath = "$(OneDrive)/KitaData/cfd"
        robot.DataMode = DataMode.Preload
        robot.AccountInitialBalance = 10000.0
        robot.AccountLeverage = 500
        robot.AccountCurrency = "EUR"
        
        robot.do_init()
        robot.do_start()
        while not robot.do_tick():
            pass
        robot.do_stop()
        
        # Test results
        test_pnl = robot.account.balance - robot.AccountInitialBalance
        test_dd = robot.max_equity_drawdown_value
        test_trades = len(robot.history)
        test_calmar = test_pnl / test_dd if test_dd != 0 else 0
        
        test_result = {
            'balance': robot.account.balance,
            'pnl': test_pnl,
            'pnl_pct': (test_pnl / robot.AccountInitialBalance) * 100,
            'max_drawdown': test_dd,
            'calmar': test_calmar,
            'trades': test_trades
        }
        
        print("\n" + "="*70)
        print("OUT-OF-SAMPLE TEST RESULTS:")
        print("="*70)
        print(f"  P&L: ${test_result['pnl']:.2f} ({test_result['pnl_pct']:+.2f}%)")
        print(f"  Calmar Ratio: {test_result['calmar']:.2f}")
        print(f"  Max Drawdown: ${test_result['max_drawdown']:.2f}")
        print(f"  Total Trades: {test_result['trades']}")
        print("="*70)
        
        # Save results
        results = {
            'best_params': best_params,
            'test_results': test_result,
            'optimization_settings': {
                'population_size': self.population_size,
                'generations': self.generations,
                'train_days': self.train_days,
                'test_days': self.test_days
            }
        }
        
        with open('genetic_optimization_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "="*70)
        print("Results saved to: genetic_optimization_results.json")
        print("="*70)
        
        return best_params, test_result


def main():
    """Run genetic optimization"""
    config_file = 'optimizer_config.json'
    
    optimizer = GeneticOptimizer(
        config_file=config_file
        # All other parameters come from config file
    )
    
    best_params, test_result = optimizer.run()
    
    print("\n" + "="*70)
    print("OPTIMIZATION COMPLETE!")
    print("="*70)


if __name__ == '__main__':
    main()

# End of file

