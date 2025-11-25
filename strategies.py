strategy_registry = {}
def add_strategy(name):
    """Decorator to add a strategy to the registry."""
    def decorator(func):
        strategy_registry[name] = func
        return func
    return decorator


@add_strategy('Pass/Come 2x Place 6&8') 
def pass_come_2x_place_68(board, game):
    
    print("Calling pass_come_2x_place_68 strategy")
    passcomewager = game.tablemin
    passcomeodds = passcomewager * 2
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
                    board[f"{x}"]["place"] = int(game.tablemin * 6 / 5 )
                    totalbet += int(game.tablemin * 6 / 5 )
        # If we rolled a number that already has a come bet, increase the odds bet
        if roll in [4,5,6,8,9,10]:
            if board[f"{roll}"]["come"] > 0 and board[f"{roll}"]["comeodds"] == 0:
                board[f"{roll}"]["comeodds"] = passcomeodds
                print(f"Adding come odds bet of {passcomeodds} on {roll}")
                totalbet += passcomeodds
            elif board[f"{roll}"]["come"] > 0 and board[f"{roll}"]["comeodds"] > 0:
                print(f"Increasing come odds bet by {passcomeincr} on {roll}")
                board[f"{roll}"]["comeodds"] += passcomeincr
                totalbet += passcomeincr

    return board, totalbet


@add_strategy('Pass/Come Press') 
def pass_come_press(board, game):
    
    passcomewager = game.tablemin
    passcomeodds = passcomewager * 2
    passcomeincr = passcomewager
    roll = game.roll
    button = game.button
    totalbet = 0
    if button == 'off':
        # Replace the pass bet
        if board["passline"] == 0:
            board["passline"] = passcomewager
            totalbet += passcomewager
        if roll in [4,5,6,8,9,10]:
            # If the button was just hit and we had a come bet, add odds to it
            if board[f"{roll}"]["come"] > 0:
                board[f"{roll}"]["comeodds"] = passcomeodds
                totalbet += passcomeodds
    else:
        if board["passoddsbet"] == 0:
            board["passoddsbet"] = passcomeodds
            totalbet += passcomeodds
        board["comeline"] = passcomewager
        totalbet += passcomewager
        for x in [4, 5, 6, 8, 9, 10]:
            if x != button and board["placebet"][x-1] == 0 and board["comebet"][x-1] == 0:
                if x in [6, 8]:
                    board["placebet"][x-1] = int(game.tablemin * 6 / 5 )
                    totalbet += int(game.tablemin * 6 / 5 )
            # if x != button and board["comebet"][x-1] != 0:
            #     board["comeoddsbet"][x-1] = passcomeodds
        # If we rolled a number that already has a come bet, increase the odds bet
        if roll != button and board["comebet"][roll-1] != 0:
            if board["comeodds"][roll-1] == 0:
                board["comeodds"][roll-1] = passcomeodds
                totalbet += passcomeodds
            else:
                board["comeodds"][roll-1] += passcomeincr
                totalbet += passcomeincr

    return board, totalbet

@add_strategy('Dark Side 3')
def dark_side_3(board, game):
    """ Place a don't pass and up to 2 don't come bets with odds behind each.  If a bet loses, play back up to 3 don't numbers."""

    totalbet = 0
    dontpasscomewager = game.tablemin
    dontcomeodds = dontpasscomewager * 6
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
        board["dontcomeline"] = dontpasscomewager
        totalbet += dontpasscomewager
        for x in [4, 5, 6, 8, 9, 10]:
            if x != button and board["placebet"][x-1] == 0 and board["dontcomebet"][x-1] == 0:
                board["placebet"][x-1] = int(game.tablemin * 6 / 5 )
                totalbet += int(game.tablemin * 6 / 5 )
        if roll != button and board["dontcomeline"][roll-1] != 0:
            if board["dontcomeodds"][roll-1] == 0:
                board["dontcomeodds"][roll-1] = dontcomeodds
                totalbet += dontcomeodds
            else:
                board["dontcomeodds"][roll-1] += dontpasscomewager * 6
                totalbet += dontpasscomewager * 6

    return board, totalbet
