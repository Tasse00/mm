from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List

from PyQt5 import QtWidgets


@dataclass
class IndicatorData:
    sensor: str

class Indicator(ABC):

    @abstractmethod
    def get_widget(self) -> QtWidgets.QWidget:
        pass

    @abstractmethod
    def update(self, val: List[Any]):
        """DataStore会依据配置传递值过来"""
        pass

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        """推测建议的实例化参数"""
        return {}

    @classmethod
    def infer_preferred_data(cls) -> IndicatorData:
        """推测建议的数据源"""
        pass
