package sound

import (
	"math"
	"slices"
	"time"

	"github.com/gopxl/beep/v2"
)

type ValueRange interface {
	MinValue(nValues int) float64
	MaxValue(nValues int) float64
	Values(nValues int) []float64
}

type SoundSeries interface {
	ValueRange
	Generate(minFreq, maxFreq, minValue, maxValue float64, nValues int, duration time.Duration, generator SoundGenerator) (beep.Streamer, error)
}

type rawSeries struct {
	values []float64
}

func (rs *rawSeries) Values(nValues int) []float64 {
	var values []float64
	numValues := len(rs.values)
	if numValues < nValues {
		for i := 0; i < nValues-numValues; i++ {
			values = append(values, math.NaN())
		}
		values = append(values, rs.values...)
	} else {
		values = rs.values[numValues-nValues:]
	}
	return values
}

type dynamicRangeSeries struct {
	rawSeries
}

func (s *dynamicRangeSeries) MinValue(nLast int) float64 {
	if len(s.values) < nLast {
		return slices.Min(s.values)
	}
	return slices.Min(s.values[len(s.values)-nLast:])
}

func (s *dynamicRangeSeries) MaxValue(nLast int) float64 {
	if len(s.values) < nLast {
		return slices.Max(s.values)
	}
	return slices.Max(s.values[len(s.values)-nLast:])
}

type fixedRangeSeries struct {
	rawSeries
	minValue float64
	maxValue float64
}

func (f *fixedRangeSeries) MinValue(nValues int) float64 { return f.minValue }
func (f *fixedRangeSeries) MaxValue(nValues int) float64 { return f.maxValue }
