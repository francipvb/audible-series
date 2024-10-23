from __future__ import annotations

from datetime import timedelta
from functools import cached_property
from typing import Iterator, Literal, overload
import warnings
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
from audible_plot.generators import AudioBuffer
from audible_plot.player import AudioPlayer
from audible_plot.render import AbstractDataRenderer
from audible_plot.utils import AbstractValueRange, DynamicValueRange, FixedRange


class AudibleSeries(Sequence[float]):
    def __init__(
        self,
        data: Sequence[float]
        | np.ndarray[tuple[int], np.dtypes.Float64DType]
        | pd.Series,
        renderer: AbstractDataRenderer,
        name: str | None = None,
        value_range: AbstractValueRange | None = None,
        *,
        is_extra: bool = False,
    ) -> None:
        if isinstance(data, np.ndarray):
            self._data = data
        else:
            self._data = np.fromiter(data, np.dtypes.Float64DType)
        if not name:
            if isinstance(data, pd.Series):
                self._name = data.name
            else:
                raise TypeError("Name is required for non-series input.")
        else:
            self._name = name

        if value_range:
            self._value_range = value_range
        else:
            if is_extra:
                raise TypeError("Value range must be specified for extra series.")
            self._value_range = None

        self._renderer = renderer
        self._is_extra = is_extra
        self._chart = None

    @property
    def chart(self) -> AudibleChart:
        if self._chart is None:
            raise RuntimeError("Chart is not set yet.")
        return self._chart

    @chart.setter
    def chart(self, value: AudibleChart) -> None:
        if self._chart is not None:
            raise TypeError(
                "The same series object cannot be used in more than one chart."
            )
        self._chart = value

    @property
    def name(self):
        return str(self._name)

    @property
    def value_range(self) -> AbstractValueRange | None:
        return self._value_range

    @overload
    def __getitem__(self, idx: int) -> float: ...

    @overload
    def __getitem__(self, idx: slice) -> Sequence[float]: ...

    def __getitem__(self, idx: slice | int) -> float | Sequence[float]:
        return self._data[idx]  # type: ignore

    def __len__(self) -> int:
        return len(self._data)

    def window(self, start: int, end: int) -> AudibleSeriesWindow:
        return AudibleSeriesWindow(self, start, end)

    @property
    def renderer(self):
        return self._renderer

    @property
    def is_extra(self):
        return self._is_extra


class AudibleSeriesWindow(Sequence[float]):
    def __init__(self, series: AudibleSeries, start: int, end: int) -> None:
        self._series = series
        self._values = series[start:end]

        self._start = start
        self._end = end

    @property
    def value_range(self) -> AbstractValueRange:
        if self._series.value_range is not None:
            return self._series.value_range
        return DynamicValueRange(self._values)

    @overload
    def __getitem__(self, idx: int) -> float: ...
    @overload
    def __getitem__(self, idx: slice) -> Sequence[float]: ...

    def __getitem__(self, idx: int | slice) -> float | Sequence[float]:
        return self._values[idx]

    def __len__(self) -> int:
        return len(self._values)

    @property
    def name(self) -> str:
        return self._series.name

    @property
    def is_extra(self):
        return self._series.is_extra

    @property
    def renderer(self):
        return self._series.renderer


class AudibleChart:
    def __init__(
        self,
        *,
        series: Sequence[AudibleSeries],
        min_freq: float,
        max_freq: float,
    ) -> None:
        self._series: dict[str, AudibleSeries] = {}
        self._len = max(len(s) for s in list(series))
        for item in series:
            if item.name in self._series:
                warnings.warn(
                    f"Series with name {item.name!r} is being added twice. Note that this will replace the previous one."
                )
            if len(item) != self._len:
                raise ValueError(f"Series {item.name!r} is not of length {self._len}.")
            self._series[item.name] = item
            item.chart = self
        self._freq_range = FixedRange(min_freq, max_freq)
        self._player = AudioPlayer()

    @property
    def player(self):
        return self._player

    def window(self, start: int, end: int) -> AudibleChartWindow:
        return AudibleChartWindow(
            series=list(self._series.values()),
            start=start,
            end=end,
            player=self._player,
        )

    @property
    def extra(self):
        return {
            name: series for name, series in self._series.items() if not series.is_extra
        }

    @property
    def related(self):
        return {
            name: series for name, series in self._series.items() if series.is_extra
        }


class AudibleChartWindow(Mapping[str, AudibleSeriesWindow]):
    def __init__(
        self,
        series: list[AudibleSeries],
        start: int,
        end: int,
        player: AudioPlayer,
    ) -> None:
        self._series = {data.name: data.window(start, end) for data in series}
        self._start = start
        self._end = end
        self._player = player

    @property
    def extra(self) -> Mapping[str, AudibleSeriesWindow]:
        return {
            name: window for name, window in self._series.items() if window.is_extra
        }

    @cached_property
    def value_range(self):
        return DynamicValueRange(
            values=[
                value
                for series in self.related.values()
                for value in (
                    series.value_range.max_value,
                    series.value_range.min_value,
                )
            ]
        )

    @property
    def related(self):
        return {
            name: window for name, window in self._series.items() if not window.is_extra
        }

    def render(
        self, name: str | Literal["all"] = "all", position: slice | int | None = None
    ) -> AudioBuffer:
        if name == "all":
            return self._render_all(position)
        else:
            return self._render_single(name, position)

    def _render_single(
        self, name: str, position: int | slice | None = None
    ) -> AudioBuffer:
        if position is None:
            position = slice(None, None)
        if isinstance(position, int):
            position = slice(position, position + 1)
        series = self._series[name]
        if series.is_extra:
            value_range = series.value_range
        else:
            value_range = self.value_range

        return series.renderer.render_values(
            value_list=series[position],
            value_range=value_range,
            duration=timedelta(seconds=0.5),
        )

    def _render_all(self, position: slice | int | None = None) -> AudioBuffer:
        sample: AudioBuffer | None = None
        for series in self._series:
            rendered = self._render_single(series, position)
            if sample is None:
                sample = rendered
            else:
                sample = sample + rendered  # type: ignore

        if sample is None:
            return np.ndarray((0, 2), np.float64)

        sample_max = np.max(np.abs(sample))
        if sample_max > 1:
            return sample / sample_max
        return sample

    def play(self, name: str | Literal["all"], position: int | slice | None = None):
        sample = self.render(name, position)
        self._player.play_raw(sample)

    def __getitem__(self, key: str) -> AudibleSeriesWindow:
        return self._series[key]

    def __len__(self) -> int:
        return len(self._series)

    def __iter__(self) -> Iterator[str]:
        return iter(self._series)
