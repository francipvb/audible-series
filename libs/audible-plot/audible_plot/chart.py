from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from functools import cached_property
from typing import Any, Hashable, Iterator, Literal, overload

import numpy as np
import pandas as pd

from audible_plot.generators import AudioBuffer
from audible_plot.player import AudioPlayer
from audible_plot.render import AbstractDataRenderer, SilentRenderer
from audible_plot.utils import AbstractValueRange, DynamicValueRange


class AudibleSeries:
    def __init__(
        self,
        data: pd.Series,
        renderer: AbstractDataRenderer,
        value_range: AbstractValueRange | None = None,
        is_extra: bool = False,
    ) -> None:
        self._data = data

        self._value_range = value_range

        self._renderer = renderer
        self._chart = None
        self._is_extra = is_extra or value_range is not None

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
    def key(self):
        return self._data.name

    @property
    def value_range(self) -> AbstractValueRange | None:
        return self._value_range

    @overload
    def __getitem__(self, idx: int) -> float: ...

    @overload
    def __getitem__(self, idx: slice) -> pd.Series: ...

    def __getitem__(self, idx: slice | int) -> float | pd.Series:
        return self._data[idx]  # type: ignore

    def __len__(self) -> int:
        return len(self._data)

    def window(self, position: slice) -> AudibleSeriesWindow:
        return AudibleSeriesWindow(self, position)

    @property
    def renderer(self):
        return self._renderer

    @property
    def is_extra(self):
        return self._is_extra

    def __str__(self) -> str:
        return str(self.key)

    def __repr__(self) -> str:
        return f"AudibleSeries({self})"


class AudibleSeriesWindow:
    def __init__(self, series: AudibleSeries, position: slice) -> None:
        self._series = series
        self._values = series[position]
        self._position = position

    @property
    def value_range(self) -> AbstractValueRange:
        if self._series.value_range is not None:
            return self._series.value_range
        return DynamicValueRange(list(self._values))

    @overload
    def __getitem__(self, idx: int) -> float: ...
    @overload
    def __getitem__(self, idx: slice) -> pd.Series: ...

    def __getitem__(self, idx: int | slice) -> float | pd.Series:
        return self._values.iloc[idx]

    def __len__(self) -> int:
        return len(self._values)

    @property
    def key(self):
        return self._series.key

    @property
    def is_extra(self):
        return self._series.is_extra

    @property
    def renderer(self):
        return self._series.renderer


@dataclass(kw_only=True, frozen=True)
class SeriesConfig:
    renderer: AbstractDataRenderer
    range: AbstractValueRange | None = None
    key: Hashable
    is_extra: bool = False


class AudibleChart:
    def __init__(
        self,
        *,
        data: pd.DataFrame | np.ndarray[Any, Any] | Sequence[Sequence[int | float]],
        config: Sequence[SeriesConfig] = [],
        sample_rate: float = 44100,
        frequency_range: AbstractValueRange,
    ) -> None:
        match data:
            case np.ndarray(shape=shape) | pd.DataFrame(shape=shape) if len(shape) != 2:
                raise TypeError(
                    "Only two-dimensional NumPY arrays and pandas dataframes are supported."
                )
            case np.ndarray():
                data = pd.DataFrame(data)
            case _:
                data = pd.DataFrame(data)

        if len(config) > len(data.columns):
            raise TypeError(
                "Config list length is greather than the number of data columns."
            )
        self._data = data
        self._player = AudioPlayer()
        self._config = {}
        for item in config:
            if item.key in self._config:
                warnings.warn(
                    f"Duplicate config key for {item.key!r}. The config will be replaced."
                )
            self._config[item.key] = item

        self._sample_rate = sample_rate
        self._frequency_range = frequency_range

    @property
    def player(self):
        return self._player

    @property
    def series(self) -> list[AudibleSeries]:
        def _map_series(series: pd.Series):
            config = self._config.get(series.name)
            if config is None:
                config = SeriesConfig(
                    key=series.name,
                    range=None,
                    renderer=SilentRenderer(),
                    # This is to avoid a bad range usage from the chart
                    is_extra=True,
                )

            return AudibleSeries(
                data=series,
                renderer=config.renderer,
                value_range=config.range,
                is_extra=config.is_extra,
            )

        return [_map_series(self._data[series]) for series in self._data.keys()]

    def window(self, window_bounds: slice | None = None) -> AudibleChartWindow:
        window_bounds = window_bounds or slice(None, None)
        return AudibleChartWindow(self, window_bounds, self._sample_rate)

    @property
    def extra(self):
        return {series.key: series for series in self.series if not series.is_extra}

    @property
    def related(self):
        return {series.key: series for series in self.series if series.is_extra}

    def __len__(self) -> int:
        return len(self._data)

    @property
    def frequency_range(self):
        return self._frequency_range


class AudibleChartWindow(Mapping[Hashable, AudibleSeriesWindow]):
    def __init__(
        self,
        chart: AudibleChart,
        position: slice,
        sample_rate: float,
    ) -> None:
        self._series = {data.key: data.window(position) for data in chart.series}
        self._player = chart.player
        self._sample_rate = sample_rate
        self._freq_range = chart.frequency_range

    @property
    def extra(self) -> Mapping[Hashable, AudibleSeriesWindow]:
        return {
            name: window for name, window in self._series.items() if window.is_extra
        }

    @property
    def series(self):
        return list(self._series.values())

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
        self,
        names: Hashable | Sequence[Hashable] | Literal["all"] = "all",
        position: slice | int | None = None,
        duration: timedelta = timedelta(seconds=0.5),
    ) -> AudioBuffer:
        if names == "all":
            names = [w.key for w in self.series]
        elif not isinstance(names, (tuple, list, set)):
            names = [names]

        sample: AudioBuffer | None = None
        for name in names:
            rendered = self._render_single(duration, name, position)
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

    def _render_single(
        self, duration: timedelta, name: Hashable, position: int | slice | None = None
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
            value_list=list(series[position]),
            value_range=value_range,
            duration=duration,
            sample_rate=self._sample_rate,
            frequency_range=self._freq_range,
        )

    def play(
        self,
        names: Hashable | Sequence[Hashable] | Literal["all"] = "all",
        position: int | slice | None = None,
        duration: timedelta = timedelta(seconds=0.5),
    ):
        sample = self.render(
            names,
            position,
            duration,
        )
        self._player.play_raw(sample)

    def __getitem__(self, key: Hashable) -> AudibleSeriesWindow:
        return self._series[key]

    def __len__(self) -> int:
        return len(self._series)

    def __iter__(self) -> Iterator[Hashable]:
        return iter(self._series)
