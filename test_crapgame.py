"""Payout / board tests for CrapGame against standard craps rules.

Run: .venv/bin/python -m unittest test_crapgame -v

Payout convention in CrapGame: a winning bet returns stake + winnings,
a push returns the stake, a loss returns nothing. Every settled bet is
cleared to 0 on both the house board and the player's board.
"""
import random
import unittest

from crapgame import CrapGame, SEATS
from player import CrapsPlayer
from stats import get_statistics
from strategies import strategy_registry

NUMBERS = [4, 5, 6, 8, 9, 10]
PASS_ODDS = {4: 2, 10: 2, 5: 3 / 2, 9: 3 / 2, 6: 6 / 5, 8: 6 / 5}     # true odds
LAY_ODDS = {4: 1 / 2, 10: 1 / 2, 5: 2 / 3, 9: 2 / 3, 6: 5 / 6, 8: 5 / 6}
PLACE = {4: 9 / 5, 10: 9 / 5, 5: 7 / 5, 9: 7 / 5, 6: 7 / 6, 8: 7 / 6}


class StubPlayer:
    """Minimal stand-in for CrapsPlayer: just a board and a payout log."""

    def __init__(self, game):
        self.player_board = {k: (dict.fromkeys(v, 0.0) if isinstance(v, dict) else 0.0)
                             for k, v in game.board.items()}
        self.payouts = {}

    def take_payout(self, bet, amount):
        self.payouts[bet] = self.payouts.get(bet, 0) + amount

    @property
    def total(self):
        return sum(self.payouts.values())


class CrapsTest(unittest.TestCase):

    def setUp(self):
        self.g = CrapGame()
        self.p = StubPlayer(self.g)
        self.g.add_player(self.p)

    # helpers -----------------------------------------------------------
    def bet(self, key, amount, num=None):
        if num is None:
            self.g.board[key][0] = float(amount)
            self.p.player_board[key] = float(amount)
        else:
            self.g.board[str(num)][key][0] = float(amount)
            self.p.player_board[str(num)][key] = float(amount)

    def on_board(self, key, num=None):
        house = self.g.board[key][0] if num is None else self.g.board[str(num)][key][0]
        player = self.p.player_board[key] if num is None else self.p.player_board[str(num)][key]
        return house or 0, player or 0

    def assertCleared(self, key, num=None):
        self.assertEqual(self.on_board(key, num), (0, 0), f"{key} {num} should be cleared")

    def roll(self, total, point=None):
        if point is not None:
            self.g.button = point
        self.g.settle_bets({"die1": None, "die2": None, "total": total})


class TestComeOut(CrapsTest):

    def test_natural_pays_pass_loses_dontpass(self):
        for total in (7, 11):
            with self.subTest(total=total):
                self.setUp()
                self.bet("passline", 10)
                self.bet("dontpassline", 10)
                self.roll(total)
                self.assertEqual(self.p.total, 20)
                self.assertCleared("passline")
                self.assertCleared("dontpassline")
                self.assertEqual(self.g.button, "off")

    def test_craps_2_3_loses_pass_pays_dontpass(self):
        for total in (2, 3):
            with self.subTest(total=total):
                self.setUp()
                self.bet("passline", 10)
                self.bet("dontpassline", 10)
                self.roll(total)
                self.assertEqual(self.p.total, 20)
                self.assertCleared("passline")
                self.assertCleared("dontpassline")

    def test_craps_12_is_bar_push_for_dontpass(self):
        self.bet("passline", 10)
        self.bet("dontpassline", 10)
        self.roll(12)
        self.assertEqual(self.p.total, 10)   # dont pass stake returned only
        self.assertCleared("passline")

    def test_point_number_sets_button_bets_stay(self):
        for n in NUMBERS:
            with self.subTest(point=n):
                self.setUp()
                self.bet("passline", 10)
                self.bet("dontpassline", 10)
                self.roll(n)
                self.assertEqual(self.g.button, n)
                self.assertEqual(self.p.total, 0)
                self.assertEqual(self.on_board("passline"), (10, 10))
                self.assertEqual(self.on_board("dontpassline"), (10, 10))

    def test_place_bets_off_on_comeout(self):
        self.bet("place", 6, num=6)
        self.roll(6)
        self.assertEqual(self.p.total, 0)
        self.assertEqual(self.on_board("place", 6), (6, 6))
        self.setUp()
        self.bet("place", 6, num=6)
        self.roll(7)
        self.assertEqual(self.on_board("place", 6), (6, 6))

    def test_comeout_7_come_bet_loses_come_odds_returned(self):
        # Come odds are "off" on the come-out by default: flat loses, odds returned.
        self.bet("come", 10, num=5)
        self.bet("comeodds", 20, num=5)
        self.roll(7)
        self.assertEqual(self.p.total, 20)
        self.assertCleared("come", 5)
        self.assertCleared("comeodds", 5)

    def test_comeout_hits_come_number_flat_wins_odds_returned(self):
        self.bet("come", 10, num=5)
        self.bet("comeodds", 20, num=5)
        self.roll(5)
        self.assertEqual(self.p.total, 20 + 20)   # flat 1:1, odds returned (off)
        self.assertCleared("come", 5)
        self.assertCleared("comeodds", 5)

    def test_comeout_7_dontcome_on_number_wins(self):
        self.bet("dontcome", 10, num=8)
        self.bet("dontcomeodds", 12, num=8)
        self.roll(7)
        self.assertEqual(self.p.total, 20 + 12 + 10)   # flat 1:1, lay 5:6 on 8
        self.assertCleared("dontcome", 8)

    def test_comeout_number_dontcome_loses_with_odds(self):
        self.bet("dontcome", 10, num=8)
        self.bet("dontcomeodds", 12, num=8)
        self.roll(8)
        self.assertEqual(self.p.total, 0)
        self.assertCleared("dontcome", 8)
        self.assertCleared("dontcomeodds", 8)


class TestPointOn(CrapsTest):

    def test_point_made_pays_pass_and_true_odds(self):
        for n in NUMBERS:
            with self.subTest(point=n):
                self.setUp()
                self.bet("passline", 10)
                self.bet("passodds", 30)
                self.bet("dontpassline", 10)
                self.bet("dontpassodds", 30)
                self.roll(n, point=n)
                self.assertAlmostEqual(self.p.total, 20 + 30 + 30 * PASS_ODDS[n])
                for k in ("passline", "passodds", "dontpassline", "dontpassodds"):
                    self.assertCleared(k)
                self.assertEqual(self.g.button, "off")

    def test_seven_out_front_side_loses(self):
        self.bet("passline", 10)
        self.bet("passodds", 30)
        for n in NUMBERS:
            self.bet("place", 6, num=n)
            self.bet("come", 10, num=n)
            self.bet("comeodds", 20, num=n)
        self.roll(7, point=4)
        self.assertEqual(self.p.total, 0)
        self.assertCleared("passline")
        self.assertCleared("passodds")
        for n in NUMBERS:
            for k in ("place", "come", "comeodds"):
                self.assertCleared(k, n)

    def test_seven_out_resets_button(self):
        self.roll(7, point=6)
        self.assertEqual(self.g.button, "off")

    def test_seven_out_pays_dontpass_and_lay_odds_for_point(self):
        for n in NUMBERS:
            with self.subTest(point=n):
                self.setUp()
                self.bet("dontpassline", 10)
                self.bet("dontpassodds", 30)
                self.roll(7, point=n)
                self.assertAlmostEqual(self.p.total, 20 + 30 + 30 * LAY_ODDS[n])
                self.assertCleared("dontpassline")
                self.assertCleared("dontpassodds")

    def test_seven_out_pays_dontcome_flat_and_odds(self):
        for n in NUMBERS:
            with self.subTest(num=n):
                self.setUp()
                self.bet("dontcome", 10, num=n)
                self.bet("dontcomeodds", 30, num=n)
                self.roll(7, point=4 if n != 4 else 10)
                self.assertAlmostEqual(self.p.total, 20 + 30 + 30 * LAY_ODDS[n])
                self.assertCleared("dontcome", n)
                self.assertCleared("dontcomeodds", n)

    def test_seven_pays_comeline_loses_dontcomeline(self):
        self.bet("comeline", 10)
        self.bet("dontcomeline", 10)
        self.roll(7, point=6)
        self.assertEqual(self.p.total, 20)
        self.assertCleared("comeline")
        self.assertCleared("dontcomeline")

    def test_eleven_pays_comeline_loses_dontcomeline(self):
        self.bet("passline", 10)
        self.bet("comeline", 10)
        self.bet("dontcomeline", 10)
        self.roll(11, point=6)
        self.assertEqual(self.p.total, 20)
        self.assertCleared("comeline")
        self.assertCleared("dontcomeline")
        self.assertEqual(self.on_board("passline"), (10, 10))
        self.assertEqual(self.g.button, 6)

    def test_craps_2_3_loses_comeline_pays_dontcomeline(self):
        for total in (2, 3):
            with self.subTest(total=total):
                self.setUp()
                self.bet("passline", 10)
                self.bet("comeline", 10)
                self.bet("dontcomeline", 10)
                self.roll(total, point=6)
                self.assertEqual(self.p.total, 20)
                self.assertCleared("comeline")
                self.assertCleared("dontcomeline")
                self.assertEqual(self.on_board("passline"), (10, 10))

    def test_craps_12_loses_comeline_pushes_dontcomeline(self):
        self.bet("comeline", 10)
        self.bet("dontcomeline", 10)
        self.roll(12, point=6)
        self.assertEqual(self.p.total, 10)
        self.assertCleared("comeline")
        self.assertCleared("dontcomeline")

    def test_place_bet_payouts(self):
        for n in NUMBERS:
            with self.subTest(num=n):
                self.setUp()
                stake = 6 if n in (6, 8) else 5
                self.bet("place", stake, num=n)
                self.roll(n, point=4 if n != 4 else 10)
                self.assertAlmostEqual(self.p.total, stake + stake * PLACE[n])
                self.assertCleared("place", n)

    def test_place_bet_on_point_number_pays_when_point_made(self):
        self.bet("place", 6, num=6)
        self.roll(6, point=6)
        self.assertAlmostEqual(self.p.total, 6 + 7)

    def test_come_bet_on_number_pays_flat_and_true_odds(self):
        for n in NUMBERS:
            with self.subTest(num=n):
                self.setUp()
                self.bet("come", 10, num=n)
                self.bet("comeodds", 30, num=n)
                self.roll(n, point=4 if n != 4 else 10)
                self.assertAlmostEqual(self.p.total, 20 + 30 + 30 * PASS_ODDS[n])
                self.assertCleared("come", n)
                self.assertCleared("comeodds", n)

    def test_come_bet_on_point_number_pays_when_point_made(self):
        self.bet("come", 10, num=6)
        self.bet("comeodds", 20, num=6)
        self.roll(6, point=6)
        self.assertAlmostEqual(self.p.total, 20 + 20 + 24)

    def test_comeline_and_dontcomeline_travel_to_number(self):
        for n in NUMBERS:
            with self.subTest(num=n):
                self.setUp()
                self.bet("comeline", 10)
                self.bet("dontcomeline", 15)
                self.roll(n, point=4 if n != 4 else 10)
                self.assertEqual(self.p.total, 0)
                self.assertCleared("comeline")
                self.assertCleared("dontcomeline")
                self.assertEqual(self.on_board("come", n), (10, 10))
                self.assertEqual(self.on_board("dontcome", n), (15, 15))

    def test_comeline_travels_when_point_made(self):
        self.bet("comeline", 10)
        self.roll(9, point=9)
        self.assertCleared("comeline")
        self.assertEqual(self.on_board("come", 9), (10, 10))

    def test_dontcome_on_number_loses_when_number_rolls(self):
        self.bet("dontcome", 10, num=5)
        self.bet("dontcomeodds", 30, num=5)
        self.roll(5, point=8)
        self.assertEqual(self.p.total, 0)
        self.assertCleared("dontcome", 5)
        self.assertCleared("dontcomeodds", 5)

    def test_dontcome_on_point_number_loses_when_point_made(self):
        self.bet("dontcome", 10, num=5)
        self.bet("dontcomeodds", 30, num=5)
        self.roll(5, point=5)
        self.assertEqual(self.p.total, 0)
        self.assertCleared("dontcome", 5)
        self.assertCleared("dontcomeodds", 5)

    def test_unrelated_number_leaves_line_bets(self):
        self.bet("passline", 10)
        self.bet("dontpassline", 10)
        self.bet("place", 5, num=5)
        self.roll(8, point=4)
        self.assertEqual(self.p.total, 0)
        self.assertEqual(self.on_board("passline"), (10, 10))
        self.assertEqual(self.on_board("dontpassline"), (10, 10))
        self.assertEqual(self.on_board("place", 5), (5, 5))
        self.assertEqual(self.g.button, 4)


class TestBoardMechanics(CrapsTest):

    def test_take_bets_maps_player_id_1_to_seat_0(self):
        self.p.player_board["passline"] = 10.0
        self.p.player_board["6"]["place"] = 6.0
        self.g.take_bets(self.p.player_board, playerid=1)
        self.assertEqual(self.g.board["passline"][0], 10.0)
        self.assertEqual(self.g.board["6"]["place"][0], 6.0)

    def test_payouts_go_to_correct_seat(self):
        p2 = StubPlayer(self.g)
        self.g.add_player(p2)
        self.g.board["passline"][1] = 25.0
        self.bet("dontpassline", 10)
        self.roll(7)
        self.assertEqual(p2.total, 50)
        self.assertEqual(self.p.total, 0)

    def test_roll_dice_fixed(self):
        self.assertEqual(self.g.roll_dice(3, 4), {"die1": 3, "die2": 4, "total": 7})
        self.assertEqual(self.g.roll, 7)

    def test_roll_dice_random_in_range(self):
        for _ in range(200):
            r = self.g.roll_dice()
            self.assertTrue(1 <= r["die1"] <= 6 and 1 <= r["die2"] <= 6)
            self.assertEqual(r["total"], r["die1"] + r["die2"])

    def test_table_full(self):
        for _ in range(SEATS - 1):  # setUp already seated one
            self.g.add_player(StubPlayer(self.g))
        with self.assertRaises(ValueError):
            self.g.add_player(StubPlayer(self.g))

    def test_move_button(self):
        self.g.move_button(6)
        self.assertEqual(self.g.button, 6)
        self.g.move_button(8)
        self.assertEqual(self.g.button, 6)
        self.g.move_button(7)
        self.assertEqual(self.g.button, "off")


class TestSimulationBookkeeping(unittest.TestCase):
    """Run real strategies end to end and check the money balances."""

    def test_money_balances_for_every_strategy(self):
        random.seed(7)
        aggressive = {"base_strategy": "Pass/Come 2x Place 6&8", "odds_press_units": 1}
        seated = [(s, None) for s in strategy_registry] + [("aggressive", aggressive)]
        # Split players across as many tables as the seat limit needs.
        games, players = [], []
        for i, (name, profile) in enumerate(seated):
            if i % SEATS == 0:
                games.append(CrapGame())
            players.append(CrapsPlayer(i % SEATS + 1, games[-1], name, 1000, profile=profile))
        for _ in range(2000):
            for g in games:
                g.play_toss()
        for p in players:
            with self.subTest(strategy=p.strategy):
                # cash = start - money put down + money paid back
                self.assertAlmostEqual(p.bankroll, 1000 - p.total_wagered + p.total_returned)
                st = get_statistics(p)
                self.assertAlmostEqual(st["final_equity"], p.bankroll + p.chips_on_table())
                self.assertAlmostEqual(st["net_result"], st["final_equity"] - 1000)
                self.assertEqual(st["total_rolls"], 2000)


class TestTableLimits(CrapsTest):

    def take(self):
        self.g.take_bets(self.p.player_board, 1)

    def test_odds_capped_at_3x4x5x(self):
        for n, cap in {4: 15, 10: 15, 5: 20, 9: 20, 6: 25, 8: 25}.items():
            self.p.player_board[str(n)].update(come=5.0, comeodds=100.0)
        self.take()
        for n, cap in {4: 15, 10: 15, 5: 20, 9: 20, 6: 25, 8: 25}.items():
            self.assertEqual(self.on_board("comeodds", n), (cap, cap))

    def test_pass_odds_capped_on_point(self):
        self.g.button = 4
        self.p.player_board.update(passline=5.0, passodds=100.0)
        self.take()
        self.assertEqual(self.p.player_board["passodds"], 15.0)

    def test_lay_odds_win_capped_at_6x_flat(self):
        self.g.button = 4
        self.p.player_board.update(dontpassline=5.0, dontpassodds=500.0)
        for n in NUMBERS:
            self.p.player_board[str(n)].update(dontcome=5.0, dontcomeodds=500.0)
        self.take()
        self.assertAlmostEqual(self.p.player_board["dontpassodds"] * LAY_ODDS[4], 15.0)
        for n in NUMBERS:
            self.assertAlmostEqual(self.p.player_board[str(n)]["dontcomeodds"], 30.0)  # 3-4-5x = 6x lay

    def test_flat_bets_capped_at_table_limit(self):
        self.p.player_board.update(passline=5000.0)
        self.p.player_board["6"]["place"] = 5000.0
        self.take()
        self.assertEqual(self.p.player_board["passline"], 1000.0)
        self.assertEqual(self.p.player_board["6"]["place"], 1000.0)

    def test_flat_odds_multiple(self):
        self.g.maxodds = "2x"
        self.p.player_board["6"].update(come=5.0, comeodds=100.0)
        self.take()
        self.assertEqual(self.p.player_board["6"]["comeodds"], 10.0)

    def test_odds_without_flat_bet_removed(self):
        self.p.player_board["6"]["comeodds"] = 10.0
        self.take()
        self.assertEqual(self.on_board("comeodds", 6), (0, 0))


class TestDontLayOneUnit(CrapsTest):

    def test_lays_odds_to_win_one_unit(self):
        from strategies import dont_lay_one_unit
        from crapgame import LAY_ODDS
        for point in NUMBERS:
            with self.subTest(point=point):
                self.setUp()
                self.g.button = point
                board = self.p.player_board
                board["dontpassline"] = 5.0
                for n in NUMBERS:
                    board[str(n)]["dontcome"] = 5.0
                dont_lay_one_unit(board, self.g, None)
                self.assertAlmostEqual(board["dontpassodds"] * LAY_ODDS[point], 5.0)
                for n in NUMBERS:
                    self.assertAlmostEqual(board[str(n)]["dontcomeodds"] * LAY_ODDS[n], 5.0)
                self.assertEqual(board["dontcomeline"], 5.0)

    def test_comeout_only_dontpass(self):
        from strategies import dont_lay_one_unit
        board = self.p.player_board
        dont_lay_one_unit(board, self.g, None)
        self.assertEqual(board["dontpassline"], 5.0)
        self.assertEqual(board["dontcomeline"], 0.0)
        self.assertEqual(board["dontpassodds"], 0.0)


class TestOddsPress(unittest.TestCase):
    """Pressing odds on a number each time it hits; seven-out resets."""

    def make(self, base="Pass/Come 2x Place 6&8", odds_press_units=1):
        self.g = CrapGame()
        self.p = CrapsPlayer(1, self.g, "test", 1000,
                             profile={"base_strategy": base, "odds_press_units": odds_press_units})
        self.g.play_toss(5, 6)  # come-out 11: pass bet goes up
        self.g.play_toss(2, 2)  # point 4

    def test_odds_press_on_come_number_capped_at_max_odds(self):
        self.make()
        self.g.play_toss(4, 5)  # come bet travels to 9 with 2x ($10) odds
        board = self.p.player_board["9"]
        self.assertEqual((board["come"], board["comeodds"]), (5.0, 10.0))
        self.g.play_toss(4, 5)  # 9 hits: new $5 come on 9, odds pressed to $15
        self.assertEqual((board["come"], board["comeodds"]), (5.0, 15.0))
        for _ in range(3):
            self.g.play_toss(4, 5)  # keeps pressing until 4x max on the 9
        self.assertEqual((board["come"], board["comeodds"]), (5.0, 20.0))
        self.assertEqual(self.p.player_board["passline"], 5.0)  # flats untouched

    def test_odds_press_resets_on_seven_out(self):
        self.make()
        self.g.play_toss(4, 5)
        self.g.play_toss(4, 5)
        self.assertEqual(self.p.pressed_odds, {9: 15.0})
        self.g.play_toss(3, 4)
        self.assertEqual(self.p.pressed_odds, {})

    def test_off_means_no_press(self):
        self.make(odds_press_units=0)
        self.g.play_toss(4, 5)
        self.g.play_toss(4, 5)
        self.assertEqual(self.p.player_board["9"]["comeodds"], 10.0)


if __name__ == "__main__":
    unittest.main()


class TestLinePlusTwoMax(CrapsTest):
    """Issues #2 / #3: pass + 2 come with max odds, and its don't-side mirror."""

    LIGHT = ("passline", "passodds", "comeline", "come", "comeodds")
    DARK = ("dontpassline", "dontpassodds", "dontcomeline", "dontcome", "dontcomeodds")

    def strat(self, dark):
        from strategies import pass_two_come_max_odds, dont_pass_two_dont_come_max_lay
        return dont_pass_two_dont_come_max_lay if dark else pass_two_come_max_odds

    def test_comeout_only_line_bet(self):
        for dark, (line, line_odds, come_line, *_ ) in ((False, self.LIGHT), (True, self.DARK)):
            with self.subTest(dark=dark):
                self.setUp()
                board = self.p.player_board
                self.strat(dark)(board, self.g, None)
                self.assertEqual((board[line], board[line_odds], board[come_line]), (5.0, 0.0, 0.0))

    def test_odds_follow_table_maxodds(self):
        for maxodds in ("2x", "3x4x5x", "10x"):
            for dark, (line, line_odds, come_line, come, come_odds) in ((False, self.LIGHT), (True, self.DARK)):
                with self.subTest(maxodds=maxodds, dark=dark):
                    self.setUp()
                    self.g.maxodds = maxodds
                    self.g.button = 4
                    board = self.p.player_board
                    board[line] = 5.0
                    board["9"][come] = 5.0
                    self.strat(dark)(board, self.g, None)
                    cap = self.g.max_lay if dark else self.g.max_odds
                    self.assertEqual(board[line_odds], cap(4, 5.0))
                    self.assertEqual(board["9"][come_odds], cap(9, 5.0))
                    self.g.take_bets(board, 1)  # house leaves max odds untouched
                    self.assertEqual(board["9"][come_odds], cap(9, 5.0))

    def test_stops_at_two_come_bets(self):
        for dark, (line, _, come_line, come, _) in ((False, self.LIGHT), (True, self.DARK)):
            with self.subTest(dark=dark):
                self.setUp()
                self.g.button = 6
                board = self.p.player_board
                board[line] = 5.0
                board["5"][come] = 5.0
                self.strat(dark)(board, self.g, None)
                self.assertEqual(board[come_line], 5.0)    # one working: add another
                board[come_line] = 0.0
                board["9"][come] = 5.0
                self.strat(dark)(board, self.g, None)
                self.assertEqual(board[come_line], 0.0)    # two working: stop

    def test_nothing_else_placed(self):
        for dark in (False, True):
            with self.subTest(dark=dark):
                self.setUp()
                self.g.button = 8
                board = self.p.player_board
                self.strat(dark)(board, self.g, None)
                for n in NUMBERS:
                    self.assertEqual(board[str(n)]["place"], 0.0)
                other = self.LIGHT if dark else self.DARK
                self.assertEqual([board[k] for k in other[:3]], [0.0, 0.0, 0.0])


class TestHedgeLadder(unittest.TestCase):
    """Issue #4: light/dark duo with mirrored flats."""

    def seat(self, light, dark, light_profile=None):
        g = CrapGame()
        return g, CrapsPlayer(1, g, light, 1000, profile=light_profile), CrapsPlayer(2, g, dark, 1000)

    def test_flat_mirror_loses_only_the_12_on_new_light_bets(self):
        random.seed(21)
        g, a, b = self.seat("Pass + 2 Come, No Odds", "Don't Pass + 2 Don't Come, Flat")
        leak = 0.0
        for _ in range(5000):
            new_bet = a.player_board["passline"] if g.button == 'off' else a.player_board["comeline"]
            if g.play_toss()["total"] == 12:
                leak += new_bet
        net = a.bankroll + a.chips_on_table() + b.bankroll + b.chips_on_table() - 2000
        self.assertGreater(leak, 0)
        self.assertAlmostEqual(net, -leak)

    def test_flat_press_grows_come_line_and_resets_on_seven_out(self):
        profile = {"base_strategy": "Pass + 2 Come, No Odds", "odds_press_units": 0, "flat_press_units": 1}
        g, a, _ = self.seat("Press flats", "Don't Pass + 2 Don't Come, Flat", profile)
        g.play_toss(3, 3)                  # point 6; first come bet goes up
        self.assertEqual(a.player_board["comeline"], 5.0)
        g.play_toss(4, 4)                  # come bet travels to 8
        g.play_toss(5, 3)                  # 8 hits: come win -> press 1 unit
        self.assertEqual(a.player_board["comeline"], 10.0)
        g.play_toss(4, 3)                  # seven-out resets the press
        g.play_toss(2, 2)                  # new point 4
        self.assertEqual(a.player_board["comeline"], 5.0)
