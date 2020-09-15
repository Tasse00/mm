from datetime import datetime
from typing import Dict, Any

import psutil
from PyQt5 import QtWidgets

from mm.indicator import Indicator
from mm.utils import convert_bytes_unit


class NetworkIndicator(Indicator):

    def __init__(self, netdev: str = 'eno1'):
        self.netdev = netdev
        self.lbl = QtWidgets.QLabel(text="")
        self.network_fmt = "Net \u21E3 {down: <10} \u21E1 {up: <10}"
        self.last_down = -1
        self.last_up = -1
        self.last_collect_at = datetime.now()
        self.last_down_speed = 0  # per second
        self.last_up_speed = 0  # per second

    def get_widget(self) -> QtWidgets.QWidget:
        return self.lbl

    def update(self):
        self.lbl.setText(self.network_fmt.format(
            down=convert_bytes_unit(self.last_down_speed) + '/s',
            up=convert_bytes_unit(self.last_up_speed) + '/s'
        ))

    def collect(self):

        with open("/proc/net/dev", "r") as fr:
            for line in fr:

                if self.netdev in line:
                    # eno1: 1488904609 1033998    0 14435    0     0          0      4277 40797706  510338    0    0    0     0       0          0
                    fields = line.split(":")[1].split()
                    new_down = int(fields[0])
                    new_up = int(fields[1])
                    curr_date = datetime.now()
                    if self.last_down != -1 and self.last_up != -1:
                        delta_down = new_down - self.last_down
                        delta_up = new_up - self.last_up
                        delta_time = curr_date - self.last_collect_at
                        self.last_up_speed = int(delta_up / delta_time.total_seconds())
                        self.last_down_speed = int(delta_down / delta_time.total_seconds())
                    self.last_collect_at = curr_date
                    self.last_down = new_down
                    self.last_up = new_up
                    break

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        params = {}
        candidates = {key: val for key, val in psutil.net_if_addrs().items() if
                      not key.startswith("v") and not key.startswith("docker")}
        for key, val in candidates.items():
            if val[0].address.startswith('192'):
                params['netdev'] = key
                break
        else:
            params['netdev'] = list(candidates.keys())[0]
        return params


class CpuIndicator(Indicator):

    def __init__(self):
        self.lbl = QtWidgets.QLabel(text="")
        self.percent = 0  # [0, 100]
        self.format = "CPU {: >3}%"

    def get_widget(self) -> QtWidgets.QWidget:
        return self.lbl

    def update(self):
        self.lbl.setText(self.format.format(round(self.percent)))

    def collect(self):
        self.percent = psutil.cpu_percent()

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        return {}


class MemoryIndicator(Indicator):

    def __init__(self):
        self.lbl = QtWidgets.QLabel(text="")
        self.percent = 0  # [0, 100]
        self.format = "MEM {: >3}%"

    def get_widget(self) -> QtWidgets.QWidget:
        return self.lbl

    def update(self):
        self.lbl.setText(self.format.format(round(self.percent)))

    def collect(self):
        self.percent = psutil.virtual_memory().percent

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        return {}


class DiskIndicator(Indicator):

    def __init__(self, partition: str = "/"):
        self.partition = partition
        self.lbl = QtWidgets.QLabel(text="")
        self.percent = 0  # [0, 100]
        self.format = "Disk {usage: >3}% W {write: <10} R {read: <10}"

        self.last_read_bytes = -1
        self.last_write_bytes = -1
        self.last_collect_at = datetime.now()

        self.read_speed = 0  # bytes per second
        self.write_speed = 0  # bytes per second

    def get_widget(self) -> QtWidgets.QWidget:
        return self.lbl

    def update(self):
        self.lbl.setText(self.format.format(usage=round(self.percent),
                                            write=convert_bytes_unit(self.write_speed) + '/s',
                                            read=convert_bytes_unit(self.read_speed) + '/s'))

    def collect(self):
        self.percent = psutil.disk_usage(self.partition).percent
        info = psutil.disk_io_counters()
        curr_date = datetime.now()
        curr_read_bytes = info.read_bytes
        curr_write_bytes = info.write_bytes

        if self.last_read_bytes != -1 and self.last_write_bytes != -1:
            delta_read_bytes = curr_read_bytes - self.last_read_bytes
            delta_write_bytes = curr_write_bytes - self.last_write_bytes

            delta_time = curr_date - self.last_collect_at

            self.read_speed = int(delta_read_bytes / delta_time.total_seconds())
            self.write_speed = int(delta_write_bytes / delta_time.total_seconds())

        self.last_read_bytes = curr_read_bytes
        self.last_write_bytes = curr_write_bytes
        self.last_collect_at = curr_date

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        params = {}
        params["partition"] = min([m[1] for m in psutil.disk_partitions()], key=lambda m: len(m))
        return params
