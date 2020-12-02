from typing import Dict, Any, List, Tuple, Optional

from PyQt5 import QtWidgets

from mm.config import IndicatorData
from mm.indicator import Indicator
from mm.utils import convert_bytes_unit


class NetworkIndicator(Indicator):

    def __init__(self):
        self.lbl = QtWidgets.QLabel(text="")
        self.network_fmt = "Net \u21E3 {down: <10} \u21E1 {up: <10}"

    def get_widget(self) -> QtWidgets.QWidget:
        return self.lbl

    def update(self, val: List[Tuple[float, float]]):
        send_rate, recv_rate = val[-1] if val else (0, 0)
        self.lbl.setText(self.network_fmt.format(
            down=convert_bytes_unit(recv_rate) + '/s',
            up=convert_bytes_unit(send_rate) + '/s'
        ))

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        return {}

    @classmethod
    def infer_preferred_data(cls) -> IndicatorData:
        return IndicatorData(sensor="mm.sensor.simple.NetworkSensor")


class CpuIndicator(Indicator):

    def __init__(self):
        self.lbl = QtWidgets.QLabel(text="")
        self.format = "CPU {: >3}%"

    def get_widget(self) -> QtWidgets.QWidget:
        return self.lbl

    def update(self, val: List[float]):
        percent = val[-1] if val else 0
        self.lbl.setText(self.format.format(round(percent)))

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        return {}

    @classmethod
    def infer_preferred_data(cls) -> IndicatorData:
        return IndicatorData(sensor="mm.sensor.simple.CpuSensor")


class MemoryIndicator(Indicator):

    def __init__(self):
        self.lbl = QtWidgets.QLabel(text="")
        self.format = "MEM {: >3}%"

    def get_widget(self) -> QtWidgets.QWidget:
        return self.lbl

    def update(self, val: List[float]):
        percent = val[-1] if val else 0
        self.lbl.setText(self.format.format(round(percent)))

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        return {}

    @classmethod
    def infer_preferred_data(cls) -> IndicatorData:
        return IndicatorData(sensor="mm.sensor.simple.MemorySensor")


class DiskIndicator(Indicator):

    def __init__(self, ):
        self.lbl = QtWidgets.QLabel(text="")
        self.format = "Disk {usage: >3}% W {write: <10} R {read: <10}"

    def get_widget(self) -> QtWidgets.QWidget:
        return self.lbl

    def update(self, val: List[Tuple[float, float, float]]):
        usage, read_speed, write_speed = val[-1] if val else (0, 0, 0)
        self.lbl.setText(self.format.format(usage=round(usage),
                                            write=convert_bytes_unit(write_speed) + '/s',
                                            read=convert_bytes_unit(read_speed) + '/s'))

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        return {}

    @classmethod
    def infer_preferred_data(cls) -> IndicatorData:
        return IndicatorData(sensor="mm.sensor.simple.DiskSensor")

class SingleDatasourceAdapter:

    def __init__(self, location_in_sample: Optional[str] = None):
        self.location_in_sample = location_in_sample
    
    def extract_value(self, values: Any):

        if self.location_in_sample:
            return eval("values{}".format(self.location_in_sample))
        else:
            return values

class TextIndicator(Indicator, SingleDatasourceAdapter):

    def __init__(self, 
                 format: str = "{value: >3}", 
                 location_in_sample: Optional[str] = None,
                 val_convert: str = 'none'):
        """
        :param val_convert: 值转换
                            none                无缩放
                            bytes               1024缩放，并跟上容量单位
                            bytes_per_second    1024缩放，并跟上速度单位
        """
        SingleDatasourceAdapter.__init__(self, location_in_sample)
        Indicator.__init__(self)

        self.format = format
        self.val_convert = val_convert
        self.label = QtWidgets.QLabel(text="")

        assert val_convert in ["none", "bytes", "bytes_per_second"]
    
    def get_widget(self) -> QtWidgets.QWidget:
        return self.label
    
    def update(self, val: List[Any]):

        if len(val) == 0:
            return
        
        value = self.extract_value(val[-1])

        if self.val_convert == 'bytes':
            value = convert_bytes_unit(value)
        elif self.val_convert == 'bytes_per_second':
            value = convert_bytes_unit(value) + '/s'
        self.label.setText(self.format.format(value=value))
        