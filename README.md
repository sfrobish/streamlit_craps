# 🎲 Streamlit Craps Simulator

A Streamlit web application that simulates playing craps with various betting strategies and reports detailed statistics from thousands of rolls.

![Craps Simulator](https://github.com/user-attachments/assets/41997216-8064-4e31-a7a0-539e8488fe86)

## Features

- **Multiple Betting Strategies**: Test different craps betting approaches
  - Pass Line
  - Don't Pass
  - Pass Line with Odds (2x or 5x)
  - Place 6
  
- **Comprehensive Simulation**: Run thousands of rounds with detailed tracking
  - Configurable base bet amounts
  - Adjustable starting bankroll
  - Custom number of rounds
  - Multiple simulation runs for variance analysis

- **Visual Analytics**: Rich visualizations and statistics
  - Bankroll progression over time
  - Win/Loss distribution
  - Bet results histogram
  - Multiple simulation comparisons
  - ROI and performance metrics

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sfrobish/streamlit_craps.git
cd streamlit_craps
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`.

## How to Use

1. **Select a Betting Strategy** from the sidebar dropdown
2. **Configure Parameters**:
   - Base Bet Amount: The amount you bet per round
   - Starting Bankroll: Your initial funds
   - Number of Rounds: How many rounds to simulate
   - Number of Simulations: Run multiple simulations to see variance
3. **Click "Run Simulation"** to see results

## Betting Strategies Explained

### Pass Line
The most common bet in craps. You win on a come-out roll of 7 or 11, lose on 2, 3, or 12. If a point is established, you win if the point is rolled again before a 7.

### Don't Pass
The opposite of the pass line. You win on 2 or 3, lose on 7 or 11 (12 is a push). After a point is established, you win if a 7 is rolled before the point.

### Pass Line + Odds
Combines the pass line bet with an odds bet after the point is established. Odds bets pay true odds:
- 2:1 for points 4 and 10
- 3:2 for points 5 and 9
- 6:5 for points 6 and 8

### Place 6
A bet that 6 will be rolled before 7. Pays 7:6 on a win.

## Project Structure

```
streamlit_craps/
├── app.py                    # Main Streamlit application
├── craps_game.py            # Craps game engine and dice rolling logic
├── betting_strategies.py    # Implementation of various betting strategies
├── simulation.py            # Simulation engine for running multiple rounds
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Technical Details

- **Python 3.12+** required
- **Dependencies**:
  - Streamlit: Web application framework
  - Pandas: Data manipulation and analysis
  - NumPy: Numerical computations
  - Plotly: Interactive visualizations

## Educational Purpose

**Important**: This simulator is for educational purposes only. The house always has an edge in casino games. This tool helps understand:
- How different betting strategies perform over time
- The variance in craps outcomes
- Bankroll management concepts
- Statistical analysis of casino games

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
