package sound

import (
	"math"
	"slices"
	"time"

	"github.com/gopxl/beep/v2"
)

type SoundSeries struct {
	Values    []float64
	PanRange  float64
	Wave      WaveForm
	Generator SoundGenerator
	Volume    float64
}

func (s *SoundSeries) Min(nLast int) float64 {
	if len(s.Values) < nLast {
		return slices.Min(s.Values)
	}
	return slices.Min(s.Values[len(s.Values)-nLast:])
}

func (s *SoundSeries) Max(nLast int) float64 {
	if len(s.Values) < nLast {
		return slices.Max(s.Values)
	}
	return slices.Max(s.Values[len(s.Values)-nLast:])
}

func (s *SoundSeries) Generate(minFreq, maxFreq, minValue, maxValue float64, nValues int, duration time.Duration) (beep.Streamer, error) {
	var tones []beep.Streamer
	var values []float64
	if len(s.Values) < nValues {
		// Fill with NaN values before the values we have in the series
		for i := 0; i < nValues-len(s.Values); i++ {
			values = append(values, math.NaN())
		}
		values = append(values, s.Values...)
	} else {
		values = s.Values[len(s.Values)-nValues:]
	}

	for _, v := range values {
		freq := calculateFreq(minValue, maxValue, minFreq, maxFreq, v)
		// Avoid very high and very low freqs:
		freqDelta := maxFreq - minFreq
		if freq > maxFreq {
			freq = maxFreq + freqDelta*0.05
		} else if freq < minFreq {
			freq = minFreq - freqDelta*0.05
		}
		var tone beep.Streamer
		var err error
		if math.IsNaN(v) {
			tone, err = s.Generator.Generate(SilenceWave, 0, duration, s.PanRange, s.Volume)
		} else {
			tone, err = s.Generator.Generate(s.Wave, freq, duration, s.PanRange, s.Volume)
		}
		if err != nil {
			return nil, err
		}

		tones = append(tones, tone)
	}

	return beep.Seq(tones...), nil
}

func calculateFreq(minValue, maxValue, minFreq, maxFreq, v float64) float64 {
	valueDelta, freqDelta := maxValue-minValue, maxFreq-minFreq
	if valueDelta == 0 {
		return minFreq
	}
	return minFreq + (freqDelta/valueDelta)*(v-minValue)
}
