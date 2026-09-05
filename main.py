import datetime
import os
import time

import bs4
import requests

BOT_TOKEN = None
USER_CHAT_ID = None
CHANNEL_CHAT_ID = None


def get_exception(function, text):
    return Exception(f"[{function}] {text}")


def get_env(key):
    function = "get_env"

    if key is None:
        raise get_exception(function, "`key` is None")

    value = os.getenv(key)

    if value is None:
        raise get_exception(function, f"`os.getenv('{key}')` is None")

    return value


def send(chat_id, text):
    global BOT_TOKEN

    function = "send"

    response = requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        {"chat_id": chat_id, "text": text}
    )

    if not response.ok:
        raise get_exception(function, response.json().get("description"))

    response = response.json().get("result").get("text")

    if response != text:
        raise get_exception(function, response)

    print(text)


def send_log(log):
    global USER_CHAT_ID

    send(USER_CHAT_ID, log)


def send_message(message):
    global CHANNEL_CHAT_ID

    send(CHANNEL_CHAT_ID, message)


def get_exchange_rate():
    response = requests.get(
        "https://finance.naver.com/marketindex/exchangeDetail.naver",
        {"marketindexCd": "FX_USDKRW"}
    )

    soup = bs4.BeautifulSoup(response.text, "html.parser")
    td = soup.find("td")
    exchange_rate = str(td.contents[0])

    exchange_rate_string = exchange_rate.removesuffix("0")
    exchange_rate_float = float(exchange_rate_string.replace(",", ""))

    return exchange_rate_string, exchange_rate_float


def main():
    global BOT_TOKEN, USER_CHAT_ID, CHANNEL_CHAT_ID

    # noinspection PyBroadException
    try:
        BOT_TOKEN = get_env("bot_token")
        USER_CHAT_ID = get_env("user_chat_id")
        CHANNEL_CHAT_ID = get_env("channel_chat_id")

        _, previous_float = get_exchange_rate()
        previous_float += 2.5
        previous_division = previous_float // 5

        send_log("Program started")

        check_exchange_rate = True
        check_running = True
    except Exception as exception:
        try:
            send_log(str(exception))
        finally:
            print(exception)

        return

    while True:
        # noinspection PyBroadException
        try:
            now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

            if now.minute % 15 == 0:
                if check_exchange_rate:
                    check_exchange_rate = False

                    current_string, current_float = get_exchange_rate()
                    current_float += 2.5
                    current_division = current_float // 5
                    current_modulo = current_float % 5
                    difference = current_division - previous_division

                    if (difference == 1 and current_modulo >= 2.5) or difference > 1:
                        send_message(f"△ {current_string} 원")
                        previous_division = current_division
                    elif (difference == -1 and current_modulo < 2.5) or difference < -1:
                        send_message(f"▼ {current_string} 원")
                        previous_division = current_division
            else:
                check_exchange_rate = True

            if now.hour == 12:
                if check_running:
                    check_running = False

                    send_log("Program running")
            else:
                check_running = True

            time.sleep(30)
        except Exception as exception:
            try:
                send_log(str(exception))
            finally:
                print(exception)


if __name__ == "__main__":
    main()
