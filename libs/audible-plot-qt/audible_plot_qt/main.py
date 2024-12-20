import sys
from pathlib import Path

import audible_plot as ap
import numpy as np
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from audible_plot_qt.chart import ChartBackend

qml_dir = Path(__file__, "..")


def build_chart():
    # The range for sine and cosine functions is between -1 and 1
    func_range = ap.FixedRange(-1, 1)

    # This is our frequency range:
    freq_range = ap.FixedRange(300, 800)

    # Values for five periods of the functions:
    values = np.linspace(0, np.pi * 10, 100, endpoint=False)

    # Function calculations:
    sine = np.sin(values)
    cosine = np.cos(values)

    # Renderer objects are used to generate audio samples from values:
    sine_renderer = ap.PitchDataRenderer(
        frequency_range=freq_range,
        generator=ap.ToneGenerator(),
        volume=0.5,
        pan=-0.3,
        enable_transitions=True,
    )
    cosine_renderer = ap.PitchDataRenderer(
        frequency_range=freq_range,
        generator=ap.ToneGenerator(),
        volume=0.5,
        pan=0.3,
        enable_transitions=True,
    )
    values_renderer = ap.PitchDataRenderer(
        frequency_range=freq_range,
        generator=ap.ToneGenerator(),
        volume=0.5,
    )
    return ap.AudibleChart(
        # Here we put the data we've generated into the chart object for processing
        data=np.column_stack((values, sine, cosine)),
        # If a data key is not in the config, it won't be rendered.
        config=[
            # Dynamic ranged series
            ap.SeriesConfig(
                key=0,
                renderer=values_renderer,
            ),
            # Fixed range configs for sine and cosine functions
            ap.SeriesConfig(
                key=1,
                renderer=sine_renderer,
                range=func_range,
            ),
            ap.SeriesConfig(
                key=2,
                renderer=cosine_renderer,
                range=func_range,
            ),
        ],
        frequency_range=freq_range,
    )


def main():
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    def handle_warnings(warnings):
        for warning in warnings:
            print(warning.toString())  # Imprime los errores en stdout

    engine.warnings.connect(handle_warnings)
    qml_file = qml_dir / "Main.qml"
    backend = ChartBackend(build_chart())
    engine.rootContext().setContextProperty("backend", backend)
    engine.setOutputWarningsToStandardError
    engine.load(QUrl(qml_file.as_uri()))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
