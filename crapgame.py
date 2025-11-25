import random
import polars as pl

from player import CrapsPlayer
from stats import collist, house_board_to_df


class CrapGame:
    """The game offerred by the casino."""
    
    def __init__(self, tablemin = 5, limit = 1000, maxodds = "3x4x5x", seed = None):
        """Initialize the craps game.
        
        Args:
            seed: Optional random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
        self.tablemin = tablemin
        self.limit = limit
        self.maxodds = maxodds
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


    def roll_dice(self):
        """Roll two dice and return the results.  This a function of the table because the house hands out the dice and the house reads a valid roll.
        
        Returns:
            Tuple of (die1, die2, total)
        """
        die1 = random.randint(1, 6)
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


    def pay_even_money(self, roll, bet_type):

        if bet_type in ['passline', 'comeline', 'dontpassline', 'dontcomeline']:
            for pos in range(len(self.board[bet_type])):
                if self.board[bet_type][pos] is not None and self.board[bet_type][pos] > 0:
                    self.players[pos].bankroll += self.board[bet_type][pos] * 2
                    self.board[bet_type][pos] = 0
                    self.players[pos].player_board[bet_type] = 0
        elif bet_type in ['come', 'dontcome']:
            for pos in range(len(self.board[f"{roll}"][bet_type])):
                if self.board[f"{roll}"][bet_type][pos] is not None and self.board[f"{roll}"][bet_type][pos] > 0:
                    self.players[pos].bankroll += self.board[f"{roll}"][bet_type][pos] * 2
                    self.board[f"{roll}"][bet_type][pos] = 0
                    self.players[pos].player_board[f"{roll}"][bet_type] = 0
            

    def pay_place(self, roll):

        if roll in [4, 10]:
            paymult = 9/5
        elif roll in [5, 9]:
            paymult = 7/5
        elif roll in [6, 8]:
            paymult = 7/6

        for pos in range(len(self.board[f"{roll}"]["place"])):
            if self.board[f"{roll}"]["place"][pos] is not None and self.board[f"{roll}"]["place"][pos] > 0:
                self.players[pos].bankroll += self.board[f"{roll}"]["place"][pos] + (self.board[f"{roll}"]["place"][pos] * paymult)
                self.board[f"{roll}"]["place"][pos] = 0
                self.players[pos].player_board[f"{roll}"]["place"] = 0

    
    def pay_odds(self, roll, is_come=True):

        if roll in [4, 10]:
            paymult = 2
        elif roll in [5, 9]:
            paymult = 3/2
        elif roll in [6, 8]:
            paymult = 6/5

        if is_come:
            for pos in range(len(self.board[f"{roll}"]["comeodds"])):
                if self.board[f"{roll}"]["comeodds"][pos] is not None and self.board[f"{roll}"]["comeodds"][pos] > 0:
                    self.players[pos].bankroll += self.board[f"{roll}"]["comeodds"][pos] + (self.board[f"{roll}"]["comeodds"][pos] * paymult)
                    self.board[f"{roll}"]["comeodds"][pos] = 0
                    self.players[pos].player_board[f"{roll}"]["comeodds"] = 0
        else:
            for pos in range(len(self.board["passodds"])):
                if self.board["passodds"][pos] is not None and self.board["passodds"][pos] > 0:
                    self.players[pos].bankroll += self.board["passodds"][pos] + (self.board["passodds"][pos] * paymult)
                    self.board["passodds"][pos] = 0
                    self.players[pos].player_board["passodds"] = 0


    def pay_darkside_odds(self):

        for num in [4,5,6,8,9,10]:
            
            if num in [4, 10]:
                paymult = 1/2
            elif num in [5, 9]:
                paymult = 2/3
            elif num in [6, 8]:
                paymult = 5/6

            for pos in range(len(self.board[f"{num}"]["dontcomeodds"])):
                if self.board[f"{num}"]["dontcomeodds"][pos] is not None and self.board[f"{num}"]["dontcomeodds"][pos] > 0:
                    self.players[pos].bankroll += self.board[f"{num}"]["dontcomeodds"][pos] + (self.board[f"{num}"]["dontcomeodds"][pos] * paymult)
                    self.board[f"{num}"]["dontcomeodds"][pos] = 0
                    self.players[pos].player_board[f"{num}"]["dontcomeodds"] = 0
            for pos in range(len(self.board["dontpassodds"])):
                if self.board["dontpassodds"][pos] is not None and self.board["dontpassodds"][pos] > 0:
                    self.players[pos].bankroll += self.board["dontpassodds"][pos] + (self.board["dontpassodds"][pos] * paymult)
                    self.board["dontpassodds"][pos] = 0
                    self.players[pos].player_board["dontpassodds"] = 0


    def settle_bets(self, rolldict) -> dict:
        """Play one round of craps (may involve multiple rolls).
        
        Returns:
            Dictionary containing round results with keys:
            - rolls: list of (die1, die2, total) tuples
            - outcome: 'win' or 'lose' for pass line bet
            - point: the point that was established (if any)
        """
        
        roll = rolldict["total"]
        button = self.button

        if button == 'off' and roll in [7, 11]:
            # Front line wins
            for pos in range(len(self.board["passline"])):
                if self.board["passline"][pos] is not None and self.board["passline"][pos] > 0:
                    self.pay_even_money(roll, "passline")
                if self.board["passodds"][pos] is not None and self.board["passodds"][pos] > 0:
                    self.pay_odds(roll, is_come=False)
            # Come line bets shouldn't be out if the button is off

            # Established come bets lose - not offering to turn them off for now
            if roll == 7:
                for boardnum in [4, 5, 6, 8, 9, 10]:
                    for pos in range(len(self.board[f"{boardnum}"]["come"])):
                        if self.board[f"{boardnum}"]["come"][pos] is not None and self.board[f"{boardnum}"]["come"][pos] > 0:
                            self.board[f"{boardnum}"]["come"][pos] = 0
                            self.players[pos].player_board[f"{boardnum}"]["come"] = 0
                    for pos in range(len(self.board[f"{boardnum}"]["comeodds"])):
                        if self.board[f"{boardnum}"]["comeodds"][pos] is not None and self.board[f"{boardnum}"]["comeodds"][pos] > 0:
                            self.board[f"{boardnum}"]["comeodds"][pos] = 0
                            self.players[pos].player_board[f"{boardnum}"]["comeodds"] = 0

            # Dark side loses
            for pos in range(len(self.board["dontpassline"])):
                if self.board["dontpassline"][pos] is not None and self.board["dontpassline"][pos] > 0:
                    self.board["dontpassline"][pos] = 0
                    self.players[pos].player_board["dontpassline"] = 0
            

        elif button == 'off' and roll in [2, 3, 12]:
            # Front line loses
            for pos in range(len(self.board["passline"])):
                if self.board["passline"][pos] is not None and self.board["passline"][pos] > 0:
                    self.board["passline"][pos] = 0
                    self.players[pos].player_board["passline"] = 0
            # Come bets shouldn't be out if the button is off

            # Bar 12 pushes on don't pass
            if roll == 12:
                for pos in range(len(self.board["dontpassline"])):
                    if self.board["dontpassline"][pos] is not None and self.board["dontpassline"][pos] > 0:
                        self.players[pos].bankroll += self.board["dontpassline"][pos]
                        self.board["dontpassline"][pos] = 0
                        self.players[pos].player_board["dontpassline"] = 0
            else:
                for pos in range(len(self.board["dontpassline"])):
                    if self.board["dontpassline"][pos] is not None and self.board["dontpassline"][pos] > 0:
                        self.pay_even_money(roll, "dontpassline")
            # Don't come bets shouldn't be out if the button is off
            
        elif button == 'off' and roll in [4, 5, 6, 8, 9, 10]:
            # We are assuing place bets come "off" when the point is not set
            # There is an enhancment to the bet strategy that leaves place bets on during the come-out
            
            # self.pay_place(roll)

            # Comebets made prior to the point being hit get paid
            self.pay_odds(roll) 

            # Dark side don't come on the number loses
            for pos in range(len(self.board[f"{roll}"]["dontcome"])):
                if self.board[f"{roll}"]["dontcome"][pos] is not None and self.board[f"{roll}"]["dontcome"][pos] > 0:
                    self.board[f"{roll}"]["dontcome"][pos] = 0
                    self.players[pos].player_board[f"{roll}"]["dontcome"] = 0

            # Set the button
            self.button = roll

        elif button != 'off' and roll == 7:
            # Collect the losing bets
            for pos in range(len(self.board["passline"])):
                if self.board["passline"][pos] is not None and self.board["passline"][pos] > 0:
                    self.board["passline"][pos] = 0
                    self.players[pos].player_board["passline"] = 0
            for pos in range(len(self.board["passodds"])):
                if self.board["passodds"][pos] is not None and self.board["passodds"][pos] > 0:
                    self.board["passodds"][pos] = 0
                    self.players[pos].player_board["passodds"] = 0
            for boardnum in [4, 5, 6, 8, 9, 10]:
                for pos in range(len(self.board[f"{boardnum}"]["place"])):
                    if self.board[f"{boardnum}"]["place"][pos] is not None and self.board[f"{boardnum}"]["place"][pos] > 0:
                        self.board[f"{boardnum}"]["place"][pos] = 0
                        self.players[pos].player_board[f"{boardnum}"]["place"] = 0
                for pos in range(len(self.board[f"{boardnum}"]["come"])):
                    if self.board[f"{boardnum}"]["come"][pos] is not None and self.board[f"{boardnum}"]["come"][pos] > 0:
                        self.board[f"{boardnum}"]["come"][pos] = 0
                        self.players[pos].player_board[f"{boardnum}"]["come"] = 0
                for pos in range(len(self.board[f"{boardnum}"]["comeodds"])):
                    if self.board[f"{boardnum}"]["comeodds"][pos] is not None and self.board[f"{boardnum}"]["comeodds"][pos] > 0:
                        self.board[f"{boardnum}"]["comeodds"][pos] = 0
                        self.players[pos].player_board[f"{boardnum}"]["comeodds"] = 0
            # Pay the comeline bets
            for pos in range(len(self.board["comeline"])):
                if self.board["comeline"][pos] is not None and self.board["comeline"][pos] > 0:
                    self.pay_even_money(roll, "comeline")

            # The dark side wins
            for pos in range(len(self.board["dontpassline"])):
                if self.board["dontpassline"][pos] is not None and self.board["dontpassline"][pos] > 0:
                    self.pay_even_money(roll, "dontpassline")
            self.pay_darkside_odds()
            # The dark side wins on all the dont come bets    

            # Don't come loses
            for pos in range(len(self.board["dontcomeline"])):
                if self.board["dontcomeline"][pos] is not None and self.board["dontcomeline"][pos] > 0:
                    self.board["dontcomeline"][pos] = 0
                    self.players[pos].player_board["dontcomeline"] = 0

        elif button != 'off' and roll == 11:
            # Pay the comeline only
            for pos in range(len(self.board["comeline"])):
                if self.board["comeline"][pos] is not None and self.board["comeline"][pos] > 0:
                    self.pay_even_money(roll, "comeline")

            # Don't come loses
            for pos in range(len(self.board["dontcomeline"])):
                if self.board["dontcomeline"][pos] is not None and self.board["dontcomeline"][pos] > 0:
                    self.board["dontcomeline"][pos] = 0
                    self.players[pos].player_board["dontcomeline"] = 0        
        
        elif button != 'off' and roll != button and roll in [4, 5, 6, 8, 9, 10]:
            # Pay the place/come
            self.pay_place(roll)
            self.pay_odds(roll)
            # Now deal with the come line bet moving.  Player strategy will have to add odds
            for pos in range(len(self.board["comeline"])):
                if self.board["comeline"][pos] is not None and self.board["comeline"][pos] > 0:
                    self.board[f"{roll}"]["come"][pos] = self.board["comeline"][pos]
                    self.board["comeline"][pos] = 0
                    self.players[pos].player_board[f"{roll}"]["come"] = self.players[pos].player_board["comeline"]
                    self.players[pos].player_board["comeline"] = 0

            # Don't come bets lose on the number
            for pos in range(len(self.board[f"{roll}"]["dontcome"])):
                if self.board[f"{roll}"]["dontcome"][pos] is not None and self.board[f"{roll}"]["dontcome"][pos] > 0:
                    self.board[f"{roll}"]["dontcome"][pos] = 0
                    self.players[pos].player_board[f"{roll}"]["dontcome"] = 0
                if self.board[f"{roll}"]["dontcomeodds"][pos] is not None and self.board[f"{roll}"]["dontcomeodds"][pos] > 0:
                    self.board[f"{roll}"]["dontcomeodds"][pos] = 0
                    self.players[pos].player_board[f"{roll}"]["dontcomeodds"] = 0
            # Don't come bets move to the number
            for pos in range(len(self.board["dontcomeline"])):
                if self.board["dontcomeline"][pos] is not None and self.board["dontcomeline"][pos] > 0:
                    self.board[f"{roll}"]["dontcome"][pos] = self.board["dontcomeline"][pos]
                    self.board["dontcomeline"][pos] = 0
                    self.players[pos].player_board[f"{roll}"]["dontcome"] = self.players[pos].player_board["dontcomeline"]
                    self.players[pos].player_board["dontcomeline"] = 0
        
        elif button != 'off' and roll == button:
            # Pay the pass line and odds
            for pos in range(len(self.board["passline"])):
                if self.board["passline"][pos] is not None and self.board["passline"][pos] > 0:
                    self.pay_even_money(roll, "passline")
            self.pay_odds(button, is_come=False)

            # Move the come line bets to the number
            for pos in range(len(self.board["comeline"])):
                if self.board["comeline"][pos] is not None and self.board["comeline"][pos] > 0:
                    self.board[f"{roll}"]["come"][pos] = self.board["comeline"][pos]
                    self.board["comeline"][pos] = 0
                    self.players[pos].player_board[f"{roll}"]["come"] = self.players[pos].player_board["comeline"]
                    self.players[pos].player_board["comeline"] = 0

            # Don't pass loses
            for pos in range(len(self.board["dontpassline"])):
                if self.board["dontpassline"][pos] is not None and self.board["dontpassline"][pos] > 0:
                    self.board["dontpassline"][pos] = 0
                    self.players[pos].player_board["dontpassline"] = 0
            for pos in range(len(self.board["dontpassodds"])):
                if self.board["dontpassodds"][pos] is not None and self.board["dontpassodds"][pos] > 0:
                    self.board["dontpassodds"][pos] = 0
                    self.players[pos].player_board["dontpassodds"] = 0

            # Reset the button
            self.button = 'off'

    def play_toss(self):
        """
            Play one toss of the dice
        """
        # We want the initial bet to be placed when the player first joins the game.  That is why we bet last.
        rolldict = self.roll_dice()
        self.settle_bets(rolldict)
        if self.button == 'off' or rolldict['total'] != 7:
            for player in self.players:
                print(f"Betting for player {player.id}")  # --- IGNORE ---
                player.place_bets()

        return rolldict