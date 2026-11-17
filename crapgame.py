import copy
import random
import polars as pl

from player import CrapsPlayer
from stats import collist, house_board_to_df

NUMBERS = [4, 5, 6, 8, 9, 10]
SEATS = 3  # players per table
TRUE_ODDS = {4: 2, 10: 2, 5: 3/2, 9: 3/2, 6: 6/5, 8: 6/5}      # pass / come odds
LAY_ODDS = {4: 1/2, 10: 1/2, 5: 2/3, 9: 2/3, 6: 5/6, 8: 5/6}   # don't pass / don't come odds
MAX_ODDS_345 = {4: 3, 10: 3, 5: 4, 9: 4, 6: 5, 8: 5}
PLACE_ODDS = {4: 9/5, 10: 9/5, 5: 7/5, 9: 7/5, 6: 7/6, 8: 7/6}



class CrapGame:
    """The game offerred by the casino."""
    
    def __init__(self, tablemin = 5.0, limit = 1000, maxodds = "3x4x5x", seed = None):
        """Initialize the craps game.
        
        Args:
            seed: Optional random seed for reproducibility
        """
        # if seed is None:
            # seed = random.seed()
        self.tablemin = tablemin
        self.limit = limit
        self.maxodds = maxodds
        self.roundnum = 0
        self.button = "off"
        self.roll = None
        self.last_event = None  # 'sevenout' | None, set by settle_bets
        self.players = []
        self.board = {  
            "passline": [None] * SEATS,
            "passodds": [None] * SEATS,
            "dontpassline": [None] * SEATS,
            "dontpassodds": [None] * SEATS,
            "comeline": [None] * SEATS,
            "dontcomeline": [None] * SEATS,
            "4": {
                "place": [None] * SEATS,
                "buy": [None] * SEATS,
                "lay": [None] * SEATS,
                "placetolose": [None] * SEATS,
                "come": [None] * SEATS,
                "comeodds": [None] * SEATS,
                "dontcome": [None] * SEATS,
                "dontcomeodds": [None] * SEATS
            },
            "5": {
                "place": [None] * SEATS,
                "buy": [None] * SEATS,
                "lay": [None] * SEATS,
                "placetolose": [None] * SEATS,
                "come": [None] * SEATS,
                "comeodds": [None] * SEATS,
                "dontcome": [None] * SEATS,
                "dontcomeodds": [None] * SEATS
            },
            "6": {
                "place": [None] * SEATS,
                "buy": [None] * SEATS,
                "lay": [None] * SEATS,
                "placetolose": [None] * SEATS,
                "come": [None] * SEATS,
                "comeodds": [None] * SEATS,
                "dontcome": [None] * SEATS,
                "dontcomeodds": [None] * SEATS
            },
            "8": {
                "place": [None] * SEATS,
                "buy": [None] * SEATS,
                "lay": [None] * SEATS,
                "placetolose": [None] * SEATS,
                "come": [None] * SEATS,
                "comeodds": [None] * SEATS,
                "dontcome": [None] * SEATS,
                "dontcomeodds": [None] * SEATS
            },
            "9": {
                "place": [None] * SEATS,
                "buy": [None] * SEATS,
                "lay": [None] * SEATS,
                "placetolose": [None] * SEATS,
                "come": [None] * SEATS,
                "comeodds": [None] * SEATS,
                "dontcome": [None] * SEATS,
                "dontcomeodds": [None] * SEATS
            },
            "10": {
                "place": [None] * SEATS,
                "buy": [None] * SEATS,
                "lay": [None] * SEATS,
                "placetolose": [None] * SEATS,
                "come": [None] * SEATS,
                "comeodds": [None] * SEATS,
                "dontcome": [None] * SEATS,
                "dontcomeodds": [None] * SEATS 
            }
        }


    def add_player(self, player: 'CrapsPlayer'):
        """Add a player to the game.
        
        Args:
            player: The CrapsPlayer instance to add
        """
        if len(self.players) >= SEATS:
            raise ValueError(f"Table is full ({SEATS} seats)")
        self.players.append(player)
        return len(self.players) - 1  # Return player position/index


    def take_bets(self, player_board, playerid):
        """Take the bets from a player and update the house board.
        Bets over the table's limits are cut down on the player's board first.

        Args:
            player_board: The player's betting board
            playerid: The player's position/index in the game
        """
        self.enforce_limits(player_board)
        id = playerid - 1   # Adjust for zero-based index
        for bet in self.board:
            if bet in ["4", "5", "6", "8", "9", "10"]:
                for subbet in self.board[bet]:
                    self.board[bet][subbet][id] = player_board[bet][subbet]
            else:
                self.board[bet][id] = player_board[bet]


    def enforce_limits(self, board):
        """Cap every bet at the table limit, and odds at the max-odds multiple of their flat bet."""
        for key, val in board.items():
            if isinstance(val, dict):
                for sub in val:
                    val[sub] = min(val[sub], self.limit)
            else:
                board[key] = min(val, self.limit)
        for n in NUMBERS:
            spot = board[str(n)]
            spot["comeodds"] = min(spot["comeodds"], self.max_odds(n, spot["come"]))
            spot["dontcomeodds"] = min(spot["dontcomeodds"], self.max_lay(n, spot["dontcome"]))
        if self.button in NUMBERS:
            board["passodds"] = min(board["passodds"], self.max_odds(self.button, board["passline"]))
            board["dontpassodds"] = min(board["dontpassodds"], self.max_lay(self.button, board["dontpassline"]))


    def odds_multiple(self, num):
        """Max odds as a multiple of the flat bet ("3x4x5x" or e.g. "2x")."""
        return MAX_ODDS_345[num] if self.maxodds == "3x4x5x" else float(self.maxodds.rstrip("x"))


    def max_odds(self, num, flat):
        """Largest pass/come odds bet allowed behind a flat bet on num."""
        return min(flat * self.odds_multiple(num), self.limit)


    def max_lay(self, num, flat):
        """Largest don't odds bet: it may win at most the max-odds multiple of the flat bet."""
        return min(flat * self.odds_multiple(num) / LAY_ODDS[num], self.limit)


    def roll_dice(self, die1=None, die2=None) -> dict:
        """Roll two dice and return the results.  This a function of the table because the house hands out the dice and the house reads a valid roll.
        
        Returns:
            Tuple of (die1, die2, total)
        """
        if die1 is None:
            die1 = random.randint(1, 6)
        if die2 is None:
            die2 = random.randint(1, 6)
        total = die1 + die2
        self.roll = total
        
        return { 
            "die1": die1, "die2": die2, "total": total
        }


    def move_button(self, roll):
        """Move the button to the given roll number."""
        if self.button == 'off' and roll in [4,5,6,8,9,10]:
            self.button = roll
        elif self.button != 'off' and roll == 7:
            self.button = 'off'


    def _settle(self, key, num=None, mult=None, label=None):
        """Settle one bet type for every seat and clear it from the board.

        mult=None: bet loses.  mult=0: push (stake returned).
        Otherwise pays stake + stake * mult.
        """
        spots = self.board[key] if num is None else self.board[str(num)][key]
        for pos, amt in enumerate(spots):
            if not amt:  # None or 0
                continue
            if mult is not None:
                self.players[pos].take_payout(label, float(amt + amt * mult))
            spots[pos] = 0.0
            pboard = self.players[pos].player_board
            if num is None:
                pboard[key] = 0.0
            else:
                pboard[str(num)][key] = 0.0


    def _move(self, line, num, key):
        """Move a come / don't come line bet onto its number."""
        for pos, amt in enumerate(self.board[line]):
            if not amt:
                continue
            self.board[str(num)][key][pos] = amt
            self.board[line][pos] = 0.0
            pboard = self.players[pos].player_board
            pboard[str(num)][key] = pboard[line]
            pboard[line] = 0.0


    def settle_bets(self, rolldict):
        """Settle every bet on the board for one roll and move the button."""
        roll = rolldict["total"]
        point = self.button
        self.last_event = None

        if point == 'off':
            # Come-out roll. Place bets and come odds are off; don't come odds work.
            if roll in (7, 11):
                self._settle("passline", mult=1, label="passlinewon")
                self._settle("dontpassline")
                if roll == 7:
                    for n in NUMBERS:
                        self._settle("come", n)
                        self._settle("comeodds", n, mult=0, label=f"come{n}oddswon")
                        self._settle("dontcome", n, mult=1, label=f"dontcome{n}won")
                        self._settle("dontcomeodds", n, mult=LAY_ODDS[n], label=f"dontcome{n}oddswon")
            elif roll in (2, 3, 12):
                self._settle("passline")
                self._settle("dontpassline", mult=0 if roll == 12 else 1, label="dontpasslinewon")
            else:
                self._settle("come", roll, mult=1, label=f"come{roll}won")
                self._settle("comeodds", roll, mult=0, label=f"come{roll}oddswon")
                self._settle("dontcome", roll)
                self._settle("dontcomeodds", roll)
                self.button = roll
            return

        if roll == 7:
            # Seven-out
            self._settle("passline")
            self._settle("passodds")
            for n in NUMBERS:
                self._settle("place", n)
                self._settle("come", n)
                self._settle("comeodds", n)
                self._settle("dontcome", n, mult=1, label=f"dontcome{n}won")
                self._settle("dontcomeodds", n, mult=LAY_ODDS[n], label=f"dontcome{n}oddswon")
            self._settle("dontpassline", mult=1, label="dontpasslinewon")
            self._settle("dontpassodds", mult=LAY_ODDS[point], label="dontpassoddswon")
            self._settle("comeline", mult=1, label="comelinewon")
            self._settle("dontcomeline")
            self.button = 'off'
            self.last_event = 'sevenout'
        elif roll == 11:
            self._settle("comeline", mult=1, label="comelinewon")
            self._settle("dontcomeline")
        elif roll in (2, 3, 12):
            self._settle("comeline")
            self._settle("dontcomeline", mult=0 if roll == 12 else 1, label="dontcomelinewon")
        else:
            # Box number: bets on that number settle, then line bets travel to it.
            self._settle("place", roll, mult=PLACE_ODDS[roll], label=f"place{roll}won")
            self._settle("come", roll, mult=1, label=f"come{roll}won")
            self._settle("comeodds", roll, mult=TRUE_ODDS[roll], label=f"come{roll}oddswon")
            self._settle("dontcome", roll)
            self._settle("dontcomeodds", roll)
            if roll == point:
                self._settle("passline", mult=1, label="passlinewon")
                self._settle("passodds", mult=TRUE_ODDS[roll], label="passoddswon")
                self._settle("dontpassline")
                self._settle("dontpassodds")
                self.button = 'off'
            self._move("comeline", roll, "come")
            self._move("dontcomeline", roll, "dontcome")


    def play_toss(self, die1=None, die2=None) -> dict:
        """
            Play one toss of the dice. We want the initial bet to be placed when the player first joins the game.  That is why we bet last.
        """
        if self.roundnum > 0:
            # Save stats and state of board if it exists
            for player in self.players:
                player.record_round(self.roundnum)
        self.roundnum += 1
        point = self.button
        rolldict = self.roll_dice(die1, die2)
        self.settle_bets(rolldict)
        rolldict["sevenout"] = point != 'off' and rolldict["total"] == 7
        # Bet after every roll, including a seven-out (bets for the next shooter's come-out).
        for player in self.players:
            player.place_bets()

        return rolldict