import pandas as pd
import numpy as np
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Algo")
    parser.add_argument('-p', required=True, help="path",type=str)
    args = parser.parse_args()
    return args.p


def main(path):
    data = pd.read_csv(path)

    data['Date'] = pd.to_datetime(data['Date'])

    # set indexes 
    data.set_index(["Ticker", "Date"], inplace=True)

    # Get the tickers
    tickers = data.index.get_level_values("Ticker").unique()

    # sorted tickers
    tickers = sorted(tickers)

    tick_count = 0
    corrs = []
    ticker1 = []
    ticker2 = []
    # find correlations between stocks
    for i in range(tick_count, len(tickers) - 1):
        for j in range(i + 1, len(tickers)):
            percent_change_a = (data.loc[tickers[i]]["Close"] - data.loc[tickers[i]]["Open"])/data.loc[tickers[i]]["Open"]
            a_series = pd.Series(percent_change_a)
            percent_change_b = (data.loc[tickers[j]]["Close"] - data.loc[tickers[j]]["Open"])/data.loc[tickers[j]]["Open"]
            b_series = pd.Series(percent_change_b)
            # ------FOR DEBUG PRUPOSES------
            # print(f"A_SERIES: \n{a_series}")
            # print(f"B_SERIES: \n{b_series}")
            # print(f"{tickers[i]} and {tickers[j]}: {a_series.corr(b_series)}")
            corr = a_series.corr(b_series)
            corrs.append(corr)
            ticker1.append(tickers[i])
            ticker2.append(tickers[j])

    correlations = pd.DataFrame({"Ticker1": ticker1, "Ticker2": ticker2, "Correlation": corrs})
    correlations = correlations.sort_values(by="Correlation", ascending=False)
    top_correlated_tickers = correlations.iloc[:6]

    top_correlated_tickers = top_correlated_tickers.reset_index(drop=True)


    # pairs trading algo implementation
    open_prices = []

    for ticker in tickers:
        stock_close_data = data.loc[ticker]["Open"]
        open_prices.append(stock_close_data.values)

    open_prices = np.stack(open_prices)

    trades = np.zeros_like(open_prices)

    min_change_percent = 0.01
    positions = [0] * len(tickers)
    tickers_to_idx = {k: v for v, k in enumerate(tickers)}
    cash_balance = 25000

    buy_percentage = 0.1

    for day in range(1, len(open_prices[0])-1):
        for idx in range(len(top_correlated_tickers) - 1):
            ticker1 = tickers_to_idx[top_correlated_tickers["Ticker1"][idx]]
            ticker2 = tickers_to_idx[top_correlated_tickers["Ticker2"][idx]]
            ticker1_pct_change = (open_prices[ticker1][day] - open_prices[ticker1][day-1]) / open_prices[ticker1][day-1]
            ticker2_pct_change = (open_prices[ticker2][day] - open_prices[ticker2][day-1]) / open_prices[ticker2][day-1]
            
            # After that, determine from the dataframe which stock had a higher percent change
            # lets say A and B are correlated, if A goes up more than B goes down above a certain constant (e), buy A; if A goes up smaller than B went down, short A
            if ticker1_pct_change > 0 and ticker2_pct_change < 0 and ((ticker1_pct_change - abs(ticker2_pct_change)) > min_change_percent):
                # buy ticker 1
                amt_to_buy = (buy_percentage * 25000) // open_prices[ticker1][day+1]
                if amt_to_buy * open_prices[ticker1][day+1] > cash_balance:
                    amt_to_buy = cash_balance // open_prices[ticker1][day+1]
                
                trades[ticker1][day+1] = amt_to_buy
                positions[ticker1] += amt_to_buy
                cash_balance -= (amt_to_buy * open_prices[ticker1][day+1])

            elif ticker1_pct_change < 0 and ticker2_pct_change > 0 and ((ticker2_pct_change - (abs(ticker1_pct_change))) > min_change_percent):
                # buy ticker 2
                amt_to_buy = (buy_percentage * 25000) // open_prices[ticker1][day+1]
                if amt_to_buy * open_prices[ticker2][day+1] > cash_balance:
                    amt_to_buy = cash_balance // open_prices[ticker2][day+1]
                
                trades[ticker2][day+1] = amt_to_buy
                positions[ticker2] += amt_to_buy
                cash_balance -= (amt_to_buy * open_prices[ticker2][day+1])

            #close out positions if both stocks moving together
            elif ticker1_pct_change > 0 and ticker2_pct_change > 0:
                if positions[ticker1] > 0:
                        trades[ticker1][day+1] = -positions[ticker1]
                        positions[ticker1] = 0
                if positions[ticker2] > 0:
                        trades[ticker2][day+1] = -positions[ticker2]
                        positions[ticker2] = 0
    #close shorts
    for stock in range(len(positions)):
        position = positions[stock]
        if position < 0:
                trades[stock][len(open_prices[0]) - 1] += -position

    np.save("trades.npy", trades)

if __name__ == "__main__":
    #get path
    path = parse_args()
    main(path)