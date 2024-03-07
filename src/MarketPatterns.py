import yfinance as yf
import pandas as pd
import numpy as np
import ta


class MarketPatterns:
    def __init__(self, ticker, start_date, end_date, interval='1d', rsi_period=14):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval
        self.rsi_period = rsi_period  # New instance variable to store the RSI period
        self.data = None
        self.aggregated_data = None
    
    def load_data(self):
        self.data = yf.download(self.ticker, start=self.start_date, end=self.end_date, interval=self.interval)
        self.data.reset_index(inplace=True)
        self.data.rename(columns={'Datetime': 'Date'}, inplace=True)
    
    def calculate_rsi(self):
        # Use instance variable for the RSI period
        self.data['RSI'] = ta.momentum.RSIIndicator(self.data['Close'], window=self.rsi_period).rsi()
        self.data['RSI_Category'] = pd.cut(self.data['RSI'],
                                           bins=[0, 50, 100],
                                           labels=['LT 50', 'GT 50'],
                                           right=False)  # Exclude the right side of bins
        
        
    def calculate_patterns(self):
        if self.data is None:
            raise ValueError('Data not loaded. Call load_data() first.')
        
        self.data['consec_higher_highs'] = 0
        self.data['consec_lower_lows'] = 0
        self.data['Pattern_Label_Current'] = ''
        
        for i in range(1, len(self.data)):
            if self.data['High'].iloc[i] > self.data['High'].iloc[i - 1]:
                self.data.at[i, 'consec_higher_highs'] = self.data.at[i-1, 'consec_higher_highs'] + 1
            else:
                self.data.at[i, 'consec_higher_highs'] = 0

            if self.data['Low'].iloc[i] < self.data['Low'].iloc[i - 1]:
                self.data.at[i, 'consec_lower_lows'] = self.data.at[i-1, 'consec_lower_lows'] + 1
            else:
                self.data.at[i, 'consec_lower_lows'] = 0

            net = self.data.at[i, 'consec_higher_highs'] - self.data.at[i, 'consec_lower_lows']
            label_str = f"HigherHigh: {self.data.at[i, 'consec_higher_highs']} LowerLow: {self.data.at[i, 'consec_lower_lows']}"
            self.data.at[i, 'Pattern_Label_Current'] = label_str

        self.data['Pattern_Label_Prior'] = self.data['Pattern_Label_Current'].shift(1)
        self.data['ROI'] = self.data['Close'] / self.data['Open'] - 1
        self.data.dropna(inplace=True)

    def analyze_probability(self):
        if self.data is None:
            raise ValueError('Data not analyzed. Call calculate_patterns() first.')

        self.calculate_rsi()  # Make sure RSI is calculated before running the analysis
        
        self.aggregated_data = self.data.groupby(['RSI_Category', 'Pattern_Label_Prior', 'Pattern_Label_Current']).agg(
            total_count=('Date', 'size'),
            # mean_roi=('ROI', 'mean')
        ).reset_index()

        current_pattern = self.data['Pattern_Label_Current'].tail(1).item()
        current_rsi_category = self.data['RSI_Category'].tail(1).item()
        current_price = self.data['Close'].tail(1).item()
        
        # Filter by both current RSI category and current pattern
        summary_stats = self.aggregated_data[
            (self.aggregated_data['Pattern_Label_Prior'] == current_pattern) &
            (self.aggregated_data['RSI_Category'] == current_rsi_category)
        ]

        probability_series = summary_stats['total_count'] / summary_stats['total_count'].sum()
        summary_stats = summary_stats.assign(Probability=probability_series)

        # Expected ROI
        # summary_stats['Expected ROI'] = summary_stats['mean_roi'] 

        # rename columns
        summary_stats.columns = ['Current RSI Category', 'Current Pattern', 
                                'Next Potential Pattern', 'Historical Counts', 
                                # 'Expected ROI',
                                'Probability']
        
        return summary_stats
