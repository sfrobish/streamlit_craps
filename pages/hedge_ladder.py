"""Issue #4: light/dark duo aggression ladder. Every rung plays the same dice; stats pool both seats."""
import random

import polars as pl
import streamlit as st

import reports
from table_settings import table_settings

st.title("Hedge ladder")
st.caption(
    "Seat 1 plays Pass + 2 Come, seat 2 plays Don't Pass + 2 Don't Come, so the flats mirror each other. "
    "Each rung changes only the odds or pressing. Casino defaults: come odds are off on the come-out, "
    "lay odds stay working. All rungs play the same dice."
)

with st.expander("Table limits"):
    table = table_settings()

with st.form("ladder"):
    c1, c2 = st.columns(2)
    bankroll = c1.number_input("Starting bankroll per seat", 100, 10_000, 1000, 100)
    num_sims = c2.number_input("Simulations per rung", 10, 5000, 200, 10,
                               help="About 6 seconds per 100. p99 needs 1,000+ to settle.")
    length_by = st.segmented_control("Session length by", ["Shooters", "Rolls"], default="Shooters", required=True)
    session_length = st.number_input("Shooters or rolls per session", 1, 2000, 10)
    run = st.form_submit_button("Run ladder", type="primary", icon=":material/stairs:")

if run:
    length = {"num_rolls": session_length} if length_by == "Rolls" else {"num_shooters": session_length}
    seed = random.randrange(1_000_000)
    with st.spinner(f"Simulating {len(reports.LADDER)} rungs..."):
        st.session_state.ladder_results = (reports.run_ladder(table, bankroll, num_sims, seed, **length), seed)

if "ladder_results" not in st.session_state:
    st.stop()

ladder, seed = st.session_state.ladder_results
money = {c: st.column_config.NumberColumn(label, format="accounting") for c, label in {
    "mean_net": "mean net", "median_net": "median net",
    "p10_net": "p10 net", "p90_net": "p90 net", "p99_net": "p99 net",
    "low_95": "low point 95%", "low_99": "low point 99%", "peak_chips": "peak chips",
    "comeout_mean": "come-out mean", "comeout_sd": "come-out sd",
    "point_on_mean": "point-on mean", "point_on_sd": "point-on sd",
}.items()}

st.subheader("Pooled results per rung")
st.caption(
    "Per session, both seats combined. Low point 95% / 99%: 95% / 99% of sessions never dipped below it. "
    "Come-out and point-on split each session's net by the kind of roll it came from. "
    f"Seed {seed}."
)
st.dataframe(ladder, hide_index=True, column_config={"rung": st.column_config.TextColumn("rung"), **money},
             alt="Pooled session stats for each rung of the hedge ladder")

st.subheader("What working lay odds add (rung 7 minus rung 3)")
st.caption("Rung 3 has odds on the light side only; rung 7 adds max lay odds on the dark side.")
diff = ladder.filter(pl.col("rung").str.starts_with("7.")).drop("rung") - ladder.filter(pl.col("rung").str.starts_with("3.")).drop("rung")
st.dataframe(diff, hide_index=True, column_config=money, alt="Rung 7 minus rung 3 for each stat")
