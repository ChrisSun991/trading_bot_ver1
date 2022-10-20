import yfinance
import pandas_ta as pdta
from alpaca_settings import *
import alpaca_trade_api as alpaca


def CheckStock(stock) -> {}:
    data = {}
    try:
        df = yfinance.download(stock, period=SCREEN_PERIOD, interval=SCREEN_INTERVAL)
        if len(df) > 0:
            df['RSI'] = pdta.rsi(df['Close'], timeperiod=14)
            bollinger = pdta.bbands(df['Close'], length=20, std=2)
            df['L_BB'] = bollinger['BBL_20_2.0']
            df['M_BB'] = bollinger['BBM_20_2.0']
            df['U_BB'] = bollinger['BBU_20_2.0']

            third_last_bar = df[-3:-2]
            second_last_bar = df[-2:-1]
            current_bar = df[-1:]

            if current_bar['RSI'].values[0] > 70 and current_bar['Close'].values[0] > current_bar['U'].values[0]:
                data = {'direction': 'DOWN', 'stock': stock, 'stop_loss': round(
                    max(second_last_bar['High'].values[0], third_last_bar['High'].values[0],
                        second_last_bar['U'].values[0]),
                    2), 'take_profit': round(min(second_last_bar['Low'].values[0], third_last_bar['Low'].values[0],
                                                 second_last_bar['M'].values[0]), 2)}
            elif current_bar['RSI'].values[0] < 30 and current_bar['Close'].values[0] < current_bar['L'].values[0]:
                data = {'direction': 'UP', 'stock': stock, 'stop_loss': round(
                    min(second_last_bar['Low'].values[0], third_last_bar['Low'].values[0],
                        second_last_bar['L'].values[0]), 2),
                        'take_profit': round(
                            max(second_last_bar['High'].values[0], third_last_bar['High'].values[0],
                                second_last_bar['M'].values[0]), 2)}
    except ValueError:
        print('Error generating statistics')

    return data


def ScreenStocks(trader: alpaca):
    assets = trader.list_assets(status='active')#, asset_class='us_equity')
    assets = [x for x in assets if x.shortable and x.exchange == 'NASDAQ']
    stocks = [x.symbol for x in assets][:SCREEN_NASDAQ_COUNT]

    screened = []
    for st in stocks:
        _stock = CheckStock(st)
        if _stock != {}:
            screened.append(_stock)
    screened = [x for x in screened if
                abs(x['stop_loss'] - x['take_profit'] > min(x['stop_loss'], x['take_profit']) * TAKE_PROFIT_DELTA)]
    return screened
