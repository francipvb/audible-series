package main

import (
	"sync"
	"time"

	"github.com/gopxl/beep/v2"
	"github.com/gopxl/beep/v2/generators"
)

type AudibleIndicator interface {
	RefMax() beep.Streamer
	RefMin() beep.Streamer
	Render() beep.Streamer
}

type pitchIndicator struct {
	Values          []float64
	MaxFreq         float64
	MinFreq         float64
	Sr              beep.SampleRate
	mu              sync.Mutex
	NValues         int
	ToneDuration    time.Duration
	SilenceDuration time.Duration
}

// RefMax implements AudibleIndicator.
func (p *pitchIndicator) RefMax() beep.Streamer {
	return p.getTone(p.MaxFreq)
}

// RefMin implements AudibleIndicator.
func (p *pitchIndicator) RefMin() beep.Streamer {
	return p.getTone(p.MinFreq)
}

// Render implements AudibleIndicator.
func (p *pitchIndicator) Render() beep.Streamer {
	if p == nil {
		return nil
	}
	if len(p.Values) < p.NValues {
		return nil
	}

	values := p.Values[len(p.Values)-p.NValues:]
	tones := make([]beep.Streamer, 0, 10)
	for _, v := range values {
		// Renderizar los valores, uno a uno
		tones = append(
			tones,
			p.getTone(p.getFreq(v)),
			generators.Silence(p.Sr.N(p.SilenceDuration)),
		)
	}
	return beep.Seq(tones...)
}

// Update implements AudibleIndicator.
func (p *pitchIndicator) Update(v float64) {
	if p == nil {
		return
	}
	p.mu.Lock()
	defer p.mu.Unlock()
	p.Values = append(p.Values, v)
	p.Values = append(p.Values, v)
}

func (p *pitchIndicator) getTone(freq float64) beep.Streamer {
	nSamples := p.Sr.N(p.ToneDuration)
	tone, err := generators.TriangleTone(p.Sr, freq)
	if err != nil {
		return generators.Silence(nSamples)
	}

	return beep.Take(nSamples, tone)
}

func (p *pitchIndicator) getFreq(value float64) float64 {
	if p == nil {
		return 0
	}
	if len(p.Values) <= p.NValues {
		return p.MinFreq
	}
	values := p.Values[len(p.Values)-p.NValues-1:]
	minValue, maxValue := getMin(values), getMax(values)
	valueDelta := maxValue - minValue
	freqDelta := p.MaxFreq - p.MinFreq
	ret := p.MinFreq + (freqDelta/valueDelta)*(value-minValue)
	return ret
}

func getMax(f []float64) float64 {
	if len(f) == 0 {
		return 0
	}
	ret := f[0]
	for _, i := range f {
		ret = max(ret, i)
	}
	return ret
}

func getMin(f []float64) float64 {
	if len(f) == 0 {
		return 0
	}
	ret := f[0]
	for _, i := range f {
		ret = min(ret, i)
	}
	return ret
}

func NewPitchIndicator(minFreq, maxFreq float64, sr beep.SampleRate, nValues int) AudibleIndicator {
	return &pitchIndicator{
		MinFreq: minFreq,
		MaxFreq: maxFreq,

		Sr:      sr,
		Values:  make([]float64, 0, 100),
		NValues: nValues,
	}
}
