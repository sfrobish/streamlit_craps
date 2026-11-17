import copy
import random
import polars as pl

from player import CrapsPlayer
from stats import collist, house_board_to_df

NUMBERS = [4, 5, 6, 8, 9, 10]
TRUE_ODDS = {4: 2, 10: 2, 5: 3/2, 9: 3/2, 6: 6/5, 8: 6/5}      # pass / come odds
LAY_ODDS = {4: 1/2, 10: 1/2, 5: 2/3, 9: 2/3, 6: 5/6, 8: 5/6}   # don't pass / don't come odds
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
        self.players = []
        self.board = {  
            "passline": [None] * 4,
            "passodds": [None] * 4,
            "dontpassline": [None] * 4,
            "dontpassodds": [None] * 4,
            "comeline": [None] * 4,
            "dontcomeline": [None] * 4,
            "4": {
                "place": [None] * 4,
                "buy": [None] * 4,
                "lay": [None] * 4,
                "placetolose": [None] * 4,
                "come": [None] * 4,
                "comeodds": [None] * 4,
                "dontcome": [None] * 4,
                "dontcomeodds": [None] * 4
            },
            "5": {
                "place": [None] * 4,
                "buy": [None] * 4,
                "lay": [None] * 4,
                "placetolose": [None] * 4,
                "come": [None] * 4,
                "comeodds": [None] * 4,
                "dontcome": [None] * 4,
                "dontcomeodds": [None] * 4
            },
            "6": {
                "place": [None] * 4,
                "buy": [None] * 4,
                "lay": [None] * 4,
                "placetolose": [None] * 4,
                "come": [None] * 4,
                "comeodds": [None] * 4,
                "dontcome": [None] * 4,
                "dontcomeodds": [None] * 4
            },
            "8": {
                "place": [None] * 4,
                "buy": [None] * 4,
                "lay": [None] * 4,
                "placetolose": [None] * 4,
                "come": [None] * 4,
                "comeodds": [None] * 4,
                "dontcome": [None] * 4,
                "dontcomeodds": [None] * 4
            },
            "9": {
                "place": [None] * 4,
                "buy": [None] * 4,
                "lay": [None] * 4,
                "placetolose": [None] * 4,
                "come": [None] * 4,
                "comeodds": [None] * 4,
                "dontcome": [None] * 4,
                "dontcomeodds": [None] * 4
            },
            "10": {
                "place": [None] * 4,
                "buy": [None] * 4,
                "lay": [None] * 4,
                "placetolose": [None] * 4,
                "come": [None] * 4,
                "comeodds": [None] * 4,
                "dontcome": [None] * 4,
                "dontcomeodds": [None] * 4 
            }
        }


    def add_player(self, player: 'CrapsPlayer'):
        """Add a player to the game.
        
        Args:
            player: The CrapsPlayer instance to add
        """
        self.players.append(player)
        return len(self.players) - 1  # Return player position/index


    def take_bets(self, player_board, playerid):
        """Take the bets from a player and update the house board.
        
        Args:
            player_board: The player's betting board
            playerid: The player's position/index in the game
        """
        id = playerid - 1   # Adjust for zero-based index
        for bet in self.board:
            if bet in ["4", "5", "6", "8", "9", "10"]:
                for subbet in self.board[bet]:
                    if player_board[bet][subbet] > 0:
                        self.board[bet][subbet][id] = player_board[bet][subbet]
            else:
                if player_board[bet] > 0:
                    self.board[bet][id] = player_board[bet]


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