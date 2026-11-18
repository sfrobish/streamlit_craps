import streamlit as st

import reports
from crapgame import SEATS
from strategies import strategy_registry
from table_settings import table_settings

profiles = st.session_state.setdefault("profiles", {})

with st.expander("Table limits"):
    table = table_settings()

length_by = st.segmented_control(
    "Session length by", ["Shooters", "Rolls"], default="Shooters", required=True,
    help="Rolls ends the session after that many rolls, even mid-hand (about 100 rolls an hour).",
)
if length_by == "Rolls":
    session_length = st.number_input("Number of Rolls", min_value=10, max_value=2000, value=100, step=10)
else:
    session_length = st.number_input("Number of Shooters", min_value=10, max_value=100, value=10, step=10)

# Number of simulations
num_simulations = st.number_input(
    "Number of Simulations",
    min_value=1,
    max_value=1000,
    value=10,
    step=1,
    help="Run multiple simulations to see variance"
)

num_players = st.number_input(
    "Number of Players",
    min_value=1,
    max_value=SEATS,
    value=1,
    step=1
)

for i in range(num_players):
    st.subheader(f"🎲 Player {i+1} Configuration")
    strategy = st.selectbox(
        f"Select Strategy for Player {i+1}",
        options=[*strategy_registry, *profiles],
        key=f"strategy_player_{i}"
    )
    starting_bankroll = st.number_input(
        f"Starting Bankroll for Player {i+1}",
        min_value=100,
        max_value=10000,
        value=1000,
        step=100,
        key=f"bankroll_player_{i}"
    )

if st.button("🎲 Run Simulation", type="primary"):
    with st.spinner("Running simulation..."):
        seats = [(st.session_state[f"strategy_player_{i}"],
                  st.session_state[f"bankroll_player_{i}"],
                  profiles.get(st.session_state[f"strategy_player_{i}"]))
                 for i in range(num_players)]
        length = {"num_rolls": session_length} if length_by == "Rolls" else {"num_shooters": session_length}
        st.session_state.sim_results = reports.run_batch(table, seats, num_simulations, **length)

if "sim_results" not in st.session_state:
    st.stop()

rolls, sessions = st.session_state.sim_results

st.subheader("1. Summary across sessions")
st.dataframe(
    reports.summary(rolls), hide_index=True, alt="Per-player summary with pooled all-seats row",
    column_config={
        "pct_ahead": st.column_config.NumberColumn("% sessions ahead", format="%.0f%%"),
        **{c: st.column_config.NumberColumn(c.replace("_", " "), format="accounting")
           for c in ["median_net", "p10_net", "p90_net", "avg_max_drawdown", "worst_low_point", "max_exposure"]},
    },
)

st.subheader("2. Team chip stack across sessions")
st.caption("Running net if the sessions were played back to back. Gray = all seats combined.")
st.altair_chart(reports.team_across_sessions(sessions), alt="Cumulative team and per-seat net across sessions")

st.subheader("3. Equity by shooter, all seats combined")
st.caption("Net after each shooter's hand with every seat added together. Bold line is the median.")
st.altair_chart(reports.equity_by_shooter(reports.all_seats(rolls)), alt="Combined net of all seats after each shooter")

st.subheader("4. Equity by shooter")
st.caption("Net after each shooter's hand. Faint lines are sessions; bold line is the median.")
st.altair_chart(reports.equity_by_shooter(rolls), alt="Net after each shooter, one panel per seat")

st.subheader("5. Session result distribution")
st.altair_chart(reports.final_distribution(sessions), alt="Histogram of session net results")

st.subheader("6. Chips on table through a hand")
st.altair_chart(reports.exposure_by_roll(rolls), alt="Average chips on table by roll within hand")

st.subheader("7. Equity paths")
st.caption("Each faint line is one session; bold line is the median session at each roll.")
st.altair_chart(reports.equity_paths(rolls), alt="Net result over rolls for every session")

st.subheader("8. Drawdown vs result")
st.caption("How deep each session dipped from its high, against where it ended.")
st.altair_chart(reports.drawdown_vs_result(sessions), alt="Max drawdown vs session net")

st.subheader("9. Dice totals vs expected")
st.caption("Bars observed, gray ticks expected. RNG sanity check.")
st.altair_chart(reports.dice_frequency(rolls), alt="Observed vs expected dice totals")
