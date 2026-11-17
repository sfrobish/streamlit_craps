"""
Player of craps - controls the bet strategy and stores the outcome of all wagers.
"""
import copy
import polars as pl

from strategies import strategy_registry
from stats import collist, player_round_row



class CrapsPlayer:
    """Represents a craps player with a betting strategy."""
    
    def __init__(self, id, crapgame, strategy, starting_bankroll, profile=None):
        """Initialize the player.
        
        Args:
            strategy: Display name of the strategy (registry key or profile name)
            starting_bankroll: Starting bankroll amount
            profile: Optional press profile (see pages/edit_strategies.py);
                its base_strategy is what actually places bets.
        """
        self.id = id
        self.crapgame = crapgame
        self.strategy = strategy
        self.profile = profile
        self.pressed_odds = {}  # number -> odds size after pressing, this shooter
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
        self.update_pressed_odds()
        base = self.profile["base_strategy"] if self.profile else self.strategy
        # Strategy's own bet total is ignored: charge what actually landed on the table.
        self.player_board, _ = strategy_registry[base](self.player_board, self.crapgame, self.prev_board)
        self.press_odds()
        self.total_bet = self.chips_on_table()
        self.crapgame.take_bets(self.player_board, self.id)
        self.total_wagered += self.total_bet - before
        self.bankroll -= self.total_bet - before


    def update_pressed_odds(self):
        """After a roll: grow the pressed odds size on a number whose odds just won. Resets each shooter."""
        p = self.profile
        if not p or not p.get("odds_press_units"):
            return
        game = self.crapgame
        if game.last_event == 'sevenout':
            self.pressed_odds = {}
            return
        roll = game.roll
        if roll not in (4, 5, 6, 8, 9, 10) or not self.prev_board:
            return
        paid = lambda label: self.current_round_payout.get(label) or 0.0
        # Come odds that were off on the come-out come back at stake, which doesn't count as a win.
        come_odds = self.prev_board[str(roll)]["comeodds"]
        won = [come_odds] if paid(f"come{roll}oddswon") > come_odds else []
        if paid("passoddswon"):
            won.append(self.prev_board["passodds"])
        if won:
            self.pressed_odds[roll] = max(won) + p["odds_press_units"] * game.tablemin


    def press_odds(self):
        """Raise odds on pressed numbers to their pressed size, capped at the table's max odds.
        Only resizes odds the strategy chose to place; flat bets are untouched."""
        game, board = self.crapgame, self.player_board
        for n, amt in self.pressed_odds.items():
            spot = board[str(n)]
            if spot["come"] and spot["comeodds"]:
                spot["comeodds"] = min(max(spot["comeodds"], amt), game.max_odds(n, spot["come"]))
            if game.button == n and board["passline"] and board["passodds"]:
                board["passodds"] = min(max(board["passodds"], amt), game.max_odds(n, board["passline"]))


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
