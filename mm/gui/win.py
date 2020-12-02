import logging
from pathlib import Path
from typing import Dict, List

from PyQt5 import QtCore, QtGui, Qt

from mm.config import SettingsStore, IndicatorSettings, SensorSettings
from mm.data import DataStore
from mm.gui.draggable import Draggable
from mm.gui.popup_menu import PopupMenu
from mm.gui.settings import SettingsDialog
from mm.indicator import Indicator
from mm.utils import dynamic_load, relaunch

logger = logging.getLogger(__name__)


class MainWindow(Draggable):

    def __init__(self, config_store: SettingsStore, data_store: DataStore):
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

        self.setting_dialog = self.init_settings_dialog()
        self.popup_menu = self.init_popup_menu(self.setting_dialog)

        # 右键菜单
        self.setContextMenuPolicy(Qt.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda: self.popup_menu.exec_(QtGui.QCursor.pos()))

    def quit(self):
        self.hide()
        QtCore.QCoreApplication.instance().quit()

    def init_popup_menu(self, settings_dialog: SettingsDialog):
        popup_menu = PopupMenu(parent=self)
        popup_menu.sig_quit.connect(self.quit)
        popup_menu.sig_settings.connect(settings_dialog.exec_)
        return popup_menu

    def init_settings_dialog(self):

        def update_settings(sensor_settings_list: List[SensorSettings],
                            indicator_settings_list: List[IndicatorSettings]):
            sd.close()

            self.config_store.config.sensors_settings = sensor_settings_list
            self.config_store.config.indicators_settings = indicator_settings_list
            self.config_store.update_config_file()

            relaunch()

        sd = SettingsDialog(config_store=self.config_store, parent=self)
        sd.sig_config_updated.connect(update_settings)
        return sd

    def connect_signals(self):
        def on_window_moved(x: int, y: int):
            self.config_store.config.pos_x = x
            self.config_store.config.pos_y = y
            self.config_store.update_config_file()

        self.sig_windowed_moved.connect(on_window_moved)

    def build_indicators(self) -> Dict[str, Indicator]:
        type_map = {}
        for ic in self.config_store.config.indicators_settings:
            indicator_cls = dynamic_load(ic.type)
            params = indicator_cls.infer_preferred_params()
            params.update(ic.kwargs)
            type_map[ic.name] = indicator_cls(**params)
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

    def render_indicator(self, indicator_settings: IndicatorSettings):
        indicator = self.indicators[indicator_settings.name]
        try:
            sequence = self.data_store.get_sequence(indicator_settings.data.sensor)
            indicator.update(sequence)
        except Exception as e:
            logger.error(f"{indicator.__class__.__name__} update failed: {e}")

    def timerEvent(self, e: QtCore.QTimerEvent) -> None:
        indicator_settings = self.timer_id_indicator_settings_map[e.timerId()]
        self.render_indicator(indicator_settings)
