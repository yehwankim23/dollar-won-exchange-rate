package main

import (
	"log"
	"math"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"golang.org/x/net/html"
)

func send(chatId string, function string, text string) error {
	log.Printf("%-16s %-20s %s\n", chatId, function, text)

	_, err := http.Get("https://api.telegram.org/bot" + os.Getenv("bot_token") +
		"/sendMessage?chat_id=" + chatId + "&text=" + text)

	return err
}

func sendLog(function string, log string) {
	send(os.Getenv("user_chat_id"), function, log)
}

func sendMessage(message string) {
	err := send(os.Getenv("channel_chat_id"), "", message)

	if err != nil {
		sendLog("sendMessage", err.Error())
	}
}

func getExchangeRate() (string, float64, bool) {
	function := "getExchangeRate"

	response, err := http.Get(
		"https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW",
	)

	if err != nil {
		sendLog(function, err.Error())
		return "", 0, false
	}

	defer response.Body.Close()

	document, err := html.Parse(response.Body)

	if err != nil {
		sendLog(function, err.Error())
		return "", 0, false
	}

	exchangeRateString := ""

	for node := range document.Descendants() {
		if node.Type == html.ElementNode && node.Data == "td" {
			exchangeRateString = node.FirstChild.Data
			break
		}
	}

	exchangeRateString = strings.TrimSuffix(strings.ReplaceAll(exchangeRateString, ",", ""), "0")
	exchangeRateFloat, err := strconv.ParseFloat(exchangeRateString, 64)

	if err != nil {
		sendLog(function, err.Error())
		return "", 0, false
	}

	return exchangeRateString, math.Floor(exchangeRateFloat / 5), true
}

func main() {
	function := "main"

	_, ok := os.LookupEnv("bot_token")

	if !ok {
		sendLog(function, "Bot token is missing")
		return
	}

	_, ok = os.LookupEnv("user_chat_id")

	if !ok {
		sendLog(function, "User chat ID is missing")
		return
	}

	_, ok = os.LookupEnv("channel_chat_id")

	if !ok {
		sendLog(function, "Channel chat ID is missing")
		return
	}

	_, previousFloor, ok := getExchangeRate()

	if !ok {
		return
	}

	sendMessage("Program started")

	checkExchangeRate := true
	checkRunning := true

	for {
		time.Sleep(30 * time.Second)

		now := time.Now().UTC().Add(time.Hour * 9)

		if now.Minute()%15 == 0 {
			if checkExchangeRate {
				checkExchangeRate = false

				exchangeRate, currentFloor, ok := getExchangeRate()

				if !ok {
					break
				}

				if currentFloor != previousFloor {
					triangle := "△"

					if currentFloor < previousFloor {
						triangle = "▽"
					}

					sendMessage(triangle + " " + exchangeRate + " 원")
				}

				previousFloor = currentFloor
			}
		} else {
			checkExchangeRate = true
		}

		if now.Hour()%6 == 0 {
			if checkRunning {
				checkRunning = false

				sendLog(function, "Program running")
			}
		} else {
			checkRunning = true
		}
	}

	sendMessage("Program stopped")
}
