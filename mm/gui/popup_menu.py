from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMenu


class PopupMenu(QMenu):

    sig_quit = pyqtSignal()
    sig_settings = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(PopupMenu, self).__init__(*args, **kwargs)

        self.act_quit = QtWidgets.QAction('退出', parent=self)
        self.act_settings = QtWidgets.QAction('设置', parent=self)
        self.act_quit.triggered.connect(self.sig_quit.emit)
        self.act_settings.triggered.connect(self.sig_settings.emit)

        self.addAction(self.act_quit)
        self.addAction(self.act_settings)
