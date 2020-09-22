from PyQt5 import Qt, QtGui, QtCore
from PyQt5.QtWidgets import QWidget


class Draggable(QWidget):
    # 带两个参数(整数,字符串)的信号
    sig_windowed_moved = QtCore.pyqtSignal(int, int)

    def __init__(self, *args, **kwargs):
        super(Draggable, self).__init__(*args, **kwargs)

        self._m_flag = False
        self._m_position = QtCore.QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.Qt.LeftButton:
            self._m_flag = True
            self._m_position = event.globalPos() - self.pos()  # 获取鼠标相对窗口的位置
            event.accept()
            self.setCursor(QtGui.QCursor(Qt.Qt.OpenHandCursor))  # 更改鼠标图标

    def mouseMoveEvent(self, e: QtGui.QMouseEvent):
        if Qt.Qt.LeftButton and self._m_flag:
            self.move(e.globalPos() - self._m_position)  # 更改窗口位置
            e.accept()

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent):
        self._m_flag = False
        self.setCursor(QtGui.QCursor(Qt.Qt.ArrowCursor))
        self.sig_windowed_moved.emit(self.pos().x(), self.pos().y())
