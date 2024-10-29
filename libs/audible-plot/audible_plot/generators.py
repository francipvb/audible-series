from datetime import timedelta
from enum import IntEnum, auto
from typing import Literal, Sequence, TypeAlias

import numpy as np

AudioBuffer: TypeAlias = np.ndarray[tuple[int, Literal[2]], np.dtypes.Float64DType]


class ToneGenerator:
    class WaveType(IntEnum):
        sine = auto()
        square = auto()
        triangle = auto()
        sawtooth = auto()

    def __init__(self, wave_type: WaveType = WaveType.sine) -> None:
        self._wave_type = wave_type

    def generate_wave(
        self,
        sample_rate: float,
        duration: timedelta,
        freq_points: Sequence[float],
    ) -> AudioBuffer:
        freq_points = list(freq_points)
        if len(freq_points) == 1:
            freq_points.append(freq_points[0])
        sample_duration = duration.total_seconds()
        raw_duration = sample_duration * (len(freq_points) - 1)
        wave_size = int(raw_duration * sample_rate)
        t = np.linspace(0, raw_duration, wave_size, endpoint=False)
        freq = np.zeros((wave_size,))
        wave = np.zeros((wave_size,))
        for freq_idx, freq_value in enumerate(freq_points):
            if freq_idx == 0:
                continue
            freq_start = freq_points[freq_idx - 1]
            freq_end = freq_value
            pos_start = int((freq_idx - 1) * sample_rate * sample_duration)
            pos_end = int(freq_idx * sample_rate * sample_duration)
            t[pos_start:pos_end] = np.linspace(
                0,
                sample_duration,
                int(sample_duration * sample_rate),
                endpoint=False,
            )
            freq[pos_start:pos_end] = freq_start + (freq_end - freq_start) * (
                t[pos_start:pos_end] / sample_duration / 2
            )

            freq_start = freq_end

        if self._wave_type in (self.WaveType.sine, self.WaveType.square):
            wave = np.sin(2 * np.pi * freq * t)
        elif self._wave_type in (self.WaveType.sawtooth, self.WaveType.triangle):
            wave = 2 * (t * freq - np.floor(0.5 + t * freq))

        if self._wave_type == self.WaveType.square:
            wave = np.sign(wave)
        elif self._wave_type == self.WaveType.triangle:
            wave = 2 * np.abs(wave) - 1

        return np.column_stack((wave, wave))  # type: ignore
