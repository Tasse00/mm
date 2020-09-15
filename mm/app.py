import logging
import os
import sys
from typing import List

from PyQt5 import QtWidgets

from mm.config import ConfigStore
from mm.indicator import Indicator
from mm.utils import dynamic_load
from mm.win import MainWindow

logger = logging.getLogger(__name__)


class Application:

    def __init__(self):
        self.home_dir = os.path.expanduser(os.environ.get("MM_HOME", "~/.mm"))
        self.config_file = os.path.join(self.home_dir, "config.json")
        self.custom_indicators_dir = os.path.join(self.home_dir, "indicators")

        self.init_mm_home()
        self.config_store = self.build_config_store()
        self.init_custom_indicators_supports()

    def init_mm_home(self):
        os.makedirs(self.home_dir, exist_ok=True)
        os.makedirs(self.custom_indicators_dir, exist_ok=True)

    def init_custom_indicators_supports(self):
        sys.path.append(self.custom_indicators_dir)

    def build_config_store(self) -> ConfigStore:
        config = ConfigStore(self.config_file)
        config.load_config()
        config.update_config_file()
        return config

    def connect_signals(self, win: MainWindow):
        def on_window_moved(x: int, y: int):
            self.config_store.config.pos_x = x
            self.config_store.config.pos_y = y
            self.config_store.update_config_file()

        win.SignalWindowMoved.connect(on_window_moved)

    def build_indicators(self) -> List[Indicator]:
        indicators = []
        for ic in self.config_store.config.indicators_settings:
            indicator_cls = dynamic_load(ic.type)
            params = indicator_cls.infer_preferred_params()
            params.update(ic.kwargs)
            indicators.append(indicator_cls(**params))

        return indicators

    def run(self):
        app = QtWidgets.QApplication(sys.argv)

        indicators = self.build_indicators()

        ex = MainWindow(indicators, self.config_store.config.global_settings)

        ex.move(self.config_store.config.pos_x, self.config_store.config.pos_y)
        self.connect_signals(ex)

        ex.startTimer(self.config_store.config.interval)
        ex.show()

        sys.exit(app.exec_())

