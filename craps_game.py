"""
Craps game engine - handles dice rolling and game state management.
"""
import random
from typing import Tuple, Optional


class CrapsGame:
    """Simulates a game of craps."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the craps game.
        
        Args:
            seed: Optional random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
        self.point = None
        self.is_come_out = True
        
    def roll_dice(self) -> Tuple[int, int, int]:
        """Roll two dice and return the results.
        
        Returns:
            Tuple of (die1, die2, total)
        """
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        total = die1 + die2
        return die1, die2, total
    
    def play_round(self) -> dict:
        """Play one round of craps (may involve multiple rolls).
        
        Returns:
            Dictionary containing round results with keys:
            - rolls: list of (die1, die2, total) tuples
            - outcome: 'win' or 'lose' for pass line bet
            - point: the point that was established (if any)
        """
        rolls = []
        
        # Come-out roll
        die1, die2, total = self.roll_dice()
        rolls.append((die1, die2, total))
        
        # Natural win on come-out
        if total in [7, 11]:
            return {
                'rolls': rolls,
                'outcome': 'win',
                'point': None
            }
        
        # Craps on come-out
        if total in [2, 3, 12]:
            return {
                'rolls': rolls,
                'outcome': 'lose',
                'point': None
            }
        
        # Point established
        point = total
        
        # Roll until point or seven
        while True:
            die1, die2, total = self.roll_dice()
            rolls.append((die1, die2, total))
            
            if total == point:
                return {
                    'rolls': rolls,
                    'outcome': 'win',
                    'point': point
                }
            
            if total == 7:
                return {
                    'rolls': rolls,
                    'outcome': 'lose',
                    'point': point
                }
