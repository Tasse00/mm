import json
import logging
import os
import sys
from dataclasses import dataclass, field, asdict
from json import JSONDecodeError
from typing import Dict, Any, List

import dacite
from PyQt5 import QtWidgets

from mm.indicator.simple import CpuIndicator, MemoryIndicator, NetworkIndicator, DiskIndicator
from mm.utils import dynamic_load
from mm.win import MainWindow

logger = logging.getLogger(__name__)


class Application:
    @dataclass
    class Config:

        @dataclass
        class IndicatorSetting:
            type: str
            kwargs: Dict[str, Any] = field(default_factory=dict)

        interval: int = 2000  # 更新间隔, ms
        pos_x: int = 400
        pos_y: int = 400
        indicators_settings: List[IndicatorSetting] = field(default_factory=list)
        global_settings: MainWindow.GlobalSettings = field(default_factory=MainWindow.GlobalSettings)

    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.home_dir = os.path.expanduser(os.environ.get("MM_HOME", "~/.mm"))
        self.config_file = os.path.join(self.home_dir, "config.json")
        self.custom_indicators_dir = os.path.join(self.home_dir, "indicators")
        os.makedirs(self.home_dir, exist_ok=True)
        os.makedirs(self.custom_indicators_dir, exist_ok=True)

        self._init_custom_plugin_supportings()
        self.config = self._load_config()
        self._update_config_file()

    def _build_init_config(self):
        """创建初始配置"""
        indicator_configs = []

        for indicator_cls in [CpuIndicator, MemoryIndicator, NetworkIndicator, DiskIndicator]:
            indicator_configs.append(
                self.Config.IndicatorSetting(type=".".join([indicator_cls.__module__, indicator_cls.__qualname__]),
                                             kwargs=indicator_cls.infer_preferred_params()))
        return indicator_configs

    def _load_config(self) -> Config:
        try:
            with open(self.config_file) as fr:
                dat = json.load(fr)
            try:
                cfg = dacite.from_dict(self.Config, dat)
            except Exception as e:
                logger.error(f"load config failed: {e}")
                raise
        except (FileNotFoundError, JSONDecodeError):
            cfg = self.Config()
            cfg.indicators_settings = self._build_init_config()
        return cfg

    def _update_config_file(self):
        # 每次加载完后需要更新配置文件内容
        with open(self.config_file, "w") as fw:
            data = asdict(self.config)
            json.dump(data, fw, indent=4)

    def _init_custom_plugin_supportings(self):
        sys.path.append(self.custom_indicators_dir)

    def _on_window_moved(self, x: int, y: int):
        self.config.pos_x = x
        self.config.pos_y = y
        self._update_config_file()

    def run(self):

        indicators = []
        for ic in self.config.indicators_settings:
            indicator_cls = dynamic_load(ic.type)
            params = indicator_cls.infer_preferred_params()
            params.update(ic.kwargs)
            indicators.append(indicator_cls(**params))

        ex = MainWindow(indicators, self.config.global_settings)

        ex.SignalWindowMoved.connect(self._on_window_moved)
        ex.move(self.config.pos_x, self.config.pos_y)
        ex.startTimer(self.config.interval)
        ex.show()

        sys.exit(self.app.exec_())
