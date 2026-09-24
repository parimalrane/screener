import yfinance as yf, pandas as pd
from asta_conditions import (is_macd_pco, is_rsi_above, is_price_above_sma, is_macd_nco, is_macd_rising, is_stochastic_buy)
import glob, re

all_files = glob.glob('data/*_stocks.csv')
valid = []
for f in all_files:
    match = re.search(r'(\d{8})_stocks\.csv', f)
    if match: valid.append((int(match.group(1)), f))
valid.sort(key=lambda x:x[0])
df_uni = pd.read_csv(valid[-1][1])
tickers = df_uni['Ticker'].head(1000).tolist()

stats = {'Total': 0, 'Mo_PCO':0, 'Mo_RSI60':0, 'Mo_SMA20':0, 'We_NCO':0, 'We_RSI40':0, 'Da_MACDRise':0, 'Da_Stoch':0, 'PassedAll': 0, 'MoAll':0, 'WeAll':0, 'MoWeAll':0}

for t in tickers:
    try:
        df_d = pd.read_csv(f'data/cache_{t}.csv', index_col='Date', parse_dates=True)
        if len(df_d) < 50: continue
        res = {'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}
        df_w = df_d.resample('W-FRI').agg(res).dropna()
        df_m = df_d.resample('ME').agg(res).dropna()
        if len(df_m) < 50: continue
        
        stats['Total'] += 1
        
        m_pco = is_macd_pco(df_m)
        m_rsi = is_rsi_above(df_m, 60)
        m_sma = is_price_above_sma(df_m, 20)
        w_nco = is_macd_nco(df_w)
        w_rsi = is_rsi_above(df_w, 40)
        d_mr = is_macd_rising(df_d)
        d_st = is_stochastic_buy(df_d, strict_crossover=True)
        
        if m_pco: stats['Mo_PCO'] += 1
        if m_rsi: stats['Mo_RSI60'] += 1
        if m_sma: stats['Mo_SMA20'] += 1
        if w_nco: stats['We_NCO'] += 1
        if w_rsi: stats['We_RSI40'] += 1
        if d_mr: stats['Da_MACDRise'] += 1
        if d_st: stats['Da_Stoch'] += 1
        
        if m_pco and m_rsi and m_sma: stats['MoAll'] += 1
        if w_nco and w_rsi: stats['WeAll'] += 1
        if m_pco and m_rsi and m_sma and w_nco and w_rsi: stats['MoWeAll'] += 1
        
        if m_pco and m_rsi and m_sma and w_nco and w_rsi and d_mr and d_st:
            stats['PassedAll'] += 1
    except Exception as e:
        pass

print(stats)
