"""Table limits and seat side bets, shared by the sim and demo pages (table values persist across page switches)."""
import streamlit as st

from player import CE_ALWAYS, CE_COMEOUT, FIELD, PLACE_68

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


def side_bet_inputs(key):
    """Render one seat's side-bet options; return them as CrapsPlayer side_bets."""
    with st.container(horizontal=True, vertical_alignment="bottom"):
        place68 = st.checkbox("Place 6 & 8", key=f"place68_{key}",
                              help="1 unit each (6/5 of the table min) while a point is on; skips the point and your come numbers.")
        field = st.checkbox("Field", key=f"field_{key}", help="1 unit every roll. 2 pays 2:1, 12 pays 3:1.")
        ce = st.segmented_control("C&E", ["Come-out", "Every roll"], key=f"ce_{key}",
                                  help="1 unit, one roll. Pays 3:1 on 2, 3, 12 and 7:1 on 11.")
    ce = {"Come-out": CE_COMEOUT, "Every roll": CE_ALWAYS}.get(ce)
    return tuple(b for b, on in ((PLACE_68, place68), (FIELD, field), (ce, ce)) if on)
