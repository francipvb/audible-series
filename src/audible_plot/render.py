from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Sequence

from audible_plot.generators import AbstractToneGenerator, AudioBuffer
from audible_plot.utils import (
    AbstractValueRange,
    ValueMapper,
    adjust_volume,
    concat_samples,
    pan_audio,
)


class AbstractDataRenderer(ABC):
    @abstractmethod
    def render(
        self,
        value: float,
        value_range: AbstractValueRange,
        duration: timedelta,
    ) -> AudioBuffer:
        raise NotImplementedError

    def render_values(
        self,
        value_list: Sequence[float],
        value_range: AbstractValueRange,
        duration: timedelta,
    ) -> AudioBuffer:
        return concat_samples(
            *list(self.render(value, value_range, duration) for value in value_list),
            sample_rate=44100,
        )


class PitchDataRenderer(AbstractDataRenderer):
    def __init__(
        self,
        frequency_range: AbstractValueRange,
        generator: AbstractToneGenerator,
        max_limit_perc: float = 0.1,
        sample_rate: float = 44100,
        enable_transitions: bool = False,
        pan: float = 0,
        volume: float = 1.0,
    ) -> None:
        super().__init__()
        self._freq_range = frequency_range
        self._max_limit_perc = max_limit_perc
        self._sample_rate = sample_rate
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
    ) -> AudioBuffer:
        if self._old_value is None:
            self._old_value = value
        mapper = ValueMapper(value_range, self._freq_range, self._max_limit_perc)
        if self._enable_transitions:
            start_freq = mapper.map_value(self._old_value)
        else:
            start_freq = mapper.map_value(value)
        end_freq = mapper.map_value(value)
        self._old_value = value

        return adjust_volume(
            pan_audio(
                self._generator.generate_wave(
                    sample_rate=self._sample_rate,
                    duration=duration,
                    freq_start=start_freq,
                    freq_end=end_freq,
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
    ) -> AudioBuffer:
        self._old_value = None
        return super().render_values(value_list, value_range, duration)
