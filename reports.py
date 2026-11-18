"""Run a batch of sessions and build the report charts for the Run Full Simulation page."""
import altair as alt
import polars as pl

from crapgame import CrapGame
from player import CrapsPlayer

SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]  # categorical slots 1-3 (one per seat)
MONEY = "(,.2f"  # d3 format: negatives as (100.00)
DICE_ODDS = {t: (6 - abs(t - 7)) / 36 for t in range(2, 13)}


def run_batch(table, seats, num_sims, num_shooters=None, num_rolls=None):
    """Play num_sims sessions. seats: list of (strategy, bankroll, profile).

    A session ends after num_shooters seven-outs or, if num_rolls is given, after that many
    rolls (possibly mid-hand; chips still on the table count toward equity).

    Returns (rolls, sessions):
      rolls    one row per toss per player: sim, roll, shooter, roll_in_shooter, total, player, equity, exposure
      sessions one row per sim per player: net, max_drawdown, peak_exposure, low_point
    """
    rows = []
    for sim in range(num_sims):
        game = CrapGame(**table)
        players = [CrapsPlayer(id=i + 1, crapgame=game, strategy=s, starting_bankroll=b, profile=p)
                   for i, (s, b, p) in enumerate(seats)]
        roll = shooter = k = 0
        while (roll < num_rolls) if num_rolls else (shooter < num_shooters):
            r = game.play_toss()
            roll += 1
            k += 1
            for pl_ in players:
                rows.append({
                    "sim": sim, "roll": roll, "shooter": shooter, "roll_in_shooter": k,
                    "total": r["total"], "player": f"P{pl_.id}: {pl_.strategy}",
                    "start": float(pl_.starting_bankroll),
                    "equity": pl_.bankroll + pl_.chips_on_table(),
                    "exposure": pl_.chips_on_table(),
                })
            if r["sevenout"]:
                shooter += 1
                k = 0
    rolls = pl.DataFrame(rows)
    return rolls, session_stats(rolls)


def session_stats(rolls):
    """One row per sim per player from the roll-by-roll equity."""
    return (
        rolls.sort("sim", "player", "roll")
        .with_columns(peak=pl.col("equity").cum_max().over("sim", "player"))
        .group_by("sim", "player")
        .agg(
            net=pl.col("equity").last() - pl.col("start").first(),
            max_drawdown=(pl.col("peak") - pl.col("equity")).max(),
            peak_exposure=pl.col("exposure").max(),
            low_point=pl.col("equity").min() - pl.col("start").first(),
        )
        .sort("sim", "player")
    )


def _color(players):
    return alt.Color("player:N", title="Player", scale=alt.Scale(domain=players, range=SERIES[:len(players)]))


def equity_paths(rolls):
    """Every session's equity vs roll (faint), plus the median path per player (bold)."""
    players = sorted(rolls["player"].unique())
    df = rolls.with_columns(net=pl.col("equity") - pl.col("start"))
    med = df.group_by("player", "roll").agg(pl.col("net").median()).sort("roll")
    base = alt.Chart(df).mark_line(strokeWidth=1, opacity=0.18).encode(
        x=alt.X("roll:Q", title="Roll #"),
        y=alt.Y("net:Q", title="Net ($)", axis=alt.Axis(format=MONEY)),
        color=_color(players),
        detail="sim:N",
    )
    median = alt.Chart(med).mark_line(strokeWidth=2.5).encode(
        x="roll:Q", y="net:Q", color=_color(players),
        tooltip=["player", "roll", alt.Tooltip("net:Q", title="Median net", format=MONEY)],
    )
    zero = alt.Chart(pl.DataFrame({"y": [0]})).mark_rule(strokeDash=[4, 4], color="gray").encode(y="y:Q")
    return (base + median + zero).properties(height=360)


def equity_by_shooter(rolls):
    """Net at the end of each shooter's hand across the session; one panel per seat."""
    players = sorted(rolls["player"].unique())
    df = (rolls.sort("roll").group_by("sim", "player", "shooter")
          .agg(net=pl.col("equity").last() - pl.col("start").first())
          .with_columns(shooter=pl.col("shooter") + 1))
    start = df.select("sim", "player").unique().with_columns(shooter=pl.lit(0, df["shooter"].dtype), net=pl.lit(0.0))
    df = pl.concat([start, df.select(start.columns)])
    x = alt.X("shooter:Q", title="After shooter #", axis=alt.Axis(tickMinStep=1))
    paths = alt.Chart().mark_line(strokeWidth=1, opacity=0.18).encode(
        x=x, y=alt.Y("net:Q", title="Net ($)", axis=alt.Axis(format=MONEY)), color=_color(players), detail="sim:N")
    median = alt.Chart().mark_line(strokeWidth=2.5, point=alt.OverlayMarkDef(size=40)).encode(
        x=x, y="median(net):Q", color=_color(players),
        tooltip=["player", "shooter", alt.Tooltip("median(net):Q", title="Median net", format=MONEY)])
    zero = alt.Chart().mark_rule(strokeDash=[4, 4], color="gray").encode(y=alt.datum(0))
    return (alt.layer(paths, median, zero, data=df).properties(height=300, width=280)
            .facet(column=alt.Column("player:N", title=None)))


def all_seats(rolls):
    """Collapse every seat into one 'All seats' player (equity, start, exposure summed)."""
    return (rolls.group_by("sim", "roll", "shooter", "roll_in_shooter", "total")
            .agg(pl.col("start", "equity", "exposure").sum())
            .with_columns(player=pl.lit("All seats")))


def team_across_sessions(sessions):
    """Running net if the sessions were played back to back: team (all seats) bold, each seat thin."""
    players = sorted(sessions["player"].unique())
    team = sessions.group_by("sim").agg(pl.col("net").sum()).with_columns(player=pl.lit("Team"))
    df = (pl.concat([sessions.select("sim", "player", "net"), team.select("sim", "player", "net")])
          .sort("sim")
          .with_columns(cum_net=pl.col("net").cum_sum().over("player"), session=pl.col("sim") + 1))
    color = alt.Color("player:N", title="Player",
                      scale=alt.Scale(domain=["Team", *players], range=["#555555", *SERIES[:len(players)]]))
    lines = alt.Chart(df).mark_line().encode(
        x=alt.X("session:Q", title="Session #", axis=alt.Axis(tickMinStep=1)),
        y=alt.Y("cum_net:Q", title="Running net ($)", axis=alt.Axis(format=MONEY)),
        color=color,
        strokeWidth=alt.condition(alt.datum.player == "Team", alt.value(3), alt.value(1.5)),
        tooltip=["player", "session", alt.Tooltip("net:Q", title="This session", format=MONEY),
                 alt.Tooltip("cum_net:Q", title="Running net", format=MONEY)],
    )
    zero = alt.Chart(pl.DataFrame({"y": [0]})).mark_rule(strokeDash=[4, 4], color="gray").encode(y="y:Q")
    return (lines + zero).properties(height=360)


def final_distribution(sessions):
    """Histogram of session net results, one row per player."""
    players = sorted(sessions["player"].unique())
    bars = alt.Chart().mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X("net:Q", bin=alt.Bin(maxbins=30), title="Session net ($)", axis=alt.Axis(format=MONEY)),
        y=alt.Y("count():Q", title="Sessions"),
        color=_color(players),
        tooltip=[alt.Tooltip("count():Q", title="Sessions")],
    )
    zero = alt.Chart().mark_rule(strokeDash=[4, 4], color="gray").encode(x=alt.datum(0))
    return (alt.layer(bars, zero, data=sessions).properties(height=160)
            .facet(row=alt.Row("player:N", title=None)).resolve_scale(y="independent"))


def drawdown_vs_result(sessions):
    """Risk vs reward: worst drop from a peak vs where the session ended."""
    players = sorted(sessions["player"].unique())
    return alt.Chart(sessions).mark_circle(size=70, opacity=0.7, stroke="white", strokeWidth=1).encode(
        x=alt.X("max_drawdown:Q", title="Max drawdown ($)", axis=alt.Axis(format=MONEY)),
        y=alt.Y("net:Q", title="Session net ($)", axis=alt.Axis(format=MONEY)),
        color=_color(players),
        tooltip=["player", "sim", alt.Tooltip("max_drawdown:Q", format=MONEY), alt.Tooltip("net:Q", format=MONEY)],
    ).properties(height=360)


def exposure_by_roll(rolls, cap=25):
    """Average chips on the table at each roll of a shooter's hand."""
    players = sorted(rolls["player"].unique())
    df = (rolls.filter(pl.col("roll_in_shooter") <= cap)
          .group_by("player", "roll_in_shooter").agg(pl.col("exposure").mean()).sort("roll_in_shooter"))
    return alt.Chart(df).mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=40)).encode(
        x=alt.X("roll_in_shooter:Q", title="Roll within shooter's hand"),
        y=alt.Y("exposure:Q", title="Avg chips on table ($)", axis=alt.Axis(format=MONEY)),
        color=_color(players),
        tooltip=["player", "roll_in_shooter", alt.Tooltip("exposure:Q", format=MONEY)],
    ).properties(height=320)


def dice_frequency(rolls):
    """Observed vs expected share of each dice total (RNG sanity check)."""
    one = rolls.filter(pl.col("player") == rolls["player"][0])
    df = one.group_by("total").agg(observed=pl.len() / len(one)).with_columns(
        expected=pl.col("total").replace_strict(DICE_ODDS)).sort("total")
    bars = alt.Chart(df).mark_bar(cornerRadiusEnd=4, color=SERIES[0]).encode(
        x=alt.X("total:O", title="Dice total", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("observed:Q", title="Share of rolls", axis=alt.Axis(format="%")),
        tooltip=["total", alt.Tooltip("observed:Q", format=".2%"), alt.Tooltip("expected:Q", format=".2%")],
    )
    ticks = alt.Chart(df).mark_tick(color="gray", thickness=2, size=30).encode(x="total:O", y="expected:Q")
    return (bars + ticks).properties(height=280)


def summary(rolls):
    """Per-player headline numbers across all sessions, plus an 'All seats' row when 2+ seats.
    The pooled row is computed from the combined chip stack, so its drawdown and low point
    are the team's, not the seats' figures added up."""
    sessions = session_stats(rolls)
    if sessions["player"].n_unique() > 1:
        sessions = pl.concat([sessions, session_stats(all_seats(rolls)).select(sessions.columns)])
    return sessions.group_by("player", maintain_order=True).agg(
        sessions=pl.len(),
        pct_ahead=(pl.col("net") > 0).mean() * 100,
        median_net=pl.col("net").median(),
        p10_net=pl.col("net").quantile(0.10),
        p90_net=pl.col("net").quantile(0.90),
        avg_max_drawdown=pl.col("max_drawdown").mean(),
        worst_low_point=pl.col("low_point").min(),
        max_exposure=pl.col("peak_exposure").max(),
    )


if __name__ == "__main__":
    table = {"tablemin": 5.0, "limit": 1000.0, "maxodds": "3x4x5x"}
    rolls, sessions = run_batch(table, [("Pass/Come 2x Place 6&8", 1000, None)], 5, 10)
    # equity bookkeeping: summed per-roll changes must equal session net
    s = sessions.sort("sim")["net"].to_list()
    per = (rolls.sort("sim", "roll").with_columns(prev=pl.col("equity").shift(1).over("sim").fill_null(pl.col("start")))
           .group_by("sim").agg((pl.col("equity") - pl.col("prev")).sum()).sort("sim")["equity"].to_list())
    assert all(abs(a - b) < 1e-6 for a, b in zip(s, per)), (s, per)
    assert len(sessions) == 5 and rolls["shooter"].max() == 9
    assert summary(rolls)["player"].to_list() == ["P1: Pass/Come 2x Place 6&8"]  # no pooled row for one seat

    # #9: session length in rolls
    r2, s2 = run_batch(table, [("Pass/Come 2x Place 6&8", 1000, None)], 4, num_rolls=37)
    assert r2.group_by("sim").agg(pl.col("roll").max())["roll"].to_list() == [37] * 4

    # #10: pooled row = combined stack; net sums, drawdown is the team's (<= sum of seats')
    seats = [("Pass/Come 2x Place 6&8", 1000, None), ("Dark Side 3", 500, None)]
    r3, s3 = run_batch(table, seats, 6, 5)
    t = summary(r3)
    assert t["player"].to_list()[-1] == "All seats" and t["sessions"].to_list() == [6, 6, 6]
    pooled = session_stats(all_seats(r3))
    assert ((pooled["net"] - s3.group_by("sim").agg(pl.col("net").sum()).sort("sim")["net"]).abs() < 1e-6).all()
    seat_dd = s3.group_by("sim").agg(pl.col("max_drawdown").sum()).sort("sim")["max_drawdown"]
    assert (pooled["max_drawdown"] <= seat_dd + 1e-6).all()

    for f in (equity_paths, equity_by_shooter, exposure_by_roll, dice_frequency):
        f(rolls).to_dict()
    for f in (final_distribution, drawdown_vs_result, team_across_sessions):
        f(sessions).to_dict()
    print(t)
    print("ok")
