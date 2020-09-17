from abc import abstractmethod
from typing import Dict, Any, List, Optional

from PyQt5 import QtWidgets, QtGui

from mm.config import IndicatorData
from mm.indicator import Indicator


class PercentHistoryWidget(QtWidgets.QWidget):

    def __init__(self,
                 val: Optional[List[float]] = None,
                 limit: float = 100.0,
                 fg_color: Optional[QtGui.QColor] = None,
                 bg_color: Optional[QtGui.QColor] = None,
                 *args, **kwargs):
        super(PercentHistoryWidget, self).__init__(*args, **kwargs)

        self.val = val or []
        self.limit = limit
        self.bg_color = bg_color or QtGui.QColor(0, 0, 0)
        self.fg_color = fg_color or QtGui.QColor(0, 255, 0)

    def setValue(self, val: List[float]):
        """
        :param val: [10.5, 20.5, 0, 100, ...] percent value list
        """
        self.val = val
        self.update()

    def setLimit(self, limit: float):
        self.limit = limit
        self.update()

    def setBgColor(self, color: QtGui.QColor):
        self.bg_color = color
        self.update()

    def setFgColor(self, color: QtGui.QColor):
        self.fg_color = color
        self.update()

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()


    def drawWidget(self, qp):
        size = self.size()
        w = size.width()
        h = size.height()

        step = (w / len(self.val)) if self.val else w

        qp.setPen(self.bg_color)
        qp.setBrush(self.bg_color)
        qp.drawRect(0, 0, w, h)

        qp.setPen(self.fg_color)
        qp.setBrush(self.fg_color)

        for idx, v in enumerate(self.val):
            v_h = int((v / self.limit) * h)
            qp.drawRect(step * idx, h - v_h, step, v_h)


class _PercentHistoryIndicator(Indicator):
    def __init__(self,
                 bg_color: str = "#000000",
                 fg_color: str = "#00FF00",
                 width: int = 80,
                 samples: int = 40):
        self.widget = PercentHistoryWidget(bg_color=QtGui.QColor(bg_color),
                                           fg_color=QtGui.QColor(fg_color))
        self.widget.setFixedWidth(width)
        self.samples = samples

    def get_widget(self) -> QtWidgets.QWidget:
        return self.widget

    def update(self, val: List[float]):
        self.widget.setValue(val[max(len(val) - self.samples, 0):])

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        return {}

    @classmethod
    @abstractmethod
    def infer_preferred_data(cls) -> IndicatorData:
        pass


class CpuIndicator(_PercentHistoryIndicator):

    @classmethod
    def infer_preferred_data(cls) -> IndicatorData:
        return IndicatorData(sensor="mm.sensor.simple.CpuSensor")


class MemoryIndicator(_PercentHistoryIndicator):

    @classmethod
    def infer_preferred_data(cls) -> IndicatorData:
        return IndicatorData(sensor="mm.sensor.simple.MemorySensor")




