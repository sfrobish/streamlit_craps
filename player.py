"""
Player of craps - controls the bet strategy and stores the outcome of all wagers.
"""
import copy
import polars as pl

from strategies import strategy_registry
from stats import collist, player_round_row



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
        self.starting_bankroll = starting_bankroll
        self.bankroll = starting_bankroll
        self.total_bet = 0
        self.prev_board = None
        self.total_wagered = 0.0   # new money put on the table
        self.total_returned = 0.0  # stake + winnings paid back
        self.player_board = {
            "passline": 0.0,
            "passodds": 0.0,
            "dontpassline": 0.0,
            "dontpassodds": 0.0,
            "comeline": 0.0,
            "dontcomeline": 0.0,
            "4": {
                "place": 0.0,
                "buy": 0.0,
                "lay": 0.0,
                "placetolose": 0.0,
                "come": 0.0,
                "comeodds": 0.0,
                "dontcome": 0.0,
                "dontcomeodds": 0.0
            },
            "5": {
                "place": 0.0,
                "buy": 0.0,
                "lay": 0.0,
                "placetolose": 0.0,
                "come": 0.0,
                "comeodds": 0.0,
                "dontcome": 0.0,
                "dontcomeodds": 0.0
            },
            "6": {
                "place": 0.0,
                "buy": 0.0,
                "lay": 0.0,
                "placetolose": 0.0,
                "come": 0.0,
                "comeodds": 0.0,
                "dontcome": 0.0,
                "dontcomeodds": 0.0
            },
            "8": {
                "place": 0.0,
                "buy": 0.0,
                "lay": 0.0,
                "placetolose": 0.0,
                "come": 0.0,
                "comeodds": 0.0,
                "dontcome": 0.0,
                "dontcomeodds": 0.0
            },
            "9": {
                "place": 0.0,
                "buy": 0.0,
                "lay": 0.0,
                "placetolose": 0.0,
                "come": 0.0,
                "comeodds": 0.0,
                "dontcome": 0.0,
                "dontcomeodds": 0.0
            },
            "10": {
                "place": 0.0,
                "buy": 0.0,
                "lay": 0.0,
                "placetolose": 0.0,
                "come": 0.0,
                "comeodds": 0.0,
                "dontcome": 0.0,
                "dontcomeodds": 0.0
            }
        }
        self.history_rows = []  # one dict per roll; DataFrame built on demand
        self.current_round_payout = { col: 0.0 for col in collist }
        self.position = crapgame.add_player(self)
        

    def place_bets(self):
        """
            Place a bet according to the strategy.
            Decrements the bankroll by the bet amount.
        """
        before = self.chips_on_table()
        # Strategy's own bet total is ignored: charge what actually landed on the table.
        self.player_board, _ = strategy_registry[self.strategy](self.player_board, self.crapgame, self.prev_board)
        self.total_bet = self.chips_on_table()
        self.crapgame.take_bets(self.player_board, self.id)
        self.total_wagered += self.total_bet - before
        self.bankroll -= self.total_bet - before


    def chips_on_table(self):
        return sum(sum(v.values()) if isinstance(v, dict) else v for v in self.player_board.values())


    @property
    def bet_history(self):
        return pl.DataFrame(self.history_rows, schema=collist, strict=False)


    def take_payout(self, bet, amount: float):
        """Add payout amount to bankroll.
        
        Args:
            amount: Amount to add to bankroll
        """
        self.current_round_payout[bet] = amount
        self.bankroll += amount
        self.total_returned += amount


    def record_round(self, roundid):
        """Record the bets and outcomes for the round."""
        round_record = {
            'player_id': self.id,
            'round_id': roundid,
            'bankroll': self.bankroll,
            'total_bets_in_play': self.total_bet
        }

        self.history_rows.append(player_round_row(round_record, self.player_board, self.current_round_payout))
        self.prev_board = copy.deepcopy(self.player_board)
        self.total_bet = 0
        self.current_round_payout = {}
