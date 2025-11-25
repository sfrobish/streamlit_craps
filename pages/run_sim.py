import polars as pl
import plotly.graph_objects as go
import plotly.express as px



# Number of rounds
num_rounds = st.sidebar.number_input(
    "Number of Shooters",
    min_value=10,
    max_value=100,
    value=10,
    step=10
)

# Number of simulations
num_simulations = st.sidebar.number_input(
    "Number of Simulations",
    min_value=1,
    max_value=1000,
    value=10,
    step=1,
    help="Run multiple simulations to see variance"
)

st.sidebar.button("🎲 Run Simulation", type="primary")