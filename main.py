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


def send_message(text: str) -> None:
    BOT.send_message(CHAT_ID, text)


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


def main() -> None:
    global run_program, pong

    # noinspection PyBroadException
    try:
        check = True
        previous_floor = 0

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

            if datetime.datetime.now().minute % 15 == 0:
                if check:
                    check = False
                    soup = bs4.BeautifulSoup(requests.get(URL).text, "html.parser")
                    container = soup.find("div", recursive=False, id="container")
                    content = container.find("div", recursive=False, id="content")
                    section = content.find("div", class_="section_calculator", recursive=False)
                    table = section.find("table", recursive=False)
                    tbody = table.find("tbody", recursive=False)
                    tr = tbody.find("tr", recursive=False)
                    td = tr.find("td", recursive=False)
                    exchange_rate = str(td.contents[0])
                    current_floor = float(exchange_rate.replace(",", "")) // 5

                    if previous_floor != 0 and current_floor != previous_floor:
                        send_message(exchange_rate + "원 "
                                     + "↓" if current_floor < previous_floor else "↑")

                    previous_floor = current_floor
            else:
                check = True

            if pong:
                pong = False
                send_message("Pong")
        except Exception:
            send_error_message()


if __name__ == "__main__":
    main()
