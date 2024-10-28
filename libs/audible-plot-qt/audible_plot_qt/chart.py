from __future__ import annotations

import builtins
from typing import Any, Dict, Hashable

import audible_plot as ap
from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
    Signal,
    Slot,
)


class ChartSlice(QObject):
    def __init__(self, slice_: slice, parent: QObject | None = None) -> None:
        super().__init__(parent)
        assert slice_.start is not None
        assert slice_.stop is not None
        assert slice_.start >= 0
        assert slice_.stop >= 0
        assert slice_.stop >= slice_.start
        self.slice = slice_

    @Property(int)
    def start(self):
        return self.slice.start

    @Property(int)
    def end(self):
        return self.slice.stop

    @Property(int)
    def center(self):
        return self.start + self.size // 2  # type: ignore

    @Property(int)
    def size(self):
        return self.end - self.start  # type: ignore


class SeriesWindowBackend(QObject):
    nameChanged = Signal()
    sizeChanged = Signal()

    def __init__(
        self,
        window: ap.AudibleSeriesWindow,
        chart_window: ChartWindowBackend,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._window = window
        self._chart_window = chart_window

    @Property(str, notify=nameChanged)  # type: ignore
    def key(self):
        key = self._window.key
        if isinstance(key, int):
            # Keys are indexes, sum one and format it as a string:
            return f"Series {key+1}"
        return str(key)

    @Slot()
    def play(self):
        return self._chart_window.play_by_key(self._window.key)

    def get_size(self) -> int:
        return len(self._window)

    size = Property(int, get_size, notify=sizeChanged)  # type: ignore

    @Slot(int, result=float)
    def at(self, pos: int) -> float:
        return float(self._window[pos])


class ChartWindowBackend(QAbstractListModel):
    SeriesRole = Qt.ItemDataRole.UserRole + 1

    def __init__(
        self,
        window: ap.AudibleChartWindow,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._window = window
        self._series = [
            SeriesWindowBackend(window, self) for window in self._window.series
        ]

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._series)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid() or index.row() >= len(self._series) or index.row() < 0:
            return None
        match role:
            case self.SeriesRole:
                return self._series[index.row()]
            case _:
                return None

    def roleNames(self) -> Dict[int, Any]:
        return {self.SeriesRole: b"series"}

    def play_by_key(self, key: Hashable):
        self._window.play(key)

    @Slot()
    def play(self):
        return self._window.play()

    @Slot(int, result=SeriesWindowBackend)
    def getByPosition(self, pos: int):
        return self._series[pos]


class ChartBackend(QObject):
    onSliceChanged = Signal(ChartSlice, name="sliceChanged")

    def __init__(
        self,
        chart: ap.AudibleChart,
        initial_size: int = 10,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._chart = chart
        self._slice = None
        position_end = len(chart)
        if len(chart) < initial_size:
            initial_slice = slice(0, len(chart))
        else:
            initial_slice = slice(position_end - initial_size, position_end)
        self._set_slice(initial_slice)
        self._window = None

    @Property(ChartSlice, notify=onSliceChanged)  # type: ignore
    def slice(self):  # type: ignore
        return self._slice

    def _set_slice(self, slice_: builtins.slice | ChartSlice):
        if slice_ is self._slice:
            return
        if isinstance(slice_, ChartSlice):
            self._slice = slice
        else:
            self._slice = ChartSlice(slice_)
        self._window = None
        self.onSliceChanged.emit(self._slice)

    @Property(QObject, notify=onSliceChanged)  # type: ignore
    def window(self):
        if not self._window:
            self._window = ChartWindowBackend(self._chart.window(self.slice.slice))  # type: ignore
        return self._window

    @Slot()
    def moveLeft(self):
        current_slice: slice = self.slice.slice  # type: ignore
        if current_slice.start == 0:
            return
        slice_size = current_slice.stop - current_slice.start
        new_slice = slice(current_slice.start - slice_size, current_slice.start)
        if new_slice.start <= 0:
            new_slice = slice(0, slice_size)
        self._set_slice(new_slice)

    @Slot()
    def moveRight(self):
        current_slice: slice = self.slice.slice  # type: ignore
        if current_slice.stop == len(self._chart):
            return
        slice_size = current_slice.stop - current_slice.start
        new_slice = slice(current_slice.stop, current_slice.stop + slice_size)
        if new_slice.stop >= len(self._chart):
            new_slice = slice(len(self._chart) - slice_size, len(self._chart))
        self._set_slice(new_slice)
