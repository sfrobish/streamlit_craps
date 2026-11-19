"""Betting strategies: how the line, come and odds bets are played. Nothing else.

Side bets (place 6 & 8, field, C&E) are per-seat options applied by the player on top of
any strategy; pressing comes from a profile (see PRESETS and pages/edit_strategies.py).
"""
NUMBERS = [4, 5, 6, 8, 9, 10]

LIGHT = ("passline", "passodds", "comeline", "come", "comeodds")
DARK = ("dontpassline", "dontpassodds", "dontcomeline", "dontcome", "dontcomeodds")
EVERY_ROLL = float("inf")  # max come bets: a new one on every roll while the point is on
UNITS_LAID_PER_UNIT_WON = {4: 2.0, 10: 2.0, 5: 1.5, 9: 1.5, 6: 1.2, 8: 1.2}

# Odds sizers: (game, number, flat bet) -> odds bet. The house caps anything over max odds.
FLAT = lambda game, num, flat: 0.0
MAX_ODDS = lambda game, num, flat: game.max_odds(num, flat)
MAX_LAY = lambda game, num, flat: game.max_lay(num, flat)
LAY_1X = lambda game, num, flat: min(flat * UNITS_LAID_PER_UNIT_WON[num], game.max_lay(num, flat))


def odds_x(k):
    return lambda game, num, flat: min(flat * k, game.max_odds(num, flat))


def line_and_come(board, game, side, max_come, odds):
    """Keep a line bet up plus up to max_come come bets, with odds(game, num, flat) behind each.
    side is LIGHT (pass/come) or DARK (don't pass/don't come); with the same max_come the two
    place flats on exactly the same rolls."""
    line, line_odds, come_line, come, come_odds = side
    point = game.button
    if point == 'off':
        if board[line] == 0:
            board[line] = game.tablemin
    else:
        if board[line] > 0 and board[line_odds] == 0:
            board[line_odds] = odds(game, point, board[line])
        working = sum(board[str(n)][come] > 0 for n in NUMBERS)
        if board[come_line] == 0 and working < max_come:
            board[come_line] = game.tablemin
    for n in NUMBERS:
        spot = board[str(n)]
        if spot[come] > 0 and spot[come_odds] == 0:
            spot[come_odds] = odds(game, n, spot[come])
    return board


# Name convention: <Bets>, <Odds>[, <Press>]
STRATEGIES = {
    "Pass + 2 Come, Flat": (LIGHT, 2, FLAT),
    "Pass + 2 Come, 1x Odds": (LIGHT, 2, odds_x(1)),
    "Pass + 2 Come, Max Odds": (LIGHT, 2, MAX_ODDS),
    "Pass + Come Every Roll, 2x Odds": (LIGHT, EVERY_ROLL, odds_x(2)),
    "Don't Pass + 2 Don't Come, Flat": (DARK, 2, FLAT),
    "Don't Pass + 2 Don't Come, Max Lay": (DARK, 2, MAX_LAY),
    "Don't Pass + Don't Come Every Roll, 1x Lay": (DARK, EVERY_ROLL, LAY_1X),
}

# Press variants. Pressing lives in the player as a profile; CrapsPlayer picks these up by name.
PRESETS = {
    "Pass + 2 Come, 1x Odds, Press Odds 1u": {"base_strategy": "Pass + 2 Come, 1x Odds", "odds_press_units": 1},
    "Pass + 2 Come, 1x Odds, Press Odds 2u": {"base_strategy": "Pass + 2 Come, 1x Odds", "odds_press_units": 2},
    "Pass + 2 Come, Max Odds, Press Flats 1u": {"base_strategy": "Pass + 2 Come, Max Odds", "flat_press_units": 1},
    "Pass + Come Every Roll, 2x Odds, Press Odds 1u": {"base_strategy": "Pass + Come Every Roll, 2x Odds", "odds_press_units": 1},
}

# strategy name -> fn(board, game) -> board
strategy_registry = {name: (lambda board, game, spec=spec: line_and_come(board, game, *spec))
                     for name, spec in STRATEGIES.items()}
strategy_registry.update({name: strategy_registry[p["base_strategy"]] for name, p in PRESETS.items()})

# Old names, so saved profile files still load. Place 6 & 8 is now a seat option.
RENAMED = {
    "Pass/Come 2x Place 6&8": "Pass + Come Every Roll, 2x Odds",
    "Pass/Come Press": "Pass + Come Every Roll, 2x Odds",
    "Dark Side 3": "Don't Pass + 2 Don't Come, Max Lay",  # its 6u lay is max lay at 3-4-5x
    "Don't Pass/Come Lay 1u": "Don't Pass + Don't Come Every Roll, 1x Lay",
    "Pass + 2 Come, No Odds": "Pass + 2 Come, Flat",
}
