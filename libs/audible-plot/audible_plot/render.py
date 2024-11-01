from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Sequence

from audible_plot.generators import AudioBuffer, ToneGenerator
from audible_plot.utils import (
    AbstractValueRange,
    ValueMapper,
    adjust_volume,
    concat_samples,
    pan_audio,
)
import numpy as np


class AbstractDataRenderer(ABC):
    @abstractmethod
    def render(
        self,
        value: float,
        value_range: AbstractValueRange,
        duration: timedelta,
        sample_rate: float,
        frequency_range: AbstractValueRange,
    ) -> AudioBuffer:
        raise NotImplementedError

    def render_values(
        self,
        value_list: Sequence[float],
        value_range: AbstractValueRange,
        duration: timedelta,
        sample_rate: float,
        frequency_range: AbstractValueRange,
    ) -> AudioBuffer:
        return concat_samples(
            *list(
                self.render(
                    value=value,
                    value_range=value_range,
                    duration=duration,
                    sample_rate=sample_rate,
                    frequency_range=frequency_range,
                )
                for value in value_list
            ),
            sample_rate=sample_rate,
        )


class PitchDataRenderer(AbstractDataRenderer):
    def __init__(
        self,
        *,
        frequency_range: AbstractValueRange | None = None,
        generator: ToneGenerator,
        max_limit_perc: float = 0.1,
        enable_transitions: bool = False,
        pan: float = 0,
        volume: float = 1.0,
    ) -> None:
        super().__init__()
        self._freq_range = frequency_range
        self._max_limit_perc = max_limit_perc
        self._generator = generator
        self._old_value = None
        self._enable_transitions = enable_transitions
        self._pan = pan
        self._volume = volume

    def render(
        self,
        value: float,
        value_range: AbstractValueRange,
        duration: timedelta,
        sample_rate: float,
        frequency_range: AbstractValueRange,
    ) -> AudioBuffer:
        # If we have a locally defined frequency range, just ignore the provided one
        freq_range = self._freq_range or frequency_range
        mapper = ValueMapper(value_range, freq_range, self._max_limit_perc)

        return adjust_volume(
            pan_audio(
                self._generator.generate_sliding(
                    sample_rate=sample_rate,
                    duration=duration,
                    freq_points=[mapper.map_value(value)],
                ),
                self._pan,
            ),
            self._volume,
        )

    def render_values(
        self,
        value_list: Sequence[float],
        value_range: AbstractValueRange,
        duration: timedelta,
        sample_rate: float,
        frequency_range: AbstractValueRange,
    ) -> AudioBuffer:
        freq_range = self._freq_range or frequency_range
        mapper = ValueMapper(value_range, freq_range, self._max_limit_perc)
        # Duplicate the first value to ensure it is rendered correctly:
        value_list = list(value_list)
        if self._enable_transitions:
            value_list.insert(0, value_list[0])
        mapped_values = [mapper.map_value(value) for value in value_list]
        if self._enable_transitions:
            sample = self._generator.generate_sliding(
                sample_rate=sample_rate,
                duration=duration,
                freq_points=mapped_values,
            )
        else:
            sample = self._generator.generate_fixed(
                sample_rate=sample_rate,
                duration=duration,
                freq_points=mapped_values,
            )

        return adjust_volume(
            buffer=pan_audio(
                buffer=sample,
                pan=self._pan,
            ),
            volume=self._volume,
        )


class SilentRenderer(AbstractDataRenderer):
    def __init__(self) -> None:
        super().__init__()

    def render(
        self,
        value: float,
        value_range: AbstractValueRange,
        duration: timedelta,
        sample_rate: float,
        frequency_range: AbstractValueRange,
    ) -> AudioBuffer:
        return np.zeros((int(duration.total_seconds() * sample_rate), 2))  # type: ignore
