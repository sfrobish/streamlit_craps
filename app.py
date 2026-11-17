"""
Streamlit app for craps simulation with betting strategies.
"""

import streamlit as st
from menu import menu


# Page configuration
st.set_page_config(
    page_title="Craps Simulator",
    page_icon="🎲",
    layout="wide"
)



# Initialize st.session_state.role to None
if "role" not in st.session_state:
    st.session_state.role = None

# Retrieve the role from Session State to initialize the widget
st.session_state._role = st.session_state.role

def set_role():
    # Callback function to save the role selection to Session State
    st.session_state.role = st.session_state._role


# Selectbox to choose role
st.selectbox(
    "Select your role:",
    [None, "user", "admin", "this doesn't do anything"],
    key="_role",
    on_change=set_role,
)
menu() # Render the dynamic menu!



    ## Good stuff but we need to make it work for one throw first
    ### Then one shooter
    ### Then multiple shooters
    ### Then multiple players
    ## Then multiple simulations
    # with st.spinner("Running simulation..."):
        
    #     # Run simulations for each player
    #     for player in players:
    #         st.header(f"📊 {player['name']} - {player['strategy_name']}")
            
    #         # Run single detailed simulation
    #         sim = CrapsSimulation(player['strategy'], player['starting_bankroll'])
    #         results_df = sim.run_simulation(num_rounds, seed=42)
    #         stats = sim.get_statistics()
            
    #         # Display statistics
    #         col1, col2, col3, col4 = st.columns(4)
        
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
            
    #         st.markdown("---")

# # Information section
# with st.expander("ℹ️ About the Strategies"):
#     st.markdown("""
#     ### Betting Strategies Explained
    
#     **Pass Line**: The most common bet in craps. You win on a come-out roll of 7 or 11, lose on 2, 3, or 12.
#     If a point is established, you win if the point is rolled again before a 7.
    
#     **Don't Pass**: The opposite of the pass line. You win on 2 or 3, lose on 7 or 11 (12 is a push).
#     After a point is established, you win if a 7 is rolled before the point.
    
#     **Pass Line + Odds**: Combines the pass line bet with an odds bet after the point is established.
#     Odds bets pay true odds: 2:1 for 4/10, 3:2 for 5/9, and 6:5 for 6/8.
    
#     **Place 6**: A bet that 6 will be rolled before 7. Pays 7:6 on a win.
    
#     ### How to Use
#     1. Select your betting strategy from the sidebar
#     2. Configure your base bet amount and starting bankroll
#     3. Choose the number of rounds to simulate
#     4. Set the number of simulations to run (more simulations show variance)
#     5. Click "Run Simulation" to see the results
#     """)

# # Footer
# st.markdown("---")
# st.markdown("""
# <div style='text-align: center'>
#     <p>🎲 Craps Simulator - Built with Streamlit</p>
#     <p><em>Remember: The house always has an edge. This is for educational purposes only.</em></p>
# </div>
# """, unsafe_allow_html=True)
