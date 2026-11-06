import sys
from pathlib import Path
# from telemetrix import telemetrix
from utils.myTelemetrix import MyTelemetrix
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QIODevice


class MyApp:
    def __init__(self):
        script_dir = Path(__file__).resolve().parent
        ui_path = script_dir / "app.ui"

        ui_file = QFile(str(ui_path))
        ui_file.open(QIODevice.ReadOnly)
        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        # INIT Widget Functions
        self.window.turnSlider.valueChanged.connect(self.on_value_changed)
        self.window.turnSlider.sliderReleased.connect(self.reset_to_neutral)


    def show(self):
        self.window.show()

    # UI LOGIC
    def on_value_changed(self, value):
        # Calculate offset from center (49)
        # Negative = Left/Backward, Positive = Right/Forward
        offset = value - 49
        self.window.turnStatus.setText(f"Slider Value: {value} | Command Offset: {offset:+d}")

    def reset_to_neutral(self):
        # Instantly snap back to 49 on release
        self.slider.setValue(49)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    conn_tele = MyTelemetrix()
    tele_app = MyApp()
    tele_app.show()
    app.aboutToQuit.connect(conn_tele.close)
    sys.exit(app.exec())