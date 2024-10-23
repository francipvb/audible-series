import numpy as np
import pyaudio

from audible_plot.generators import AudioBuffer


class AudioPlayer:
    def __init__(self) -> None:
        self._pyaudio = pyaudio.PyAudio()

    def play_raw(self, buffer: AudioBuffer) -> None:
        stream = self._pyaudio.open(
            rate=44100,
            channels=2,
            format=pyaudio.paFloat32,
            output=True,
            start=True,
        )
        stream.write(buffer.astype(np.float32).tobytes())
        stream.close()
