from abc import ABC, abstractmethod
from typing import Dict, Any

from PyQt5 import QtWidgets


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


