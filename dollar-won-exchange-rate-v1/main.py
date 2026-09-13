import datetime
import sys
import time
import traceback

import bs4
import requests
import telegram
import telegram.ext

CHAT_ID = int("")
TOKEN = ""
PASSWORD = ""

BOT = telegram.Bot(TOKEN)

pong = True
run_program = True

URL = "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW"

CHANNEL_ID = "@dwexr"


def send_message(text: str, chat_id: int | str = CHAT_ID) -> None:
    BOT.send_message(chat_id, text)


def send_error_message() -> None:
    global pong

    stack_traces = traceback.format_exc().splitlines()
    message = stack_traces[1].strip() + "()\n\n" + stack_traces[2].strip() + "\n\n"

    if len(stack_traces) > 4:
        message += stack_traces[3].strip() + "()\n\n" + stack_traces[4].strip() + "\n\n"

    send_message(message + stack_traces[-1])
    pong = True


def ping(update: telegram.Update, _: telegram.ext.CallbackContext) -> None:
    global pong

    # noinspection PyBroadException
    try:
        if update.effective_chat.id == CHAT_ID:
            pong = True
    except Exception:
        send_error_message()


def pause(update: telegram.Update, context: telegram.ext.CallbackContext) -> None:
    global run_program

    # noinspection PyBroadException
    try:
        if update.effective_chat.id != CHAT_ID:
            return

        # noinspection PyBroadException
        try:
            password = context.args[0]
        except Exception:
            send_message("Syntax: /pause [password]")
            return

        if password != PASSWORD:
            send_message("Incorrect password")
            return

        run_program = False
        send_message("Program paused")
    except Exception:
        send_error_message()


def resume(update: telegram.Update, context: telegram.ext.CallbackContext) -> None:
    global run_program

    # noinspection PyBroadException
    try:
        if update.effective_chat.id != CHAT_ID:
            return

        # noinspection PyBroadException
        try:
            password = context.args[0]
        except Exception:
            send_message("Syntax: /resume [password]")
            return

        if password != PASSWORD:
            send_message("Incorrect password")
            return

        run_program = True
        send_message("Program resumed")
    except Exception:
        send_error_message()


def get_exchange_rate() -> str:
    soup = bs4.BeautifulSoup(requests.get(URL).text, "html.parser")
    container = soup.find("div", recursive=False, id="container")
    content = container.find("div", recursive=False, id="content")
    section = content.find("div", class_="section_calculator", recursive=False)
    table = section.find("table", recursive=False)
    tbody = table.find("tbody", recursive=False)
    tr = tbody.find("tr", recursive=False)
    td = tr.find("td", recursive=False)
    return str(td.contents[0])[:-1]


def main() -> None:
    global run_program, pong

    # noinspection PyBroadException
    try:
        check_exchange_rate = True
        check_running = True

        exchange_rate = get_exchange_rate()
        previous_floor = float(exchange_rate.replace(",", "")) // 5

        updater = telegram.ext.Updater(TOKEN)
        dispatcher = updater.dispatcher

        dispatcher.add_handler(telegram.ext.CommandHandler("ping", ping))
        dispatcher.add_handler(telegram.ext.CommandHandler("pause", pause))
        dispatcher.add_handler(telegram.ext.CommandHandler("resume", resume))

        updater.start_polling()
        send_message("Program started")
    except Exception:
        send_error_message()
        send_message("Program stopped")
        sys.exit(-1)

    while True:
        # noinspection PyBroadException
        try:
            time.sleep(3)

            if not run_program:
                continue

            today = datetime.datetime.now()

            if today.minute % 15 == 0:
                if check_exchange_rate:
                    check_exchange_rate = False

                    exchange_rate = get_exchange_rate()
                    current_floor = float(exchange_rate.replace(",", "")) // 5

                    if current_floor != previous_floor:
                        send_message(("▽" if current_floor < previous_floor else "△") + " "
                                     + exchange_rate + " 원", CHANNEL_ID)

                    previous_floor = current_floor
            else:
                check_exchange_rate = True

            if today.hour in [9, 15, 21]:
                if check_running:
                    check_running = False
                    send_message("Program running")
            else:
                check_running = True

            if pong:
                pong = False
                send_message("Pong")
        except Exception:
            send_error_message()


if __name__ == "__main__":
    main()
