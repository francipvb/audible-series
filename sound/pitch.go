package sound

import (
	"math"
	"time"

	"github.com/gopxl/beep/v2"
)

type PitchSoundSeries struct {
	ValueRange
	PanRange float64
	Volume   float64
	Wave     WaveForm
}

func NewPitchSoundSeries(values []float64, waveform WaveForm, panRange float64, volume float64) *PitchSoundSeries {
	return &PitchSoundSeries{
		ValueRange: &dynamicRangeSeries{
			rawSeries: rawSeries{values: values},
		},
		Wave:     waveform,
		PanRange: panRange,
		Volume:   volume,
	}
}

func NewFixedRangePitchSeries(values []float64, minValue, maxValue, panRange, volume float64, waveForm WaveForm) *PitchSoundSeries {
	return &PitchSoundSeries{
		ValueRange: &fixedRangeSeries{
			rawSeries: rawSeries{
				values: values,
			},
			minValue: minValue,
			maxValue: maxValue,
		},
		PanRange: panRange,
		Volume:   volume,
		Wave:     waveForm,
	}
}

func (s *PitchSoundSeries) Generate(minFreq, maxFreq, minValue, maxValue float64, nValues int, duration time.Duration, generator SoundGenerator) (beep.Streamer, error) {
	var tones []beep.Streamer
	values := s.Values(nValues)

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
			tone, err = generator.Generate(SilenceWave, 0, duration, s.PanRange, s.Volume)
		} else {
			tone, err = generator.Generate(s.Wave, freq, duration, s.PanRange, s.Volume)
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
