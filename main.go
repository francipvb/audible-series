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
	// Inicia el sistema de audio.
	//
	// Internamente, se usa oto para la reproducción.
	sr := beep.SampleRate(44100)
	if err := speaker.Init(sr, 1024); err != nil {
		panic(err)
	}

	// Nos conectamos a la API de binance futures para obtener los últimos precios de cierre del par BTC-USDT:
	client := futures.NewClient("", "")
	klinesService := client.NewKlinesService()
	klines, err := klinesService.Symbol("BTCUSDT").Interval("4h").Do(context.Background())
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

	// Este struct genera streams audibles de una serie de datos:
	pitchInd := pitchIndicator{
		// Calculamos la SMA y la proveemos
		Values: talib.Sma(prices, 20),

		// Frecuencias mínima y máxima:
		MinFreq: 300,
		MaxFreq: 700,

		// Samplerate del sonido, importante para generar las muestras
		Sr: sr,

		// Cuantos valores se van a reproducir, esto también determina cuanto se suaviza la diferencia entre las señales
		NValues: 30,

		// Duración de los tonos
		ToneDuration: time.Millisecond * 300,

		// Duración de los espacios en silencio
		SilenceDuration: time.Millisecond * 100,
	}

	// Primero reproducimos los marcadores
	speaker.PlayAndWait(beep.Take(sr.N(time.Millisecond*300), pitchInd.RefMax()))
	speaker.PlayAndWait(beep.Take(sr.N(time.Millisecond*200), pitchInd.RefMin()))

	// Y la muestra
	speaker.PlayAndWait(pitchInd.Render())
}
