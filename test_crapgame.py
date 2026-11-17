"""Payout / board tests for CrapGame against standard craps rules.

Run: .venv/bin/python -m unittest test_crapgame -v

Payout convention in CrapGame: a winning bet returns stake + winnings,
a push returns the stake, a loss returns nothing. Every settled bet is
cleared to 0 on both the house board and the player's board.
"""
import random
import unittest

from crapgame import CrapGame
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
        g = CrapGame()
        players = [CrapsPlayer(i + 1, g, s, 1000) for i, s in enumerate(strategy_registry)]
        for _ in range(2000):
            g.play_toss()
        for p in players:
            with self.subTest(strategy=p.strategy):
                # cash = start - money put down + money paid back
                self.assertAlmostEqual(p.bankroll, 1000 - p.total_wagered + p.total_returned)
                st = get_statistics(p)
                self.assertAlmostEqual(st["final_equity"], p.bankroll + p.chips_on_table())
                self.assertAlmostEqual(st["net_result"], st["final_equity"] - 1000)
                self.assertEqual(st["total_rolls"], 2000)


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


if __name__ == "__main__":
    unittest.main()
