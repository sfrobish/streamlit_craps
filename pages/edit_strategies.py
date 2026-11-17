"""Build press profiles: a base strategy plus odds pressing on numbers that hit.
Profiles live in session state; download/upload JSON to keep them."""
import json

import streamlit as st

from strategies import strategy_registry

NEW = "New profile"
DEFAULTS = {
    "base_strategy": next(iter(strategy_registry)),
    "odds_press_units": 1,
}

profiles = st.session_state.setdefault("profiles", {})


def load_profile():
    """Copy the selected profile into the form widgets."""
    choice = st.session_state.profile_choice
    p = {**DEFAULTS, **profiles.get(choice, {})}
    st.session_state.p_name = "" if choice == NEW else choice
    for k, v in p.items():
        st.session_state[f"p_{k}"] = v


def save_profile():
    name = st.session_state.p_name.strip()
    if not name:
        st.error("Name is required.")
        return
    if name in strategy_registry:
        st.error(f"'{name}' is a built-in strategy name; pick another.")
        return
    old = st.session_state.profile_choice
    if old != NEW and old != name:
        profiles.pop(old, None)  # renamed
    profiles[name] = {k: st.session_state[f"p_{k}"] for k in DEFAULTS}
    st.session_state.profile_choice = name


def delete_profile():
    profiles.pop(st.session_state.profile_choice, None)
    st.session_state.profile_choice = NEW
    load_profile()


def upload_profiles():
    f = st.session_state.profile_upload
    if f is None:
        return
    try:
        loaded = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        st.error("Not a valid profiles JSON file.")
        return
    for name, p in loaded.items():
        if isinstance(p, dict) and p.get("base_strategy") in strategy_registry:
            profiles[name] = {**DEFAULTS, **{k: p[k] for k in DEFAULTS if k in p}}


if "profile_choice" not in st.session_state:
    st.session_state.profile_choice = NEW
    load_profile()

st.title("Edit strategies")
st.caption(
    "Pick a base strategy, then how hard it presses the odds while a shooter is hot. "
    "Presses reset on the seven-out."
)

st.selectbox("Profile", [NEW, *profiles], key="profile_choice", on_change=load_profile)

with st.form("profile_form", border=True):
    st.text_input("Name", key="p_name")
    st.selectbox("Base strategy", list(strategy_registry), key="p_base_strategy")

    st.subheader("Press the odds", divider=True)
    st.number_input(
        "Units added to a number's odds each time it hits (0 = off)",
        min_value=0, max_value=10, key="p_odds_press_units",
        help="When your come or pass odds on a number win, the next odds on that number grow "
             "by this many table-min units, up to the table's max odds (3x/4x/5x). "
             "The flat come bet stays the same.",
    )

    st.form_submit_button("Save", type="primary", on_click=save_profile)

if st.session_state.profile_choice != NEW:
    st.button("Delete profile", icon=":material/delete:", on_click=delete_profile)

st.subheader("Keep your profiles")
st.caption("Profiles last for this browser session only.")
with st.container(horizontal=True, vertical_alignment="bottom"):
    st.download_button(
        "Download JSON",
        json.dumps(profiles, indent=2),
        file_name="craps_profiles.json",
        mime="application/json",
        icon=":material/download:",
        disabled=not profiles,
    )
    st.file_uploader("Load JSON", type="json", key="profile_upload", on_change=upload_profiles)
