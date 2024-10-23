from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Sequence, override
import numpy as np

from .generators import AudioBuffer


class AbstractValueRange(ABC):
    @property
    @abstractmethod
    def min_value(self) -> float:
        raise NotImplementedError

    @property
    @abstractmethod
    def max_value(self) -> float:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.min_value!r}, {self.max_value!r})"


class FixedRange(AbstractValueRange):
    def __init__(self, min_value: float, max_value: float) -> None:
        super().__init__()
        self._min = min_value
        self._max = max_value

    @property
    @override
    def min_value(self):
        return self._min

    @property
    @override
    def max_value(self):
        return self._max


class DynamicValueRange(AbstractValueRange):
    def __init__(self, values: Sequence[float]) -> None:
        super().__init__()
        self._values = values

    @property
    def min_value(self):
        return min(*self._values)

    @property
    @override
    def max_value(self):
        return max(*self._values)


class ValueMapper:
    def __init__(
        self,
        source: AbstractValueRange,
        target: AbstractValueRange,
        max_limit: float | None = None,
    ) -> None:
        self._source = source
        self._target = target
        self._limit_value = max_limit

    @property
    def source(self):
        return self._source

    @property
    def target(self):
        return self._target

    def map_value(self, value: float) -> float:
        source_delta = self.source.max_value - self.source.min_value
        target_delta = self.target.max_value - self.target.min_value
        return_value = (
            value - self.source.min_value
        ) / source_delta * target_delta + self.target.min_value
        if self._limit_value is not None:
            if return_value > self.target.max_value:
                return_value = min(
                    return_value,
                    self.target.max_value + target_delta * self._limit_value,
                )
            elif value < self.target.min_value:
                return_value = max(
                    return_value,
                    self.target.min_value - target_delta * self._limit_value,
                )
        return return_value

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.source!r}, {self.target!r}, {self._limit_value!r})"


def pan_audio(buffer: AudioBuffer, pan: float) -> AudioBuffer:
    left = buffer[:, 0]
    right = buffer[:, 1]
    return np.column_stack(
        (
            left * np.cos((1 + pan) * np.pi / 4),
            right * np.sin((1 + pan) * np.pi / 4),
        ),
    )  # type: ignore


def concat_samples(
    *buffers: AudioBuffer,
    sample_rate: float,
    transition_duration: timedelta = timedelta(milliseconds=100),
) -> AudioBuffer:
    final_buffer = np.ndarray((0, 2), np.float64)

    if len(buffers) == 0:
        return final_buffer

    # Concatenar cada buffer asegurando transiciones suaves
    for buffer in buffers:
        if len(final_buffer) == 0:
            final_buffer = buffer
            continue

        final_buffer = np.vstack(
            (
                final_buffer,
                buffer,
            )
        )

    return final_buffer  # type: ignore


def adjust_volume(buffer: AudioBuffer, volume: float) -> AudioBuffer:
    return buffer * volume  # type: ignore
