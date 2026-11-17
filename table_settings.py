"""Table limits shared by the sim and demo pages (values persist across page switches)."""
import streamlit as st

MAX_ODDS_OPTIONS = ["1x", "2x", "3x4x5x", "5x", "10x", "100x"]


def table_settings():
    """Render table min / limit / max odds inputs; return them as CrapGame kwargs."""
    tablemin = st.number_input(
        "Table minimum ($)", min_value=1, max_value=500, value=5, step=5,
        key="table_min", persist_state="session",
        help="Base bet unit for every strategy.",
    )
    limit = st.number_input(
        "Table limit ($)", min_value=int(tablemin), max_value=100_000, value=max(1000, int(tablemin)), step=100,
        key="table_limit", persist_state="session",
        help="No single bet may exceed this.",
    )
    maxodds = st.selectbox(
        "Max odds", MAX_ODDS_OPTIONS, index=MAX_ODDS_OPTIONS.index("3x4x5x"),
        key="table_maxodds", persist_state="session",
        help="Odds allowed behind a pass/come bet, as a multiple of the flat bet. "
             "Lay odds may win up to the same multiple.",
    )
    return {"tablemin": float(tablemin), "limit": float(limit), "maxodds": maxodds}
