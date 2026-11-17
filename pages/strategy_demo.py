import time
import streamlit as st
import polars as pl


from crapgame import CrapGame, SEATS
from player import CrapsPlayer
from strategies import strategy_registry
from simulation import run_multiple_simulations

# Title and description
st.title("🎲 Craps Betting Strategy Simulator")
st.markdown("""
Simulate thousands of craps rolls with different betting strategies to analyze their performance.
Choose a strategy, configure your parameters, and see how your bankroll would perform over time.
""")

if "crapgame" not in st.session_state:
    st.session_state.crapgame = CrapGame()
if "players" not in st.session_state:
    st.session_state.players = {}
profiles = st.session_state.setdefault("profiles", {})
strategy_options = [*strategy_registry, *profiles]


# Sidebar for configuration
st.sidebar.header("Demo Configuration")

# Number of players
num_players = st.sidebar.number_input(
    "Number of Players",
    min_value=1,
    max_value=SEATS,
    value=1,
    step=1,
    help=f"Select how many players to simulate (1-{SEATS})"
)

# Create columns for player inputs
cols = st.columns(num_players)

debugmode = st.sidebar.checkbox("Enable Debug Mode", value=False)

# Player configuration section
for i in range(num_players):
    with cols[i]:
        st.subheader(f"🎲 Player {i+1}")
        playing = st.toggle(
            f"Enable Player {i+1}",
            value=False,
            key=f"enable_player_{i}"
        )        
        if not playing:
            continue

        strategy_type = st.selectbox(
            "Betting Strategy",
            strategy_options,
            key=f"strategy_{i}"
        )
                    
        starting_bankroll = st.number_input(
            "Starting Bankroll ($)",
            min_value=100.0,
            max_value=100000.0,
            value=1000.0,
            step=100.0,
            key=f"bankroll_{i}"
        )
        
        if f"Player_{i+1}" not in st.session_state.players.keys():
            player = CrapsPlayer(
                i+1,
                st.session_state.crapgame,
                strategy=strategy_type,
                starting_bankroll=starting_bankroll,
                profile=profiles.get(strategy_type),
            )
            st.session_state.players[f"Player_{i+1}"] = player
        else:
            player = st.session_state.players[f"Player_{i+1}"]
            player.strategy = strategy_type
            player.profile = profiles.get(strategy_type)
            

        if debugmode:
            player.board

        ante = st.button("Place Bets", type="primary", key=f"place_bets_{i}")
        if ante:
            player.place_bets()
            st.rerun()

        st.markdown("**Bet Amounts**")
        for bet in player.player_board:
            if bet in ["4", "5", "6", "8", "9", "10"]:
                for subbet in player.player_board[bet]:
                    if player.player_board[bet][subbet] > 0:
                        st.write(f"{bet} {subbet}: ${player.player_board[bet][subbet]}")
            else:
                if player.player_board[bet] > 0:
                    st.write(f"{bet}: ${player.player_board[bet]}")

        st.write(f"**Current Bet Total:** ${player.total_bet:.2f}")
        st.write(f"**Current Bankroll:** ${player.bankroll:.2f}")
        st.write(f"**Sum:** ${player.bankroll + player.total_bet:.2f}")


st.markdown("---")
st.write(f"Button = {st.session_state.crapgame.button}")
# Single roll button
tosscol, setcol, resetcol, unused = st.columns([1,1,1,6])

die1, die2 = None, None
if setcol.toggle("📌 Set Dice", value=False):
    die1 = setcol.slider("Die 1", min_value=1, max_value=6, key="set_die1")
    die2 = setcol.slider("Die 2", min_value=1, max_value=6, key="set_die2")

if tosscol.button("🎲 Toss Dice", type="primary"):
    rolldict = st.session_state.crapgame.play_toss(die1, die2)
    st.session_state.rollhistory.append(rolldict)
    st.rerun()
   
    
if resetcol.button("🔄 Reset Game"):
    st.session_state.crapgame = CrapGame()
    st.session_state.players = {}
    st.session_state.rollhistory = []
    st.rerun()


if "rollhistory" in st.session_state:
    if len(st.session_state.rollhistory) > 0:
        for i, roll in enumerate(st.session_state.rollhistory):
            st.image([f"resources/images/dice{roll['die1']}.png", f"resources/images/dice{roll['die2']}.png"], width=50)
else:
    st.session_state.rollhistory = []

if st.session_state.rollhistory and st.session_state.rollhistory[-1].get("sevenout"):
    placeholder = st.empty()
    with placeholder.container():
        st.write("Seven out! New shooter coming up.")
        time.sleep(7)
    placeholder.empty()
    st.session_state.rollhistory = []
    st.rerun()