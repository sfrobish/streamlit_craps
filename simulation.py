"""
Simulation engine for running thousands of craps rounds.
"""
from typing import List, Dict
import pandas as pd
from craps_game import CrapsGame
from betting_strategies import BettingStrategy


class CrapsSimulation:
    """Run craps simulations with various betting strategies."""
    
    def __init__(self, strategy: BettingStrategy, starting_bankroll: float = 1000.0):
        """Initialize the simulation.
        
        Args:
            strategy: The betting strategy to use
            starting_bankroll: Starting bankroll amount
        """
        self.strategy = strategy
        self.starting_bankroll = starting_bankroll
        self.results = []
    
    def run_simulation(self, num_rounds: int, seed: int = None) -> pd.DataFrame:
        """Run a simulation for a specified number of rounds.
        
        Args:
            num_rounds: Number of rounds to simulate
            seed: Optional random seed for reproducibility
            
        Returns:
            DataFrame with simulation results
        """
        game = CrapsGame(seed=seed)
        bankroll = self.starting_bankroll
        results = []
        
        for round_num in range(1, num_rounds + 1):
            # Play a round
            round_result = game.play_round()
            
            # Calculate bet result
            bet_result = self.strategy.calculate_result(round_result)
            bankroll += bet_result
            
            # Store results
            results.append({
                'round': round_num,
                'outcome': round_result['outcome'],
                'point': round_result['point'],
                'num_rolls': len(round_result['rolls']),
                'bet_result': bet_result,
                'bankroll': bankroll,
                'total_rolls': sum(r['num_rolls'] for r in results) + len(round_result['rolls'])
            })
            
            # Stop if bankroll is depleted
            if bankroll <= 0:
                break
        
        self.results = results
        return pd.DataFrame(results)
    
    def get_statistics(self) -> Dict:
        """Calculate statistics from the simulation results.
        
        Returns:
            Dictionary with various statistics
        """
        if not self.results:
            return {}
        
        df = pd.DataFrame(self.results)
        
        wins = len(df[df['outcome'] == 'win'])
        losses = len(df[df['outcome'] == 'lose'])
        total_rounds = len(df)
        
        final_bankroll = df['bankroll'].iloc[-1]
        min_bankroll = df['bankroll'].min()
        max_bankroll = df['bankroll'].max()
        
        total_wagered = abs(df['bet_result'].sum())
        net_result = final_bankroll - self.starting_bankroll
        
        return {
            'total_rounds': total_rounds,
            'total_rolls': df['total_rolls'].iloc[-1] if len(df) > 0 else 0,
            'wins': wins,
            'losses': losses,
            'win_rate': wins / total_rounds if total_rounds > 0 else 0,
            'starting_bankroll': self.starting_bankroll,
            'final_bankroll': final_bankroll,
            'min_bankroll': min_bankroll,
            'max_bankroll': max_bankroll,
            'net_result': net_result,
            'roi': (net_result / self.starting_bankroll * 100) if self.starting_bankroll > 0 else 0,
        }


def run_multiple_simulations(
    strategy: BettingStrategy,
    num_simulations: int,
    rounds_per_simulation: int,
    starting_bankroll: float = 1000.0
) -> pd.DataFrame:
    """Run multiple simulations and aggregate results.
    
    Args:
        strategy: The betting strategy to use
        num_simulations: Number of simulations to run
        rounds_per_simulation: Number of rounds per simulation
        starting_bankroll: Starting bankroll for each simulation
        
    Returns:
        DataFrame with aggregated results from all simulations
    """
    all_stats = []
    
    for sim_num in range(1, num_simulations + 1):
        sim = CrapsSimulation(strategy, starting_bankroll)
        sim.run_simulation(rounds_per_simulation, seed=sim_num)
        stats = sim.get_statistics()
        stats['simulation'] = sim_num
        all_stats.append(stats)
    
    return pd.DataFrame(all_stats)
