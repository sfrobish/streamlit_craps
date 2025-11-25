"""
Simulation engine for running thousands of craps rounds.
"""
from typing import List, Dict
import polars as pl
from crapgame import CrapGame
from strategies import strategy_registry



    
def run_simulation(num_rounds: int, seed: int = None) -> pl.DataFrame:
    """Run a simulation for a specified number of rounds.
    
    Args:
        num_rounds: Number of rounds to simulate
        seed: Optional random seed for reproducibility
        
    Returns:
        DataFrame with simulation results
    """
    game = CrapGame(seed=seed)

    overalldf = pl.DataFrame()
    rolls = []

    for round_num in range(1, num_rounds + 1):
        # Play a round
        rounddict = game.play_round()
        rolls.append(rounddict["rolls"])
        historydf = rounddict["historydf"]
        overalldf = overalldf.vstack(historydf)
        
    return rolls, overalldf

    
def get_statistics(self) -> Dict:
    """Calculate statistics from the simulation results.
    
    Returns:
        Dictionary with various statistics
    """
    if not self.results:
        return {}
    
    df = pl.DataFrame(self.results)
    
    wins = len(df.filter(pl.col('outcome') == 'win'))
    losses = len(df.filter(pl.col('outcome') == 'lose'))
    total_rounds = len(df)
    
    final_bankroll = df['bankroll'][-1]
    min_bankroll = df['bankroll'].min()
    max_bankroll = df['bankroll'].max()
    
    total_wagered = abs(df['bet_result'].sum())
    net_result = final_bankroll - self.starting_bankroll
    
    return {
        'total_rounds': total_rounds,
        'total_rolls': df['total_rolls'][-1] if len(df) > 0 else 0,
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


def run_multiple_simulations(num_simulations, session_length):
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

        rolls, overalldf = run_simulation(session_length, seed=sim_num)
        

    return
