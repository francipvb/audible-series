package sound

import (
	"errors"
	"time"

	"github.com/gopxl/beep/v2"
	"github.com/gopxl/beep/v2/effects"
	"github.com/gopxl/beep/v2/generators"
)

type WaveForm int

const (
	SineWave WaveForm = iota
	SquareWave
	TriangleWave
	SawtoothWave
	ReverseSawtoothWave
	SilenceWave
)

type SoundGenerator struct {
	sampleRate beep.SampleRate
}

func NewGenerator(sr beep.SampleRate) *SoundGenerator {
	return &SoundGenerator{sampleRate: sr}
}

func (g *SoundGenerator) Generate(wave WaveForm, freq float64, duration time.Duration, pan float64, volume float64) (beep.Streamer, error) {
	var generated beep.Streamer
	var err error
	switch wave {
	case SineWave:
		generated, err = generators.SineTone(g.sampleRate, freq)
	case SquareWave:
		generated, err = generators.SquareTone(g.sampleRate, freq)
	case TriangleWave:
		generated, err = generators.TriangleTone(g.sampleRate, freq)
	case SawtoothWave:
		generated, err = generators.SawtoothTone(g.sampleRate, freq)
	case ReverseSawtoothWave:
		generated, err = generators.SawtoothToneReversed(g.sampleRate, freq)
	case SilenceWave:
		return generators.Silence(g.sampleRate.N(duration)), nil
	default:
		return nil, errors.ErrUnsupported
	}
	if err != nil {
		return nil, err
	}

	generated = beep.Take(g.sampleRate.N(duration), generated)
	generated = &effects.Pan{Streamer: generated, Pan: pan}
	generated = &effects.Volume{Streamer: generated, Base: 2, Volume: volume}
	return generated, nil
}
