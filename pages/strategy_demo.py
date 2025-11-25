import time
import streamlit as st
import polars as pl


from crapgame import CrapGame
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
if "active_players" not in st.session_state:
    st.session_state.active_players = [False, False, False, False]
strategy_options = strategy_registry.keys()


# Sidebar for configuration
st.sidebar.header("Demo Configuration")

# Number of players
num_players = st.sidebar.number_input(
    "Number of Players",
    min_value=1,
    max_value=4,
    value=1,
    step=1,
    help="Select how many players to simulate (1-4)"
)

# Create columns for player inputs
if num_players == 1:
    cols = [st.container()]
elif num_players == 2:
    cols = st.columns(2)
elif num_players == 3:
    cols = st.columns(3)
else:  # 4 players
    cols = st.columns(4)

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
                starting_bankroll=starting_bankroll
            )
            st.session_state.players[f"Player_{i+1}"] = player
        else:
            player = st.session_state.players[f"Player_{i+1}"]

        if debugmode:
            st.session_state.crapgame
        
        if player.player_board["passline"] == 0 and player.player_board["dontpassline"] == 0:
            print(f"Player {i+1} Strategy: {strategy_type} about to place first bet")
            player.place_bets()

        st.markdown("**Bet Amounts**")
        for bet in player.player_board:
            if bet in ["4", "5", "6", "8", "9", "10"]:
                for subbet in player.player_board[bet]:
                    if player.player_board[bet][subbet] > 0:
                        st.write(f"{bet} {subbet}: ${player.player_board[bet][subbet]}")
            else:
                if player.player_board[bet] > 0:
                    st.write(f"{bet}: ${player.player_board[bet]}")

        st.write(f"**Current Bankroll:** ${player.bankroll:.2f}")


st.markdown("---")
st.write(f"Button = {st.session_state.crapgame.button}")
# Single roll button
tosscol, resetcol, unused = st.columns([1,1,7])
if tosscol.button("🎲 Toss Dice", type="primary"):
    rolldict = st.session_state.crapgame.play_toss()
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

if st.session_state.crapgame.button != 'off' and st.session_state.crapgame.roll == 7:
    placeholder = st.empty()
    with placeholder.container():
        st.write("Seven out! New shooter coming up.")
        time.sleep(7)
    placeholder.empty()
    st.session_state.crapgame.button = 'off'
    st.session_state.crapgame.roll = None
    st.session_state.rollhistory = []
    st.rerun()