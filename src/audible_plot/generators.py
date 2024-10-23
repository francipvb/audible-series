from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Literal, TypeAlias

import numpy as np

AudioBuffer: TypeAlias = np.ndarray[tuple[int, Literal[2]], np.dtypes.Float64DType]


class AbstractToneGenerator(ABC):
    @abstractmethod
    def generate_wave(
        self,
        sample_rate: float,
        duration: timedelta,
        freq_start: float,
        freq_end: float | None = None,
    ) -> AudioBuffer:
        raise NotImplementedError


class SineToneGenerator(AbstractToneGenerator):
    def generate_wave(
        self,
        sample_rate: float,
        duration: timedelta,
        freq_start: float,
        freq_end: float | None = None,
    ) -> AudioBuffer:
        if freq_end is None:
            freq_end = freq_start
        raw_duration = duration.total_seconds()
        t = np.linspace(
            0,
            raw_duration,
            int(raw_duration * sample_rate),
            endpoint=True,
        )
        freq = freq_start + (freq_end - freq_start) * (t / raw_duration / 2)
        wave = np.sin(2 * np.pi * freq * t)

        return np.column_stack((wave, wave))  # type: ignore
