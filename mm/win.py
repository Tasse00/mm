import logging
from dataclasses import dataclass
from typing import List

from PyQt5 import QtWidgets, QtCore, QtGui, Qt

from mm.indicator import Indicator

logger = logging.getLogger(__name__)


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

    def _get_font(self) -> QtGui.QFont:
        return QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)

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

    def timerEvent(self, e: QtCore.QTimerEvent) -> None:

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
