import asyncio
from datetime import datetime
from typing import Dict, Any, Tuple

import psutil

from mm.config import SensorStoreSettings
from mm.sensor import Sensor


class CpuSensor(Sensor):
    DataType = float

    def sync_collect(self) -> float:
        return psutil.cpu_percent()

    async def collect(self) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.sync_collect)

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        return {}

    @classmethod
    def infer_preferred_store_settings(cls) -> SensorStoreSettings:
        return SensorStoreSettings(length=100)


class MemorySensor(Sensor):
    DataType = float

    def sync_collect(self) -> float:
        return psutil.virtual_memory().percent

    async def collect(self) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.sync_collect)

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        return {}

    @classmethod
    def infer_preferred_store_settings(cls) -> SensorStoreSettings:
        return SensorStoreSettings(length=100)


class DiskSensor(Sensor):
    DataType = Tuple[float, float, float]

    def __init__(self, partition: str = "/"):
        self.partition = partition

        self.last_read_bytes = -1
        self.last_write_bytes = -1
        self.last_collect_at = datetime.now()

    def sync_collect(self) -> DataType:
        usage = psutil.disk_usage(self.partition).percent
        read_speed, write_speed = 0, 0

        info = psutil.disk_io_counters()
        curr_date = datetime.now()

        if self.last_read_bytes != -1 and self.last_write_bytes != -1:
            duration = (curr_date - self.last_collect_at).total_seconds()
            read_speed = (info.read_bytes - self.last_read_bytes) / duration
            write_speed = (info.write_bytes - self.last_write_bytes) / duration

        self.last_read_bytes = info.read_bytes
        self.last_write_bytes = info.write_bytes
        self.last_collect_at = curr_date

        return usage, read_speed, write_speed

    async def collect(self) -> DataType:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.sync_collect)

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        params = {}
        params["partition"] = min([m[1] for m in psutil.disk_partitions()], key=lambda m: len(m))
        return params

    @classmethod
    def infer_preferred_store_settings(cls) -> SensorStoreSettings:
        return SensorStoreSettings(length=100)


class NetworkSensor(Sensor):
    DataType = Tuple[float, float]

    def __init__(self):
        self.last_bytes_recv = -1
        self.last_bytes_sent = -1
        self.last_collect_at = datetime.now()

    def sync_collect(self) -> DataType:
        send_rate, recv_rate = 0, 0
        info = psutil.net_io_counters()
        curr_datetime = datetime.now()

        if self.last_bytes_recv != -1 and self.last_bytes_sent != -1:
            duration = (curr_datetime - self.last_collect_at).total_seconds()
            send_rate = (info.bytes_sent - self.last_bytes_sent) / duration
            recv_rate = (info.bytes_recv - self.last_bytes_recv) / duration

        self.last_collect_at = curr_datetime
        self.last_bytes_recv = info.bytes_recv
        self.last_bytes_sent = info.bytes_sent

        return send_rate, recv_rate

    async def collect(self) -> DataType:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.sync_collect)

    @classmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        return {}

    @classmethod
    def infer_preferred_store_settings(cls) -> SensorStoreSettings:
        return SensorStoreSettings(length=100)
