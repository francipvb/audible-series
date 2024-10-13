package sound

import (
	"github.com/gopxl/beep/v2"
	"github.com/gopxl/beep/v2/speaker"
)

type PlaybackController struct {
	sr beep.SampleRate
}

func NewPlaybackController(sr beep.SampleRate, bufferSize int) PlaybackController {
	pc := PlaybackController{
		sr: sr,
	}
	speaker.Init(sr, bufferSize)
	return pc
}

func (pc *PlaybackController) Play(s ...beep.Streamer) {
	speaker.Play(s...)
}

func (pc *PlaybackController) Generator() *SoundGenerator {
	return &SoundGenerator{sampleRate: pc.sr}
}

func (pc *PlaybackController) PlayAndWait(s ...beep.Streamer) {
	speaker.PlayAndWait(s...)
}

func (pc *PlaybackController) SampleRate() beep.SampleRate {
	return pc.sr
}
