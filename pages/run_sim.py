import random
from player import CrapsPlayer
import streamlit as st
import polars as pl
import plotly.graph_objects as go
import plotly.express as px

from crapgame import CrapGame, SEATS
from strategies import strategy_registry
from stats import get_statistics

profiles = st.session_state.setdefault("profiles", {})

# Number of rounds
num_rounds = st.number_input(
    "Number of Shooters",
    min_value=10,
    max_value=100,
    value=10,
    step=10
)

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
        for n_sim in range(num_simulations):
            game = CrapGame(tablemin=5,limit=1000,maxodds="3x4x5x")
            for i in range(num_players):
                CrapsPlayer(  # __init__ seats itself via game.add_player
                    id=i+1,
                    crapgame=game,
                    strategy=st.session_state[f"strategy_player_{i}"],
                    starting_bankroll=st.session_state[f"bankroll_player_{i}"],
                    profile=profiles.get(st.session_state[f"strategy_player_{i}"]),
                )
            for n_shooter in range(num_rounds):
                while not game.play_toss()["sevenout"]:
                    pass


    player_stats = {}     

    for player in game.players:
        player_stats[player.id] = get_statistics(player)

    st.write(player_stats)

         
            
    # # Display statistics
    # col1, col2, col3, col4 = st.columns(4)
        
    #     with col1:
    #         st.metric(
    #             "Final Bankroll",
    #             f"${stats['final_bankroll']:.2f}",
    #             f"{stats['net_result']:+.2f}"
    #         )
        
    #     with col2:
    #         st.metric(
    #             "Total Rounds",
    #             f"{stats['total_rounds']:,}",
    #             f"{stats['total_rolls']:,} rolls"
    #         )
        
    #     with col3:
    #         st.metric(
    #             "Win Rate",
    #             f"{stats['win_rate']*100:.1f}%",
    #             f"{stats['wins']}/{stats['total_rounds']}"
    #         )
        
    #     with col4:
    #         st.metric(
    #             "ROI",
    #             f"{stats['roi']:.2f}%"
    #         )
        
    #         # Bankroll over time chart
    #         st.subheader("Bankroll Over Time")
    #         fig = px.line(
    #             results_df.to_pandas(),
    #             x='round',
    #             y='bankroll',
    #             title='Bankroll Progress',
    #             labels={'round': 'Round Number', 'bankroll': 'Bankroll ($)'}
    #         )
    #         fig.add_hline(
    #             y=player['starting_bankroll'],
    #             line_dash="dash",
    #             line_color="gray",
    #             annotation_text="Starting Bankroll"
    #         )
    #         st.plotly_chart(fig, width='stretch')
            
    #         # Win/Loss distribution
    #         col1, col2 = st.columns(2)
            
    #         with col1:
    #             st.subheader("Outcome Distribution")
    #             outcome_counts = results_df['outcome'].value_counts()
    #             fig_pie = px.pie(
    #                 values=outcome_counts['count'].to_list(),
    #                 names=outcome_counts['outcome'].to_list(),
    #                 title='Outcome Distribution',
    #                 color=outcome_counts['outcome'].to_list(),
    #                 color_discrete_map={'win': 'green', 'lose': 'red'}
    #             )
    #             st.plotly_chart(fig_pie, width='stretch')
            
    #         with col2:
    #             st.subheader("Bet Results Distribution")
    #             fig_hist = px.histogram(
    #                 results_df.to_pandas(),
    #                 x='bet_result',
    #                 title='Bet Results Histogram',
    #                 labels={'bet_result': 'Bet Result ($)', 'count': 'Frequency'},
    #                 nbins=50
    #             )
    #             st.plotly_chart(fig_hist, width='stretch')
            
    #         # Multiple simulations for variance analysis
    #         if num_simulations > 1:
    #             st.subheader("📈 Multiple Simulations Analysis")
    #             with st.spinner(f"Running {num_simulations} simulations..."):
    #                 multi_results = run_multiple_simulations(
    #                     player['strategy'],
    #                     num_simulations,
    #                     num_rounds,
    #                     player['starting_bankroll']
    #                 )
                    
    #                 # Summary statistics
    #                 st.write("Summary Statistics Across All Simulations")
                    
    #                 col1, col2, col3, col4 = st.columns(4)
                    
    #                 with col1:
    #                     avg_final = multi_results['final_bankroll'].mean()
    #                     st.metric(
    #                         "Avg Final Bankroll",
    #                         f"${avg_final:.2f}",
    #                         f"{avg_final - player['starting_bankroll']:+.2f}"
    #                     )
                    
    #                 with col2:
    #                     st.metric(
    #                         "Best Result",
    #                         f"${multi_results['final_bankroll'].max():.2f}"
    #                     )
                    
    #                 with col3:
    #                     st.metric(
    #                         "Worst Result",
    #                         f"${multi_results['final_bankroll'].min():.2f}"
    #                     )
                    
    #                 with col4:
    #                     avg_roi = multi_results['roi'].mean()
    #                     st.metric(
    #                         "Avg ROI",
    #                         f"{avg_roi:.2f}%"
    #                     )
                    
    #                 # Distribution of final bankrolls
    #                 fig_dist = px.histogram(
    #                     multi_results.to_pandas(),
    #                     x='final_bankroll',
    #                     title='Final Bankroll Distribution',
    #                     labels={'final_bankroll': 'Final Bankroll ($)', 'count': 'Frequency'},
    #                     nbins=30
    #                 )
    #                 fig_dist.add_vline(
    #                     x=player['starting_bankroll'],
    #                     line_dash="dash",
    #                     line_color="gray",
    #                     annotation_text="Starting Bankroll"
    #                 )
    #                 st.plotly_chart(fig_dist, width='stretch')
                    
    #                 # Show detailed results table
    #                 with st.expander("View Detailed Results"):
    #                     st.dataframe(
    #                         multi_results.select([
    #                             'simulation', 'total_rounds', 'total_rolls',
    #                             'win_rate', 'final_bankroll', 'net_result', 'roi'
    #                         ]).to_pandas().style.format({
    #                             'win_rate': '{:.2%}',
    #                             'final_bankroll': '${:.2f}',
    #                             'net_result': '${:+.2f}',
    #                             'roi': '{:.2f}%'
    #                         }),
    #                         width='stretch'
    #                     )