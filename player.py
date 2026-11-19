"""
Player of craps - controls the bet strategy and stores the outcome of all wagers.
"""
import copy
import polars as pl

from strategies import PRESETS, strategy_registry
from stats import collist, player_round_row

# Seat options (side bets), added on top of any strategy.
PLACE_68, FIELD, CE_COMEOUT, CE_ALWAYS = "Place 6&8", "Field", "C&E come-out", "C&E every roll"


class CrapsPlayer:
    """Represents a craps player with a betting strategy."""

    def __init__(self, id, crapgame, strategy, starting_bankroll, profile=None, side_bets=()):
        """Initialize the player.

        Args:
            strategy: Display name of the strategy (registry key or profile name)
            starting_bankroll: Starting bankroll amount
            profile: Optional press profile (see pages/edit_strategies.py);
                its base_strategy is what actually places bets.
            side_bets: any of PLACE_68, FIELD, CE_COMEOUT, CE_ALWAYS
        """
        self.id = id
        self.crapgame = crapgame
        self.strategy = strategy
        self.profile = profile or PRESETS.get(strategy)
        self.side_bets = set(side_bets)
        self.pressed_odds = {}  # number -> odds size after pressing, this shooter
        self.pressed_flat = 0.0  # extra come-line flat from come wins (profile flat_press_units), this shooter
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
            "field": 0.0,
            "ce": 0.0,
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
        self.player_board = strategy_registry[base](self.player_board, self.crapgame)
        self.press_odds()
        self.add_side_bets()
        self.crapgame.take_bets(self.player_board, self.id)  # house trims anything over its limits
        self.total_bet = self.chips_on_table()
        self.total_wagered += self.total_bet - before
        self.bankroll -= self.total_bet - before


    def update_pressed_odds(self):
        """After a roll: grow the pressed odds size on a number whose odds just won. Resets each shooter."""
        p = self.profile
        if not p or not (p.get("odds_press_units") or p.get("flat_press_units")):
            return
        game = self.crapgame
        if game.last_event == 'sevenout':
            self.pressed_odds = {}
            self.pressed_flat = 0.0
            return
        roll = game.roll
        if roll not in (4, 5, 6, 8, 9, 10) or not self.prev_board:
            return
        paid = lambda label: self.current_round_payout.get(label) or 0.0
        if p.get("flat_press_units") and paid(f"come{roll}won"):
            self.pressed_flat += p["flat_press_units"] * game.tablemin
        if not p.get("odds_press_units"):
            return
        # Come odds that were off on the come-out come back at stake, which doesn't count as a win.
        come_odds = self.prev_board[str(roll)]["comeodds"]
        won = [come_odds] if paid(f"come{roll}oddswon") > come_odds else []
        if paid("passoddswon"):
            won.append(self.prev_board["passodds"])
        if won:
            self.pressed_odds[roll] = max(won) + p["odds_press_units"] * game.tablemin


    def press_odds(self):
        """Raise odds on pressed numbers to their pressed size (the house caps it at max odds),
        and the new come-line bet by any flat press. Only resizes bets the strategy chose to place."""
        board = self.player_board
        if self.pressed_flat and board["comeline"]:
            board["comeline"] = max(board["comeline"], self.crapgame.tablemin + self.pressed_flat)
        for n, amt in self.pressed_odds.items():
            spot = board[str(n)]
            if spot["come"] and spot["comeodds"]:
                spot["comeodds"] = max(spot["comeodds"], amt)
            if self.crapgame.button == n and board["passline"] and board["passodds"]:
                board["passodds"] = max(board["passodds"], amt)


    def add_side_bets(self):
        """Seat options on top of the strategy, each 1 unit (place 6/8 at 6/5 unit).
        Place 6 & 8 go up while a point is on, skipping the point and numbers with this seat's come bet."""
        board, game, unit = self.player_board, self.crapgame, self.crapgame.tablemin
        if PLACE_68 in self.side_bets and game.button != 'off':
            for n in ("6", "8"):
                if game.button != int(n) and not board[n]["come"] and not board[n]["place"]:
                    board[n]["place"] = unit * 6 / 5
        if FIELD in self.side_bets:
            board["field"] = unit
        if CE_ALWAYS in self.side_bets or (CE_COMEOUT in self.side_bets and game.button == 'off'):
            board["ce"] = unit


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
