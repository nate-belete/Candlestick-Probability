
import streamlit as st
import matplotlib.pyplot as plt
from adjustText import adjust_text  
import seaborn as sns

import pandas as pd
from datetime import datetime, timedelta
from src.MarketPatterns import MarketPatterns  # Import the class from the src folder

# Streamlit app layout
st.title('Market Pattern Analysis')

# Sidebar inputs
st.sidebar.header('User Input Parameters')
ticker = st.sidebar.text_input('Ticker Symbol', value='AAPL')
start_date = st.sidebar.date_input('Start Date', datetime(2000, 1, 1))
end_date = st.sidebar.date_input('End Date', datetime.now()) # + timedelta(days=1)
interval_options = [ '5m', '15m', '30m', '1h', '1d', '1wk', '1mo', ]
interval = st.sidebar.selectbox('Interval for Data', interval_options, index=4)
rsi_period = st.sidebar.number_input('RSI Period', value=14, min_value=1)

# Button to run analysis
run_analysis = st.sidebar.button('Run Analysis')

# Analyze market patterns function
def analyze_market_patterns(ticker, start_date, end_date, interval, rsi_period):
    """
    Analyzes market patterns based on the given inputs and returns a summary and remarks.
    """
    # Ensure the end date is included in the analysis
    end_date = end_date + timedelta(days=1)
    market_patterns = MarketPatterns(
        ticker=ticker,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        interval=interval,
        rsi_period=rsi_period,
    )

    # Initialize return values with defaults
    empty_df = pd.DataFrame()
    analysis_remarks = "Please try with a shorter timeframe and re-submit."
    plot_buffer = None

    try:
        market_patterns.load_data()
        market_patterns.calculate_patterns()
        summary_stats = market_patterns.analyze_probability()
        filtered_probability_summary = summary_stats[summary_stats['Probability'] > 0]

        remarks = f"**User Selections:**\n\n"
        remarks += f"- Ticker: `{ticker}`\n"
        remarks += f"- Analysis Period: `{start_date.strftime('%Y-%m-%d')}` to `{(end_date).strftime('%Y-%m-%d')}`\n"
        remarks += f"- Data Interval: `{interval}`\n"
        remarks += f"- RSI Period: `{rsi_period}`\n\n"

        # Analyze total count and highest probability
        total_count = filtered_probability_summary['Historical Counts'].sum()
        highest_probability = filtered_probability_summary['Probability'].max()
        currentPattern = filtered_probability_summary['Current Pattern'].head(1).item()

        # Add analysis information to the narrative remarks
        remarks += f"**Analysis Summary:**\n\n"
        remarks += f"The current pattern of `{currentPattern}` occurred `{total_count}` times in the historical data. "

        # Check if there is at least one pattern with a non-zero probability
        if highest_probability > 0:
            highest_prob_row = filtered_probability_summary.loc[filtered_probability_summary['Probability'].idxmax()]
            highest_prob_next_pattern = highest_prob_row['Next Potential Pattern']
            remarks += (f"The next potential pattern with the highest likelihood of occurrence, based on historical data, " 
                        f"is `{highest_prob_next_pattern}` with a probability of `{highest_probability:.1%}`.")


            remarks += f"\n\n**Historical Statistics:**\n\n"
            remarks += f"- Next Potential Pattern: `{highest_prob_next_pattern}`\n"
            remarks += f"- Probability: `{highest_probability:.1%}`\n"

            # Call at the end of your analysis function, before returning results:
            if not filtered_probability_summary.empty:
                # Styling
                sns.set(style="whitegrid")  # Use seaborn styling for nicer plots

                # Plotting
                fig, ax = plt.subplots(figsize=(12, 8))
                scatter = ax.scatter(
                    x=filtered_probability_summary['Historical Counts'],
                    y=filtered_probability_summary['Probability'] * 100,  # Convert to percentage
                    alpha=0.6,
                    s=150,  # Increase marker size
                    cmap='viridis'
                )

                # Adding labels and storing them in a list for later adjustment
                texts = []
                for i, txt in enumerate(filtered_probability_summary['Next Potential Pattern']):
                    labels = f"{txt}\n{filtered_probability_summary['Probability'].iat[i]:.2%}"
                    texts.append(ax.text(filtered_probability_summary['Historical Counts'].iat[i],
                            filtered_probability_summary['Probability'].iat[i] * 100,
                            labels,
                            fontsize=9,  # Set a larger font size for annotations
                            ha='center'))

                # Automatically adjust text to minimize overlaps
                adjust_text(texts, arrowprops=dict(arrowstyle='->', color='red'), ax=ax)

                plt.colorbar(scatter, label='Probability (%)')
                plt.title('Historical Counts vs Probability', fontsize=16)
                plt.xlabel('Historical Counts', fontsize=14)
                plt.ylabel('Probability (%)', fontsize=14)
                plt.tight_layout()

                # Save
                from io import BytesIO
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches="tight")
                buffer.seek(0)

                # Clean up plot memory
                plt.close()

                # Add the plot to the remarks or return it with the other results
                return filtered_probability_summary, remarks, buffer
            else:
                # If no data to plot
                return filtered_probability_summary, remarks, None

        else:
            remarks += "There were no patterns with a probability greater than zero found in the historical data."

        # Return the summary DataFrame and the narrative remarks
        return filtered_probability_summary, remarks

    # except Exception as e:
        # return pd.DataFrame(), f"An error occurred: {e}"
    except Exception as e:
        error_message = (f"An error occurred\n\n"
                         f"**Suggestion:** Consider using a shorter timeframe and re-submitting the analysis.")
        analysis_remarks = error_message
        return empty_df, analysis_remarks, plot_buffer

    # If all goes well, return the results as earlier
    return filtered_probability_summary, analysis_remarks, plot_buffer


if run_analysis:
    st.subheader('Analyzing Market Patterns')
    
    # Call the function to perform the analysis
    results, analysis_remarks, plot_buffer = analyze_market_patterns(ticker, start_date, end_date, interval, rsi_period)
    
    st.write(analysis_remarks)  # Display analysis remarks

    if not results.empty:
        st.table(results)  # Display the analysis results in a table
        if plot_buffer:
            st.subheader('Scatter Plot of Historical Counts vs Probability')
            st.image(plot_buffer)  # Display the scatter plot
        st.success('Analysis Complete!')
    else:
        st.error(analysis_remarks)