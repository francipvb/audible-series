package sound

import "github.com/gopxl/beep/v2"

type DataMapper struct {
	Wave       WaveForm
	SampleRate beep.SampleRate
	MinFreq    float64
	MaxFreq    float64
}
