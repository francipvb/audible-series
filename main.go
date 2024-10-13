package main

import (
	"audible-series/sound"
	"context"
	"fmt"
	"strconv"
	"time"

	"github.com/adshao/go-binance/v2/futures"
	"github.com/markcheno/go-talib"
)

func main() {
	// Inicia el sistema de audio.
	//
	// Internamente, se usa oto para la reproducción.
	pc := sound.NewPlaybackController(44100, 4096)
	// Nos conectamos a la API de binance futures para obtener los últimos precios de cierre del par BTC-USDT:
	client := futures.NewClient("", "")
	klinesService := client.NewKlinesService()
	klines, err := klinesService.Symbol("BTCUSDT").Interval("1m").Do(context.Background())
	if err != nil {
		fmt.Println(err)
		return
	}

	// Tenemos los datos, ahora sacar lo que nos interesa, los precios de ciere
	prices := make([]float64, 00, 100)
	for _, i := range klines {
		price, err := strconv.ParseFloat(i.Close, 64)
		if err != nil {
			fmt.Println(err)
			return
		}
		prices = append(prices, price)
	}

	chart := sound.SoundGraph{
		Series: []sound.SoundSeries{
			{
				Values:    talib.Ema(prices, 20),
				PanRange:  0.5,
				Wave:      sound.SineWave,
				Generator: *pc.Generator(),
				Volume:    -1,
			},
			{
				Values:    talib.Ema(prices, 200),
				PanRange:  -0.5,
				Wave:      sound.TriangleWave,
				Generator: *pc.Generator(),
				Volume:    -1,
			},
		},
		BaseFreq:  200,
		FreqRange: 600,
	}

	stream, err := chart.Render(300, time.Millisecond*100)
	if err != nil {
		panic(err)
	}

	pc.PlayAndWait(stream)
}
