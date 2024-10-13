package main

import (
	"audible-series/sound"
	"context"
	"fmt"
	"os"
	"path"
	"strconv"
	"time"

	"github.com/adshao/go-binance/v2/futures"
	"github.com/gopxl/beep/v2"
	"github.com/gopxl/beep/v2/wav"
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
	klines, err := klinesService.Symbol("BTCUSDT").Interval("1d").Do(context.Background())
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
	upperband, _, lowerband := talib.BBands(prices, 20, 2, 2, talib.SMA)
	rsi := talib.Rsi(prices, 14)

	chart := sound.SoundGraph{
		Series: []sound.SoundSeries{
			sound.NewPitchSoundSeries(upperband, sound.SineWave, 0.2, -4),
			sound.NewPitchSoundSeries(lowerband, sound.SineWave, -0.2, -4),
			// sound.NewPitchSoundSeries(prices, sound.SquareWave, 0, -3),
		},
		SideSeries: []sound.SoundSeries{
			sound.NewFixedRangePitchSeries(rsi, 0, 100, 0, -1, sound.TriangleWave),
		},
		BaseFreq:  200,
		FreqRange: 600,
	}

	stream, err := chart.Render(300, time.Millisecond*100, *pc.Generator())
	if err != nil {
		panic(err)
	}

	pc.PlayAndWait(stream)
	workingDir, err := os.Getwd()
	if err != nil {
		panic(err)
	}

	fileStream, err := os.OpenFile(path.Join(workingDir, "muestra.wav"), os.O_CREATE|os.O_RDWR, os.ModePerm)
	if err != nil {
		panic(err)
	}
	defer fileStream.Close()
	stream, err = chart.Render(30, time.Millisecond*300, *pc.Generator())
	if err != nil {
		client.Logger.Panic(err)
	}
	wav.Encode(fileStream, stream, beep.Format{SampleRate: pc.SampleRate(), NumChannels: 2, Precision: 2})
}
