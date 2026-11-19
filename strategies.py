NUMBERS = [4, 5, 6, 8, 9, 10]

strategy_registry = {}
def add_strategy(name):
    """Decorator to add a strategy to the registry."""
    def decorator(func):
        strategy_registry[name] = func
        return func
    return decorator


@add_strategy('Pass/Come 2x Place 6&8') 
def pass_come_2x_place_68(board, game, prevboard):
    
    passcomewager = game.tablemin
    passcomeodds = passcomewager * 2.0
    passcomeincr = passcomewager
    totalbet = 0
    button = game.button
    roll = game.roll
    if button == 'off':
        # Replace the pass bet
        if board["passline"] == 0:
            board["passline"] = passcomewager
            totalbet += passcomewager
        if roll in [4,5,6,8,9,10]:
            # If the button was just hit and we had a come bet, add odds to it
            if roll is not None and board[f"{roll}"]["come"] > 0:
                board[f"{roll}"]["comeodds"] = passcomeodds
                totalbet += passcomeodds
    else:
        # If we just established the point and have a pass bet, add odds to it
        if board["passline"] > 0 and board["passodds"] == 0:
            board["passodds"] = passcomeodds
            totalbet += passcomeodds
        board["comeline"] = passcomewager
        totalbet += passcomewager
        for x in [4, 5, 6, 8, 9, 10]:
            if x != button and board[f"{x}"]["place"] == 0 and board[f"{x}"]["come"] == 0:
                if x in [6, 8]:
                    board[f"{x}"]["place"] = game.tablemin * 6 / 5.0
                    totalbet += game.tablemin * 6 / 5.0
        # If we rolled a number that already has a come bet, increase the odds bet
        if roll in [4,5,6,8,9,10]:
            if board[f"{roll}"]["come"] > 0 and board[f"{roll}"]["comeodds"] == 0:
                board[f"{roll}"]["comeodds"] = passcomeodds
                totalbet += passcomeodds
            elif board[f"{roll}"]["come"] > 0 and board[f"{roll}"]["comeodds"] > 0:
                board[f"{roll}"]["comeodds"] += passcomeincr
                totalbet += passcomeincr

    return board, totalbet


@add_strategy('Pass/Come Press') 
def pass_come_press(board, game, prevboard):
    
    passcomewager = game.tablemin
    passcomeodds = passcomewager * 2.0
    passcomeincr = passcomewager
    totalbet = 0
    button = game.button
    roll = game.roll
    if button == 'off':
        # Replace the pass bet
        if board["passline"] == 0:
            board["passline"] = passcomewager
            totalbet += passcomewager
        if roll in [4,5,6,8,9,10]:
            # If the button was just hit and we had a come bet, add odds to it
            if roll is not None and board[f"{roll}"]["come"] > 0:
                board[f"{roll}"]["comeodds"] = passcomeodds
                totalbet += passcomeodds
    else:
        # If we just established the point and have a pass bet, add odds to it
        if board["passline"] > 0 and board["passodds"] == 0:
            board["passodds"] = passcomeodds
            totalbet += passcomeodds
        board["comeline"] = passcomewager
        totalbet += passcomewager
        for x in [4, 5, 6, 8, 9, 10]:
            if x != button and board[f"{x}"]["place"] == 0 and board[f"{x}"]["come"] == 0:
                if x in [6, 8]:
                    board[f"{x}"]["place"] = game.tablemin * 6 / 5.0
                    totalbet += game.tablemin * 6 / 5.0
        # If we rolled a number that already has a come bet, increase the odds bet
        if roll in [4,5,6,8,9,10]:
            if board[f"{roll}"]["come"] > 0 and prevboard[f"{roll}"]["comeodds"] == 0:
                board[f"{roll}"]["comeodds"] = passcomeodds
                totalbet += passcomeodds
            elif board[f"{roll}"]["come"] > 0 and prevboard[f"{roll}"]["comeodds"] > 0:
                board[f"{roll}"]["comeodds"] = prevboard[f"{roll}"]["comeodds"] + passcomeincr
                totalbet += passcomeincr

    return board, totalbet


@add_strategy('Dark Side 3')
def dark_side_3(board, game, prevboard):
    """ Place a don't pass and up to 2 don't come bets with odds behind each.  If a bet loses, play back up to 3 don't numbers."""

    totalbet = 0.0
    dontpasscomewager = game.tablemin
    dontcomeodds = dontpasscomewager * 6.0
    button = game.button
    roll = game.roll
    if button == 'off':
        # Replace the don't pass bet
        if board["dontpassline"] == 0:
            board["dontpassline"] = dontpasscomewager
            totalbet += dontpasscomewager
    else:
        if board["dontpassodds"] == 0:
            board["dontpassodds"] = dontcomeodds
            totalbet += dontcomeodds
        
        dontcount = 0
        for x in [4, 5, 6, 8, 9, 10]:
            if x != button and board[f"{x}"]["place"] == 0 and board[f"{x}"]["dontcome"] == 0:
                if x in [6, 8]:
                    board[f"{x}"]["place"] = game.tablemin * 6 / 5.0
                    totalbet += game.tablemin * 6 / 5.0
            if x != button and board[f"{x}"]["dontcome"] != 0:
                dontcount += 1

        if dontcount < 2:
            board["dontcomeline"] = dontpasscomewager
            totalbet += dontpasscomewager
            
        if roll != button and roll in [4,5,6,8,9,10] and board[f"{roll}"]["dontcome"] != 0:
            if board[f"{roll}"]["dontcomeodds"] == 0:
                board[f"{roll}"]["dontcomeodds"] = dontcomeodds
                totalbet += dontcomeodds

    return board, totalbet


@add_strategy("Don't Pass/Come Lay 1u")
def dont_lay_one_unit(board, game, prevboard):
    """Don't pass, plus a new don't come on every roll while the point is on.
    Every don't bet gets lay odds sized to win exactly one unit (table min).
    Odds stay working through the come-out."""
    unit = game.tablemin
    lay_to_win_one = {4: 2.0, 10: 2.0, 5: 1.5, 9: 1.5, 6: 1.2, 8: 1.2}  # units laid per unit won
    totalbet = 0.0
    button = game.button

    if button == 'off':
        if board["dontpassline"] == 0:
            board["dontpassline"] = unit
            totalbet += unit
    else:
        if board["dontpassline"] > 0 and board["dontpassodds"] == 0:
            board["dontpassodds"] = unit * lay_to_win_one[button]
            totalbet += board["dontpassodds"]
        if board["dontcomeline"] == 0:
            board["dontcomeline"] = unit
            totalbet += unit

    for x in [4, 5, 6, 8, 9, 10]:
        if board[f"{x}"]["dontcome"] > 0 and board[f"{x}"]["dontcomeodds"] == 0:
            board[f"{x}"]["dontcomeodds"] = unit * lay_to_win_one[x]
            totalbet += board[f"{x}"]["dontcomeodds"]

    return board, totalbet


def _line_plus_two(board, game, line, line_odds, come_line, come, come_odds, odds):
    """Keep a line bet up plus up to 2 come bets, with odds(num, flat) behind each (0 = no odds).
    Shared by the light side (pass/come) and its dark-side mirror (don't pass/don't come); with the
    same bet counts the two place flats on exactly the same rolls."""
    unit = game.tablemin
    before = board[line] + board[line_odds] + board[come_line] + sum(board[str(n)][come] + board[str(n)][come_odds] for n in NUMBERS)
    point = game.button
    if point == 'off':
        if board[line] == 0:
            board[line] = unit
    else:
        if board[line] > 0 and board[line_odds] == 0:
            board[line_odds] = odds(point, board[line])
        working = sum(board[str(n)][come] > 0 for n in NUMBERS)
        if board[come_line] == 0 and working < 2:
            board[come_line] = unit
    for n in NUMBERS:
        spot = board[str(n)]
        if spot[come] > 0 and spot[come_odds] == 0:
            spot[come_odds] = odds(n, spot[come])
    after = board[line] + board[line_odds] + board[come_line] + sum(board[str(n)][come] + board[str(n)][come_odds] for n in NUMBERS)
    return board, after - before


@add_strategy('Pass + 2 Come, Max Odds')
def pass_two_come_max_odds(board, game, prevboard):
    """Pass line plus up to 2 come bets, max odds (per the table's maxodds) behind each. Nothing else."""
    return _line_plus_two(board, game, "passline", "passodds", "comeline", "come", "comeodds", game.max_odds)


@add_strategy("Don't Pass + 2 Don't Come, Max Lay")
def dont_pass_two_dont_come_max_lay(board, game, prevboard):
    """Mirror of 'Pass + 2 Come, Max Odds': don't pass plus up to 2 don't come bets, max lay behind each.

    Paired with the light version at the same table it is not a perfect hedge: besides the 12
    (bar push), come odds are off on the come-out while lay odds stay working, so a come-out
    roll that hits a come number or a 7 moves the pair (standard rules, kept on purpose)."""
    return _line_plus_two(board, game, "dontpassline", "dontpassodds", "dontcomeline", "dontcome", "dontcomeodds", game.max_lay)


NO_ODDS = lambda num, flat: 0.0


@add_strategy('Pass + 2 Come, No Odds')
def pass_two_come_no_odds(board, game, prevboard):
    """Pass line plus up to 2 come bets, flat only."""
    return _line_plus_two(board, game, "passline", "passodds", "comeline", "come", "comeodds", NO_ODDS)


@add_strategy('Pass + 2 Come, 1x Odds')
def pass_two_come_1x_odds(board, game, prevboard):
    """Pass line plus up to 2 come bets with 1x odds. Pair with a press profile to grow the odds."""
    return _line_plus_two(board, game, "passline", "passodds", "comeline", "come", "comeodds",
                          lambda num, flat: min(flat, game.max_odds(num, flat)))


@add_strategy("Don't Pass + 2 Don't Come, Flat")
def dont_pass_two_dont_come_flat(board, game, prevboard):
    """Mirror of the 'Pass + 2 Come' family with no lay odds: the flat hedge for the light side."""
    return _line_plus_two(board, game, "dontpassline", "dontpassodds", "dontcomeline", "dontcome", "dontcomeodds", NO_ODDS)


# Issue #4 hedge ladder: one strategy per rung, both sides on one board, flats mirrored.
# Each odds(game) returns the odds(num, flat) callable _line_plus_two expects.
ONE_X = lambda game: lambda num, flat: min(flat, game.max_odds(num, flat))
MAX_ODDS = lambda game: game.max_odds
MAX_LAY = lambda game: game.max_lay
NONE = lambda game: NO_ODDS


def _hedge(light_odds, dark_odds):
    def strategy(board, game, prevboard):
        board, light = _line_plus_two(board, game, "passline", "passodds", "comeline", "come", "comeodds", light_odds(game))
        board, dark = _line_plus_two(board, game, "dontpassline", "dontpassodds", "dontcomeline", "dontcome", "dontcomeodds", dark_odds(game))
        return board, light + dark
    return strategy


HEDGE_FLAT, HEDGE_1X, HEDGE_MAX = "Hedge 1: Flat Mirror", "Hedge 2: Light 1x Odds", "Hedge 3: Light Max Odds"
add_strategy(HEDGE_FLAT)(_hedge(NONE, NONE))
add_strategy(HEDGE_1X)(_hedge(ONE_X, NONE))
add_strategy(HEDGE_MAX)(_hedge(MAX_ODDS, NONE))
add_strategy("Hedge 7: Max Odds Both Sides")(_hedge(MAX_ODDS, MAX_LAY))

# Rungs 4-6 press, which lives in the player as a profile; CrapsPlayer picks these up by name.
# Only the light side presses; dark flats stay 1 unit on purpose (per #4 discussion).
PRESETS = {
    "Hedge 4: Light 1x Odds, Press 1u": {"base_strategy": HEDGE_1X, "odds_press_units": 1},
    "Hedge 5: Light 1x Odds, Press 2u": {"base_strategy": HEDGE_1X, "odds_press_units": 2},
    "Hedge 6: Light Max Odds, Press Come Flats 1u": {"base_strategy": HEDGE_MAX, "flat_press_units": 1},
}
for _name, _p in PRESETS.items():
    add_strategy(_name)(strategy_registry[_p["base_strategy"]])
