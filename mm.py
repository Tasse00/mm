import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from json import JSONDecodeError
from typing import List, Dict, Any

import dacite
import psutil
from PyQt5 import Qt, QtGui, QtWidgets, QtCore
from PyQt5.QtCore import QCoreApplication, QTimerEvent
from PyQt5.QtGui import QCursor, QFontDatabase, QFont, QMouseEvent
from PyQt5.QtWidgets import QApplication

logger = logging.getLogger(__name__)


def convert_bytes_unit(byte: int) -> str:
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    for unit in units:
        if byte < 1000:
            return f"{'%.2f' % byte}{unit}"
        byte /= 1024


class Indicator(ABC):

    @abstractmethod
    def get_widget(self) -> QtWidgets.QWidget:
        pass

    @abstractmethod
    def update(self):
        """update widget"""
        pass

    @abstractmethod
    def collect(self):
        """collect sensor data"""
        pass

    @classmethod
    @abstractmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        pass


class NetworkIndicator(Indicator):

    def __init__(self, netdev: str = 'eno1'):
        self.netdev = netdev
        self.lbl = QtWidgets.QLabel(text="")
        self.network_fmt = "Net \u21E3 {down: <10} \u21E1 {up: <10}"
        self.last_down = -1
        self.last_up = -1
        self.last_collect_at = datetime.now()
        self.last_down_speed = 0  # per second
        self.last_up_speed = 0  # per second

    def get_widget(self) -> QtWidgets.QWidget:
        return self.lbl

    def update(self):
        self.lbl.setText(self.network_fmt.format(
            down=convert_bytes_unit(self.last_down_speed) + '/s',
            up=convert_bytes_unit(self.last_up_speed) + '/s'
        ))

    def collect(self):

        with open("/proc/net/dev", "r") as fr:
            for line in fr:

                if self.netdev in line:
                    # eno1: 1488904609 1033998    0 14435    0     0          0      4277 40797706  510338    0    0    0     0       0          0
                    fields = line.split(":")[1].split()
                    new_down = int(fields[0])
                    new_up = int(fields[1])
                    curr_date = datetime.now()
                    if self.last_down != -1 and self.last_up != -1:
                        delta_down = new_down - self.last_down
                        delta_up = new_up - self.last_up
                        delta_time = curr_date - self.last_collect_at
                        self.last_up_speed = int(delta_up / delta_time.total_seconds())
                        self.last_down_speed = int(delta_down / delta_time.total_seconds())
                    self.last_collect_at = curr_date
                    self.last_down = new_down
                    self.last_up = new_up
                    break

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        params = {}
        candidates = {key: val for key, val in psutil.net_if_addrs().items() if
                      not key.startswith("v") and not key.startswith("docker")}
        for key, val in candidates.items():
            if val[0].address.startswith('192'):
                params['netdev'] = key
                break
        else:
            params['netdev'] = list(candidates.keys())[0]
        return params


class CpuIndicator(Indicator):

    def __init__(self):
        self.lbl = QtWidgets.QLabel(text="")
        self.percent = 0  # [0, 100]
        self.format = "CPU {: >3}%"

    def get_widget(self) -> QtWidgets.QWidget:
        return self.lbl

    def update(self):
        self.lbl.setText(self.format.format(round(self.percent)))

    def collect(self):
        self.percent = psutil.cpu_percent()

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        return {}


class MemoryIndicator(Indicator):

    def __init__(self):
        self.lbl = QtWidgets.QLabel(text="")
        self.percent = 0  # [0, 100]
        self.format = "MEM {: >3}%"

    def get_widget(self) -> QtWidgets.QWidget:
        return self.lbl

    def update(self):
        self.lbl.setText(self.format.format(round(self.percent)))

    def collect(self):
        self.percent = psutil.virtual_memory().percent

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        return {}


class DiskIndicator(Indicator):

    def __init__(self, partition: str = "/"):
        self.partition = partition
        self.lbl = QtWidgets.QLabel(text="")
        self.percent = 0  # [0, 100]
        self.format = "Disk {usage: >3}% W {write: <10} R {read: <10}"

        self.last_read_bytes = -1
        self.last_write_bytes = -1
        self.last_collect_at = datetime.now()

        self.read_speed = 0  # bytes per second
        self.write_speed = 0  # bytes per second

    def get_widget(self) -> QtWidgets.QWidget:
        return self.lbl

    def update(self):
        self.lbl.setText(self.format.format(usage=round(self.percent),
                                            write=convert_bytes_unit(self.write_speed) + '/s',
                                            read=convert_bytes_unit(self.read_speed) + '/s'))

    def collect(self):
        self.percent = psutil.disk_usage(self.partition).percent
        info = psutil.disk_io_counters()
        curr_date = datetime.now()
        curr_read_bytes = info.read_bytes
        curr_write_bytes = info.write_bytes

        if self.last_read_bytes != -1 and self.last_write_bytes != -1:
            delta_read_bytes = curr_read_bytes - self.last_read_bytes
            delta_write_bytes = curr_write_bytes - self.last_write_bytes

            delta_time = curr_date - self.last_collect_at

            self.read_speed = int(delta_read_bytes / delta_time.total_seconds())
            self.write_speed = int(delta_write_bytes / delta_time.total_seconds())

        self.last_read_bytes = curr_read_bytes
        self.last_write_bytes = curr_write_bytes
        self.last_collect_at = curr_date

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        params = {}
        params["partition"] = min([m[1] for m in psutil.disk_partitions()], key=lambda m: len(m))
        return params


class MainWindow(QtWidgets.QWidget):

    # 带两个参数(整数,字符串)的信号
    SignalWindowMoved = QtCore.pyqtSignal(int, int)

    @dataclass
    class GlobalSettings:
        color: str = "blue"

    def __init__(self, indicators: List[Indicator], global_settings: GlobalSettings):
        super(MainWindow, self).__init__()

        self.indicators = indicators

        self.setFont(self._get_font())

        self.setStyleSheet(f"color: {global_settings.color}")
        self._init_frameless_transparent()
        self._init_ui()

    def _get_font(self) -> QFont:
        return QFontDatabase.systemFont(QFontDatabase.FixedFont)

    def _init_frameless_transparent(self):
        self.setWindowFlags(Qt.Qt.FramelessWindowHint | Qt.Qt.WindowStaysOnTopHint | Qt.Qt.Tool)  # 无边框，置顶
        self.setAttribute(Qt.Qt.WA_TranslucentBackground)  # 透明背景色

    def _init_ui(self):

        layout = QtWidgets.QHBoxLayout()

        for indicator in self.indicators:
            layout.addWidget(indicator.get_widget())

        self.setLayout(layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.Qt.LeftButton:
            self.m_flag = True
            self.m_Position = event.globalPos() - self.pos()  # 获取鼠标相对窗口的位置
            event.accept()
            self.setCursor(QCursor(Qt.Qt.OpenHandCursor))  # 更改鼠标图标

    def mouseMoveEvent(self, QMouseEvent):
        if Qt.Qt.LeftButton and self.m_flag:
            self.move(QMouseEvent.globalPos() - self.m_Position)  # 更改窗口位置
            QMouseEvent.accept()

    def mouseReleaseEvent(self, a0:QMouseEvent):
        self.m_flag = False
        self.setCursor(QCursor(Qt.Qt.ArrowCursor))

        self.SignalWindowMoved.emit(self.pos().x(), self.pos().y())


    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if e.key() == QtCore.Qt.Key_Escape:
            QCoreApplication.instance().quit()

    def timerEvent(self, e: QTimerEvent) -> None:

        for indicator in self.indicators:
            try:
                indicator.collect()
            except Exception as e:
                logger.error(f"{indicator.__class__.__name__} collect failed: {e}")

        for indicator in self.indicators:
            try:
                indicator.update()
            except Exception as e:
                logger.error(f"{indicator.__class__.__name__} update failed: {e}")



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
        self.app = QApplication(sys.argv)
        self.config_file = os.path.expanduser(os.environ.get("MM_HOME", "~/.mm.json"))
        self.config = self.load_config(self.config_file)
        self.update_config_file(self.config_file, self.config)

    def _build_init_config(self):
        """创建初始配置"""
        indicator_configs = []

        for indicator_cls in [CpuIndicator, MemoryIndicator, NetworkIndicator, DiskIndicator]:
            indicator_configs.append(self.Config.IndicatorSetting(type=indicator_cls.__name__,
                                                                  kwargs=indicator_cls.infer_preferred_params()))
        return indicator_configs

    def load_config(self, config_file: str) -> Config:
        try:
            with open(config_file) as fr:
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

    def update_config_file(self, config_file: str, config: Config):
        # 每次加载完后需要更新配置文件内容
        with open(config_file, "w") as fw:
            data = asdict(config)
            json.dump(data, fw, indent=4)

    def _get_indicator_cls(self, type: str):
        # TODO dynamic import
        return {
            DiskIndicator.__name__: DiskIndicator,
            CpuIndicator.__name__: CpuIndicator,
            MemoryIndicator.__name__: MemoryIndicator,
            NetworkIndicator.__name__: NetworkIndicator,
        }[type]

    def on_window_moved(self, x: int, y: int):
        self.config.pos_x = x
        self.config.pos_y = y
        self.update_config_file(self.config_file, self.config)

    def run(self):

        indicators = []
        for ic in self.config.indicators_settings:
            indicator_cls = self._get_indicator_cls(ic.type)
            params = indicator_cls.infer_preferred_params()
            params.update(ic.kwargs)
            indicators.append(indicator_cls(**params))

        ex = MainWindow(indicators, self.config.global_settings)

        ex.SignalWindowMoved.connect(self.on_window_moved)
        ex.move(self.config.pos_x, self.config.pos_y)
        ex.startTimer(self.config.interval)
        ex.show()

        sys.exit(self.app.exec_())


if __name__ == "__main__":
    Application().run()
