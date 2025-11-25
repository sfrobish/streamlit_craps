"""
Player of craps - controls the bet strategy and stores the outcome of all wagers.
"""

from strategies import strategy_registry
from stats import collist
import polars as pl
from typing import Tuple, Optional


class CrapsPlayer:
    """Represents a craps player with a betting strategy."""
    
    def __init__(self, id, crapgame, strategy, starting_bankroll):
        """Initialize the player.
        
        Args:
            strategy: The betting strategy to use
            starting_bankroll: Starting bankroll amount
        """
        self.id = id
        self.crapgame = crapgame
        self.strategy = strategy
        self.bankroll = starting_bankroll
        self.player_board = {
            "passline": 0,
            "passodds": 0,
            "dontpassline": 0,
            "dontpassodds": 0,
            "comeline": 0,
            "dontcomeline": 0,
            "4": {
                "place": 0,
                "buy": 0,
                "lay": 0,
                "placetolose": 0,
                "come": 0,
                "comeodds": 0,
                "dontcome": 0,
                "dontcomeodds": 0
            },
            "5": {
                "place": 0,
                "buy": 0,
                "lay": 0,
                "placetolose": 0,
                "come": 0,
                "comeodds": 0,
                "dontcome": 0,
                "dontcomeodds": 0
            },
            "6": {
                "place": 0,
                "buy": 0,
                "lay": 0,
                "placetolose": 0,
                "come": 0,
                "comeodds": 0,
                "dontcome": 0,
                "dontcomeodds": 0
            },
            "8": {
                "place": 0,
                "buy": 0,
                "lay": 0,
                "placetolose": 0,
                "come": 0,
                "comeodds": 0,
                "dontcome": 0,
                "dontcomeodds": 0
            },
            "9": {
                "place": 0,
                "buy": 0,
                "lay": 0,
                "placetolose": 0,
                "come": 0,
                "comeodds": 0,
                "dontcome": 0,
                "dontcomeodds": 0
            },
            "10": {
                "place": 0,
                "buy": 0,
                "lay": 0,
                "placetolose": 0,
                "come": 0,
                "comeodds": 0,
                "dontcome": 0,
                "dontcomeodds": 0
            }
        }
        self.bet_history = pl.DataFrame(schema=collist)
        self.position = crapgame.add_player(self)
        

    def place_bets(self):
        """
            Place a bet according to the strategy.
            Decrements the bankroll by the bet amount.
        """
        self.player_board, totalbet = strategy_registry[self.strategy](self.player_board, self.crapgame)
        self.crapgame.take_bets(self.player_board, self.id)
        self.bankroll -= totalbet

