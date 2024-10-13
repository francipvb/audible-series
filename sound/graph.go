package sound

import (
	"slices"
	"time"

	"github.com/IBM/fp-go/array"
	"github.com/IBM/fp-go/function"
	"github.com/gopxl/beep/v2"
)

type SoundGraph struct {
	Series     []SoundSeries
	SideSeries []SoundSeries
	BaseFreq   float64
	FreqRange  float64
}

func (g *SoundGraph) MinValue(nLast int) float64 {
	return function.Pipe2(
		g.Series,
		array.Map(func(s SoundSeries) float64 {
			return s.MinValue(nLast)
		}),
		slices.Min,
	)
}

func (g *SoundGraph) MaxValue(nLast int) float64 {
	return function.Pipe2(
		g.Series,
		array.Map(func(s SoundSeries) float64 {
			return s.MaxValue(nLast)
		}),
		slices.Max,
	)
}

func (g *SoundGraph) Render(nValues int, duration time.Duration, generator SoundGenerator) (beep.Streamer, error) {
	var streams []beep.Streamer
	minValue, maxValue := g.MinValue(nValues), g.MaxValue(nValues)
	minFreq := g.BaseFreq
	maxFreq := minFreq + g.FreqRange
	for _, series := range g.Series {
		stream, err := series.Generate(minFreq, maxFreq, minValue, maxValue, nValues, duration, generator)
		if err != nil {
			return nil, err
		}
		streams = append(streams, stream)

	}
	for _, series := range g.SideSeries {
		stream, err := series.Generate(minFreq, maxFreq, series.MinValue(nValues), series.MaxValue(nValues), nValues, duration, generator)
		if err != nil {
			return nil, err
		}
		streams = append(streams, stream)
	}

	return beep.Mix(streams...), nil
}
