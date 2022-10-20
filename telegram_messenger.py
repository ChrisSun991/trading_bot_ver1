import requests
from alpaca_settings import *


def send_message(message):
    resp = requests.post(
        "{0}/{1}/sendMessage?chat_id={2}&parse_mode=Markdown&text={3}".format(TELEGRAM_URL, TELEGRAM_BOT_ID,
                                                                              TELEGRAM_CHAN_ID, message))
    return resp
