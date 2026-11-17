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
