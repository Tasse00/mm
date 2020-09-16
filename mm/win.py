import logging
from pathlib import Path
from typing import Dict

from PyQt5 import QtWidgets, QtCore, QtGui, Qt

from mm.config import ConfigStore, IndicatorSettings
from mm.data import DataStore
from mm.indicator import Indicator
from mm.utils import dynamic_load

logger = logging.getLogger(__name__)


class MainWindow(QtWidgets.QWidget):
    # 带两个参数(整数,字符串)的信号
    SignalWindowMoved = QtCore.pyqtSignal(int, int)

    def __init__(self, config_store: ConfigStore, data_store: DataStore):
        super(MainWindow, self).__init__()

        self.config_store = config_store
        self.data_store = data_store

        self.indicators = self.build_indicators()

        self.setFont(self._get_font())
        self._init_frameless_transparent()
        self._init_ui()
        self.move(self.config_store.config.pos_x, self.config_store.config.pos_y)
        self.connect_signals()
        self.show()

        self.timer_id_indicator_settings_map: Dict[int, IndicatorSettings] = {}
        for indicator_settings in self.config_store.config.indicators_settings:
            timer_id = self.startTimer(indicator_settings.interval)
            self.timer_id_indicator_settings_map[timer_id] = indicator_settings

        # 初始渲染
        for indicator_settings in self.config_store.config.indicators_settings:
            self.render_indicator(indicator_settings)

    def connect_signals(self):
        def on_window_moved(x: int, y: int):
            self.config_store.config.pos_x = x
            self.config_store.config.pos_y = y
            self.config_store.update_config_file()

        self.SignalWindowMoved.connect(on_window_moved)

    def build_indicators(self) -> Dict[str, Indicator]:

        type_map = {}
        for ic in self.config_store.config.indicators_settings:
            indicator_cls = dynamic_load(ic.type)
            params = indicator_cls.infer_preferred_params()
            params.update(ic.kwargs)
            type_map[ic.type] = indicator_cls(**params)
        return type_map

    def _get_font(self) -> QtGui.QFont:
        return QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)

    def _init_frameless_transparent(self):
        self.setWindowFlags(Qt.Qt.FramelessWindowHint | Qt.Qt.WindowStaysOnTopHint | Qt.Qt.Tool)  # 无边框，置顶
        self.setAttribute(Qt.Qt.WA_TranslucentBackground)  # 透明背景色

    def _init_ui(self):

        from PyQt5.uic import loadUi
        ui_file = self.config_store.config.ui_file or Path(__file__).parent.joinpath("default.ui")
        loadUi(ui_file, self)

        for indicator in self.indicators.values():
            self.wrapper.layout().addWidget(indicator.get_widget())

    def mousePressEvent(self, event):
        if event.button() == Qt.Qt.LeftButton:
            self.m_flag = True
            self.m_Position = event.globalPos() - self.pos()  # 获取鼠标相对窗口的位置
            event.accept()
            self.setCursor(QtGui.QCursor(Qt.Qt.OpenHandCursor))  # 更改鼠标图标

    def mouseMoveEvent(self, e: QtGui.QMouseEvent):
        if Qt.Qt.LeftButton and self.m_flag:
            self.move(e.globalPos() - self.m_Position)  # 更改窗口位置
            e.accept()

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent):
        self.m_flag = False
        self.setCursor(QtGui.QCursor(Qt.Qt.ArrowCursor))

        self.SignalWindowMoved.emit(self.pos().x(), self.pos().y())

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if e.key() == QtCore.Qt.Key_Escape:
            QtCore.QCoreApplication.instance().quit()

    def render_indicator(self, indicator_settings: IndicatorSettings):
        indicator = self.indicators[indicator_settings.type]
        try:
            sequence = self.data_store.get_sequence(indicator_settings.data.sensor)
            indicator.update(sequence)
        except Exception as e:
            logger.error(f"{indicator.__class__.__name__} update failed: {e}")

    def timerEvent(self, e: QtCore.QTimerEvent) -> None:
        indicator_settings = self.timer_id_indicator_settings_map[e.timerId()]
        self.render_indicator(indicator_settings)
