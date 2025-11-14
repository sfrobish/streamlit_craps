"""
Betting strategies for craps simulation.
"""
from abc import ABC, abstractmethod
from typing import Dict


class BettingStrategy(ABC):
    """Base class for betting strategies."""
    
    def __init__(self, base_bet: float = 5.0):
        """Initialize the betting strategy.
        
        Args:
            base_bet: The base bet amount
        """
        self.base_bet = base_bet
        self.name = "Base Strategy"
    
    @abstractmethod
    def calculate_result(self, round_result: dict) -> float:
        """Calculate the net result (win/loss) for a round.
        
        Args:
            round_result: Dictionary with round information
            
        Returns:
            Net win/loss amount (positive for win, negative for loss)
        """
        pass


class PassLineBet(BettingStrategy):
    """Pass line betting strategy - bet with the shooter."""
    
    def __init__(self, base_bet: float = 5.0):
        super().__init__(base_bet)
        self.name = "Pass Line"
    
    def calculate_result(self, round_result: dict) -> float:
        """Calculate result for pass line bet.
        
        Pass line wins on 7 or 11 on come-out, loses on 2, 3, 12.
        After point is established, wins if point is rolled before 7.
        """
        if round_result['outcome'] == 'win':
            return self.base_bet
        else:
            return -self.base_bet


class DontPassBet(BettingStrategy):
    """Don't pass betting strategy - bet against the shooter."""
    
    def __init__(self, base_bet: float = 5.0):
        super().__init__(base_bet)
        self.name = "Don't Pass"
    
    def calculate_result(self, round_result: dict) -> float:
        """Calculate result for don't pass bet.
        
        Don't pass loses on 7 or 11 on come-out, wins on 2 or 3 (pushes on 12).
        After point is established, wins if 7 is rolled before point.
        """
        rolls = round_result['rolls']
        first_roll_total = rolls[0][2]
        
        # Come-out roll outcomes
        if len(rolls) == 1:
            if first_roll_total in [7, 11]:
                return -self.base_bet
            elif first_roll_total in [2, 3]:
                return self.base_bet
            elif first_roll_total == 12:
                return 0.0  # Push
        
        # Point play (opposite of pass line)
        if round_result['outcome'] == 'lose':
            return self.base_bet
        else:
            return -self.base_bet


class PassLineWithOdds(BettingStrategy):
    """Pass line with odds bet strategy."""
    
    def __init__(self, base_bet: float = 5.0, odds_multiplier: float = 2.0):
        """Initialize pass line with odds.
        
        Args:
            base_bet: The base pass line bet
            odds_multiplier: Multiple of base bet for odds (e.g., 2x odds)
        """
        super().__init__(base_bet)
        self.odds_multiplier = odds_multiplier
        self.name = f"Pass Line + {odds_multiplier}x Odds"
    
    def calculate_result(self, round_result: dict) -> float:
        """Calculate result for pass line with odds.
        
        Odds bet pays true odds: 2:1 for 4/10, 3:2 for 5/9, 6:5 for 6/8.
        """
        # Base pass line bet
        result = self.base_bet if round_result['outcome'] == 'win' else -self.base_bet
        
        # If point was established, calculate odds bet result
        if round_result['point'] is not None:
            odds_bet = self.base_bet * self.odds_multiplier
            point = round_result['point']
            
            if round_result['outcome'] == 'win':
                # True odds payouts
                if point in [4, 10]:
                    odds_payout = odds_bet * 2  # 2:1
                elif point in [5, 9]:
                    odds_payout = odds_bet * 3 / 2  # 3:2
                else:  # 6 or 8
                    odds_payout = odds_bet * 6 / 5  # 6:5
                result += odds_payout
            else:
                # Lost the odds bet
                result -= odds_bet
        
        return result


class PlaceBetSix(BettingStrategy):
    """Place bet on 6 strategy."""
    
    def __init__(self, base_bet: float = 6.0):
        """Initialize place bet on 6.
        
        Args:
            base_bet: The bet amount (should be multiple of 6 for proper payouts)
        """
        super().__init__(base_bet)
        self.name = "Place 6"
    
    def calculate_result(self, round_result: dict) -> float:
        """Calculate result for place bet on 6.
        
        Place 6 pays 7:6. Wins if 6 is rolled, loses if 7 is rolled.
        """
        rolls = round_result['rolls']
        
        # Check all rolls after come-out
        for i, (die1, die2, total) in enumerate(rolls):
            if i == 0:
                continue  # Skip come-out roll
            
            if total == 6:
                return self.base_bet * 7 / 6  # 7:6 payout
            elif total == 7:
                return -self.base_bet
        
        # If we get here, neither 6 nor 7 was rolled (shouldn't happen)
        return 0.0
