import yfinance
import pandas_ta as pdta
from alpaca_settings import *
import alpaca_trade_api as alpaca
from telegram_messenger import *
from stocks import *
from LSTM_pred import *
import numpy as np


def Trade(api, stock, op, shares2trade, take_profit, stop_loss):
    api.submit(symbol=stock, qty=shares2trade, side=op, type='market', order_class='bracket', time_in_force='day',
               take_profit={'limit_price': take_profit}, stop_loss={'stop_price': stop_loss})
    message = "\n\t {0}, quantity: {1}, \n\t\t were {2}".format(stock, shares2trade, op)
    send_message("{0}: entered the market with ".format(TRADER_NAME) + message)
    # f'{TRADER_NAME}: we entered the market with:' + message)
    return True


def trader_start(request):
    trader = alpaca.REST(TRADER_API_KEY, TRADER_API_SECRET, TRADER_API_URL)
    account = trader.get_account()
    clock = trader.get_clock()

    if bool(account):
        message = "{0} for *{1}* ; current capital is ${2} and non-marginable buying power is ${3}" \
            .format(TRADER_NAME, account.account_number, account.portfolio_value, account.non_marginable_buying_power)
        # message = f'''{TRADER_NAME}: for *{account.account_number}*current capital is _{account.portfolio_value}$_and
        # non marginable buying power is _{account.non_marginable_buying_power}$_ '''
        send_message(message)

    if clock.is_open:
        if account.non_marginable_buying_power < CASH_LIMIT:
            message = "{0} : No Cash or limit exceeded".format(TRADER_NAME)
            send_message(message)
        else:
            screened = ScreenStocks(trader)
            if len(screened):
                CASH_FOR_TRADE_PER_SHARE = (account.non_marginable_buying_power - CASH_LIMIT) / len(screened)
                for item in screened:
                    predictions = predict(df=item['stock'], fetch=None)
                    STOCK = item['stock']
                    OPERATION = 'buy' if item['direction'] == 'UP' else 'sell'
                    STOP_LOSS = min([item['stop_loss']] + predictions) if item['direction'] == 'UP' \
                        else max([item['stop_loss']] + predictions)
                    TAKE_PROFIT = max([item['take_profit']] + predictions) if item['direction'] == 'UP' \
                        else min([item['take_profit']] + predictions)
                    SHARE_PRICE = round(min(STOP_LOSS, TAKE_PROFIT), 2)
                    SHARES_TO_TRADE = np.floor(CASH_FOR_TRADE_PER_SHARE / SHARE_PRICE)
                    try:
                        if abs(STOP_LOSS - TAKE_PROFIT) > SHARE_PRICE * TAKE_PROFIT_DELTA and SHARES_TO_TRADE > 0:
                            Trade(alpaca, STOCK, OPERATION, SHARES_TO_TRADE, TAKE_PROFIT, STOP_LOSS)
                            print('{0}: {1}, {2}, {3}, {4}'.format(STOCK, STOP_LOSS, TAKE_PROFIT, OPERATION,
                                                                   SHARES_TO_TRADE))
                    except ValueError:
                        print('Trade Error')

    portfolio = trader.list_positions()
    if portfolio:
        message = "{0}: We have {1} open positions".format(TRADER_NAME, len(portfolio))
        for i in portfolio:
            message = message + "\n\t {0}: quantity:{1} {2} for {3} \n\t\t\t current price {4} \n\t\t profit {5}" \
                .format(i.symbol, i.qty, i.side, i.market_value, i.current_price, i.unrealized_pl)
        send_message(message)

    if not clock.is_open:
        message = "{0}: The market is *CLOSED*, try again later".format(TRADER_NAME)
        send_message(message)

    return "{0}: DONE!".format(TRADER_NAME)


if __name__=='__main__':
    trader_start({})
