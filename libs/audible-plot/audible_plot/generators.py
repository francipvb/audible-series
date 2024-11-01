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

    def generate_sliding(
        self,
        sample_rate: float,
        duration: timedelta,
        freq_points: Sequence[float],
    ) -> AudioBuffer:
        freq_points = list(freq_points)

        if len(freq_points) == 1:
            freq_points.append(freq_points[0])
        sample_duration = duration.total_seconds()
        sample_size = int(sample_duration * sample_rate)
        raw_duration = sample_duration * (len(freq_points) - 1)
        wave_size = int(raw_duration * sample_rate)
        freq = np.zeros((wave_size,))
        wave = np.zeros((wave_size,))
        for freq_idx, freq_value in enumerate(freq_points):
            if freq_idx == 0:
                continue
            freq_start = freq_points[freq_idx - 1]
            freq_end = freq_value
            pos_start = int((freq_idx - 1) * sample_rate * sample_duration)
            pos_end = int(freq_idx * sample_rate * sample_duration)
            freq[pos_start:pos_end] = np.linspace(freq_start, freq_end, sample_size)

        phase = 2 * np.pi * np.cumsum(freq) / sample_rate
        if self._wave_type in (self.WaveType.sine, self.WaveType.square):
            wave = np.sin(phase)
        elif self._wave_type in (self.WaveType.sawtooth, self.WaveType.triangle):
            wave = 2 * (phase / (2 * np.pi) - np.floor(phase / (2 * np.pi) + 0.5))

        if self._wave_type == self.WaveType.square:
            wave = np.sign(wave)
        elif self._wave_type == self.WaveType.triangle:
            wave = 2 * np.abs(wave) - 1

        return np.column_stack((wave, wave))  # type: ignore

    def generate_fixed(
        self,
        sample_rate: float,
        duration: timedelta,
        freq_points: Sequence[float],
    ) -> AudioBuffer:
        freq_points = list(freq_points)

        sample_duration = duration.total_seconds()
        sample_size = int(sample_duration * sample_rate)
        raw_duration = sample_duration * (len(freq_points))
        wave_size = int(raw_duration * sample_rate)
        freq = np.zeros((wave_size,))
        wave = np.zeros((wave_size,))
        for freq_idx, freq_value in enumerate(freq_points):
            pos_start = int(freq_idx * sample_size)
            pos_end = int((freq_idx + 1) * sample_rate * sample_duration)
            freq[pos_start:pos_end] = freq_value

        phase = 2 * np.pi * np.cumsum(freq) / sample_rate
        if self._wave_type in (self.WaveType.sine, self.WaveType.square):
            wave = np.sin(phase)
        elif self._wave_type in (self.WaveType.sawtooth, self.WaveType.triangle):
            wave = 2 * (phase / (2 * np.pi) - np.floor(phase / (2 * np.pi) + 0.5))

        if self._wave_type == self.WaveType.square:
            wave = np.sign(wave)
        elif self._wave_type == self.WaveType.triangle:
            wave = 2 * np.abs(wave) - 1

        return np.column_stack((wave, wave))  # type: ignore
