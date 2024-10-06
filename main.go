package main

import (
	"context"
	"fmt"
	"strconv"
	"time"

	"github.com/adshao/go-binance/v2/futures"
	"github.com/gopxl/beep/v2"
	"github.com/gopxl/beep/v2/speaker"
	"github.com/markcheno/go-talib"
)

func main() {
	// Inicia el sistema de audio
	sr := beep.SampleRate(44100)
	if err := speaker.Init(sr, 1024); err != nil {
		panic(err)
	}

	client := futures.NewClient("", "")
	klinesService := client.NewKlinesService()
	klines, err := klinesService.Symbol("BTCUSDT").Interval("4h").Do(context.Background())
	if err != nil {
		fmt.Println(err)
		return
	}
	prices := make([]float64, 00, 100)
	for _, i := range klines {
		x, err := strconv.ParseFloat(i.Close, 64)
		if err != nil {
			fmt.Println(err)
			return
		}
		prices = append(prices, x)
	}

	// Crea un nuevo pitchIndicator
	pitchInd := pitchIndicator{
		Values:          talib.Sma(prices, 20),
		MaxFreq:         700,
		MinFreq:         300,
		Sr:              sr,
		NValues:         30,
		ToneDuration:    time.Millisecond * 300,
		SilenceDuration: time.Millisecond * 100,
	}

	// Reproduce el flujo continuo
	speaker.PlayAndWait(beep.Take(sr.N(time.Millisecond*300), pitchInd.RefMax()))
	speaker.PlayAndWait(beep.Take(sr.N(time.Millisecond*200), pitchInd.RefMin()))
	speaker.PlayAndWait(pitchInd.Render())
}
