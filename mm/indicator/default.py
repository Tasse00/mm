from typing import Dict, Any, List, Tuple

import psutil
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPainter, QFont, QColor

from mm.indicator import Indicator


class StackBar(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

        self.setFixedWidth(40)
        self.setFixedHeight(40)

    def initUI(self):
        self.valueLimit = 100
        self.layers = []

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

    def setLayers(self, layers: List[Tuple[int, Tuple[int, int, int]]]):
        self.layers = layers

    def setLimit(self, value: int):
        self.valueLimit = value

    def drawWidget(self, qp: QPainter):
        size = self.size()
        w = size.width()
        h = size.height()

        start_h = 0
        for val, color in self.layers:
            layer_h = int((val / self.valueLimit) * h)

            qp.setPen(QColor(0,0,0))
            qp.setBrush(QColor(0,0,0))
            qp.drawRect(0, 0, w, h)

            qp.setPen(QColor(*color))
            qp.setBrush(QColor(*color))

            qp.drawRect(0, h - start_h, w, layer_h)
            start_h += layer_h


class CpuIndicator(Indicator):

    def __init__(self):
        self.bar = StackBar()

        self.percent = 0  # [0, 100]

    def get_widget(self) -> QtWidgets.QWidget:
        return self.bar

    def update(self):
        self.bar.setLayers([
            (self.percent, (0, 255, 0))
        ])

    # self.lbl.setText(self.format.format(round(self.percent)))

    def collect(self):
        self.percent = psutil.cpu_percent()


    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        return {}
