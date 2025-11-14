"""
Streamlit app for craps simulation with betting strategies.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from betting_strategies import PassLineBet, DontPassBet, PassLineWithOdds, PlaceBetSix
from simulation import CrapsSimulation, run_multiple_simulations


# Page configuration
st.set_page_config(
    page_title="Craps Simulator",
    page_icon="🎲",
    layout="wide"
)

# Title and description
st.title("🎲 Craps Betting Strategy Simulator")
st.markdown("""
Simulate thousands of craps rolls with different betting strategies to analyze their performance.
Choose a strategy, configure your parameters, and see how your bankroll would perform over time.
""")

# Sidebar for configuration
st.sidebar.header("Simulation Configuration")

# Strategy selection
strategy_type = st.sidebar.selectbox(
    "Select Betting Strategy",
    ["Pass Line", "Don't Pass", "Pass Line + 2x Odds", "Pass Line + 5x Odds", "Place 6"]
)

# Base bet amount
base_bet = st.sidebar.number_input(
    "Base Bet Amount ($)",
    min_value=1.0,
    max_value=100.0,
    value=5.0,
    step=1.0
)

# Starting bankroll
starting_bankroll = st.sidebar.number_input(
    "Starting Bankroll ($)",
    min_value=100.0,
    max_value=100000.0,
    value=1000.0,
    step=100.0
)

# Number of rounds
num_rounds = st.sidebar.number_input(
    "Number of Rounds",
    min_value=10,
    max_value=10000,
    value=1000,
    step=100
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

# Create strategy based on selection
if strategy_type == "Pass Line":
    strategy = PassLineBet(base_bet)
elif strategy_type == "Don't Pass":
    strategy = DontPassBet(base_bet)
elif strategy_type == "Pass Line + 2x Odds":
    strategy = PassLineWithOdds(base_bet, odds_multiplier=2.0)
elif strategy_type == "Pass Line + 5x Odds":
    strategy = PassLineWithOdds(base_bet, odds_multiplier=5.0)
else:  # Place 6
    strategy = PlaceBetSix(base_bet)

# Run simulation button
if st.sidebar.button("🎲 Run Simulation", type="primary"):
    with st.spinner("Running simulation..."):
        # Run single detailed simulation
        sim = CrapsSimulation(strategy, starting_bankroll)
        results_df = sim.run_simulation(num_rounds, seed=42)
        stats = sim.get_statistics()
        
        # Display statistics
        st.header("📊 Simulation Results")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Final Bankroll",
                f"${stats['final_bankroll']:.2f}",
                f"{stats['net_result']:+.2f}"
            )
        
        with col2:
            st.metric(
                "Total Rounds",
                f"{stats['total_rounds']:,}",
                f"{stats['total_rolls']:,} rolls"
            )
        
        with col3:
            st.metric(
                "Win Rate",
                f"{stats['win_rate']*100:.1f}%",
                f"{stats['wins']}/{stats['total_rounds']}"
            )
        
        with col4:
            st.metric(
                "ROI",
                f"{stats['roi']:.2f}%"
            )
        
        # Bankroll over time chart
        st.subheader("Bankroll Over Time")
        fig = px.line(
            results_df,
            x='round',
            y='bankroll',
            title='Bankroll Progress',
            labels={'round': 'Round Number', 'bankroll': 'Bankroll ($)'}
        )
        fig.add_hline(
            y=starting_bankroll,
            line_dash="dash",
            line_color="gray",
            annotation_text="Starting Bankroll"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Win/Loss distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Outcome Distribution")
            outcome_counts = results_df['outcome'].value_counts()
            fig_pie = px.pie(
                values=outcome_counts.values,
                names=outcome_counts.index,
                title='Win/Loss Distribution',
                color=outcome_counts.index,
                color_discrete_map={'win': 'green', 'lose': 'red'}
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("Bet Results Distribution")
            fig_hist = px.histogram(
                results_df,
                x='bet_result',
                title='Bet Results Histogram',
                labels={'bet_result': 'Bet Result ($)', 'count': 'Frequency'},
                nbins=50
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        # Multiple simulations for variance analysis
        if num_simulations > 1:
            st.header("📈 Multiple Simulations Analysis")
            with st.spinner(f"Running {num_simulations} simulations..."):
                multi_results = run_multiple_simulations(
                    strategy,
                    num_simulations,
                    num_rounds,
                    starting_bankroll
                )
                
                # Summary statistics
                st.subheader("Summary Statistics Across All Simulations")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_final = multi_results['final_bankroll'].mean()
                    st.metric(
                        "Avg Final Bankroll",
                        f"${avg_final:.2f}",
                        f"{avg_final - starting_bankroll:+.2f}"
                    )
                
                with col2:
                    st.metric(
                        "Best Result",
                        f"${multi_results['final_bankroll'].max():.2f}"
                    )
                
                with col3:
                    st.metric(
                        "Worst Result",
                        f"${multi_results['final_bankroll'].min():.2f}"
                    )
                
                with col4:
                    avg_roi = multi_results['roi'].mean()
                    st.metric(
                        "Avg ROI",
                        f"{avg_roi:.2f}%"
                    )
                
                # Distribution of final bankrolls
                st.subheader("Distribution of Final Bankrolls")
                fig_dist = px.histogram(
                    multi_results,
                    x='final_bankroll',
                    title='Final Bankroll Distribution',
                    labels={'final_bankroll': 'Final Bankroll ($)', 'count': 'Frequency'},
                    nbins=30
                )
                fig_dist.add_vline(
                    x=starting_bankroll,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text="Starting Bankroll"
                )
                st.plotly_chart(fig_dist, use_container_width=True)
                
                # Show detailed results table
                with st.expander("View Detailed Results"):
                    st.dataframe(
                        multi_results[[
                            'simulation', 'total_rounds', 'total_rolls',
                            'win_rate', 'final_bankroll', 'net_result', 'roi'
                        ]].style.format({
                            'win_rate': '{:.2%}',
                            'final_bankroll': '${:.2f}',
                            'net_result': '${:+.2f}',
                            'roi': '{:.2f}%'
                        }),
                        use_container_width=True
                    )

# Information section
with st.expander("ℹ️ About the Strategies"):
    st.markdown("""
    ### Betting Strategies Explained
    
    **Pass Line**: The most common bet in craps. You win on a come-out roll of 7 or 11, lose on 2, 3, or 12.
    If a point is established, you win if the point is rolled again before a 7.
    
    **Don't Pass**: The opposite of the pass line. You win on 2 or 3, lose on 7 or 11 (12 is a push).
    After a point is established, you win if a 7 is rolled before the point.
    
    **Pass Line + Odds**: Combines the pass line bet with an odds bet after the point is established.
    Odds bets pay true odds: 2:1 for 4/10, 3:2 for 5/9, and 6:5 for 6/8.
    
    **Place 6**: A bet that 6 will be rolled before 7. Pays 7:6 on a win.
    
    ### How to Use
    1. Select your betting strategy from the sidebar
    2. Configure your base bet amount and starting bankroll
    3. Choose the number of rounds to simulate
    4. Set the number of simulations to run (more simulations show variance)
    5. Click "Run Simulation" to see the results
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🎲 Craps Simulator - Built with Streamlit</p>
    <p><em>Remember: The house always has an edge. This is for educational purposes only.</em></p>
</div>
""", unsafe_allow_html=True)
