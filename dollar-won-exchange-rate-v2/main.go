package main

import (
	"encoding/json"
	"log"
	"math"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"golang.org/x/net/html"
)

type DataJson struct {
	PreviousDivision int `json:"previousDivision"`
}

func send(chatId string, function string, text string) error {
	log.Printf("%-16s %-24s %s\n", chatId, function, text)

	_, err := http.Get("https://api.telegram.org/bot" + os.Getenv("bot_token") +
		"/sendMessage?chat_id=" + chatId + "&text=" + text)

	return err
}

func sendLog(function string, log string) {
	send(os.Getenv("user_chat_id"), function, log)
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

	return exchangeRateString, exchangeRateFloat, true
}

func savePreviousDivision(previousDivision int) {
	function := "savePreviousDivision"

	dataJson := DataJson{
		PreviousDivision: previousDivision,
	}

	dataBytes, err := json.Marshal(dataJson)

	if err != nil {
		sendLog(function, err.Error())
		return
	}

	err = os.WriteFile("./data/data.json", dataBytes, 0600)

	if err != nil {
		sendLog(function, err.Error())
		return
	}
}

func sendMessage(message string) {
	err := send(os.Getenv("channel_chat_id"), "", message)

	if err != nil {
		sendLog("sendMessage", err.Error())
	}
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

	_, previousFloat, ok := getExchangeRate()

	if !ok {
		return
	}

	dataBytes, err := os.ReadFile("./data/data.json")
	var previousDivision int

	if err != nil {
		previousDivision = int(math.Floor(previousFloat / 5))
	} else {
		var dataJson DataJson
		err = json.Unmarshal(dataBytes, &dataJson)

		if err != nil {
			sendLog(function, err.Error())
			return
		}

		previousDivision = dataJson.PreviousDivision
	}

	sendLog(function, "Program started")

	checkExchangeRate := true
	checkRunning := true

	for {
		time.Sleep(30 * time.Second)

		now := time.Now().UTC().Add(time.Hour * 9)

		if now.Minute()%15 == 0 {
			if checkExchangeRate {
				checkExchangeRate = false

				currentString, currentFloat, ok := getExchangeRate()

				if !ok {
					break
				}

				currentFloat += 2.5
				currentDivision := int(math.Floor(currentFloat / 5))
				currentModulo := math.Mod(currentFloat, 5)
				difference := currentDivision - previousDivision

				if (difference == 1 && currentModulo >= 2.5) || difference > 1 {
					previousDivision = currentDivision
					savePreviousDivision(previousDivision)
					sendMessage("△ " + currentString + " 원")
				} else if (difference == -1 && currentModulo < 2.5) || difference < -1 {
					previousDivision = currentDivision
					savePreviousDivision(previousDivision)
					sendMessage("▼ " + currentString + " 원")
				}
			}
		} else {
			checkExchangeRate = true
		}

		if now.Hour() == 12 {
			if checkRunning {
				checkRunning = false

				sendLog(function, "Program running")
			}
		} else {
			checkRunning = true
		}
	}

	sendLog(function, "Program stopped")
}
